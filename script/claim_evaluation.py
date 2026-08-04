from quality_score import calculate_quality_scores
from claim_score import calculate_claim_score
from interpretation import interpret_claim_score


def evaluate_claim(claim, studies):
    """Score every study for a claim, combine the scores into a claim
    score, and interpret it as a confidence level.

    Returns (claim_score, confidence, study_scores).
    """
    study_scores = calculate_quality_scores(studies).tolist()

    claim_score = calculate_claim_score(study_scores)
    confidence = interpret_claim_score(claim_score)

    return claim_score, confidence, study_scores
