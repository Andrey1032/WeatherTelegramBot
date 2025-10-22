import logger  # Загружаем конфигурацию логгера
from telegram_bot import bot
from scheduler import start_schedule_thread

if __name__ == "__main__":
    start_schedule_thread()
    bot.infinity_polling()