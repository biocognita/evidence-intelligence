def generate_claim_report(claim, studies, confidence_score, confidence, study_scores=None):

    study_ids = studies["Study ID"].tolist()

    if study_scores is not None:
        study_breakdown = [
            {
                "study_id": study_id,
                "quality_score": round(score, 2)
            }
            for study_id, score in zip(study_ids, study_scores)
        ]
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