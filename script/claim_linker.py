def get_studies_for_claim(data, claim_id):
    studies = data[data["Claim ID"] == claim_id]
    return studies