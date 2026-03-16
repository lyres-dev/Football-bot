import requests
import json
import time
from datetime import datetime, timedelta
import telebot
from telebot.types import Message
import schedule
import threading

# ============================================
# ТВОИ ДАННЫЕ
# ============================================
TELEGRAM_TOKEN = "8625272420:AAGUjyGKxx244b-5w-rOh5jr8cLoSGTZogY"
RAPIDAPI_KEY = "dade7fd2cemsh3c92b6c8694bcfcp1f9dd7jsn3ac6634b0610"
# ============================================

# ПРИНУДИТЕЛЬНО СБРАСЫВАЕМ ВСЕ СТАРЫЕ ПОДКЛЮЧЕНИЯ
print("🔄 Сброс старых подключений...")
requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=True')
print("✅ Сброс выполнен")

# СОЗДАЕМ БОТА С ОЧИСТКОЙ
bot = telebot.TeleBot(TELEGRAM_TOKEN, skip_pending=True)

def get_current_season():
    today = datetime.now()
    year = today.year
    month = today.month
    if month <= 6:
        return str(year - 1)
    else:
        return str(year)

print("⚽ Football Analyst Bot")
print(f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}")
print(f"🤖 Бот: @Footballlyres_bot")

# ============================================
# ВСЕ ТВОИ ЛИГИ
# ============================================
LEAGUES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ": 39,
    "🇪🇸 Ла Лига": 140,
    "🇩🇪 Бундеслига": 78,
    "🇮🇹 Серия А": 135,
    "🇷🇺 РПЛ": 235,
    "🇧🇷 Бразильская Серия А": 71,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Чемпионшип": 40,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Лига 1": 41,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Лига 2": 42,
}

LEAGUE_NAMES = {v: k for k, v in LEAGUES.items()}
predictions_db = {}

# ============================================
# КОМАНДА ДЛЯ ПРОВЕРКИ
# ============================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = f"""
⚽ *Football Analyst* ⚽
📅 {datetime.now().strftime('%d.%m.%Y')}

✅ Бот работает!
🔍 Используй /predict_all для прогнозов
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['test'])
def send_test(message):
    bot.reply_to(message, "✅ Бот работает и отвечает!")

# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    print("=" * 40)
    print("✅ БОТ ГОТОВ К РАБОТЕ")
    print("=" * 40)
    print("📡 Запускаю прослушивание команд...")
    
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        time.sleep(5)
        print("🔄 Перезапуск...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
