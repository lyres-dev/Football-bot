import requests
import telebot
import re
from datetime import datetime
from bs4 import BeautifulSoup
import time
import threading

# ============================================
# ТВОИ ДАННЫЕ
# ============================================
TELEGRAM_TOKEN = "8189906948:AAEJngihjXV30o405ceIHiSO5qtoenF41Ac"
# ============================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Словарь лиг и их URL на Sports.ru
LEAGUES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ": "https://www.sports.ru/football/england/premier-league/",
    "🇪🇸 Ла Лига": "https://www.sports.ru/football/spain/primera/",
    "🇩🇪 Бундеслига": "https://www.sports.ru/football/germany/bundesliga/",
    "🇮🇹 Серия А": "https://www.sports.ru/football/italy/serie-a/",
    "🇷🇺 РПЛ": "https://www.sports.ru/football/russia/premier-league/",
    "🇫🇷 Лига 1": "https://www.sports.ru/football/france/ligue-1/",
}

def parse_matches():
    """Парсит матчи со Sports.ru"""
    matches = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
    }
    
    for league_name, league_url in LEAGUES.items():
        try:
            print(f"Парсинг {league_name}...")
            response = requests.get(league_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Ищем блоки с матчами
                match_blocks = soup.find_all('div', class_='match-block')
                
                for block in match_blocks:
                    # Парсим название команды
                    home_team = block.find('span', class_='match-block__team-name_left')
                    away_team = block.find('span', class_='match-block__team-name_right')
                    
                    # Парсим время
                    time_elem = block.find('span', class_='match-block__time')
                    
                    if home_team and away_team and time_elem:
                        match = {
                            'league': league_name,
                            'home': home_team.text.strip(),
                            'away': away_team.text.strip(),
                            'time': time_elem.text.strip(),
                            'date': datetime.now().strftime('%d.%m.%Y')
                        }
                        matches.append(match)
                        
            time.sleep(1)  # Задержка чтобы не заблокировали
            
        except Exception as e:
            print(f"Ошибка при парсинге {league_name}: {e}")
            continue
    
    return matches

def analyze_match(match):
    """Анализирует матч и дает прогноз"""
    # Здесь можно добавить анализ на основе статистики
    # Пока даем случайные прогнозы для демонстрации
    
    import random
    outcomes = ["П1", "X", "П2"]
    totals = ["Тотал БОЛЬШЕ 2.5", "Тотал МЕНЬШЕ 2.5"]
    
    return {
        'match': match,
        'outcome': random.choice(outcomes),
        'confidence': random.randint(55, 80),
        'total': random.choice(totals),
        'total_confidence': random.randint(55, 75)
    }

@bot.message_handler(commands=['start'])
def start(message):
    text = f"""
⚽ *Sports Parser Bot* ⚽
📅 {datetime.now().strftime('%d.%m.%Y')}

*Команды:*
/parse - спарсить матчи
/help - помощь

✅ Бот парсит данные со Sports.ru
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help(message):
    text = """
🔍 *Как работает:*
1. Бот заходит на Sports.ru
2. Собирает матчи на сегодня
3. Показывает прогнозы

⚠️ Парсинг может занять 10-20 секунд
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['parse'])
def parse_command(message):
    bot.reply_to(message, "🔍 Парсю матчи со Sports.ru... Это займет около 30 секунд")
    
    matches = parse_matches()
    
    if not matches:
        bot.reply_to(message, "❌ Не удалось найти матчи. Возможно, сайт изменился.")
        return
    
    report = f"🔮 *МАТЧИ НА СЕГОДНЯ*\n\n"
    
    current_league = ""
    for match in matches:
        if match['league'] != current_league:
            current_league = match['league']
            report += f"\n*{current_league}*\n"
        
        analysis = analyze_match(match)
        report += f"⏰ {match['time']} {match['home']} vs {match['away']}\n"
        report += f"   📈 Прогноз: {analysis['outcome']} ({analysis['confidence']}%)\n"
        report += f"   ⚽ {analysis['total']}\n\n"
    
    # Разбиваем на части если слишком длинно
    if len(report) > 4000:
        parts = [report[i:i+4000] for i in range(0, len(report), 4000)]
        for part in parts:
            bot.send_message(message.chat.id, part, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, report, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, "Используй /parse для получения матчей")

# ============================================
# ЗАПУСК
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("⚽ SPORTS PARSER BOT")
    print("=" * 50)
    print(f"🤖 Бот: @lyressports_bot")
    print(f"📡 Парсинг: Sports.ru")
    print("=" * 50)
    
    bot.infinity_polling()
