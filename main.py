import os
import time
import logging
import threading
import requests
from flask import Flask

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

app = Flask(__name__)

TOKEN = os.getenv("8818194468:AAE62UW5SQEe-1O09p0G9eo0B6ZRw778mr413:34")
CHAT_ID = os.getenv("8034348951")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

API_URL = "https://patentiautotrasporto.mit.gov.it/bonuspatente/api/beneficiario/getPlafond"
SITE_URL = "https://patentiautotrasporto.mit.gov.it/bonuspatente/#/beneficiario/homePage"

@app.route('/')
def health_check():
    return "OK", 200

def send_telegram_message(message: str) -> bool:
    if not TOKEN or not CHAT_ID:
        logging.error("BOT_TOKEN або CHAT_ID не вказані у Environment Variables!")
        return False
        
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(telegram_url, json=payload, timeout=8)
        response.raise_for_status()
        logging.info("Повідомлення успішно відправлено в Telegram.")
        return True
    except requests.exceptions.RequestException as err:
        logging.error(f"Помилка відправки в Telegram: {err}")
        return False

def check_bonus_availability() -> dict | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": SITE_URL
    }
    try:
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        logging.warning(f"Не вдалося отримати дані з API: {err}")
        return None

def monitor_loop():
    logging.info("Фоновий потік моніторингу запущено.")
    
    send_telegram_message("🤖 **Бот успішно запущений!**\nМоніторинг Bonus Patente активовано.")
    
    currently_esauriti = True

    while True:
        data = check_bonus_availability()
        if data is not None:
            is_esauriti = data.get("buoniEsauriti", True)
            
            if currently_esauriti and not is_esauriti:
                logging.info("Зміна стану: З'ЯВИЛИСЯ ВІЛЬНІ БОНУСИ!")
                send_telegram_message(
                    "🚨 **УВАГА! З'ЯВИЛИСЯ НОВІ БОНУСИ!** 🚨\n\n"
                    "Повідомлення про вичерпання зникло, є вільні ваучери!\n"
                    f"🔗 **Перейти на сайт:** {SITE_URL}"
                )
                currently_esauriti = False
            elif is_esauriti:
                currently_esauriti = True
                
        time.sleep(CHECK_INTERVAL)

threading.Thread(target=monitor_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)