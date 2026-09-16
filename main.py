import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

TOKEN = os.getenv("8818194468:AAGfrSUY2yC_YDxqG44A1QgYVHY1gndznAE")
CHAT_ID = os.getenv("8034348951s")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

API_URL = "https://patentiautotrasporto.mit.gov.it/bonuspatente/api/beneficiario/getPlafond"
SITE_URL = "https://patentiautotrasporto.mit.gov.it/bonuspatente/#/beneficiario/homePage"

@app.route('/')
def home():
    return "Bot is running!", 200

def send_telegram_message(message):
    print(f"DEBUG: Намагаємося надіслати повідомлення... TOKEN={bool(TOKEN)}, CHAT_ID={bool(CHAT_ID)}")
    if not TOKEN or not CHAT_ID:
        print("❌ ПОМИЛКА: BOT_TOKEN або CHAT_ID порожні в Environment Variables!")
        return False
        
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        print(f"📡 Відповідь Telegram: {response.status_code} | {response.text}")
        return response.ok
    except Exception as e:
        print(f"❌ Помилка запиту до Telegram: {e}")
        return False

def check_bonus_availability():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": SITE_URL
    }
    try:
        response = requests.get(API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        print(f"⚠️ Статус відповіді Bonus Patente: {response.status_code}")
        return None
    except Exception as e:
        print(f"❌ Помилка з'єднання з сайтом: {e}")
        return None

def monitor_loop():
    print("🚀 Початок роботи фонового потоку monitor_loop...")
    time.sleep(3)
    send_telegram_message("🤖 **Бот успішно запущений!**\nМоніторинг Bonus Patente активовано.")
    
    currently_esauriti = True

    while True:
        data = check_bonus_availability()
        if data is not None:
            is_esauriti = data.get("buoniEsauriti", True)
            if currently_esauriti and not is_esauriti:
                send_telegram_message(
                    "🚨 **УВАГА! З'ЯВИЛИСЯ НОВІ БОНУСИ!** 🚨\n\n"
                    "Повідомлення про вичерпання зникло, є вільні ваучери!\n"
                    f"🔗 **Перейти на сайт:** {SITE_URL}"
                )
                currently_esauriti = False
            elif is_esauriti:
                currently_esauriti = True

        time.sleep(CHECK_INTERVAL)

# Запускаємо фоновий потік ДО запуску Flask
t = threading.Thread(target=monitor_loop, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)