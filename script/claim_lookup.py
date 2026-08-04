def build_claims_index(claim_data):
    """Return {Claim ID: claim-dict} built once for O(1) claim lookups.
    First occurrence wins for duplicate Claim IDs."""
    claims = {}
    for _, row in claim_data.drop_duplicates(subset=["Claim ID"], keep="first").iterrows():
        claims[row["Claim ID"]] = {
            "Claim ID": row["Claim ID"],
            "Claim": row["Claim"],
            "Intervention": row["Intervention"],
            "Outcome": row["Outcome"],
            "Population": row["Population"]
        }
    return claims


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
