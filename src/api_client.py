import requests
from config import WEATHER_API_KEY
from utils import retry

@retry(max_attempts=3, delay_seconds=(5, 30))
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
        "Часовой пояс": data['tzoffset'],
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
            "Ветер": data["currentConditions"]["windspeed"],
            "Прогноз": data["currentConditions"]["conditions"]
        },
    }
    return result_data