import os
import json
import time
import logging
from schedule import every, run_pending
from threading import Thread
from src.config import USER_SETTINGS_DIR

def load_user_settings(user_id):
    file_path = os.path.join(USER_SETTINGS_DIR, f"{user_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return None

def save_user_settings(user_id, settings):
    file_path = os.path.join(USER_SETTINGS_DIR, f"{user_id}.json")
    try:
        with open(file_path, 'w') as file:
            json.dump(settings, file)
    except Exception as e:
        logging.error(f"Ошибка сохранения настроек пользователя {user_id}: {e}")

def start_schedule_thread():
    thread = Thread(target=schedule_loop)
    thread.start()



def schedule_loop():
    scheduled_jobs = {}

    users_with_settings = []
    for filename in os.listdir(USER_SETTINGS_DIR):
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