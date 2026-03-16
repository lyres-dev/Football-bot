import requests
import telebot
from datetime import datetime
import time

# ============================================
# ТВОИ ДАННЫЕ
# ============================================
TELEGRAM_TOKEN = "8189906948:AAEJngihjXV30o405ceIHiSO5qtoenF41Ac"
# ============================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def get_todays_matches():
    """Получает ТОЛЬКО сегодняшние матчи"""
    
    # Используем сайт с расписанием на сегодня
    url = "https://www.flashscorekz.com/football/today/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return parse_flashscore(response.text)
    except:
        return None

def parse_flashscore(html):
    """Парсит HTML FlashScore"""
    
    # Список лиг которые нам нужны
    target_leagues = [
        "Premier League",
        "LaLiga",
        "Bundesliga",
        "Serie A",
        "Russian Premier",
        "Brazilian Serie A",
        "Championship"
    ]
    
    matches = []
    lines = html.split('\n')
    
    current_league = ""
    
    for line in lines:
        # Ищем названия лиг
        for league in target_leagues:
            if league in line:
                current_league = league
                break
        
        # Ищем матчи (паттерн: время, команды)
        if "event__match" in line and current_league:
            # Простой парсинг - ищем время и команды
            time_match = re.search(r'\d{2}:\d{2}', line)
            teams = re.findall(r'>([^<]+)</a>', line)
            
            if time_match and len(teams) >= 2:
                match = {
                    'league': current_league,
                    'time': time_match.group(),
                    'home': teams[0],
                    'away': teams[1],
                    'date': datetime.now().strftime('%d.%m.%Y')
                }
                matches.append(match)
    
    return matches

@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = f"""
⚽ *FlashScore Parser* ⚽
📅 Сегодня: {datetime.now().strftime('%d.%m.%Y')}

*Команды:*
/today - матчи на сегодня
/help - помощь

✅ Парсинг FlashScore
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['today'])
def today_matches(message):
    bot.reply_to(message, "🔍 Получаю сегодняшние матчи...")
    
    matches = get_todays_matches()
    
    if not matches:
        bot.reply_to(message, "❌ Не удалось найти матчи или их нет сегодня")
        return
    
    # Группируем по лигам
    leagues = {}
    for match in matches:
        if match['league'] not in leagues:
            leagues[match['league']] = []
        leagues[match['league']].append(match)
    
    report = f"⚽ *МАТЧИ {datetime.now().strftime('%d.%m.%Y')}*\n\n"
    
    for league, matches_list in leagues.items():
        report += f"*{league}:*\n"
        for match in matches_list[:5]:  # Макс 5 матчей на лигу
            report += f"⏰ {match['time']} {match['home']} vs {match['away']}\n"
        report += "\n"
    
    bot.send_message(message.chat.id, report, parse_mode='Markdown')

if __name__ == "__main__":
    print("⚽ FlashScore Parser запущен")
    bot.infinity_polling()
