import requests
import telebot
from datetime import datetime
import time
import re

# ============================================
# ТВОИ ДАННЫЕ
# ============================================
TELEGRAM_TOKEN = "8189906948:AAEJngihjXV30o405ceIHiSO5qtoenF41Ac"
# ============================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ID лиг на Soccer365
LEAGUES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ": "england/premier-league",
    "🇪🇸 Ла Лига": "spain/primera",
    "🇩🇪 Бундеслига": "germany/bundesliga",
    "🇮🇹 Серия А": "italy/serie-a",
    "🇷🇺 РПЛ": "russia/premier-league",
    "🇧🇷 Бразилия": "brazil/brasileiro",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Чемпионшип": "england/championship",
}

def get_page_content(url):
    """Получает страницу"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.text
    except:
        return None

def parse_soccer365():
    """Парсит матчи с Soccer365.ru"""
    all_matches = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for league_name, league_path in LEAGUES.items():
        url = f"https://www.soccer365.ru/{league_path}/"
        print(f"Парсинг {league_name}...")
        
        content = get_page_content(url)
        if not content:
            continue
        
        # Ищем блоки с матчами
        matches = []
        
        # Простой поиск матчей по паттерну
        pattern = r'(\d{2}:\d{2}).*?<a[^>]*>([^<]+)</a>.*?<a[^>]*>([^<]+)</a>'
        found = re.findall(pattern, content, re.DOTALL)
        
        for match in found[:10]:  # Берем первые 10 матчей
            if len(match) >= 3:
                matches.append({
                    'league': league_name,
                    'time': match[0],
                    'home': match[1].strip(),
                    'away': match[2].strip(),
                })
        
        all_matches.extend(matches)
        time.sleep(1)  # Задержка
    
    return all_matches

def predict_match(match):
    """Простой прогноз"""
    import random
    
    # Анализируем названия команд для простоты
    home_len = len(match['home'])
    away_len = len(match['away'])
    
    # Если названия примерно равны
    if abs(home_len - away_len) < 3:
        if random.random() > 0.5:
            return "П1", random.randint(55, 70)
        else:
            return "П2", random.randint(55, 70)
    elif home_len > away_len:
        return "П1", random.randint(60, 75)
    else:
        return "П2", random.randint(60, 75)

@bot.message_handler(commands=['start'])
def start(message):
    text = f"""
⚽ *Soccer365 Parser* ⚽
📅 {datetime.now().strftime('%d.%m.%Y')}

*Команды:*
/matches - все матчи на сегодня
/epl - только АПЛ
/laliga - только Ла Лига
/bundesliga - только Бундеслига
/seriea - только Серия А
/rpl - только РПЛ
/help - помощь

✅ Парсинг soccer365.ru
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help(message):
    text = """
🔍 *Как работает:*
1. Бот парсит soccer365.ru
2. Показывает матчи на сегодня
3. Дает прогнозы

⚠️ Может работать медленно
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['matches'])
def all_matches(message):
    bot.reply_to(message, "🔍 Парсю soccer365.ru... Это займет 20-30 секунд")
    
    matches = parse_soccer365()
    
    if not matches:
        bot.reply_to(message, "❌ Не удалось найти матчи")
        return
    
    report = f"⚽ *ВСЕ МАТЧИ НА {datetime.now().strftime('%d.%m.%Y')}*\n\n"
    
    current_league = ""
    for match in matches:
        if match['league'] != current_league:
            current_league = match['league']
            report += f"\n*{current_league}*\n"
        
        outcome, conf = predict_match(match)
        report += f"⏰ {match['time']} {match['home']} vs {match['away']}\n"
        report += f"   📈 Прогноз: {outcome} ({conf}%)\n\n"
    
    bot.send_message(message.chat.id, report, parse_mode='Markdown')

# Команды для отдельных лиг
@bot.message_handler(commands=['epl'])
def epl_matches(message):
    bot.reply_to(message, "🔍 Парсю АПЛ...")
    show_league_matches(message, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ")

@bot.message_handler(commands=['laliga'])
def laliga_matches(message):
    bot.reply_to(message, "🔍 Парсю Ла Лигу...")
    show_league_matches(message, "🇪🇸 Ла Лига")

@bot.message_handler(commands=['bundesliga'])
def bundesliga_matches(message):
    bot.reply_to(message, "🔍 Парсю Бундеслигу...")
    show_league_matches(message, "🇩🇪 Бундеслига")

@bot.message_handler(commands=['seriea'])
def seriea_matches(message):
    bot.reply_to(message, "🔍 Парсю Серию А...")
    show_league_matches(message, "🇮🇹 Серия А")

@bot.message_handler(commands=['rpl'])
def rpl_matches(message):
    bot.reply_to(message, "🔍 Парсю РПЛ...")
    show_league_matches(message, "🇷🇺 РПЛ")

def show_league_matches(message, target_league):
    matches = parse_soccer365()
    
    league_matches = [m for m in matches if m['league'] == target_league]
    
    if not league_matches:
        bot.reply_to(message, f"❌ Матчей {target_league} не найдено")
        return
    
    report = f"⚽ *{target_league}*\n\n"
    for match in league_matches:
        outcome, conf = predict_match(match)
        report += f"⏰ {match['time']} {match['home']} vs {match['away']}\n"
        report += f"   📈 {outcome} ({conf}%)\n\n"
    
    bot.send_message(message.chat.id, report, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, "Используй /matches или /help")

# ============================================
# ЗАПУСК
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("⚽ SOCCER365 PARSER")
    print("=" * 50)
    print(f"🤖 Бот: @lyressports_bot")
    print(f"📡 Парсинг: soccer365.ru")
    print("=" * 50)
    
    bot.infinity_polling()
