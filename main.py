import os
import time
import requests

# Зчитування конфігурації з налаштувань Render.com
TOKEN = os.getenv("8818194468:AAGfrSUY2yC_YDxqG44A1QgYVHY1gndznAE")
CHAT_ID = os.getenv("8034348951")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

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
        print(f"Статус відповіді сервера: {response.status_code}")
        return None
    except Exception as e:
        print(f"Помилка з'єднання: {e}")
        return None

def main():
    send_telegram_message("🤖 **Бот запущен!**\nМоніторинг Bonus Patente активовано (перевірка кожні 30 сек).")
    
    currently_esauriti = True
    
    while True:
        data = check_bonus_availability()
        
        if data is not None:
            # Логіка: шукаємо прапорець вичерпаності ваучерів
            is_esauriti = data.get("buoniEsauriti", True)
            
            if currently_esauriti and not is_esauriti:
                # Надсилається, якщо ваучери перейшли в статус "доступні"
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
    main()