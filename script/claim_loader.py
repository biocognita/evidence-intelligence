import pandas as pd
from config import SPREADSHEET_ID, CLAIM_DATABASE_GID
from data_loader import strip_cell_whitespace, compress_string_columns


def load_claim_database():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={CLAIM_DATABASE_GID}"
    data = pd.read_csv(csv_url)
    data.columns = data.columns.str.strip()
    data = strip_cell_whitespace(data)
    data = compress_string_columns(data)  # RAM optimization for the 512 MB Render limit
    return data
