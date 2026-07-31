from data_loader import load_database
from claim_loader import load_claim_database
from claim_lookup import get_claim
from claim_report import generate_claim_report
from quality_score import calculate_quality_score
from claim_score import calculate_claim_score
from interpretation import interpret_claim_score
from claim_menu import print_main_menu

import re

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

        claim_id = input("\nSearch Claim ID: ").strip().upper()

        if claim_id == "":
            print("Please enter a Claim ID.")
            continue

        if not re.match(r"^C[0-9]{4}$", claim_id):
            print("Invalid Claim ID format.")
            continue

        claim = get_claim(claim_data, claim_id)

        if claim is None:
            continue

        studies = data[data["Claim ID"] == claim_id]

        if studies.empty:
            print(f"\nNo studies are linked to {claim_id} yet.")
            input("\nPress Enter to return to the main menu...")
            continue

        study_scores = []

        for index, study in studies.iterrows():
            score = calculate_quality_score(study)
            study_scores.append(score)

        claim_score = calculate_claim_score(study_scores)
        confidence = interpret_claim_score(claim_score)

        generate_claim_report(
            claim,
            studies,
            round(claim_score, 2),
            confidence,
            study_scores
        )

        input("\nPress Enter to return to the main menu...")

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