from config import (
    HIGH_CONFIDENCE_THRESHOLD,
    MODERATE_CONFIDENCE_THRESHOLD,
    HIGH_CONFIDENCE_LABEL,
    MODERATE_CONFIDENCE_LABEL,
    LOW_CONFIDENCE_LABEL,
)


# Confidence Score to level
def interpret_claim_score(score):
    if score >= HIGH_CONFIDENCE_THRESHOLD:
        return HIGH_CONFIDENCE_LABEL
    elif score >= MODERATE_CONFIDENCE_THRESHOLD:
        return MODERATE_CONFIDENCE_LABEL
    else:
        return LOW_CONFIDENCE_LABEL
