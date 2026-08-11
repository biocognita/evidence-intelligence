CLAIM_INDEX_COLUMNS = ["Claim ID", "Claim", "Intervention", "Outcome", "Population"]


def build_claims_index(claim_data):
    """Return {Claim ID: claim-dict} built once for O(1) claim lookups.
    First occurrence wins for duplicate Claim IDs.

    Vectorized via to_dict() instead of iterrows() — iterrows is 10-100x
    slower per row and this runs on every 5-minute cache refresh."""
    unique = claim_data.drop_duplicates(subset=["Claim ID"], keep="first")
    return {
        record["Claim ID"]: record
        for record in unique[CLAIM_INDEX_COLUMNS].to_dict("records")
    }


def get_claim(claim_data, claim_id):

    claim = claim_data[
        claim_data["Claim ID"] == claim_id
    ]

    if claim.empty:
        print("Claim not found")
        return None

    claim = claim.iloc[0]

    return {
        "Claim ID": claim["Claim ID"],
        "Claim": claim["Claim"],
        "Intervention": claim["Intervention"],
        "Outcome": claim["Outcome"],
        "Population": claim["Population"]
    }
