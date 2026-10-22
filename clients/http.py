import random
import time
from typing import Any

import requests

from clients.exceptions import ExternalServiceError, HttpStatusError

TIMEOUT = (3, 7)
MAX_ATTEMPTS = 3
RETRY_STATUSES = {429, 500, 502, 503, 504}


def retry_delay(attempt: int, retry_after: str | None = None) -> float:
    """Use Retry-After seconds when valid, otherwise exponential backoff."""
    if retry_after is not None:
        try:
            delay = float(retry_after)
            if 0 <= delay < float("inf"):
                return delay
        except ValueError:
            pass
    return 2**attempt + random.uniform(0, 0.25)


def get_json(url: str, params: dict[str, str | int | float] | None = None) -> Any:
    """GET JSON, with three attempts for transient failures only."""
    for attempt in range(MAX_ATTEMPTS):
        try:
            response = requests.get(
                url,
                params=params,
                headers={"Accept": "application/json", "User-Agent": "CitySummary/1.0"},
                timeout=TIMEOUT,
                allow_redirects=False,
            )
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:
            if attempt == MAX_ATTEMPTS - 1:
                raise ExternalServiceError(
                    "Внешний сервис недоступен после трёх попыток"
                ) from exc
            time.sleep(retry_delay(attempt))
            continue
        except requests.exceptions.RequestException as exc:
            raise ExternalServiceError("Не удалось выполнить внешний запрос") from exc

        try:
            if response.status_code in RETRY_STATUSES:
                if attempt == MAX_ATTEMPTS - 1:
                    raise ExternalServiceError(
                        f"Внешний сервис недоступен после трёх попыток "
                        f"(HTTP {response.status_code})"
                    )
                delay = retry_delay(
                    attempt,
                    response.headers.get("Retry-After")
                    if response.status_code == 429
                    else None,
                )
            elif response.status_code != 200:
                raise HttpStatusError(response.status_code)
            else:
                content_type = response.headers.get("Content-Type", "").split(";")[0]
                content_type = content_type.strip().lower()
                if content_type != "application/json" and not content_type.endswith(
                    "+json"
                ):
                    raise ExternalServiceError("Внешний сервис вернул ответ не в JSON")
                try:
                    return response.json()
                except ValueError as exc:
                    raise ExternalServiceError(
                        "Внешний сервис вернул некорректный JSON"
                    ) from exc
        finally:
            response.close()
        time.sleep(delay)

    raise ExternalServiceError("Внешний сервис недоступен")
