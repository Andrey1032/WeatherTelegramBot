import sys
import requests
import time
import json
import os
import logging
from schedule import every, run_pending
from requests.exceptions import RequestException
from datetime import date, datetime, timedelta
from threading import Thread
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Настройка логгера: запись в файл + вывод в консоль
log_formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d]: %(message)s')
file_handler = logging.FileHandler('bot.log')
console_handler = logging.StreamHandler(sys.stdout)

for handler in [file_handler, console_handler]:
    handler.setFormatter(log_formatter)
    logging.root.addHandler(handler)

logging.root.setLevel(logging.INFO)

WEATHER_API_KEY = "4X6CBNA8AWJG45VGD2DEGLQSV"
TG_BOT_TOKEN = "7210067939:AAEWk5gO6OJIcUYLFvuNgygYa2m3XeLVUdc"

USER_SETTINGS_DIR = "./user_settings/"
os.makedirs(USER_SETTINGS_DIR, exist_ok=True)


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


def retry(max_attempts=3, delay_seconds=(5, 30)):
    def decorator(func):
        def wrapper_retry(*args, **kwargs):
            attempts = 0
            while attempts <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except RequestException as e:
                    attempts += 1
                    if attempts > max_attempts:
                        raise Exception("Максимальное количество попыток превышено.")
                    else:
                        logging.error(f"Ошибка при выполнении запроса ({attempts}). Ошибка: {e}")
                        print(f"Ошибка при выполнении запроса ({attempts}). Повторная попытка через {delay_seconds[attempts-1]} сек...")
                        time.sleep(delay_seconds[attempts-1])
        return wrapper_retry
    return decorator


@retry(max_attempts=3, delay_seconds=(5, 30))
def get_weather_from_api(*, date: str, city: str) -> dict:
    url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{date}/{date}'
    response = requests.get(url, params={
        "unitGroup": 'metric',
        "lang": "ru",
        "include": "days,alerts,current,events",
        "key": WEATHER_API_KEY
    })
    data = response.json()

    result_data = {
        "Адрес": data['resolvedAddress'],
        "Часовой пояс": data['tzoffset'],
        "Сегодня": {
            "Температура": data["days"][0]["temp"],
            "Макс. температура": data["days"][0]["tempmax"],
            "Мин. температура": data["days"][0]["tempmin"],
            "Ветер": data["days"][0]["windspeed"],
            "Влажность": data["days"][0]["humidity"],
            "Прогноз": data["days"][0]["description"]
        },
        "Прямо сейчас": {
            "Температура": data["currentConditions"]["temp"],
            "Влажность": data["currentConditions"]["humidity"],
            "Ветер": data["currentConditions"]["windspeed"],
            "Прогноз": data["currentConditions"]["conditions"]
        },
    }
    return result_data


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
    while True:
        # Планирование уведомлений выполняется ТОЛЬКО ОДИН РАЗ!
        users_with_settings = []
        for filename in os.listdir(USER_SETTINGS_DIR):
            if filename.endswith(".json"):
                user_id = int(filename[:-5])  # Удаляем расширение .json
                settings = load_user_settings(user_id)
                if settings:
                    users_with_settings.append((user_id, settings["notification_time"]))
        
        # Добавляем уведомления для каждого пользователя только однажды
        for user_id, notification_time in users_with_settings:
            every().day.at(notification_time).do(send_weather, user_id=user_id)
        
        # Выход из функции после первого выполнения
        break

    # Основной цикл для проверки и выполнения заданий
    while True:
        run_pending()
        time.sleep(1)


def subtract_hours(time_str):
    # Преобразуем строку типа '10:02' в объект datetime
    time_obj = datetime.strptime(time_str+":00", '%H:%M:%S')
    
    # Отнимаем 5 часов
    new_time = time_obj - timedelta(hours=5)
    
    # Возвращаем обратно в формат 'ЧЧ:ММ'
    return new_time.strftime('%H:%M:%S')


def set_notification_time(message):
    user_id = message.from_user.id
    notification_time = message.text.strip()
    parts = notification_time.split(":")

    # Проверка правильности ввода времени
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        bot.send_message(message.chat.id, "Некорректный формат времени. Введите ЧЧ:ММ.")
        return
    hour, minute = map(int, parts)
    if not (0 <= hour < 24 and 0 <= minute < 60):
        bot.send_message(message.chat.id, "Некорректный формат времени. Введите ЧЧ:ММ.")
        return

    # Сохраняем новые настройки
    settings = {"user_id": user_id, "notification_time": subtract_hours(notification_time)}
    save_user_settings(user_id, settings)
    bot.send_message(message.chat.id, f"Уведомления будут приходить ежедневно в {notification_time}.")


WEATHER_COMMANDS = {
    "Показать погоду": "get_weather",
    "Настроить ежедневные уведомления": "set_notifications",
}
bot = TeleBot(TG_BOT_TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for command in WEATHER_COMMANDS.keys():
        item_button = KeyboardButton(command)
        markup.add(item_button)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите команду:", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text in WEATHER_COMMANDS.keys())
def handle_commands(message):
    if message.text == "Показать погоду":
        send_weather(message.from_user.id)
    elif message.text == "Настроить ежедневные уведомления":
        bot.send_message(message.chat.id, "Введите время (ЧЧ:ММ) в которое хотите получать прогноз погоды")


@bot.message_handler(func=lambda m: len(m.text.split(":")) == 2)
def handle_set_notifications(message):
    set_notification_time(message)


start_schedule_thread()
bot.infinity_polling()