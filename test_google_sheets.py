from google.auth import default
from googleapiclient.discovery import build

SPREADSHEET_ID = "1xOteKssAdemVcZgsplpn3aWfojYt2RikcZfNg9gycHQ"

credentials, _ = default(
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)

service = build("sheets", "v4", credentials=credentials)

result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="A1:Z20"
).execute()

rows = result.get("values", [])

print(f"Successfully retrieved {len(rows)} rows.")

for row in rows[:5]:
    print(row)