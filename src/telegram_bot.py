import logging
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from src.config import TG_BOT_TOKEN
from datetime import date 
from requests.exceptions import RequestException
from src.api_client import get_weather_from_api
from src.scheduler import (
    save_user_settings,
    subtract_hours,
    start_schedule_thread
)

bot = TeleBot(TG_BOT_TOKEN)

WEATHER_COMMANDS = {
    "Показать погоду": "get_weather",
    "Настроить ежедневные уведомления": "set_notifications",
}

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

if __name__ == "__main__":
    start_schedule_thread()
    bot.infinity_polling()