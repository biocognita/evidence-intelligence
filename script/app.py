from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
import time

from data_loader import load_database
from claim_loader import load_claim_database
from claim_lookup import build_claims_index
from claim_evaluation import evaluate_claim
from claim_report import generate_claim_report

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
        studies = data["study_by_claim"].loc[claim_id]
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

    return jsonify(report)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
