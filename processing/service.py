from typing import TypedDict

from clients.rates import get_rate
from clients.weather import get_weather
from processing.preprocessing import (
    ProcessedRate,
    ProcessedWeather,
    preprocess_rate,
    preprocess_weather,
)


class CitySummary(TypedDict):
    city: str
    weather: ProcessedWeather
    rates: ProcessedRate


def build_city_summary(city: str, currency: str = "USD") -> CitySummary:
    city = city.strip()
    currency = currency.strip().upper()
    weather = get_weather(city)
    rate = get_rate(currency)
    return {
        "city": city,
        "weather": preprocess_weather(weather),
        "rates": preprocess_rate(currency, rate),
    }
