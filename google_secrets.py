import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = 'service_account.json'  # имя файла, который ты загрузил на сервер
SPREADSHEET_NAME = 'Тест SMM'                  # имя твоей таблицы
SECRETS_SHEET = 'secrets'                      # имя листа (у тебя снизу так называется)

def get_secrets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(SECRETS_SHEET)
    data = sheet.get_all_values()

    # Преобразуем список строк в словарь {ключ: значение}
    secrets = {}
    for row in data[1:]:  # Пропускаем заголовок
        if len(row) >= 2 and row[0] and row[1]:
            secrets[row[0].strip()] = row[1].strip()
    return secrets

# Пример теста (можно удалить):
if __name__ == "__main__":
    secrets = get_secrets()
    print(secrets)
