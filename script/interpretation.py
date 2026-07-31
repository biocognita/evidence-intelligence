#Confidence Score to level
def interpret_claim_score(score):
    if score >= 80:
        return "High confidence"
    elif score >= 50:
        return "Moderate confidence"
    else:
        return "Low confidence"