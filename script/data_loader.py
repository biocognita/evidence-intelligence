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


def compress_string_columns(df, max_unique_ratio=0.5):
    """Shrink RAM: store repeated text as pandas 'category' codes instead
    of a separate Python string object per cell. Category dtype dedupes the
    underlying strings, so columns like Claim ID / Outcome / Intervention
    can be several times smaller in memory.

    Only low-cardinality text columns are compressed (unique values < 50%
    of rows). High-cardinality text (unique Study IDs, long free-text) gains
    nothing from category and is left as-is.

    Run AFTER strip_cell_whitespace: category columns would otherwise be
    skipped by the whitespace stripper, which only touches text dtypes.
    """
    row_count = len(df)
    for column in df.columns:
        dtype = df[column].dtype
        is_text = dtype == object or isinstance(dtype, pd.StringDtype)
        if is_text and row_count > 0:
            unique_ratio = df[column].nunique(dropna=False) / row_count
            if unique_ratio < max_unique_ratio:
                df[column] = df[column].astype("category")
    return df


def load_database():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={STUDY_DATABASE_GID}"
    data = pd.read_csv(csv_url)
    data.columns = data.columns.str.strip()
    data = strip_cell_whitespace(data)
    data = compress_string_columns(data)  # RAM optimization for the 512 MB Render limit
    # Remove unapproved studies
    data = data.dropna(subset=["Study ID"])
    return data
