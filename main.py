from src.logger import *
from src.telegram_bot import bot
from src.scheduler import start_schedule_thread

if __name__ == "__main__":
    start_schedule_thread()
    bot.infinity_polling()