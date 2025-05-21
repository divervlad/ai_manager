import os
import time
from collections import defaultdict
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

load_dotenv()

VK_API_VERSION = os.getenv("VK_API_VERSION")
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_CONFIRMATION_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN")
ADMIN_VK_ID = int(os.getenv("ADMIN_VK_ID", 0))

app = FastAPI()

# Словарь для отслеживания времени сообщений по user_id
user_message_log = defaultdict(list)
blocked_users = {}

# Порог для антиспама
SPAM_TIME_WINDOW = 30  # секунд
SPAM_MESSAGE_LIMIT = 5  # сообщений за это время

def is_spamming(user_id: int) -> bool:
    now = time.time()
    message_times = user_message_log[user_id]

    # Убираем устаревшие сообщения
    message_times = [t for t in message_times if now - t < SPAM_TIME_WINDOW]
    user_message_log[user_id] = message_times

    # Добавляем текущее сообщение
    user_message_log[user_id].append(now)

    # Проверка на превышение лимита
    if len(user_message_log[user_id]) > SPAM_MESSAGE_LIMIT:
        blocked_users[user_id] = now  # Время блокировки
        return True
    return False

def is_user_blocked(user_id: int) -> bool:
    blocked_time = blocked_users.get(user_id)
    if blocked_time and (time.time() - blocked_time < 300):  # 5 минут блокировки
        return True
    elif blocked_time:
        del blocked_users[user_id]  # Разблокируем
    return False

def notify_admin(user_id: int):
    message = f"🔒 Пользователь с ID {user_id} заблокирован за спам. Проверьте ситуацию."
    requests.post("https://api.vk.com/method/messages.send", params={
        "access_token": VK_GROUP_TOKEN,
        "v": VK_API_VERSION,
        "user_id": ADMIN_VK_ID,
        "message": message,
        "random_id": int(time.time())
    })

@app.post("/vk_callback")
async def handle_event(request: Request):
    data = await request.json()
    if "type" not in data:
        return PlainTextResponse("ok")

    if data["type"] == "confirmation":
        return PlainTextResponse(VK_CONFIRMATION_TOKEN)

    if data["type"] == "message_new":
        user_id = data["object"]["message"]["from_id"]

        if is_user_blocked(user_id):
            return PlainTextResponse("ok")

        if is_spamming(user_id):
            notify_admin(user_id)
            send_message(user_id, "Вы слишком часто отправляете сообщения. Пожалуйста, подождите немного, с вами свяжется администратор.")
            return PlainTextResponse("ok")

        user_message = data["object"]["message"]["text"].lower()
        # Здесь можешь вставить свою основную логику ответа
        send_message(user_id, "Сообщение принято. Чем могу помочь?")

    return PlainTextResponse("ok")

def send_message(user_id: int, text: str):
    requests.post("https://api.vk.com/method/messages.send", params={
        "access_token": VK_GROUP_TOKEN,
        "v": VK_API_VERSION,
        "user_id": user_id,
        "message": text,
        "random_id": int(time.time())
    })
