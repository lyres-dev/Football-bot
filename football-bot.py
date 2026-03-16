import requests
import json
import time
from datetime import datetime, timedelta
import telebot
from telebot.types import Message
import schedule
import threading

# ============================================
# ТОКЕНЫ НАПРЯМУЮ (БЕЗ ПЕРЕМЕННЫХ)
# ============================================
TELEGRAM_TOKEN = "8189906948:AAEJngihjXV30o405ceIHiSO5qtoenF41Ac"
RAPIDAPI_KEY = "dade7fd2cemsh3c92b6c8694bcfcp1f9dd7jsn3ac6634b0610"
# ============================================

print("⚽ ЗАПУСК БОТА")
print(f"🤖 Бот: @lyressports_bot")
print(f"🔑 Токен: {TELEGRAM_TOKEN[:10]}...")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Бот работает!")

@bot.message_handler(commands=['test'])
def test(message):
    bot.reply_to(message, "✅ Бот отвечает!")

print("🚀 Запуск...")
bot.infinity_polling()
