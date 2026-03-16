import requests
import json
import time
from datetime import datetime, timedelta
import telebot
from telebot.types import Message
import schedule
import threading

# ============================================
# ТВОИ ДАННЫЕ (ТОЛЬКО ТОКЕН ТЕЛЕГРАМ)
# ============================================
TELEGRAM_TOKEN = "8189906948:AAEJngihjXV30o405ceIHiSO5qtoenF41Ac"
# ============================================

# Сброс вебхуков
requests.get(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=True')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ID лиг для TheSportsDB
LEAGUES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ": "4328",
    "🇪🇸 Ла Лига": "4335",
    "🇩🇪 Бундеслига": "4331",
    "🇮🇹 Серия А": "4332",
    "🇷🇺 РПЛ": "4346",
    "🇧🇷 Бразильская Серия А": "4344",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Чемпионшип": "4329",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Лига 1": "4339",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Лига 2": "4340",
}

LEAGUE_NAMES = {v: k for k, v in LEAGUES.items()}
predictions_db = {}

print("⚽ TheSportsDB Bot - БЕЗ КЛЮЧА")
print(f"🤖 Бот: @lyressports_bot")
print(f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}")

def get_todays_matches():
    """Получает матчи на сегодня из TheSportsDB"""
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?day={today}&s=Soccer"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'events' in data and data['events']:
                return data['events']
    except Exception as e:
        print(f"Ошибка: {e}")
    
    return []

def get_team_history(team_id):
    """Получает последние матчи команды"""
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={team_id}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and data['results']:
                return data['results']
    except Exception as e:
        print(f"Ошибка: {e}")
    
    return []

def analyze_match(match):
    """Анализирует матч и дает прогноз"""
    match_id = match['idEvent']
    home_team = match['strHomeTeam']
    away_team = match['strAwayTeam']
    match_time = match['strTime'] if 'strTime' in match else "00:00"
    league_id = match['idLeague']
    league_name = LEAGUE_NAMES.get(league_id, match.get('strLeague', 'Неизвестная лига'))
    
    # Получаем историю команд
    home_team_id = match['idHomeTeam']
    away_team_id = match['idAwayTeam']
    
    home_history = get_team_history(home_team_id)
    away_history = get_team_history(away_team_id)
    
    # Анализируем форму
    home_form = analyze_team_form(home_history, home_team)
    away_form = analyze_team_form(away_history, away_team)
    
    # Прогноз на основе формы
    if home_form['points'] > away_form['points']:
        outcome = "П1"
        confidence = 60 + (home_form['points'] - away_form['points']) * 5
    elif away_form['points'] > home_form['points']:
        outcome = "П2"
        confidence = 60 + (away_form['points'] - home_form['points']) * 5
    else:
        outcome = "X"
        confidence = 40
    
    # Прогноз на тотал
    total_goals = home_form['avg_goals'] + away_form['avg_goals']
    if total_goals > 2.5:
        total_pred = "Тотал БОЛЬШЕ 2.5"
        total_conf = min(80, 50 + (total_goals - 2.5) * 20)
    else:
        total_pred = "Тотал МЕНЬШЕ 2.5"
        total_conf = min(80, 50 + (2.5 - total_goals) * 20)
    
    prediction = {
        'match_id': match_id,
        'home': home_team,
        'away': away_team,
        'time': match_time,
        'league_name': league_name,
        'outcome': outcome,
        'confidence': round(min(confidence, 85), 1),
        'total': total_pred,
        'total_confidence': round(total_conf, 1),
        'home_form': f"{home_form['wins']}-{home_form['draws']}-{home_form['losses']}",
        'away_form': f"{away_form['wins']}-{away_form['draws']}-{away_form['losses']}",
    }
    
    return prediction

def analyze_team_form(history, team_name):
    """Анализирует форму команды по истории матчей"""
    stats = {
        'wins': 0, 'draws': 0, 'losses': 0,
        'goals_scored': 0, 'goals_conceded': 0,
        'points': 0, 'avg_goals': 0,
        'matches': len(history[:5])  # Последние 5 матчей
    }
    
    for match in history[:5]:  # Берем последние 5 матчей
        if match['strHomeTeam'] == team_name:
            home_score = int(match['intHomeScore'] or 0)
            away_score = int(match['intAwayScore'] or 0)
            
            stats['goals_scored'] += home_score
            stats['goals_conceded'] += away_score
            
            if home_score > away_score:
                stats['wins'] += 1
                stats['points'] += 3
            elif home_score == away_score:
                stats['draws'] += 1
                stats['points'] += 1
            else:
                stats['losses'] += 1
        else:
            home_score = int(match['intHomeScore'] or 0)
            away_score = int(match['intAwayScore'] or 0)
            
            stats['goals_scored'] += away_score
            stats['goals_conceded'] += home_score
            
            if away_score > home_score:
                stats['wins'] += 1
                stats['points'] += 3
            elif away_score == home_score:
                stats['draws'] += 1
                stats['points'] += 1
            else:
                stats['losses'] += 1
    
    if stats['matches'] > 0:
        stats['avg_goals'] = stats['goals_scored'] / stats['matches']
    
    return stats

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = f"""
⚽ *Lyres Sports Bot* ⚽
📅 {datetime.now().strftime('%d.%m.%Y')}

*Команды:*
/predict - прогнозы на сегодня
/reports - отчеты по матчам
/test - проверка
/help - помощь

✅ Работает без ключа API!
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    text = """
🔍 *Как работает:*
• Получает данные с TheSportsDB
• Анализирует последние 5 матчей команд
• Дает прогноз на исход и тотал

📊 *Прогноз включает:*
• Исход (П1, X, П2) с % уверенности
• Тотал (Больше/Меньше 2.5)
• Форму команд

📋 *После матчей:*
/reports - увидишь точность прогнозов
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['test'])
def test(message):
    bot.reply_to(message, "✅ Бот работает! Использую TheSportsDB")

@bot.message_handler(commands=['predict'])
def predict(message):
    bot.reply_to(message, "🔍 Получаю матчи на сегодня...")
    
    global predictions_db
    predictions_db = {}
    
    matches = get_todays_matches()
    
    if not matches:
        bot.reply_to(message, "😴 Сегодня нет матчей в базе данных")
        return
    
    report = f"🔮 *ПРОГНОЗЫ НА {datetime.now().strftime('%d.%m.%Y')}*\n\n"
    match_count = 0
    
    for match in matches:
        if match['idLeague'] in LEAGUES.keys():
            prediction = analyze_match(match)
            if prediction:
                predictions_db[prediction['match_id']] = prediction
                report += f"*{prediction['league_name']}*\n"
                report += f"⏰ {prediction['time']} {prediction['home']} vs {prediction['away']}\n"
                report += f"   📈 Исход: {prediction['outcome']} ({prediction['confidence']}%)\n"
                report += f"   ⚽ Тотал: {prediction['total']} ({prediction['total_confidence']}%)\n"
                report += f"   📊 Форма: {prediction['home_form']} | {prediction['away_form']}\n"
                report += f"   🔑 `{prediction['match_id']}`\n\n"
                match_count += 1
    
    if match_count == 0:
        bot.reply_to(message, "😴 В твоих лигах сегодня нет матчей")
    else:
        bot.send_message(message.chat.id, report, parse_mode='Markdown')

@bot.message_handler(commands=['reports'])
def send_reports(message):
    bot.reply_to(message, "📋 Функция отчетов будет добавлена в следующей версии")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, "Используй /predict или /help")

# ============================================
# ЗАПУСК
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("⚽ БЕЗКЛЮЧЕВАЯ ВЕРСИЯ ЗАПУЩЕНА")
    print("=" * 50)
    print(f"🤖 Бот: @lyressports_bot")
    print("📡 Использую TheSportsDB")
    print("✅ Ключ не требуется!")
    print("=" * 50)
    
    bot.infinity_polling()
