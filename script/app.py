from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import gc
import json
import os
import time

from data_loader import load_database
from claim_loader import load_claim_database
from claim_lookup import build_claims_index
from claim_evaluation import evaluate_claim
from claim_report import generate_claim_report, build_study_breakdown

WEBSITE_DIR = os.path.join(os.path.dirname(__file__), "..", "website")

app = Flask(__name__, static_folder=WEBSITE_DIR, static_url_path="")
CORS(app)

CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", 300))  # refresh sheet data every 5 minutes

_cache = {
    "study_data": None,
    "claim_data": None,
    "claims_by_id": None,
    "study_by_claim": None,
    "loaded_at": 0
}


def get_data():
    """Refresh the cached data + indexes from Google Sheets if the cache is
    missing or older than CACHE_TTL_SECONDS. Returns the cache dict."""

    now = time.time()
    is_stale = (now - _cache["loaded_at"]) > CACHE_TTL_SECONDS

    if _cache["study_data"] is None or is_stale:
        study_data = load_database()
        claim_data = load_claim_database()

        _cache["study_data"] = study_data
        _cache["claim_data"] = claim_data
        _cache["claims_by_id"] = build_claims_index(claim_data)
        # One indexed copy of the study data (instead of per-group copies) so
        # memory stays ~1x even with millions of studies.
        _cache["study_by_claim"] = study_data.set_index("Claim ID", drop=False)
        _cache["loaded_at"] = now

    return _cache


@app.route("/")
def home():
    return send_from_directory(WEBSITE_DIR, "index.html")


@app.route("/reportpage.html")
def report_page():
    return send_from_directory(WEBSITE_DIR, "reportpage.html")


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
    with its confidence score, evidence strength and per-study breakdown
    (computed from the cached study data), and per-request temporaries are
    released before the response goes out.
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

    # Lazy filtering: only rows containing the query (case-insensitive) are
    # materialized. astype("string") keeps this working even if the
    # searched column is a low-cardinality column (compressed to category
    # dtype), and regex=False treats the query as literal text (a query
    # like "C+" must not be interpreted as a regular expression).
    if search_column == "All fields":
        # OR together matches from every searchable text column.
        masks = [
            claims[col].astype("string").str.contains(query, case=False, na=False, regex=False)
            for col in ALL_FIELDS_COLUMNS
        ]
        mask = masks[0]
        for other in masks[1:]:
            mask = mask | other
        matched = claims[mask]
        del masks
    else:
        matched = claims[
            claims[search_column]
            .astype("string")
            .str.contains(query, case=False, na=False, regex=False)
        ]

    total = len(matched)

    # Slice BEFORE serializing so only the requested page is ever
    # materialized as JSON (the memory win from pagination).
    page = matched.iloc[offset:offset + limit]

    # to_json() emits `null` for NaN/empty cells (browsers reject the raw
    # `NaN` literal that to_dict() would leave in the payload).
    results = json.loads(page.to_json(orient="records"))

    # Enrich each result with its confidence score + strength + per-study
    # breakdown using the cached study index (no extra Google Sheets
    # calls). Skip claims with no studies rather than failing the search.
    for record in results:
        claim_id = record.get("Claim ID")
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
        record["confidence_score"] = round(score, 2)
        record["evidence_strength"] = strength
        record["study_breakdown"] = build_study_breakdown(studies, study_scores)
        del studies, study_scores

    # Aggressive memory reclaim on the 512 MB Render free tier.
    del matched, page, claims, data
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

    # Aggressive memory reclaim on the 512 MB Render free tier: drop the
    # per-request temporaries now that the JSON payload is built, and ask
    # the garbage collector to release any cyclic garbage immediately.
    del studies, study_scores, claim
    gc.collect()

    return jsonify(report)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
