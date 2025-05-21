import gspread
from google.oauth2.service_account import Credentials

# Путь к твоему JSON-файлу
SERVICE_ACCOUNT_FILE = 'service_account.json'
# Название таблицы (или используем ID)
SPREADSHEET_NAME = '1_YXwI1nVXKaqBdsBEZMLlbWZ6ilNCDfJeTM5I4X1Lag'
SECRETS_SHEET = 'Secrets'  # Имя листа, если у тебя их несколько

def get_secrets():
    # Подключаемся к Google Sheets
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(SECRETS_SHEET)
    data = sheet.get_all_values()
    # Составляем словарь секретов
    secrets = {row[0]: row[1] for row in data if len(row) > 1}
    return secrets

# Для проверки (можно удалить):
if __name__ == "__main__":
    secrets = get_secrets()
    print(secrets)
