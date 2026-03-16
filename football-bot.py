import requests
import json
import time
import os
from datetime import datetime, timedelta
import telebot
from telebot.types import Message
import schedule
import threading

# ============================================
# ТВОИ ДАННЫЕ (Railway сам подставит их из Variables)
# ============================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', "8625272420:AAGsmzyEYufDtRV70uocQhWLbHt8NwIZQv0")
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', "dade7fd2cemsh3c92b6c8694bcfcp1f9dd7jsn3ac6634b0610")
# ============================================

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
print(f"🏆 Сезон: {get_current_season()}")
print(f"🤖 Бот: @Footballlyres_bot")
print(f"🔑 Токен загружен: {'✅' if TELEGRAM_TOKEN else '❌'}")
print(f"🔑 API ключ загружен: {'✅' if RAPIDAPI_KEY else '❌'}")

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
bot = telebot.TeleBot(TELEGRAM_TOKEN, skip_pending=True)

def make_api_request(url, querystring):
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    try:
        print(f"📡 Запрос к API: {url}")
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return None

def get_todays_matches(league_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    today = datetime.now().strftime("%Y-%m-%d")
    querystring = {
        "league": league_id,
        "season": get_current_season(),
        "from": today,
        "to": today,
        "timezone": "Europe/Moscow"
    }
    data = make_api_request(url, querystring)
    if data and 'response' in data:
        return data['response']
    return []

def get_team_form(team_id, league_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {
        "team": team_id,
        "league": league_id,
        "season": get_current_season(),
        "last": "5",
        "status": "FT"
    }
    data = make_api_request(url, querystring)
    if not data or 'response' not in data:
        return None
    fixtures = data['response']
    if len(fixtures) == 0:
        return None
    stats = {
        'wins': 0, 'draws': 0, 'losses': 0,
        'goals_scored': 0, 'goals_conceded': 0,
        'both_scored': 0,
        'matches_analyzed': len(fixtures)
    }
    for match in fixtures:
        if match['teams']['home']['id'] == team_id:
            goals_for = match['goals']['home']
            goals_against = match['goals']['away']
            winner = match['teams']['home']['winner']
        else:
            goals_for = match['goals']['away']
            goals_against = match['goals']['home']
            winner = match['teams']['away']['winner']
        stats['goals_scored'] += goals_for
        stats['goals_conceded'] += goals_against
        if winner:
            stats['wins'] += 1
        elif match['teams']['home']['winner'] is False and match['teams']['away']['winner'] is False:
            stats['draws'] += 1
        else:
            stats['losses'] += 1
        if goals_for > 0 and goals_against > 0:
            stats['both_scored'] += 1
    return stats

def predict_match(match_data):
    league_id = match_data['league']['id']
    home_id = match_data['teams']['home']['id']
    away_id = match_data['teams']['away']['id']
    home_name = match_data['teams']['home']['name']
    away_name = match_data['teams']['away']['name']
    match_date = match_data['fixture']['date']
    match_time = match_date[11:16]
    match_id = match_data['fixture']['id']
    
    home_form = get_team_form(home_id, league_id)
    away_form = get_team_form(away_id, league_id)
    
    if not home_form or not away_form:
        return None
    
    home_avg_scored = home_form['goals_scored'] / home_form['matches_analyzed']
    home_avg_conceded = home_form['goals_conceded'] / home_form['matches_analyzed']
    away_avg_scored = away_form['goals_scored'] / away_form['matches_analyzed']
    away_avg_conceded = away_form['goals_conceded'] / away_form['matches_analyzed']
    
    home_strength = home_avg_scored * 1.2 - away_avg_conceded * 0.8 + 0.3
    away_strength = away_avg_scored * 1.2 - home_avg_conceded * 0.8
    total_strength = home_strength + away_strength
    
    if total_strength > 0:
        home_win_prob = (home_strength / total_strength) * 100
        away_win_prob = (away_strength / total_strength) * 100
    else:
        home_win_prob = 40
        away_win_prob = 40
    draw_prob = 100 - home_win_prob - away_win_prob
    
    if home_win_prob > 45:
        outcome = "П1"
        confidence = home_win_prob
    elif away_win_prob > 45:
        outcome = "П2"
        confidence = away_win_prob
    else:
        outcome = "X"
        confidence = draw_prob
    
    expected_total = home_avg_scored + away_avg_scored + home_avg_conceded + away_avg_conceded
    expected_total = expected_total / 2
    
    if expected_total > 2.7:
        total_pred = "Тотал БОЛЬШЕ 2.5"
        total_conf = min(85, 50 + (expected_total - 2.5) * 30)
    elif expected_total < 2.3:
        total_pred = "Тотал МЕНЬШЕ 2.5"
        total_conf = min(85, 50 + (2.5 - expected_total) * 30)
    else:
        total_pred = "Тотал 2.5 (неопределенно)"
        total_conf = 50
    
    home_btts_percent = (home_form['both_scored'] / home_form['matches_analyzed']) * 100
    away_btts_percent = (away_form['both_scored'] / away_form['matches_analyzed']) * 100
    avg_btts_percent = (home_btts_percent + away_btts_percent) / 2
    
    if avg_btts_percent > 60:
        btts_pred = "Обе забьют - ДА"
        btts_conf = avg_btts_percent
    else:
        btts_pred = "Обе забьют - НЕТ"
        btts_conf = 100 - avg_btts_percent
    
    home_form_str = f"{home_form['wins']}-{home_form['draws']}-{home_form['losses']}"
    away_form_str = f"{away_form['wins']}-{away_form['draws']}-{away_form['losses']}"
    
    prediction = {
        'match_id': match_id,
        'home': home_name,
        'away': away_name,
        'time': match_time,
        'date': match_date[:10],
        'league_id': league_id,
        'league_name': LEAGUE_NAMES.get(league_id, f"Лига {league_id}"),
        'outcome': outcome,
        'outcome_confidence': round(confidence, 1),
        'total': total_pred,
        'total_confidence': round(total_conf, 1),
        'btts': btts_pred,
        'btts_confidence': round(btts_conf, 1),
        'home_form': home_form_str,
        'away_form': away_form_str,
    }
    
    return prediction

def get_match_details(match_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"id": match_id}
    data = make_api_request(url, querystring)
    if data and 'response' in data and len(data['response']) > 0:
        return data['response'][0]
    return None

def generate_match_report(match_id):
    global predictions_db
    if match_id not in predictions_db:
        return "❌ Прогноз не найден"
    
    pred = predictions_db[match_id]
    match_data = get_match_details(match_id)
    
    if not match_data or match_data['fixture']['status']['short'] != 'FT':
        return "⏳ Матч еще не завершен"
    
    home_goals = match_data['goals']['home']
    away_goals = match_data['goals']['away']
    total_goals = home_goals + away_goals
    
    if home_goals > away_goals:
        actual_outcome = "П1"
    elif away_goals > home_goals:
        actual_outcome = "П2"
    else:
        actual_outcome = "X"
    
    actual_total = "БОЛЬШЕ 2.5" if total_goals > 2.5 else "МЕНЬШЕ 2.5"
    both_scored = home_goals > 0 and away_goals > 0
    actual_btts = "ДА" if both_scored else "НЕТ"
    
    outcome_icon = "✅" if actual_outcome == pred['outcome'] else "❌"
    total_icon = "✅" if actual_total in pred['total'] else "❌"
    btts_icon = "✅" if actual_btts in pred['btts'] else "❌"
    
    report = f"""
📊 *ОТЧЕТ ПО МАТЧУ*
━━━━━━━━━━━━━━━━
🏆 {pred['league_name']}
⚔️ {pred['home']} vs {pred['away']}
📅 {match_data['fixture']['date'][:10]}

*РЕЗУЛЬТАТ*
{pred['home']} {home_goals} : {away_goals} {pred['away']}

*СРАВНЕНИЕ*
📈 Исход: {pred['outcome']} ({pred['outcome_confidence']}%) {outcome_icon}
   Факт: {actual_outcome}

⚽ Тотал: {pred['total']} ({pred['total_confidence']}%) {total_icon}
   Факт: {actual_total}

🤝 Обе забьют: {pred['btts']} ({pred['btts_confidence']}%) {btts_icon}
   Факт: {actual_btts}
━━━━━━━━━━━━━━━━
"""
    return report

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = f"""
⚽ *Football Analyst* ⚽
📅 {datetime.now().strftime('%d.%m.%Y')}
🏆 Сезон: {get_current_season()}-{int(get_current_season())+1}

*Команды:*
/predict_all - прогнозы на все лиги
/predict_top5 - только топ-5 лиг
/reports - отчеты по матчам
/help - помощь

✅ Бот @Footballlyres_bot работает 24/7!
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    text = """
*КАК ПОЛЬЗОВАТЬСЯ:*

1️⃣ /predict_all - прогнозы на сегодня
2️⃣ Смотри матчи
3️⃣ /reports - отчеты после матчей

*Чтобы получить отчет по конкретному матчу:*
1. В прогнозе есть ID матча: `198765`
2. Напиши: `/report_198765`
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['reports'])
def send_reports(message):
    bot.reply_to(message, "📋 Собираю отчеты...")
    reports = []
    for match_id in predictions_db.keys():
        report = generate_match_report(match_id)
        if "не завершен" not in report and "не найден" not in report:
            reports.append(report)
    if not reports:
        bot.reply_to(message, "⏳ Нет завершенных матчей")
    else:
        bot.send_message(message.chat.id, "\n---\n".join(reports), parse_mode='Markdown')

@bot.message_handler(commands=['report_'])
def handle_report(message):
    try:
        match_id = message.text.split('_')[1]
        if match_id.isdigit():
            report = generate_match_report(int(match_id))
            bot.reply_to(message, report, parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Неверный формат. Используй: /report_123456")
    except:
        bot.reply_to(message, "❌ Ошибка. Используй: /report_123456")

def generate_predictions(league_filter=None):
    global predictions_db
    predictions_db = {}
    report = f"🔮 *ПРОГНОЗЫ НА {datetime.now().strftime('%d.%m.%Y')}*\n\n"
    
    for league_name, league_id in LEAGUES.items():
        if league_filter == 'top5' and league_id not in [39, 140, 78, 135, 235]:
            continue
        matches = get_todays_matches(league_id)
        if matches:
            report += f"*{league_name}:*\n"
            for match in matches:
                prediction = predict_match(match)
                if prediction:
                    predictions_db[prediction['match_id']] = prediction
                    report += f"⏰ {prediction['time']} {prediction['home']} vs {prediction['away']}\n"
                    report += f"   📈 {prediction['outcome']} ({prediction['outcome_confidence']}%)\n"
                    report += f"   ⚽ {prediction['total']}\n"
                    report += f"   🤝 {prediction['btts']}\n"
                    report += f"   🔑 `{prediction['match_id']}`\n\n"
            report += "---\n"
    return report

@bot.message_handler(commands=['predict_all'])
def predict_all(message):
    bot.reply_to(message, "🔍 Анализирую матчи...")
    report = generate_predictions()
    bot.send_message(message.chat.id, report, parse_mode='Markdown')

@bot.message_handler(commands=['predict_top5'])
def predict_top5(message):
    bot.reply_to(message, "🔍 Анализирую топ-5...")
    report = generate_predictions(league_filter='top5')
    bot.send_message(message.chat.id, report, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, "Используй /predict_all или /help")

def send_daily_predictions():
    global predictions_db
    predictions_db = {}
    for league_name, league_id in LEAGUES.items():
        matches = get_todays_matches(league_id)
        for match in matches:
            prediction = predict_match(match)
            if prediction:
                predictions_db[prediction['match_id']] = prediction
    print(f"✅ Прогнозы на {datetime.now().date()} сохранены")

def run_scheduler():
    schedule.every().day.at("09:00").do(send_daily_predictions)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    print("=" * 40)
    print("⚽ ЗАПУСК БОТА @Footballlyres_bot")
    print("=" * 40)
    print(f"🤖 Статус: ONLINE")
    print(f"📡 Проверка API...")
    
    # Тестовый запрос
    test_data = get_todays_matches(39)
    if test_data is not None:
        print("✅ API подключен")
    else:
        print("⚠️ API проблема, но бот продолжает работу")
    
    print("🔄 Запуск планировщика...")
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    print("✅ Бот готов к работе!")
    print("=" * 40)
    
    bot.infinity_polling()
