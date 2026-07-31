from claim_loader import load_claim_database
from claim_lookup import get_claim


def main():
    claim_data = load_claim_database()

    claim = get_claim(
        claim_data,
        "C0001"
    )

    print(claim)


if __name__ == "__main__":
    main()