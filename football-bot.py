import requests
import telebot
from datetime import datetime
import re
import time

# ============================================
# ТВОИ ДАННЫЕ
# ============================================
TELEGRAM_TOKEN = "8189906948:AAEJngihjXV30o405ceIHiSO5qtoenF41Ac"
# ============================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

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

def parse_all_matches():
    """Парсит ВСЕ матчи с главной страницы"""
    
    url = "https://www.soccer365.ru/"
    content = get_page_content(url)
    
    if not content:
        return []
    
    matches = []
    
    # Разбиваем на строки
    lines = content.split('\n')
    
    current_league = "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Другие лиги"
    
    for i, line in enumerate(lines):
        # Ищем названия лиг
        if 'class="live-title"' in line or 'class="league"' in line:
            league_match = re.search(r'>([^<]+)</a>', line)
            if league_match:
                current_league = league_match.group(1).strip()
        
        # Ищем матчи (время и команды)
        if 'class="score">' in line or 'class="time"' in line:
            # Ищем время
            time_match = re.search(r'(\d{2}:\d{2})', line)
            if not time_match:
                continue
            
            # Ищем названия команд (они обычно в следующих строках)
            home_team = ""
            away_team = ""
            
            # Проверяем следующие несколько строк
            for j in range(1, 5):
                if i+j < len(lines):
                    # Ищем ссылки на команды
                    team_match = re.findall(r'<a[^>]*>([^<]+)</a>', lines[i+j])
                    if len(team_match) >= 2:
                        home_team = team_match[0].strip()
                        away_team = team_match[1].strip()
                        break
            
            if time_match and home_team and away_team:
                matches.append({
                    'league': current_league,
                    'time': time_match.group(1),
                    'home': home_team,
                    'away': away_team,
                    'date': datetime.now().strftime('%d.%m.%Y')
                })
    
    # Убираем дубликаты
    unique_matches = []
    seen = set()
    
    for match in matches:
        key = f"{match['home']}-{match['away']}-{match['time']}"
        if key not in seen:
            seen.add(key)
            unique_matches.append(match)
    
    return unique_matches

@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = f"""
⚽ *Soccer365 Parser* ⚽
📅 {datetime.now().strftime('%d.%m.%Y')}

*Команды:*
/matches - все матчи на сегодня
/test - проверка

✅ Парсинг soccer365.ru
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['test'])
def test(message):
    bot.reply_to(message, "✅ Бот работает! Пробуй /matches")

@bot.message_handler(commands=['matches'])
def matches(message):
    bot.reply_to(message, "🔍 Получаю матчи с soccer365.ru... Это займет 10-15 секунд")
    
    matches = parse_all_matches()
    
    if not matches:
        bot.reply_to(message, "❌ Не удалось найти матчи. Проверь доступность сайта.")
        return
    
    # Группируем по лигам
    leagues = {}
    for match in matches:
        if match['league'] not in leagues:
            leagues[match['league']] = []
        leagues[match['league']].append(match)
    
    report = f"⚽ *МАТЧИ НА {datetime.now().strftime('%d.%m.%Y')}*\n\n"
    total = 0
    
    for league, league_matches in leagues.items():
        if league_matches:
            report += f"*{league}*\n"
            for match in league_matches[:5]:  # Макс 5 матчей на лигу
                report += f"⏰ {match['time']} {match['home']} vs {match['away']}\n"
                total += 1
            report += "\n"
    
    report += f"\n📊 Всего матчей: {total}"
    
    if len(report) > 4000:
        parts = [report[i:i+4000] for i in range(0, len(report), 4000)]
        for part in parts:
            bot.send_message(message.chat.id, part, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, report, parse_mode='Markdown')

if __name__ == "__main__":
    print("=" * 50)
    print("⚽ SOCCER365 УНИВЕРСАЛЬНЫЙ ПАРСЕР")
    print("=" * 50)
    print(f"🤖 Бот: @lyressports_bot")
    print("✅ Запущен...")
    print("=" * 50)
    
    bot.infinity_polling()
