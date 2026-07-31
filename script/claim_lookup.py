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