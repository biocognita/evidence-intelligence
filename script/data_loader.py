import pandas as pd
from config import SPREADSHEET_ID, STUDY_DATABASE_GID

def load_database():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={STUDY_DATABASE_GID}"
    data = pd.read_csv(csv_url)
    data.columns = data.columns.str.strip()
    # Remove unapproved studies
    data = data.dropna(subset=["Study ID"])
    return data