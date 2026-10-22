import contextlib
import io
import json
import unittest
from unittest.mock import patch

from clients.exceptions import ExternalServiceError, NotFoundError
from main import main

SUMMARY = {
    "city": "Moscow",
    "weather": {"temp_c": -3.2, "description": "clear sky", "warm_clothes": True},
    "rates": {"currency": "USD", "rate_to_rub": 92.15, "expensive": False},
}


class CliTests(unittest.TestCase):
    @patch("main.build_city_summary", return_value=SUMMARY)
    def test_success_and_default_currency(self, build):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["--city", "Moscow"]), 0)
        build.assert_called_once_with("Moscow", "USD")
        self.assertIn("Тёплая одежда: да", output.getvalue())
        self.assertIn("USD→RUB: 92.15", output.getvalue())
        self.assertIn("Дорогой курс: нет", output.getvalue())

    @patch("main.build_city_summary", return_value=SUMMARY)
    def test_json_is_valid_and_currency_is_normalized(self, build):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(
                main(["--city", "Moscow", "--currency", "eur", "--json"]), 0
            )
        self.assertEqual(json.loads(output.getvalue()), SUMMARY)
        build.assert_called_once_with("Moscow", "EUR")

    @patch("main.build_city_summary")
    def test_bad_arguments_exit_2_before_network(self, build):
        for args in (
            [],
            ["--city", " "],
            ["--city", "Moscow", "--currency", "EU"],
            ["--city", "Moscow", "--currency", "123"],
            ["--unknown"],
        ):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    main(args)
                self.assertEqual(caught.exception.code, 2)
        build.assert_not_called()

    @patch("main.build_city_summary")
    def test_application_errors_exit_3_or_4_and_only_use_stderr(self, build):
        for error, expected in [
            (NotFoundError("Город не найден"), 3),
            (NotFoundError("Код валюты не найден"), 3),
            (ExternalServiceError("Недоступен"), 4),
        ]:
            with self.subTest(error=error):
                build.side_effect = error
                stdout, stderr = io.StringIO(), io.StringIO()
                with (
                    contextlib.redirect_stdout(stdout),
                    contextlib.redirect_stderr(stderr),
                ):
                    self.assertEqual(main(["--city", "Moscow"]), expected)
                self.assertEqual(stdout.getvalue(), "")
                self.assertIn(str(error), stderr.getvalue())
