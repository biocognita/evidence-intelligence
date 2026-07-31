from claim_lookup import get_claim


def grouping_claim(data, claim_data):

    groups = data.groupby("Claim ID")

    claim_groups = []

    for claim_id, studies in groups:

        claim = get_claim(
            claim_data,
            claim_id
        )

        claim_groups.append(
            (
                claim_id,
                claim,
                studies
            )
        )

    return claim_groups