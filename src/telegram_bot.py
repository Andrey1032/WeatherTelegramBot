from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from src.config import TG_BOT_TOKEN
from src.scheduler import (
    save_user_settings,
    subtract_hours,
    send_weather,
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
        send_weather(bot, message.from_user.id)
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

if __name__ == "__main__":
    start_schedule_thread()
    bot.infinity_polling()