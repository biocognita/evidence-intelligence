from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import gc
import json
import os
import re
import threading
import time

CONTACT_EMAIL = "biocognita@gmail.com"
# Loose per-IP throttle so the free-tier email quota can't be drained by
# one visitor spamming the form.
_CONTACT_RATE_LIMIT = 10
_CONTACT_WINDOW_SECONDS = 3600
_contact_attempts = {}  # ip -> [timestamps]
_contact_lock = threading.Lock()

CONTACT_TOPICS = [
    "General question", "Claim correction", "Study suggestion", "Feedback", "Other",
]
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

from data_loader import load_database
from claim_loader import load_claim_database
from claim_lookup import build_claims_index
from claim_evaluation import evaluate_claim
from claim_report import generate_claim_report, build_study_breakdown

WEBSITE_DIR = os.path.join(os.path.dirname(__file__), "..", "website")

app = Flask(__name__, static_folder=WEBSITE_DIR, static_url_path="")
CORS(app)

CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", 300))  # refresh sheet data every 5 minutes

# Columns users may search via ?col=. Kept explicit so the front-end
# always matches what the backend will accept.
SEARCHABLE_COLUMNS = ["Claim", "Intervention", "Outcome", "Population"]

# A bare query (?q= without ?col=) matches ANY of these text fields, so
# "melatonin" finds the claim, and "1683" finds claims citing studies
# with that sample size. The claim ID itself is included.
ALL_FIELDS_COLUMNS = ["Claim ID"] + SEARCHABLE_COLUMNS

# Pagination defaults for /search so huge result sets are never all
# serialized in one response.
SEARCH_DEFAULT_LIMIT = 20
SEARCH_MAX_LIMIT = 100

# Upper bound on the per-claim memo caches. Scores only change when the
# sheet refreshes, so memoizing them makes repeat lookups dict hits — but
# a crawler hitting thousands of distinct claim IDs must not grow memory
# unboundedly within a 5-minute generation, so the caches are capped and
# reset on every refresh anyway.
MAX_MEMOIZED_CLAIMS = 1000

_cache = {
    "study_data": None,
    "claim_data": None,
    "claims_by_id": None,
    "study_by_claim": None,
    # claim column -> string-dtype Series, pre-cast ONCE at refresh time.
    # .str.contains() needs string dtype (the cached frames are stored as
    # memory-shrinking category), and astype() per request is pure Python
    # — the single biggest CPU waste on Render's 0.1 core.
    "search_columns": None,
    # claim ID -> {confidence_score, evidence_strength, study_breakdown}
    "claim_enrichment": None,
    # claim ID -> full report dict (built once per cache generation)
    "claim_reports": None,
    "loaded_at": 0,
}

# Guards get_data() so two gunicorn threads can't both download the sheet
# on the same expiry (double Google rate-limit usage + double CPU cost).
_refresh_lock = threading.Lock()


def get_data():
    """Return the cache, refreshing from Google Sheets only when it is
    missing or older than CACHE_TTL_SECONDS. Double-checked locking keeps
    concurrent requests from triggering duplicate refreshes."""
    now = time.time()
    is_fresh = (
        _cache["claim_data"] is not None
        and (now - _cache["loaded_at"]) <= CACHE_TTL_SECONDS
    )
    if is_fresh:
        return _cache

    with _refresh_lock:
        # Another thread may have refreshed while we waited for the lock.
        now = time.time()
        if (
            _cache["claim_data"] is not None
            and (now - _cache["loaded_at"]) <= CACHE_TTL_SECONDS
        ):
            return _cache

        study_data = load_database()
        claim_data = load_claim_database()

        _cache["study_data"] = study_data
        _cache["claim_data"] = claim_data
        _cache["claims_by_id"] = build_claims_index(claim_data)
        # One indexed copy of the study data (instead of per-group copies) so
        # memory stays ~1x even with millions of studies.
        _cache["study_by_claim"] = study_data.set_index("Claim ID", drop=False)
        # Pre-cast the searchable columns to string dtype once here instead
        # of on every request. This duplicates the claims table's text as
        # uncompressed strings (RAM cost ~= one extra claims-table copy —
        # negligible at the current scale, and it removes the per-request
        # astype() that dominated CPU on the 0.1 core).
        _cache["search_columns"] = {
            col: claim_data[col].astype("string")
            for col in ALL_FIELDS_COLUMNS
        }
        # Fresh memo caches per generation — scores are deterministic until
        # the sheet data changes, so never recompute them per request.
        _cache["claim_enrichment"] = {}
        _cache["claim_reports"] = {}
        _cache["loaded_at"] = time.time()

    return _cache


@app.route("/")
def home():
    return send_from_directory(WEBSITE_DIR, "index.html")


@app.route("/reportpage.html")
def report_page():
    return send_from_directory(WEBSITE_DIR, "reportpage.html")


@app.route("/contactpage.html")
def contact_page():
    return send_from_directory(WEBSITE_DIR, "contactpage.html")


def _clamp_int(value, default, minimum, maximum):
    """Parse an int query param safely; return `default` on garbage."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(parsed, maximum))


@app.route("/search")
def search_claims():
    """Case-insensitive substring search over a claim text column.

    Examples:
      /search?q=melatonin                       -> search the Claim text
      /search?q=melatonin&col=Intervention      -> search the Intervention column
      /search?q=melatonin&limit=10&offset=20    -> paginate the results

    Only the matched page is serialized to JSON. Each result is enriched
    with its confidence score, evidence strength and per-study breakdown —
    served from the per-claim memo cache after the first hit, so repeat
    searches (and search-as-you-type) are pure dict lookups, not re-scoring
    every study on Render's 0.1 core.
    """

    query = (request.args.get("q") or "").strip()

    if not query:
        return jsonify({"error": "Missing query parameter: ?q=<text>"}), 400

    # Validate the requested column. If ?col= is missing or names a column
    # we don't know, search across ALL text fields (never trust client
    # input blindly — fall back to the broad search, not to nothing).
    requested_col = (request.args.get("col") or "").strip()
    if requested_col in SEARCHABLE_COLUMNS:
        search_column = requested_col
    else:
        search_column = "All fields"

    # Pagination: clamp so a huge or negative limit can't blow up memory.
    limit = _clamp_int(request.args.get("limit"), SEARCH_DEFAULT_LIMIT, 1, SEARCH_MAX_LIMIT)
    offset = _clamp_int(request.args.get("offset"), 0, 0, 10_000)

    try:
        data = get_data()
    except Exception:
        app.logger.exception("Failed to load evidence database from Google Sheets")
        return jsonify({
            "error": "Couldn't load the evidence database from Google Sheets. "
                     "Please try again later."
        }), 503

    claims = data["claim_data"]
    search_columns = data["search_columns"]  # pre-cast string Series

    # Lazy filtering: only rows containing the query (case-insensitive) are
    # materialized. The columns are already string dtype (cast once at
    # refresh), and regex=False treats the query as literal text (a query
    # like "C+" must not be interpreted as a regular expression).
    if search_column == "All fields":
        # OR together matches from every searchable text column.
        mask = search_columns[ALL_FIELDS_COLUMNS[0]].str.contains(
            query, case=False, na=False, regex=False
        )
        for col in ALL_FIELDS_COLUMNS[1:]:
            mask = mask | search_columns[col].str.contains(
                query, case=False, na=False, regex=False
            )
        matched = claims[mask]
    else:
        matched = claims[
            search_columns[search_column].str.contains(
                query, case=False, na=False, regex=False
            )
        ]

    total = len(matched)

    # Slice BEFORE serializing so only the requested page is ever
    # materialized as JSON (the memory win from pagination).
    page = matched.iloc[offset:offset + limit]

    # to_json() emits `null` for NaN/empty cells (browsers reject the raw
    # `NaN` literal that to_dict() would leave in the payload).
    results = json.loads(page.to_json(orient="records"))

    # Enrich each result from the memo cache, computing on first encounter
    # only. Skip claims with no studies rather than failing the search.
    enrichment = data["claim_enrichment"]
    for record in results:
        claim_id = record.get("Claim ID")
        cached = enrichment.get(claim_id)
        if cached is not None:
            record.update(cached)
            continue
        try:
            # .loc[[claim_id]] (double brackets) always yields a DataFrame,
            # even for claims with exactly one study (.loc[claim_id] would
            # return a bare Series and break vectorized scoring).
            studies = data["study_by_claim"].loc[[claim_id]]
        except KeyError:
            continue
        try:
            score, strength, study_scores = evaluate_claim(record, studies)
        except Exception:
            continue
        cached = {
            "confidence_score": round(score, 2),
            "evidence_strength": strength,
            "study_breakdown": build_study_breakdown(studies, study_scores),
        }
        enrichment[claim_id] = cached
        record.update(cached)

    if len(enrichment) > MAX_MEMOIZED_CLAIMS:
        enrichment.clear()

    # Aggressive memory reclaim on the 512 MB Render free tier.
    del matched, page, claims, search_columns
    gc.collect()

    return jsonify({
        "query": query,
        "column": search_column,
        "count": len(results),
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + len(results)) < total,
        "results": results
    })


@app.route("/contact", methods=["POST"])
def contact_form():
    """Receive the contact-page form and email it to CONTACT_EMAIL.

    Sends via Resend (RESEND_API_KEY env var). If the key isn't set the
    request still succeeds from the visitor's point of view, and the
    message is logged so nothing is silently lost.
    """
    data = request.get_json(silent=True) or {}
    # Newlines in name/topic would break the email subject — flatten them.
    name = str(data.get("name") or "").replace("\r", " ").replace("\n", " ").strip()
    email = str(data.get("email") or "").strip()
    topic = str(data.get("topic") or "General question").strip()
    message = str(data.get("message") or "").strip()
    website = str(data.get("website") or "").strip()

    # Honeypot: bots fill the hidden "website" field — drop silently.
    if website:
        return jsonify({"ok": True})

    if not name or not email or not message:
        return jsonify({"error": "Please fill in your name, email and message."}), 400
    if not _EMAIL_RE.match(email):
        return jsonify({"error": "Please enter a valid email address."}), 400
    if len(message) > 5000 or len(name) > 100 or len(email) > 200:
        return jsonify({"error": "Message is too long."}), 400
    # Only ever echo back a known topic, never an arbitrary client string.
    if topic not in CONTACT_TOPICS:
        topic = "General question"

    # Per-IP rate limit (best-effort, in-memory). Checked before sending so
    # a spammer can't drain the free-tier quota; timestamps are only added
    # once a send actually succeeds (see below).
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    now = time.time()
    with _contact_lock:
        recent = [t for t in _contact_attempts.get(ip, []) if now - t < _CONTACT_WINDOW_SECONDS]
        if len(recent) >= _CONTACT_RATE_LIMIT:
            return jsonify({"error": "Too many messages — please try again later."}), 429
        _contact_attempts[ip] = recent

    api_key = os.environ.get("RESEND_API_KEY")
    if api_key:
        try:
            import resend
            resend.api_key = api_key
            resend.Emails.send({
                "from": "Evidence Intelligence <onboarding@resend.dev>",
                "to": [CONTACT_EMAIL],
                "reply_to": email,
                "subject": f"[Evidence Intelligence] {topic} — from {name}",
                "text": f"Name: {name}\nEmail: {email}\nTopic: {topic}\n\n{message}",
            })
        except Exception:
            app.logger.exception("Failed to send contact email via Resend")
            return jsonify({"error": "Couldn't send your message — please try again later."}), 502
        # Only count a send once it succeeded, so a transient Resend failure
        # doesn't burn the visitor's quota.
        with _contact_lock:
            recent = _contact_attempts.get(ip, [])
            recent.append(now)
            _contact_attempts[ip] = recent
        # Prune IPs with no recent attempts so the dict can't grow forever
        # on the 512 MB tier.
        with _contact_lock:
            for stale_ip in [k for k, v in _contact_attempts.items() if not v]:
                del _contact_attempts[stale_ip]
    else:
        # No key configured: keep the visitor's success experience and
        # log the message so it's recoverable.
        app.logger.warning(
            "RESEND_API_KEY not set — contact form dropped. %s <%s> topic=%s: %s",
            name, email, topic, message[:200]
        )

    return jsonify({"ok": True})


@app.route("/claim/<claim_id>")
def get_claim_report(claim_id):

    # Normalize so e.g. /claim/c0001 works the same as /claim/C0001.
    # No strict format check: the sheet is the source of truth, so any
    # claim ID that exists there resolves, and anything else 404s.
    claim_id = claim_id.strip().upper()

    try:
        data = get_data()
    except Exception:
        app.logger.exception("Failed to load evidence database from Google Sheets")
        return jsonify({
            "error": "Couldn't load the evidence database from Google Sheets. "
                     "Please try again later."
        }), 503

    claim = data["claims_by_id"].get(claim_id)

    if claim is None:
        return jsonify({"error": f"Claim {claim_id} not found"}), 404

    # Serve the fully-built report from the memo cache when available —
    # the report only depends on cached data, so it is identical (and
    # expensive to rebuild) within a cache generation.
    report = data["claim_reports"].get(claim_id)

    if report is None:
        try:
            # .loc[[claim_id]] (double brackets) always yields a DataFrame,
            # even for claims with exactly one study (.loc[claim_id] would
            # return a bare Series and break vectorized scoring).
            studies = data["study_by_claim"].loc[[claim_id]]
        except KeyError:
            studies = data["study_data"].iloc[0:0]

        confidence_score, confidence, study_scores = evaluate_claim(claim, studies)

        report = generate_claim_report(
            claim,
            studies,
            round(confidence_score, 2),
            confidence,
            study_scores
        )
        data["claim_reports"][claim_id] = report

        if len(data["claim_reports"]) > MAX_MEMOIZED_CLAIMS:
            data["claim_reports"].clear()

        # Aggressive memory reclaim on the 512 MB Render free tier: drop the
        # per-request temporaries now that the JSON payload is built, and ask
        # the garbage collector to release any cyclic garbage immediately.
        del studies, study_scores, claim, confidence_score, confidence
        gc.collect()

    return jsonify(report)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
