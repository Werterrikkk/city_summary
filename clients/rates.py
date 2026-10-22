import math

from clients.exceptions import ExternalServiceError, HttpStatusError, NotFoundError
from clients.http import get_json


def get_rate(currency: str) -> float:
    try:
        data = get_json(f"https://api.frankfurter.dev/v2/rate/{currency}/RUB")
    except HttpStatusError as error:
        if error.status_code in (404, 422):
            raise NotFoundError(f"Валюта не найдена: {currency}") from error
        raise

    rate = data.get("rate")
    if data.get("base") != currency or data.get("quote") != "RUB":
        raise ExternalServiceError("Некорректная валютная пара")
    if type(rate) not in (int, float) or not math.isfinite(rate) or rate <= 0:
        raise ExternalServiceError("Некорректный курс валюты")
    return float(rate)
