import math
from typing import Any

from clients.exceptions import ExternalServiceError


def require_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExternalServiceError(f"Некорректное числовое поле: {field}")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ExternalServiceError(f"Слишком большое значение: {field}") from exc
    if not math.isfinite(result):
        raise ExternalServiceError(f"Неконечное значение: {field}")
    return result
