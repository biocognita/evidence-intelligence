import pandas as pd
from config import SPREADSHEET_ID, STUDY_DATABASE_GID


def strip_cell_whitespace(df):
    """Trim stray whitespace from text cells (e.g. " C0001 " -> "C0001").
    Numeric cells and non-string values are left untouched."""
    for column in df.columns:
        dtype = df[column].dtype
        is_text = dtype == object or isinstance(dtype, pd.StringDtype)
        if is_text:
            df[column] = df[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
    return df


def load_database():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={STUDY_DATABASE_GID}"
    data = pd.read_csv(csv_url)
    data.columns = data.columns.str.strip()
    data = strip_cell_whitespace(data)
    # Remove unapproved studies
    data = data.dropna(subset=["Study ID"])
    return data
