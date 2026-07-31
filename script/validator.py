def validate_database(data):
    print("\nValidating Database........")
    print("\nMissing Values:")
    missing_values = data.isnull().sum()
    print(missing_values)
    report = {
        "missing_values": missing_values,
        "data_types": data.dtypes
    }
    for column in missing_values.index:
        if missing_values[column] > 0:
            print(f"Warning: {column} has {missing_values[column]} missing values.")
    print("\nValidation Complete")
    return report