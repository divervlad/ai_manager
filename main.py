import os
from dotenv import load_dotenv
import requests
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import openai
from rapidfuzz import fuzz, process
from knowledge_base import context_data

load_dotenv()

VK_API_VERSION = os.getenv("VK_API_VERSION")
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_CONFIRMATION_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "8989898989")
ADMIN_VK_ID = int(os.getenv("ADMIN_VK_ID", 0))  # айди администратора (0 — по умолчанию)

app = FastAPI()

ADMIN_KEYWORDS = [
    "позвать админа", "администратор", "соедините с админом",
    "свяжите с администратором", "нужен админ", "хочу к администратору"
]

def get_context(group_id):
    return context_data.get(str(group_id), {})

def fuzzy_find_answer(group_id, message, min_score=80):
    ctx = get_context(group_id)
    faq = ctx.get("faq", [])
    questions = [item["q"] for item in faq]
    result = process.extractOne(message, questions, scorer=fuzz.token_set_ratio)
    if result:
        print(f"Fuzzy search: input='{message}' | match='{result[0]}' | score={result[1]}")
    if result and result[1] >= min_score:
        idx = questions.index(result[0])
        return faq[idx]["a"]
    return None

def gpt_support_answer(context, message):
    if not OPENAI_API_KEY:
        print("Нет ключа OpenAI.")
        return None

    prompt = (
        f"Ты — вежливый чат-бот службы доставки еды \"{context.get('company_name', 'компания')}\". "
        f"Описание: {context.get('description', '')}\n"
        f"Тебя спрашивают: \"{message}\"\n"
        f"Ответь как сотрудник поддержки доставки еды. "
        f"Если не можешь помочь, напиши только: 'Я чат-бот службы доставки еды. "
        f"Готов помочь по вопросам заказа, оплаты и доставки! Уточните ваш вопрос, пожалуйста.'"
    )
    try:
        print("ВЫЗЫВАЮ GPT С prompt:", prompt)
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        print("RAW GPT RESPONSE:", response)
        reply = response.choices[0].message.content.strip() if response.choices else None
        print("ОТВЕТ GPT:", reply)
        return reply
    except Exception as e:
        print(f"GPT ERROR: {e}")
        return None

def send_vk_message(user_id, group_id, message):
    data = {
        "user_id": user_id,
        "random_id": 0,
        "message": message,
        "access_token": VK_GROUP_TOKEN,
        "v": VK_API_VERSION,
        "group_id": group_id,
    }
    try:
        r = requests.post("https://api.vk.com/method/messages.send", data=data)
        print(f"VK MESSAGE SENT TO {user_id}: {r.text}")
    except Exception as e:
        print(f"VK SEND ERROR: {e}")

def send_admin_alert(user_id, group_id, user_message):
    dialog_url = f"https://vk.com/gim{group_id}?sel={user_id}"
    msg = (
        f"❗ Пользователь запросил администратора!\n"
        f"[id{user_id}|Перейти к диалогу]\n"
        f"Сообщение: \"{user_message}\"\n"
        f"{dialog_url}"
    )
    send_vk_message(ADMIN_VK_ID, group_id, msg)

def is_admin_call(text):
    text = text.lower()
    for key in ADMIN_KEYWORDS:
        if key in text:
            return True
    return False

@app.get("/vk_callback")
async def vk_callback_get():
    return PlainTextResponse("ok")

@app.post("/vk_callback")
async def vk_callback(req: Request):
    try:
        body = await req.json()
        print("VK CALLBACK BODY:", body)
        if body.get("type") == "confirmation":
            return PlainTextResponse(VK_CONFIRMATION_TOKEN)

        if body.get("type") == "message_new":
            group_id = body.get("group_id")
            user_id = body["object"]["message"].get("from_id")
            text = body["object"]["message"].get("text", "")
            print(f"New message from user {user_id} in group {group_id}: {text}")

            # 1. Проверяем команду вызова администратора
            if is_admin_call(text):
                print("Команда вызова админа обнаружена.")
                send_admin_alert(user_id, group_id, text)
                send_vk_message(user_id, group_id, "Соединяю с администратором. Ожидайте, он свяжется с вами в ближайшее время.")
                return PlainTextResponse("ok")

            # 2. Пробуем найти ответ по базе знаний
            ctx = get_context(group_id)
            answer = fuzzy_find_answer(group_id, text)
            print("Ответ из базы знаний:", answer)
            # 3. Если не нашли — спрашиваем GPT как службу поддержки
            if not answer:
                print("База не помогла, пробуем GPT.")
                answer = gpt_support_answer(ctx, text)
            # 4. Если GPT не дал ответа — дефолтная фраза
            if not answer or len(answer.strip()) == 0:
                print("GPT не дал ответа, дефолт.")
                answer = f"Извините, не могу сейчас ответить на ваш вопрос. Попробуйте позвонить по номеру {ADMIN_PHONE}."
            send_vk_message(user_id, group_id, answer)
            return PlainTextResponse("ok")
        return PlainTextResponse("ok")
    except Exception as e:
        print(f"ERROR VK_CALLBACK: {e}")
        return PlainTextResponse("ok")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
