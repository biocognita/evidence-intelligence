from claim_lookup import build_claims_index


def grouping_claim(data, claim_data):
    # Build a claim_id -> claim index once so we don't rescan the whole
    # claim table for every group (O(claims x studies) -> O(claims + studies)).
    claims_by_id = build_claims_index(claim_data)

    claim_groups = []

    for claim_id, studies in data.groupby("Claim ID"):
        claim_groups.append(
            (
                claim_id,
                claims_by_id.get(claim_id),
                studies
            )
        )

    return claim_groups
