import unittest
from unittest.mock import patch

from processing.preprocessing import preprocess_rate, preprocess_weather
from processing.service import build_city_summary


class PreprocessingTests(unittest.TestCase):
    def test_warm_clothes_threshold(self):
        for temp, expected in [(-0.1, True), (0, False), (20, False)]:
            with self.subTest(temp=temp):
                weather = {"temp_c": temp, "description": "clear sky"}
                self.assertEqual(preprocess_weather(weather)["warm_clothes"], expected)
                self.assertNotIn("warm_clothes", weather)

    def test_expensive_threshold(self):
        for rate, expected in [(99.99, False), (100, False), (100.01, True)]:
            with self.subTest(rate=rate):
                self.assertEqual(preprocess_rate("USD", rate)["expensive"], expected)

    @patch("processing.service.get_rate", return_value=101)
    @patch(
        "processing.service.get_weather",
        return_value={"temp_c": -1, "description": "snow"},
    )
    def test_builds_expected_summary_with_default_currency(self, weather, rate):
        self.assertEqual(
            build_city_summary(" Moscow "),
            {
                "city": "Moscow",
                "weather": {"temp_c": -1, "description": "snow", "warm_clothes": True},
                "rates": {"currency": "USD", "rate_to_rub": 101, "expensive": True},
            },
        )
        weather.assert_called_once_with("Moscow")
        rate.assert_called_once_with("USD")
