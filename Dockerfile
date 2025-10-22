# Базовый образ Python
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt ./

# Установливаем требуемые зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы приложения
COPY src ./src
COPY main.py .
# Запуск приложения
CMD ["python", "-u", "main.py"]