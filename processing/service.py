from clients.rates import get_rate
from clients.weather import get_weather
from processing.preprocessing import preprocess_rate, preprocess_weather


def build_city_summary(city: str, currency: str = "USD") -> dict:
    weather = get_weather(city)
    rate = get_rate(currency)
    return {
        "city": city,
        "weather": preprocess_weather(weather),
        "rates": preprocess_rate(currency, rate),
    }
