import unittest
from unittest.mock import patch

from clients.exceptions import ExternalServiceError, HttpStatusError, NotFoundError
from clients.rates import get_rate
from clients.weather import get_weather

LOCATION = {"results": [{"latitude": 55.75, "longitude": 37.62}]}
WEATHER = {"current": {"temperature_2m": -3.2, "weather_code": 0}}
RATE = {"base": "USD", "quote": "RUB", "rate": 92.15}


class WeatherTests(unittest.TestCase):
    @patch("clients.weather.get_json", side_effect=[LOCATION, WEATHER])
    def test_weather_uses_geocoding_then_forecast(self, get):
        self.assertEqual(
            get_weather("Moscow"), {"temp_c": -3.2, "description": "clear sky"}
        )
        self.assertEqual(get.call_count, 2)
        params = get.call_args_list[1].args[1]
        self.assertEqual(params["latitude"], 55.75)
        self.assertEqual(params["longitude"], 37.62)
        self.assertEqual(params["temperature_unit"], "celsius")

    @patch("clients.weather.get_json")
    def test_missing_city(self, get):
        for payload in ({}, {"results": []}, {"generationtime_ms": 1}):
            with self.subTest(payload=payload):
                get.return_value = payload
                with self.assertRaises(NotFoundError):
                    get_weather("NoSuchCity")

    @patch("clients.weather.get_json")
    def test_bad_geocoding_contract(self, get):
        for payload in (
            [],
            {"error": True},
            {"results": None},
            {"results": [None]},
            {"results": [{}]},
            {"results": [{"latitude": True, "longitude": 0}]},
            {"results": [{"latitude": 100, "longitude": 0}]},
        ):
            with self.subTest(payload=payload):
                get.return_value = payload
                with self.assertRaises(ExternalServiceError):
                    get_weather("Moscow")

    @patch("clients.weather.get_json")
    def test_bad_weather_contract(self, get):
        for payload in (
            [],
            {},
            {"current": None},
            {"current": {}},
            {"current": {"temperature_2m": "-3", "weather_code": 0}},
            {"current": {"temperature_2m": float("nan"), "weather_code": 0}},
            {"current": {"temperature_2m": True, "weather_code": 0}},
            {"current": {"temperature_2m": 1, "weather_code": True}},
            {"current": {"temperature_2m": 1, "weather_code": 999}},
        ):
            with self.subTest(payload=payload):
                get.side_effect = [LOCATION, payload]
                with self.assertRaises(ExternalServiceError):
                    get_weather("Moscow")


class RatesTests(unittest.TestCase):
    @patch("clients.rates.get_json", return_value=RATE)
    def test_normalizes_currency_and_returns_float(self, get):
        self.assertEqual(get_rate(" usd "), 92.15)
        self.assertTrue(get.call_args.args[0].endswith("/USD/RUB"))

    @patch("clients.rates.get_json")
    def test_unknown_currency_is_not_found(self, get):
        for status in (404, 422):
            with self.subTest(status=status):
                get.side_effect = HttpStatusError(status)
                with self.assertRaises(NotFoundError):
                    get_rate("ZZZ")

    @patch("clients.rates.get_json", side_effect=HttpStatusError(403))
    def test_forbidden_is_service_error(self, get):
        with self.assertRaises(ExternalServiceError):
            get_rate("USD")

    @patch("clients.rates.get_json")
    def test_bad_rate_contract(self, get):
        payloads = [[], {}, {**RATE, "base": "EUR"}, {**RATE, "quote": "EUR"}]
        payloads.extend(
            {**RATE, "rate": value}
            for value in (None, True, "90", 0, -1, float("inf"), float("nan"))
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                get.return_value = payload
                with self.assertRaises(ExternalServiceError):
                    get_rate("USD")
