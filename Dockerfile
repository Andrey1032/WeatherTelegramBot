# Базовый образ Python
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt ./

# Установливаем требуемые зависимости
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
# Запуск приложения
CMD ["python", "bot.py"]