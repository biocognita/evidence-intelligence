def validate_claim_database(claim_data,data):
    print("\nValidating Claim Database......")
    required_columns = [
        "Claim ID",
        "Claim",
        "Intervention",
        "Outcome",
        "Population"
    ]
    print("\nMissing Values:")
    missing_values = claim_data[required_columns].isnull().sum()
    print(missing_values)
    report = {
        "missing_values": missing_values,
        "data_types": claim_data.dtypes
    }
    for column in missing_values.index:
        if missing_values[column] > 0:
            print(f"Warning: {column} has {missing_values[column]} missing values.")

    # Check that every Claim ID used by a study actually exists in the claims sheet
    study_claim_ids = set(data["Claim ID"].dropna().unique())
    known_claim_ids = set(claim_data["Claim ID"].dropna().unique())
    orphan_claim_ids = study_claim_ids - known_claim_ids

    if orphan_claim_ids:
        print(f"Warning: {len(orphan_claim_ids)} Claim ID(s) in the study data have no matching entry in the claims sheet: {sorted(orphan_claim_ids)}")

    report["orphan_claim_ids"] = orphan_claim_ids

    print("\nValidation Complete")
    return report