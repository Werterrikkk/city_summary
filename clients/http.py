import math
import time

import requests

from clients.exceptions import ExternalServiceError, HttpStatusError


def get_json(url: str, params: dict | None = None) -> dict:
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=10)
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as error:
            if attempt == 2:
                raise ExternalServiceError(
                    "Сервис недоступен после трёх попыток"
                ) from error
            time.sleep(1)
            continue
        except requests.exceptions.RequestException as error:
            raise ExternalServiceError("Не удалось выполнить запрос") from error

        if response.status_code in (429, 500, 502, 503, 504):
            delay = 1.0
            if response.status_code == 429:
                try:
                    delay = float(response.headers.get("Retry-After", "1"))
                    if not math.isfinite(delay) or delay < 0:
                        delay = 1.0
                except ValueError:
                    delay = 1.0
            response.close()
            if attempt == 2:
                raise ExternalServiceError("Сервис недоступен после трёх попыток")
            time.sleep(delay)
            continue

        try:
            if response.status_code != 200:
                raise HttpStatusError(response.status_code)
            data = response.json()
            if not isinstance(data, dict):
                raise ExternalServiceError("Некорректный ответ сервиса")
            return data
        except ValueError as error:
            raise ExternalServiceError("Сервис вернул некорректный JSON") from error
        finally:
            response.close()

    raise ExternalServiceError("Сервис недоступен")
