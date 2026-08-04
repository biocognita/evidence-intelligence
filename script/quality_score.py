import math

import numpy as np
import pandas as pd

from config import (
    STUDY_TYPE_POINTS,
    RANDOMIZED_VALUE,
    RANDOMIZED_POINTS,
    BLINDED_VALUE,
    BLINDED_POINTS,
    PLACEBO_CONTROLLED_VALUE,
    PLACEBO_CONTROLLED_POINTS,
    SAMPLE_SIZE_SCORE_CAP,
)


def sample_size_score(sample_size):
    """Points for sample size on a log10 scale, capped."""
    if pd.isna(sample_size):
        return 0
    if not isinstance(sample_size, (int, float)):
        # e.g. "TBD" entered in the sheet - treat as no sample size info
        return 0
    if sample_size <= 0:
        return 0
    return min(math.log10(sample_size), SAMPLE_SIZE_SCORE_CAP)


def calculate_quality_score(study):
    """Score a single study (a pandas Series). Kept for small/compat use."""
    score = 0
    score += STUDY_TYPE_POINTS.get(study["Study Type Score"], 0)
    if study["Randomized"] == RANDOMIZED_VALUE:
        score += RANDOMIZED_POINTS
    if study["Blinded"] == BLINDED_VALUE:
        score += BLINDED_POINTS
    if study["Placebo controlled"] == PLACEBO_CONTROLLED_VALUE:
        score += PLACEBO_CONTROLLED_POINTS
    score += sample_size_score(study["Sample size"])
    return score


def calculate_quality_scores(studies):
    """Vectorized version of calculate_quality_score for a whole DataFrame.
    Produces identical scores but runs far faster on large study sets."""
    study_type = studies["Study Type Score"]

    levels = sorted(STUDY_TYPE_POINTS.items(), key=lambda item: item[0], reverse=True)
    conditions = [study_type == level for level, _ in levels]
    choices = [points for _, points in levels]
    type_points = np.select(conditions, choices, default=0)

    randomized = (studies["Randomized"] == RANDOMIZED_VALUE).to_numpy()
    blinded = (studies["Blinded"] == BLINDED_VALUE).to_numpy()
    placebo = (studies["Placebo controlled"] == PLACEBO_CONTROLLED_VALUE).to_numpy()
    flag_points = (
        randomized * RANDOMIZED_POINTS
        + blinded * BLINDED_POINTS
        + placebo * PLACEBO_CONTROLLED_POINTS
    )

    sample = studies["Sample size"]
    is_numeric = sample.map(lambda value: isinstance(value, (int, float)))
    numeric = pd.to_numeric(sample, errors="coerce")
    with np.errstate(divide="ignore", invalid="ignore"):
        logs = np.where((numeric > 0), np.log10(numeric), 0.0)
    logs = np.minimum(logs, SAMPLE_SIZE_SCORE_CAP)
    sample_scores = np.where(is_numeric, logs, 0.0)

    scores = type_points + flag_points + sample_scores
    return pd.Series(scores, index=studies.index)
