def _study_summary(study_row):
    """Build a one-line human summary of a study from the raw columns
    (sample size, publication year, design flags, outcome direction).
    Missing/NA cells are skipped so the line never says 'nan'."""
    parts = []

    randomized = study_row.get("Randomized")
    if randomized is not None and str(randomized).strip() not in ("", "nan", "NaN", "NA"):
        try:
            if int(randomized) == 1:
                parts.append("Randomized")
        except (TypeError, ValueError):
            pass

    sample = study_row.get("Sample size")
    if sample is not None and str(sample).strip() not in ("", "nan", "NaN", "NA"):
        try:
            parts.append(f"n={int(sample)}")
        except (TypeError, ValueError):
            pass

    year = study_row.get("Publication year")
    if year is not None and str(year).strip() not in ("", "nan", "NaN", "NA"):
        try:
            parts.append(str(int(year)))
        except (TypeError, ValueError):
            pass

    outcome = study_row.get("Outcome (+/0/-)")
    if outcome is not None and str(outcome).strip() not in ("", "nan", "NaN", "NA"):
        try:
            direction = int(outcome)
            label = {1: "positive outcome", 0: "neutral outcome", -1: "negative outcome"}.get(direction)
            if label:
                parts.append(label)
        except (TypeError, ValueError):
            pass

    return " · ".join(parts) or "Study details not available"


def build_study_breakdown(studies, study_scores):
    """Build the per-study breakdown list, one entry per supporting study.
    Shared by /claim and /search so both pages show identical data."""
    records = studies.to_dict("records")
    return [
        {
            "study_id": study_id,
            "quality_score": round(score, 2),
            "summary": _study_summary(record)
        }
        for study_id, score, record in zip(
            studies["Study ID"].tolist(), study_scores, records
        )
    ]


def generate_claim_report(claim, studies, confidence_score, confidence, study_scores=None):

    study_ids = studies["Study ID"].tolist()

    if study_scores is not None:
        study_breakdown = build_study_breakdown(studies, study_scores)
    else:
        study_breakdown = None

    report = {
        "claim": claim["Claim"],
        "intervention": claim["Intervention"],
        "population": claim["Population"],
        "confidence_score": confidence_score,
        "evidence_strength": confidence,
        "supporting_studies": study_ids,
        "study_breakdown": study_breakdown
    }

    return report