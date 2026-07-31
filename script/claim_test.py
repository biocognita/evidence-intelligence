from data_loader import load_database
from claim_loader import load_claim_database
from claim_linker import get_studies_for_claim
from claim_validator import validate_claim_database

def main():
    print("import worked")

    data = load_database()

    claims = load_claim_database()

    studies = get_studies_for_claim(data, "C0001")

    print("Claim:")
    print(claims)

    print("\nStudies supporting C0001:")
    print(studies)


if __name__ == "__main__":
    main()