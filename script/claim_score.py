def calculate_claim_score(study_scores):
    number_of_studies = len(study_scores)

    if number_of_studies == 0:
        return 0

    total = sum(study_scores)
    claim_score = total / number_of_studies
    return claim_score