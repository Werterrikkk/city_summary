import math

from clients.exceptions import ExternalServiceError, NotFoundError
from clients.http import get_json


def get_weather(city: str) -> dict:
    geo_data = get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "en"},
    )
    results = geo_data.get("results", [])
    if geo_data.get("error") or not isinstance(results, list):
        raise ExternalServiceError("Некорректный ответ геокодинга")
    if not results:
        raise NotFoundError(f"Город не найден: {city}")
    location = results[0]
    if not isinstance(location, dict):
        raise ExternalServiceError("Некорректные данные города")
    lat = location.get("latitude")
    lon = location.get("longitude")
    if not all(
        type(value) in (int, float) and math.isfinite(value) for value in (lat, lon)
    ):
        raise ExternalServiceError("Некорректные координаты города")
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ExternalServiceError("Некорректные координаты города")

    data = get_json(
        "https://api.open-meteo.com/v1/forecast",
        {"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code"},
    )
    current = data.get("current")
    if not isinstance(current, dict):
        raise ExternalServiceError("В ответе нет данных о погоде")
    temp = current.get("temperature_2m")
    code = current.get("weather_code")
    if (
        type(temp) not in (int, float)
        or not math.isfinite(temp)
        or type(code) is not int
    ):
        raise ExternalServiceError("Некорректные данные о погоде")

    if code == 0:
        description = "clear sky"
    elif code in (1, 2, 3):
        description = "cloudy"
    elif code in (45, 48):
        description = "fog"
    elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        description = "rain"
    elif code in (71, 73, 75, 77, 85, 86):
        description = "snow"
    elif code in (95, 96, 99):
        description = "thunderstorm"
    else:
        raise ExternalServiceError("Неизвестный код погоды")
    return {"temp_c": float(temp), "description": description}
