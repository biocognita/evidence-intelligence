from data_loader import load_database
from claim_loader import load_claim_database

from validator import validate_database
from claim_validator import validate_claim_database

from grouping_claim import grouping_claim
from claim_report import generate_claim_report
from claim_evaluation import evaluate_claim


def run_evidence_pipeline():

    # ----------------------------
    # 1. Load databases
    # ----------------------------

    data = load_database()
    print("\nDATABASE LOADED SUCCESSFULLY")

    claim_data = load_claim_database()
    print("CLAIMS LOADED SUCCESSFULLY")


    # ----------------------------
    # 2. Validate databases
    # ----------------------------

    database_report = validate_database(data)

    claim_validation = validate_claim_database(
        claim_data,
        data
    )


    # ----------------------------
    # 3. Group studies by claims
    # ----------------------------

    claim_groups = grouping_claim(
        data,
        claim_data
    )  


    # ----------------------------
    # 4. Evaluate every claim
    # ----------------------------

    for claim_id, claim, studies in claim_groups:

        if claim_id in claim_validation["orphan_claim_ids"]:
            print("\n----------------------------")
            print("Skipping:", claim_id, "(no matching entry in claims sheet)")
            continue

        print("\n----------------------------")
        print("Evaluating:", claim_id)
        # Score individual studies, combine into a claim score,
        # and interpret the confidence level
        claim_score, confidence, study_scores = evaluate_claim(
            claim,
            studies
        )
        print(
            "Claim Score:",
            round(claim_score, 2)
        )
        print(
            "Confidence:",
            confidence
        )
        # Generate user-facing report
        generate_claim_report(
            claim,
            studies,
            round(claim_score, 2),
            confidence,
            study_scores
        )


def main():

    run_evidence_pipeline()


if __name__ == "__main__":
    main()