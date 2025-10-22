import logging
import sys

# Настройка логгера: запись в файл + вывод в консоль
log_formatter = logging.Formatter(
    '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d]: %(message)s')
file_handler = logging.FileHandler('bot.log')
console_handler = logging.StreamHandler(sys.stdout)

for handler in [file_handler, console_handler]:
    handler.setFormatter(log_formatter)
    logging.root.addHandler(handler)

logging.root.setLevel(logging.INFO)