# Google Sheets source
SPREADSHEET_ID = "1MEh7BxFm_m8nxgvhy-XA_4YD9aGM6fA0Wb1nAO4zPIg"
STUDY_DATABASE_GID = "945515403"
CLAIM_DATABASE_GID = "1370727994"

# ----- Study quality scoring -----
# Points awarded for each "Study Type Score" value
STUDY_TYPE_POINTS = {
    5: 20,
    4: 15,
    3: 10,
    2: 5,
    1: 1,
}
# Sheet encoding for the flags: the spreadsheet stores these as numbers
RANDOMIZED_VALUE = 1
RANDOMIZED_POINTS = 10
BLINDED_VALUE = 1
BLINDED_POINTS = 10
PLACEBO_CONTROLLED_VALUE = 3
PLACEBO_CONTROLLED_POINTS = 10
SAMPLE_SIZE_SCORE_CAP = 10  # max points from sample size (log10 scale)

# ----- Confidence interpretation -----
HIGH_CONFIDENCE_THRESHOLD = 80
MODERATE_CONFIDENCE_THRESHOLD = 50
HIGH_CONFIDENCE_LABEL = "High confidence"
MODERATE_CONFIDENCE_LABEL = "Moderate confidence"
LOW_CONFIDENCE_LABEL = "Low confidence"

# ----- Claim ID format -----
CLAIM_ID_PATTERN = r"^C[0-9]{4}$"

# ----- Claim database validation -----
REQUIRED_CLAIM_COLUMNS = [
    "Claim ID",
    "Claim",
    "Intervention",
    "Outcome",
    "Population"
]
