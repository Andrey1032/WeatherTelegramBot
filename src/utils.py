import functools
import time
import logging
from requests.exceptions import RequestException

def retry(max_attempts=3, delay_seconds=(5, 30)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper_retry(*args, **kwargs):
            attempts = 0
            while attempts <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except RequestException as e:
                    attempts += 1
                    if attempts > max_attempts:
                        raise Exception("Максимальное количество попыток превышено.")
                    else:
                        logging.error(f"Ошибка при выполнении запроса ({attempts}). Ошибка: {e}")
                        print(f"Ошибка при выполнении запроса ({attempts}). Повторная попытка через {delay_seconds[attempts-1]} сек...")
                        time.sleep(delay_seconds[attempts-1])
        return wrapper_retry
    return decorator