from data_loader import load_database
from claim_loader import load_claim_database
from claim_lookup import get_claim
from claim_report import generate_claim_report
from claim_evaluation import evaluate_claim
from claim_menu import print_main_menu
from config import CLAIM_ID_PATTERN

import re


def print_report(report):
    print("\n========================================")
    print("CLAIM REPORT")
    print("========================================")
    print(f"Claim: {report['claim']}")
    print(f"Intervention: {report['intervention']}")
    print(f"Population: {report['population']}")
    print(f"Confidence Score: {report['confidence_score']}/100")
    print(f"Evidence Strength: {report['evidence_strength']}")
    print("Supporting Studies: " + ", ".join(report["supporting_studies"]))
    if report["study_breakdown"]:
        print("Study Breakdown:")
        for study in report["study_breakdown"]:
            print(f"  {study['study_id']}: {study['quality_score']}")
    print("========================================")


def search_claim(data, claim_data):

    claim_id = input("\nSearch Claim ID: ").strip().upper()

    if claim_id == "":
        print("Please enter a Claim ID.")
        return

    if not re.match(CLAIM_ID_PATTERN, claim_id):
        print("Invalid Claim ID format.")
        return

    claim = get_claim(claim_data, claim_id)

    if claim is None:
        return

    studies = data[data["Claim ID"] == claim_id]

    if studies.empty:
        print(f"\nNo studies are linked to {claim_id} yet.")
        input("\nPress Enter to return to the main menu...")
        return

    claim_score, confidence, study_scores = evaluate_claim(claim, studies)

    report = generate_claim_report(
        claim,
        studies,
        round(claim_score, 2),
        confidence,
        study_scores
    )

    print_report(report)

    input("\nPress Enter to return to the main menu...")


def main():

    # Load databases once
    data = load_database()
    claim_data = load_claim_database()

    while True:

        print_main_menu()

        choice = input("Select an option: ").strip()

        # ------------------------------------
        # Option 1 - Search a Claim
        # ------------------------------------
        if choice == "1":

            search_claim(data, claim_data)

        # ------------------------------------
        # Option 2 - Compare Claims
        # ------------------------------------
        elif choice == "2":

            print("\nCompare Claims")
            print("Feature coming soon!")

            input("\nPress Enter to return to the main menu...")

        # ------------------------------------
        # Option 3 - View All Claims
        # ------------------------------------
        elif choice == "3":

            print("\nAvailable Claims")
            print("----------------")

            for index, row in claim_data.iterrows():
                print(f"{row['Claim ID']} - {row['Claim']}")

            input("\nPress Enter to return to the main menu...")

        # ------------------------------------
        # Option 4 - Exit
        # ------------------------------------
        elif choice == "4":

            print("\nThank you for using Evidence Intelligence.")
            break

        # ------------------------------------
        # Invalid Menu Choice
        # ------------------------------------
        else:

            print("\nInvalid option. Please choose 1-4.")


if __name__ == "__main__":
    main()
