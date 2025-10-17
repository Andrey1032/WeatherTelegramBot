# Базовый образ Python
FROM python:3.10-slim-buster

# Установка базовых инструментов
RUN apt-get update && \
    apt-get install -y wget curl git

# Клонируем проект в контейнер
COPY . /app/
WORKDIR /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Команда для старта приложения
CMD ["python", "bot.py"]