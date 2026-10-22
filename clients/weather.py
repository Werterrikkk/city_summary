from typing import TypedDict

from clients.exceptions import ExternalServiceError, NotFoundError
from clients.http import get_json
from clients.validation import require_number

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_DESCRIPTIONS = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow fall",
    73: "moderate snow fall",
    75: "heavy snow fall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


class Weather(TypedDict):
    temp_c: float
    description: str


def get_weather(city: str) -> Weather:
    locations = get_json(
        GEOCODING_URL, {"name": city, "count": 1, "language": "en", "format": "json"}
    )
    if not isinstance(locations, dict) or locations.get("error"):
        raise ExternalServiceError("Некорректный ответ геокодинга")
    # Open-Meteo omits results when there are no matches.
    results = locations.get("results", [])
    if not isinstance(results, list):
        raise ExternalServiceError("Некорректный список городов")
    if not results:
        raise NotFoundError(f"Город не найден: {city}")
    location = results[0]
    if not isinstance(location, dict):
        raise ExternalServiceError("Некорректные данные города")
    latitude = require_number(location.get("latitude"), "latitude")
    longitude = require_number(location.get("longitude"), "longitude")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ExternalServiceError("Координаты города вне допустимого диапазона")

    data = get_json(
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code",
            "temperature_unit": "celsius",
        },
    )
    if not isinstance(data, dict) or not isinstance(data.get("current"), dict):
        raise ExternalServiceError("В ответе погоды нет объекта current")
    current = data["current"]
    temp_c = require_number(current.get("temperature_2m"), "temperature_2m")
    code = current.get("weather_code")
    if type(code) is not int or code not in WEATHER_DESCRIPTIONS:
        raise ExternalServiceError("Неизвестный или некорректный код погоды")
    return {"temp_c": temp_c, "description": WEATHER_DESCRIPTIONS[code]}
