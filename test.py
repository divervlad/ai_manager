import requests

# Замени на свой адрес и путь!
url = "https://bd4w-150-241-90-5.ngrok-free.app/vk_callback"

data = {
    "type": "confirmation",
    "group_id": 168792022   # <-- твой VK group_id
}

response = requests.post(url, json=data)
print("Статус:", response.status_code)
print("Ответ:", repr(response.text))
