from typing import TypedDict

from clients.weather import Weather


class ProcessedWeather(Weather):
    warm_clothes: bool


class ProcessedRate(TypedDict):
    currency: str
    rate_to_rub: float
    expensive: bool


def preprocess_weather(weather: Weather) -> ProcessedWeather:
    return {**weather, "warm_clothes": weather["temp_c"] < 0}


def preprocess_rate(currency: str, rate: float) -> ProcessedRate:
    return {"currency": currency, "rate_to_rub": rate, "expensive": rate > 100}
