# Используем базовый образ Python 3.13
FROM python:3.13

# Создаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы проекта внутрь рабочей директории
COPY . .

# Устанавливаем зависимости из файла requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем приложение
CMD ["python", "bot.py"]