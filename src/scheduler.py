import os
import json
import time
from datetime import date 
from requests.exceptions import RequestException
import logging
from schedule import every, run_pending
from threading import Thread
from telegram_bot import bot
import config
from api_client import get_weather_from_api

def load_user_settings(user_id):
    file_path = os.path.join(config.USER_SETTINGS_DIR, f"{user_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return None

def save_user_settings(user_id, settings):
    file_path = os.path.join(config.USER_SETTINGS_DIR, f"{user_id}.json")
    try:
        with open(file_path, 'w') as file:
            json.dump(settings, file)
    except Exception as e:
        logging.error(f"Ошибка сохранения настроек пользователя {user_id}: {e}")

def start_schedule_thread():
    thread = Thread(target=schedule_loop)
    thread.start()

def send_weather(user_id):
    today_date = str(date.today())
    try:
        weather = get_weather_from_api(date=today_date, city="Оренбург")
        result = [
            f"Погода в городе {weather['Адрес']}:",
            f"Сегодня:\n"
            f"Темп.: {weather['Сегодня']['Температура']}°C\n"
            f"Макс. темп.: {weather['Сегодня']['Макс. температура']}°C\n"
            f"Мин. темп.: {weather['Сегодня']['Мин. температура']}°C\n"
            f"Ветер: {weather['Сегодня']['Ветер']} м/с\n"
            f"Влажность: {weather['Сегодня']['Влажность']}%\n"
            f"Описание: {weather['Сегодня']['Прогноз']}\n",
            f"\nСейчас:\n"
            f"Темп.: {weather['Прямо сейчас']['Температура']}°C\n"
            f"Влажность: {weather['Прямо сейчас']['Влажность']}%\n"
            f"Ветер: {weather['Прямо сейчас']['Ветер']} м/с\n"
            f"Описание: {weather['Прямо сейчас']['Прогноз']}"
        ]
        bot.send_message(user_id, "\n".join(result))
    except RequestException as e:
        logging.error(f"Ошибка получения погоды: {e}")
        bot.send_message(user_id, "Возникла ошибка при получении погоды.")

def schedule_loop():
    scheduled_jobs = {}

    users_with_settings = []
    for filename in os.listdir(config.USER_SETTINGS_DIR):
        if filename.endswith(".json"):
            user_id = int(filename[:-5])  # Удаляем расширение .json
            settings = load_user_settings(user_id)
            if settings:
                users_with_settings.append((user_id, settings["notification_time"]))

    # Обновляем существующие задания и добавляем новые
    for user_id, notification_time in users_with_settings:
        job_key = f"{user_id}-{notification_time}"
        if job_key not in scheduled_jobs:
            job = every().day.at(notification_time).do(send_weather, user_id=user_id)
            scheduled_jobs[job_key] = job
        else:
            existing_job = scheduled_jobs.pop(job_key, None)
            if existing_job is not None:
                existing_job.cancel()

    while True:
        run_pending()
        time.sleep(1)

def subtract_hours(time_str):
    from datetime import datetime, timedelta
    # Преобразуем строку типа '10:02' в объект datetime
    time_obj = datetime.strptime(time_str+":00", '%H:%M:%S')

    # Отнимаем 5 часов
    new_time = time_obj - timedelta(hours=5)

    # Возвращаем обратно в формат 'ЧЧ:ММ'
    return new_time.strftime('%H:%M:%S')