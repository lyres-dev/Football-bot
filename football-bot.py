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
TELEGRAM_TOKEN = "8189906948:AAEJngihjXV30o405ceIHiSO5qtoenF41Ac"
FOOTBALL_DATA_KEY = "a7ed4a97c64f488d93451b95c177eb68"
# ============================================

# Сброс вебхуков
requests.get(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=True')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ID лиг для Football-Data.org
LEAGUES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ": 2021,
    "🇪🇸 Ла Лига": 2014,
    "🇩🇪 Бундеслига": 2002,
    "🇮🇹 Серия А": 2019,
    "🇷🇺 РПЛ": 235,  # Может отличаться
    "🇧🇷 Бразильская Серия А": 2013,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Чемпионшип": 2016,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Лига 1": 2024,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Лига 2": 2025,
}

LEAGUE_NAMES = {v: k for k, v in LEAGUES.items()}
predictions_db = {}

print("⚽ Football Data Bot - ПОЛНАЯ ВЕРСИЯ")
print(f"🤖 Бот: @lyressports_bot")
print(f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}")

def make_football_request(endpoint, params=None):
    """Запрос к Football-Data.org API"""
    url = f"https://api.football-data.org/v4/{endpoint}"
    headers = {
        "X-Auth-Token": FOOTBALL_DATA_KEY
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка API: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None

def get_todays_matches():
    """Получает матчи на сегодня"""
    today = datetime.now().strftime("%Y-%m-%d")
    params = {
        "dateFrom": today,
        "dateTo": today
    }
    data = make_football_request("matches", params)
    if data and 'matches' in data:
        return data['matches']
    return []

def get_team_matches(team_id, limit=5):
    """Получает последние матчи команды"""
    params = {
        "limit": limit,
        "status": "FINISHED"
    }
    data = make_football_request(f"teams/{team_id}/matches", params)
    if data and 'matches' in data:
        return data['matches']
    return []

def analyze_team_form(matches):
    """Анализирует форму команды по последним матчам"""
    if not matches:
        return None
    
    stats = {
        'wins': 0,
        'draws': 0,
        'losses': 0,
        'goals_scored': 0,
        'goals_conceded': 0,
        'both_scored': 0,
        'total_matches': len(matches)
    }
    
    for match in matches:
        # Определяем, где наша команда
        if match['score']['winner'] == 'HOME_TEAM':
            stats['wins'] += 1
        elif match['score']['winner'] == 'AWAY_TEAM':
            stats['losses'] += 1
        else:
            stats['draws'] += 1
        
        # Голы
        stats['goals_scored'] += match['score']['fullTime']['home'] if match['score']['fullTime']['home'] else 0
        stats['goals_conceded'] += match['score']['fullTime']['away'] if match['score']['fullTime']['away'] else 0
        
        # Обе забьют
        if match['score']['fullTime']['home'] and match['score']['fullTime']['away']:
            if match['score']['fullTime']['home'] > 0 and match['score']['fullTime']['away'] > 0:
                stats['both_scored'] += 1
    
    return stats

def predict_match(match):
    """ДЕТАЛЬНЫЙ АНАЛИЗ МАТЧА"""
    home_team = match['homeTeam']
    away_team = match['awayTeam']
    match_time = match['utcDate'][11:16]
    match_id = match['id']
    league_id = match['competition']['id']
    league_name = LEAGUE_NAMES.get(league_id, match['competition']['name'])
    
    # Получаем форму команд
    home_matches = get_team_matches(home_team['id'], 5)
    away_matches = get_team_matches(away_team['id'], 5)
    
    home_stats = analyze_team_form(home_matches)
    away_stats = analyze_team_form(away_matches)
    
    if not home_stats or not away_stats:
        return None
    
    # Расчет средних показателей
    home_avg_scored = home_stats['goals_scored'] / home_stats['total_matches'] if home_stats['total_matches'] > 0 else 0
    home_avg_conceded = home_stats['goals_conceded'] / home_stats['total_matches'] if home_stats['total_matches'] > 0 else 0
    away_avg_scored = away_stats['goals_scored'] / away_stats['total_matches'] if away_stats['total_matches'] > 0 else 0
    away_avg_conceded = away_stats['goals_conceded'] / away_stats['total_matches'] if away_stats['total_matches'] > 0 else 0
    
    # ПРОГНОЗ НА ИСХОД
    home_strength = (home_avg_scored * 1.2) - (away_avg_conceded * 0.8) + 0.3
    away_strength = (away_avg_scored * 1.2) - (home_avg_conceded * 0.8)
    total_strength = home_strength + away_strength
    
    if total_strength > 0:
        home_win_prob = (home_strength / total_strength) * 100
        away_win_prob = (away_strength / total_strength) * 100
    else:
        home_win_prob = 40
        away_win_prob = 40
    
    draw_prob = 100 - home_win_prob - away_win_prob
    if draw_prob < 0:
        draw_prob = 20
    
    if home_win_prob > 45:
        outcome = "П1"
        confidence = home_win_prob
    elif away_win_prob > 45:
        outcome = "П2"
        confidence = away_win_prob
    else:
        outcome = "X"
        confidence = draw_prob
    
    # ПРОГНОЗ НА ТОТАЛ
    expected_total = (home_avg_scored + away_avg_scored + home_avg_conceded + away_avg_conceded) / 2
    
    if expected_total > 2.7:
        total_pred = "Тотал БОЛЬШЕ 2.5"
        total_conf = min(85, 50 + (expected_total - 2.5) * 30)
    elif expected_total < 2.3:
        total_pred = "Тотал МЕНЬШЕ 2.5"
        total_conf = min(85, 50 + (2.5 - expected_total) * 30)
    else:
        total_pred = "Тотал 2.5 (неопределенно)"
        total_conf = 50
    
    # ПРОГНОЗ НА ОБЕ ЗАБЬЮТ
    home_btts = (home_stats['both_scored'] / home_stats['total_matches'] * 100) if home_stats['total_matches'] > 0 else 0
    away_btts = (away_stats['both_scored'] / away_stats['total_matches'] * 100) if away_stats['total_matches'] > 0 else 0
    avg_btts = (home_btts + away_btts) / 2
    
    btts_pred = "Обе забьют - ДА" if avg_btts > 60 else "Обе забьют - НЕТ"
    
    # Форма команд для отображения
    home_form_str = f"{home_stats['wins']}-{home_stats['draws']}-{home_stats['losses']}"
    away_form_str = f"{away_stats['wins']}-{away_stats['draws']}-{away_stats['losses']}"
    
    prediction = {
        'match_id': match_id,
        'home': home_team['name'],
        'away': away_team['name'],
        'time': match_time,
        'date': match['utcDate'][:10],
        'league_name': league_name,
        'outcome': outcome,
        'outcome_confidence': round(confidence, 1),
        'total': total_pred,
        'total_confidence': round(total_conf, 1),
        'btts': btts_pred,
        'home_form': home_form_str,
        'away_form': away_form_str,
        'home_avg': f"{home_avg_scored:.1f}/{home_avg_conceded:.1f}",
        'away_avg': f"{away_avg_scored:.1f}/{away_avg_conceded:.1f}"
    }
    
    return prediction

def check_match_result(match_id):
    """Проверяет результат завершенного матча"""
    data = make_football_request(f"matches/{match_id}")
    if data:
        return data
    return None

def generate_match_report(match_id):
    """Генерирует отчет по матчу"""
    global predictions_db
    
    if match_id not in predictions_db:
        return "❌ Прогноз не найден"
    
    pred = predictions_db[match_id]
    match_data = check_match_result(match_id)
    
    if not match_data or match_data['status'] != 'FINISHED':
        return "⏳ Матч еще не завершен"
    
    # Результат
    home_goals = match_data['score']['fullTime']['home']
    away_goals = match_data['score']['fullTime']['away']
    
    if home_goals > away_goals:
        actual_outcome = "П1"
    elif away_goals > home_goals:
        actual_outcome = "П2"
    else:
        actual_outcome = "X"
    
    total_goals = home_goals + away_goals
    actual_total = "БОЛЬШЕ 2.5" if total_goals > 2.5 else "МЕНЬШЕ 2.5"
    
    both_scored = home_goals > 0 and away_goals > 0
    actual_btts = "ДА" if both_scored else "НЕТ"
    
    outcome_icon = "✅" if actual_outcome == pred['outcome'] else "❌"
    total_icon = "✅" if actual_total in pred['total'] else "❌"
    btts_icon = "✅" if actual_btts == pred['btts'] else "❌"
    
    report = f"""
📊 *ОТЧЕТ ПО МАТЧУ*
━━━━━━━━━━━━━━━━
🏆 {pred['league_name']}
⚔️ {pred['home']} vs {pred['away']}
📅 {pred['date']}

*РЕЗУЛЬТАТ*
{pred['home']} {home_goals} : {away_goals} {pred['away']}

*СРАВНЕНИЕ С ПРОГНОЗОМ*
📈 Исход: {pred['outcome']} ({pred['outcome_confidence']}%) {outcome_icon}
   Факт: {actual_outcome}

⚽ Тотал: {pred['total']} ({pred['total_confidence']}%) {total_icon}
   Факт: {actual_total}

🤝 Обе забьют: {pred['btts']} {btts_icon}
   Факт: {actual_btts}

📊 Статистика команд (до матча):
🏠 {pred['home']}: {pred['home_form']} (ср. {pred['home_avg']})
✈️ {pred['away']}: {pred['away_form']} (ср. {pred['away_avg']})
━━━━━━━━━━━━━━━━
"""
    return report

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = f"""
⚽ *Lyres Sports Bot* ⚽
📅 {datetime.now().strftime('%d.%m.%Y')}

*Доступные команды:*
/predict - прогнозы на сегодня
/reports - отчеты по матчам
/report_[ID] - отчет по конкретному матчу
/stats - статистика прогнозов
/help - помощь

*Анализируемые лиги:* АПЛ, ЛаЛига, Бундеслига, Серия А, Бразилия, Чемпионшип
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    text = """
🔍 *КАК РАБОТАЕТ:*
• Анализ последних 5 матчей каждой команды
• Учет забитых/пропущенных голов
• Прогноз исхода с % уверенности
• Прогноз тотала (Больше/Меньше 2.5)
• Прогноз на "Обе забьют"

📋 *После матчей используй:*
/reports - все отчеты
/report_12345 - конкретный матч

📊 *Статистика:*
/stats - точность прогнозов
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['predict'])
def predict(message):
    bot.reply_to(message, "🔍 Анализирую матчи на сегодня...")
    
    global predictions_db
    predictions_db = {}
    
    matches = get_todays_matches()
    
    if not matches:
        bot.reply_to(message, "😴 Сегодня нет матчей")
        return
    
    report = f"🔮 *ПРОГНОЗЫ НА {datetime.now().strftime('%d.%m.%Y')}*\n\n"
    
    for match in matches:
        if match['competition']['id'] in LEAGUES.values():
            prediction = predict_match(match)
            if prediction:
                predictions_db[prediction['match_id']] = prediction
                report += f"*{prediction['league_name']}*\n"
                report += f"⏰ {prediction['time']} {prediction['home']} vs {prediction['away']}\n"
                report += f"   📈 Исход: {prediction['outcome']} ({prediction['outcome_confidence']}%)\n"
                report += f"   ⚽ Тотал: {prediction['total']} ({prediction['total_confidence']}%)\n"
                report += f"   🤝 {prediction['btts']}\n"
                report += f"   📊 Форма: {prediction['home_form']} | {prediction['away_form']}\n"
                report += f"   🔑 `{prediction['match_id']}`\n\n"
    
    bot.send_message(message.chat.id, report, parse_mode='Markdown')

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
        for report in reports:
            bot.send_message(message.chat.id, report, parse_mode='Markdown')

@bot.message_handler(commands=['report_'])
def handle_report(message):
    try:
        match_id = int(message.text.split('_')[1])
        report = generate_match_report(match_id)
        bot.reply_to(message, report, parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Используй: /report_12345")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    bot.reply_to(message, "📊 Статистика будет после первых матчей")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, "Используй /predict или /help")

# ============================================
# ЗАПУСК
# ============================================

def send_daily_predictions():
    """Автоматический сбор прогнозов"""
    global predictions_db
    predictions_db = {}
    matches = get_todays_matches()
    for match in matches:
        if match['competition']['id'] in LEAGUES.values():
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
    print("=" * 50)
    print("⚽ ЗАПУСК ПОЛНОЙ ВЕРСИИ")
    print("=" * 50)
    print(f"📊 Лиг в базе: {len(LEAGUES)}")
    print(f"🤖 Бот: @lyressports_bot")
    
    # Запуск планировщика
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    print("✅ Бот готов к работе!")
    bot.infinity_polling()
