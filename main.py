import os
import time
import requests

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))  # Перевірка кожні 30 секунд

API_URL = "https://patentiautotrasporto.mit.gov.it/bonuspatente/api/beneficiario/getPlafond"
SITE_URL = "https://patentiautotrasporto.mit.gov.it/bonuspatente/#/beneficiario/homePage"

def send_telegram_message(message):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(telegram_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Помилка надсилання в Telegram: {e}")

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
        print(f"Статус відповіді: {response.status_code}")
        return None
    except Exception as e:
        print(f"Помилка запиту: {e}")
        return None

def main():
    send_telegram_message("🤖 **Бот активований!**\nСтежимо за Bonus Patente кожні 30 секунд...")
    
    text_was_present = True
    
    while True:
        data = check_bonus_availability()
        
        if data is not None:
            # Отримуємо значення прапорця вичерпання ваучерів
            is_esauriti = data.get("buoniEsauriti", True)
            
            if text_was_present and not is_esauriti:
                # Повідомлення надсилається ТІЛЬКИ коли статус змінився на "Є БОНУСИ"
                send_telegram_message(
                    "🚨 **УВАГА! З'ЯВИЛИСЯ НОВІ БОНУСИ!** 🚨\n\n"
                    "Ваучери більше не вичерпані! Терміново заходьте на сайт:\n"
                    f"🔗 {SITE_URL}"
                )
                text_was_present = False
            elif is_esauriti:
                text_was_present = True
                print("Ваучери все ще вичерпані (esauriti)...")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()