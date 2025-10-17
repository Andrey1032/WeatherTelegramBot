import requests
import time
import os
import json
from schedule import every, run_pending
from requests.exceptions import RequestException
from datetime import date
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # '4X6CBNA8AWJG45VGD2DEGLQSV'
# '7210067939:AAEWk5gO6OJIcUYLFvuNgygYa2m3XeLVUdc'
TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

PROXIES = {
    "http": "http://proxy.net.osu.ru:3128",
    "https": "http://proxy.net.osu.ru:3128"
}


def retry(func):
    def wrapper_retry(*args, **kwargs):
        retries = [5, 30]
        for seconds in retries:
            try:
                return func(*args, **kwargs)
            except RequestException:
                print(f"Failed to get data. Retrying in {seconds} seconds")
                time.sleep(seconds)
        return func(*args, **kwargs)
    return wrapper_retry


@retry
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
            "Ветер": data["days"][0]["windspeed"],
            "Прогноз": data["currentConditions"]["conditions"]
        },
    }
    return result_data


dateToday = str(date.today())


# dateToday = str(date.today())

# weather_by_days = get_weather_from_api(
#     date=dateToday, city="Оренбург")

# with open(f"weather_{dateToday}", 'w', encoding='utf-8') as file:
#     json.dump(weather_by_days, file, indent=4, ensure_ascii=False)

WEATHER_COMMANDS = {
    "Показать погоду": "get_weather",
    "Настроить ежедневные уведомления": "notifications",
}

try:
    bot = TeleBot(TG_BOT_TOKEN or "")

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = ReplyKeyboardMarkup(row_width=2)
        for command in WEATHER_COMMANDS.keys():
            item_button = KeyboardButton(command)
            markup.add(item_button)

    @bot.message_handler(func=lambda message: message.text in WEATHER_COMMANDS.keys())
    def send_weather(message):
        weather_command = WEATHER_COMMANDS[message.text]
        if weather_command == WEATHER_COMMANDS["Показать погоду"]:
            dateToday = str(date.today())
            weather = get_weather_from_api(
                date=dateToday, city="Оренбург")
            weather_str = json.dumps(weather, indent=4, ensure_ascii=False)
            bot.send_message(
                message.chat.id, f'<pre>{weather_str}</pre>', parse_mode="HTML")

    @bot.message_handler(func=lambda message: message.text in WEATHER_COMMANDS.keys())
    def send_notifications(message):
        weather_command = WEATHER_COMMANDS[message.text]
        if weather_command == WEATHER_COMMANDS["Настроить ежедневные уведомления"]:
            bot.send_message(
                message.chat.id, "Введите время (ЧЧ:ММ) в которое хотите получать прогноз погоды")

    @bot.message_handler(func=lambda message: len(message.text.split(":")) == 2)
    def add_notifications(message):
        every().day.at(message.text).do(lambda: send_weather(
            message={"text": "Показать погоду"}))

    bot.infinity_polling()

    while True:
        run_pending()

except:
    print("Ошибка работы бота")
