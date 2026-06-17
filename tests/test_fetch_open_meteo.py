from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "weather-briefing-analyst" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import fetch_open_meteo  # noqa: E402


def valid_payload() -> dict:
    return {
        "latitude": 39.9,
        "longitude": 116.4,
        "hourly": {
            "time": ["2026-06-17T00:00", "2026-06-17T01:00"],
            "temperature_2m": [20.0, 21.0],
        },
        "daily": {
            "time": ["2026-06-17"],
            "temperature_2m_max": [28.0],
        },
    }


class FetchOpenMeteoTests(unittest.TestCase):
    def test_invalid_coordinates_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fetch_open_meteo.fetch_forecast(91, 116.4)

        with self.assertRaises(ValueError):
            fetch_open_meteo.fetch_forecast(39.9, 181)

    def test_invalid_days_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fetch_open_meteo.fetch_forecast(39.9, 116.4, days=17)

    def test_source_time_is_forecast_valid_from(self) -> None:
        with patch.object(fetch_open_meteo, "fetch_json", return_value=valid_payload()):
            result = fetch_open_meteo.fetch_forecast(39.9, 116.4, days=1)

        status = result["source_status"][0]
        self.assertEqual(status["status"], "ok")
        self.assertEqual(status["forecast_valid_from"], "2026-06-17T00:00")
        self.assertIsNone(status["provider_generated_at"])
        self.assertNotIn("source_time", status)

    def test_request_forces_metric_units(self) -> None:
        captured_urls = []

        def fake_fetch_json(url: str, *_args: object, **_kwargs: object) -> dict:
            captured_urls.append(url)
            return valid_payload()

        with patch.object(fetch_open_meteo, "fetch_json", side_effect=fake_fetch_json):
            result = fetch_open_meteo.fetch_forecast(39.9, 116.4, days=1)

        self.assertIsNotNone(result["forecast"])
        params = parse_qs(urlparse(captured_urls[0]).query)
        self.assertEqual(params["temperature_unit"], ["celsius"])
        self.assertEqual(params["wind_speed_unit"], ["kmh"])
        self.assertEqual(params["precipitation_unit"], ["mm"])

    def test_api_error_is_reported_as_failed_source(self) -> None:
        with patch.object(
            fetch_open_meteo,
            "fetch_json",
            return_value={"error": True, "reason": "bad request"},
        ):
            result = fetch_open_meteo.fetch_forecast(39.9, 116.4)

        self.assertIsNone(result["forecast"])
        self.assertEqual(result["source_status"][0]["status"], "failed")
        self.assertIn("bad request", result["source_status"][0]["reason"])

    def test_inconsistent_series_lengths_are_failed(self) -> None:
        payload = valid_payload()
        payload["hourly"]["temperature_2m"] = [20.0]

        with patch.object(fetch_open_meteo, "fetch_json", return_value=payload):
            result = fetch_open_meteo.fetch_forecast(39.9, 116.4)

        self.assertIsNone(result["forecast"])
        self.assertEqual(result["source_status"][0]["status"], "failed")
        self.assertIn("inconsistent hourly.temperature_2m length", result["source_status"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
