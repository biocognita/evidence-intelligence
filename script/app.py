from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
import time

from data_loader import load_database
from claim_loader import load_claim_database
from claim_lookup import get_claim
from claim_linker import get_studies_for_claim
from quality_score import calculate_quality_score
from claim_score import calculate_claim_score
from interpretation import interpret_claim_score
from claim_report import generate_claim_report

WEBSITE_DIR = os.path.join(os.path.dirname(__file__), "..", "website")

app = Flask(__name__, static_folder=WEBSITE_DIR, static_url_path="")
CORS(app)

CACHE_TTL_SECONDS = 5 * 60  # refresh sheet data every 5 minutes

_cache = {
    "study_data": None,
    "claim_data": None,
    "loaded_at": 0
}


def get_data():
    """Return (study_data, claim_data), refreshing from Google Sheets
    if the cache is missing or older than CACHE_TTL_SECONDS."""

    now = time.time()
    is_stale = (now - _cache["loaded_at"]) > CACHE_TTL_SECONDS

    if _cache["study_data"] is None or is_stale:
        _cache["study_data"] = load_database()
        _cache["claim_data"] = load_claim_database()
        _cache["loaded_at"] = now

    return _cache["study_data"], _cache["claim_data"]


@app.route("/")
def home():
    return send_from_directory(WEBSITE_DIR, "index.html")


@app.route("/reportpage.html")
def report_page():
    return send_from_directory(WEBSITE_DIR, "reportpage.html")


@app.route("/claim/<claim_id>")
def get_claim_report(claim_id):

    study_data, claim_data = get_data()

    claim = get_claim(claim_data, claim_id)

    if claim is None:
        return jsonify({"error": f"Claim {claim_id} not found"}), 404

    studies = get_studies_for_claim(study_data, claim_id)

    study_scores = []

    for _, study in studies.iterrows():
        score = calculate_quality_score(study)
        study_scores.append(score)

    confidence_score = calculate_claim_score(study_scores)

    confidence = interpret_claim_score(confidence_score)

    report = generate_claim_report(
        claim,
        studies,
        confidence_score,
        confidence,
        study_scores
    )

    return jsonify(report)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)