import requests
import telebot
import re
from datetime import datetime
import time

# ============================================
# ТВОИ ДАННЫЕ
# ============================================
TELEGRAM_TOKEN = "8189906948:AAEJngihjXV30o405ceIHiSO5qtoenF41Ac"
# ============================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def get_page_content(url):
    """Получает содержимое страницы"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.text if response.status_code == 200 else None
    except:
        return None

def parse_championat():
    """Парсит матчи с Championat.com"""
    
    # Прямые ссылки на матчи дня
    urls = [
        "https://www.championat.com/football/_england.html",
        "https://www.championat.com/football/_spain.html", 
        "https://www.championat.com/football/_germany.html",
        "https://www.championat.com/football/_italy.html",
        "https://www.championat.com/football/_russia.html"
    ]
    
    matches = []
    
    for url in urls:
        content = get_page_content(url)
        if content:
            # Ищем названия лиг
            if "england" in url:
                league = "🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ"
            elif "spain" in url:
                league = "🇪🇸 Ла Лига"
            elif "germany" in url:
                league = "🇩🇪 Бундеслига"
            elif "italy" in url:
                league = "🇮🇹 Серия А"
            elif "russia" in url:
                league = "🇷🇺 РПЛ"
            else:
                league = "Другая лига"
            
            # Простой поиск матчей (по паттерну)
            # Ищем что-то похожее на "Команда - Команда"
            import re
            pattern = r'([А-Яа-яA-Za-z\s]+)\s*[-–—]\s*([А-Яа-яA-Za-z\s]+)'
            found = re.findall(pattern, content)
            
            for match in found[:5]:  # Берем первые 5 матчей
                if len(match[0]) > 3 and len(match[1]) > 3:  # Фильтр коротких названий
                    matches.append({
                        'league': league,
                        'home': match[0].strip(),
                        'away': match[1].strip(),
                        'time': "19:30",  # Время по умолчанию
                    })
            
            time.sleep(1)  # Задержка
    
    return matches

def analyze_match(match):
    """Простой анализ матча"""
    import random
    
    # Случайный прогноз для демонстрации
    outcomes = ["П1", "X", "П2"]
    totals = ["Тотал БОЛЬШЕ 2.5", "Тотал МЕНЬШЕ 2.5"]
    
    return {
        'match': match,
        'outcome': random.choice(outcomes),
        'confidence': random.randint(55, 80),
        'total': random.choice(totals),
    }

@bot.message_handler(commands=['start'])
def start(message):
    text = f"""
⚽ *Championat Parser* ⚽
📅 {datetime.now().strftime('%d.%m.%Y')}

*Команды:*
/matches - показать матчи
/help - помощь

✅ Парсинг Championat.com
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help(message):
    text = """
🔍 *Как работает:*
Бот собирает данные напрямую с Championat.com

⚠️ Может работать медленно из-за задержек
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['matches'])
def get_matches(message):
    bot.reply_to(message, "🔍 Парсю Championat.com... Подожди 10-15 секунд")
    
    matches = parse_championat()
    
    if not matches:
        bot.reply_to(message, "❌ Не удалось найти матчи. Сайт мог измениться.")
        return
    
    report = f"🔮 *МАТЧИ НА СЕГОДНЯ*\n\n"
    
    for match in matches[:10]:  # Показываем первые 10
        analysis = analyze_match(match)
        report += f"*{match['league']}*\n"
        report += f"⏰ {match['time']} {match['home']} vs {match['away']}\n"
        report += f"   📈 {analysis['outcome']} ({analysis['confidence']}%)\n"
        report += f"   ⚽ {analysis['total']}\n\n"
    
    bot.send_message(message.chat.id, report, parse_mode='Markdown')

if __name__ == "__main__":
    print("⚽ Championat Parser запущен")
    bot.infinity_polling()
