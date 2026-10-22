import re

from clients.exceptions import ExternalServiceError, HttpStatusError, NotFoundError
from clients.http import get_json
from clients.validation import require_number

RATE_URL = "https://api.frankfurter.dev/v2/rate/{currency}/RUB"


def get_rate(currency: str) -> float:
    currency = currency.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise NotFoundError(f"Код валюты не найден: {currency}")
    try:
        data = get_json(RATE_URL.format(currency=currency))
    except HttpStatusError as exc:
        # Frankfurter v2 returns 422 for an unknown currency.
        if exc.status_code in {404, 422}:
            raise NotFoundError(f"Код валюты не найден: {currency}") from exc
        raise
    if not isinstance(data, dict):
        raise ExternalServiceError("Некорректный ответ сервиса курсов")
    if data.get("base") != currency or data.get("quote") != "RUB":
        raise ExternalServiceError("Сервис курсов вернул другую валютную пару")
    rate = require_number(data.get("rate"), "rate")
    if rate <= 0:
        raise ExternalServiceError("Курс должен быть положительным")
    return rate
