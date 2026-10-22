import unittest
from unittest.mock import Mock, call, patch

import requests

from clients.exceptions import ExternalServiceError, HttpStatusError
from clients.http import TIMEOUT, get_json, retry_delay


def response(status: int = 200, payload=None, headers=None) -> Mock:
    result = Mock()
    result.status_code = status
    result.headers = {"Content-Type": "application/json", **(headers or {})}
    result.json.return_value = {"ok": True} if payload is None else payload
    return result


class HttpTests(unittest.TestCase):
    @patch("clients.http.requests.get")
    def test_get_has_timeout_headers_and_query_params(self, get):
        reply = response()
        get.return_value = reply
        self.assertEqual(
            get_json("https://example.test", {"city": "Москва"}), {"ok": True}
        )
        kwargs = get.call_args.kwargs
        self.assertEqual(kwargs["timeout"], TIMEOUT)
        self.assertTrue(all(0 < limit <= 10 for limit in TIMEOUT))
        self.assertEqual(kwargs["params"], {"city": "Москва"})
        self.assertEqual(kwargs["headers"]["Accept"], "application/json")
        self.assertFalse(kwargs["allow_redirects"])
        reply.close.assert_called_once()

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_network_failures_retry_twice_then_succeed(self, get, sleep):
        get.side_effect = [requests.Timeout(), requests.ConnectionError(), response()]
        self.assertEqual(get_json("https://example.test"), {"ok": True})
        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_network_retry_exhaustion(self, get, sleep):
        for error in (requests.Timeout, requests.ConnectionError):
            with self.subTest(error=error):
                get.reset_mock()
                sleep.reset_mock()
                get.side_effect = error("test network failure")
                with self.assertRaises(ExternalServiceError):
                    get_json("https://example.test")
                self.assertEqual(get.call_count, 3)
                self.assertEqual(sleep.call_count, 2)

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_each_temporary_status_retries_three_attempts(self, get, sleep):
        for status in (500, 502, 503, 504):
            with self.subTest(status=status):
                get.reset_mock()
                sleep.reset_mock()
                replies = [response(status), response(status), response(status)]
                get.side_effect = replies
                with self.assertRaises(ExternalServiceError):
                    get_json("https://example.test")
                self.assertEqual(get.call_count, 3)
                self.assertEqual(sleep.call_count, 2)
                for reply in replies:
                    reply.close.assert_called_once()

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_429_honors_numeric_retry_after(self, get, sleep):
        get.side_effect = [
            response(429, headers={"Retry-After": "3"}),
            response(429, headers={"Retry-After": "0.5"}),
            response(),
        ]
        get_json("https://example.test")
        self.assertEqual(sleep.call_args_list, [call(3.0), call(0.5)])

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_429_exhaustion(self, get, sleep):
        get.side_effect = [
            response(429, headers={"Retry-After": "0"}) for _ in range(3)
        ]
        with self.assertRaises(ExternalServiceError):
            get_json("https://example.test")
        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_args_list, [call(0.0), call(0.0)])

    @patch("clients.http.random.uniform", return_value=0.1)
    def test_invalid_retry_after_falls_back_to_backoff(self, random):
        for value in (None, "invalid", "-1", "NaN", "inf"):
            with self.subTest(value=value):
                self.assertAlmostEqual(retry_delay(0, value), 1.1)
                self.assertAlmostEqual(retry_delay(1, value), 2.1)

    @patch("clients.http.requests.get")
    def test_permanent_http_errors_are_not_retried(self, get):
        for status in (301, 400, 401, 403, 404, 422):
            with self.subTest(status=status):
                get.reset_mock()
                get.return_value = response(status)
                with self.assertRaises(HttpStatusError) as caught:
                    get_json("https://example.test")
                self.assertEqual(caught.exception.status_code, status)
                get.assert_called_once()

    @patch("clients.http.requests.get")
    def test_html_response_is_rejected_before_json_parsing(self, get):
        reply = response(headers={"Content-Type": "text/html"})
        get.return_value = reply
        with self.assertRaises(ExternalServiceError):
            get_json("https://example.test")
        reply.json.assert_not_called()
        reply.close.assert_called_once()

    @patch("clients.http.requests.get")
    def test_invalid_json_is_translated_to_application_error(self, get):
        reply = response()
        reply.json.side_effect = ValueError("bad JSON")
        get.return_value = reply
        with self.assertRaises(ExternalServiceError):
            get_json("https://example.test")
        reply.close.assert_called_once()
