import os
import time
import threading
import requests
from flask import Flask

# Міні-сервер для безкоштовного Web Service на Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bonus Patente Bot is active!"

# Зчитування конфігурації з Environment Variables на Render
TOKEN = os.getenv("8818194468:AAGfrSUY2yC_YDxqG44A1QgYVHY1gndznAE")
CHAT_ID = os.getenv("8034348951")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))  # Перевірка сайту кожні 30 сек
HOURLY_INTERVAL = 3600  # 1 година (3600 секунд)

API_URL = "https://patentiautotrasporto.mit.gov.it/bonuspatente/api/beneficiario/getPlafond"
SITE_URL = "https://patentiautotrasporto.mit.gov.it/bonuspatente/#/beneficiario/homePage"

def send_telegram_message(message):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        return response.ok
    except Exception as e:
        print(f"Помилка надсилання в Telegram: {e}")
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
        print(f"Статус відповіді сервера: {response.status_code}")
        return None
    except Exception as e:
        print(f"Помилка з'єднання з API: {e}")
        return None

# Окремий потік для відправки щогодинного статусу "Онлайн"
def hourly_status_loop():
    while True:
        time.sleep(HOURLY_INTERVAL)
        send_telegram_message("🟢 **Бот працює!**\nМоніторинг Bonus Patente продовжується у штатному режимі.")

# Основний потік моніторингу сайту
def bot_loop():
    # Затримка 5 секунд для стабілізації мережевого з'єднання Render
    time.sleep(5)
    
    send_telegram_message("🤖 **Бот успішно запущений!**\nМоніторинг Bonus Patente активовано (перевірка кожні 30 сек).")
    
    currently_esauriti = True
    
    while True:
        data = check_bonus_availability()
        
        if data is not None:
            is_esauriti = data.get("buoniEsauriti", True)
            
            # Якщо ваучери були вичерпані, але статус змінився (з'явилися нові)
            if currently_esauriti and not is_esauriti:
                send_telegram_message(
                    "🚨 **УВАГА! З'ЯВИЛИСЯ НОВІ БОНУСИ!** 🚨\n\n"
                    "Повідомлення про вичерпання зникло, є вільні ваучери!\n"
                    f"🔗 **Перейти на сайт:** {SITE_URL}"
                )
                currently_esauriti = False
            elif is_esauriti:
                currently_esauriti = True
                print("Статус: ваучери все ще вичерпані (esauriti)...")
                
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # Запуск основниого моніторингу
    monitor_thread = threading.Thread(target=bot_loop)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Запуск щогодинного підтвердження роботи
    hourly_thread = threading.Thread(target=hourly_status_loop)
    hourly_thread.daemon = True
    hourly_thread.start()
    
    # Запуск веб-сервера Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)