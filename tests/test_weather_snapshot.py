from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "weather-briefing-analyst" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import weather_snapshot  # noqa: E402


def location() -> dict:
    return {
        "query": "北京市朝阳区",
        "name": "Chaoyang District",
        "latitude": 39.92,
        "longitude": 116.44,
        "timezone": "Asia/Shanghai",
        "country": "China",
        "admin1": "Beijing",
        "admin2": None,
        "admin3": None,
        "match_confidence": "high",
        "candidates": [],
    }


def forecast_payload() -> dict:
    return {
        "latitude": 39.92,
        "longitude": 116.44,
        "timezone": "Asia/Shanghai",
        "timezone_abbreviation": "GMT+8",
        "utc_offset_seconds": 28800,
        "hourly_units": {
            "temperature_2m": "°C",
            "precipitation": "mm",
            "wind_speed_10m": "km/h",
            "visibility": "m",
        },
        "daily_units": {
            "temperature_2m_max": "°C",
            "precipitation_sum": "mm",
            "wind_speed_10m_max": "km/h",
        },
        "daily": {
            "time": ["2026-06-17"],
            "weather_code": [3],
            "temperature_2m_max": [31.0],
            "temperature_2m_min": [22.0],
            "precipitation_sum": [0.4],
            "precipitation_probability_max": [30],
            "wind_speed_10m_max": [15.0],
            "wind_gusts_10m_max": [28.0],
        },
        "hourly": {
            "time": ["2026-06-17T09:00"],
            "weather_code": [3],
            "temperature_2m": [25.0],
            "relative_humidity_2m": [62],
            "precipitation": [0.0],
            "precipitation_probability": [10],
            "rain": [0.0],
            "showers": [0.0],
            "cloud_cover": [90],
            "wind_speed_10m": [9.0],
            "wind_gusts_10m": [18.0],
            "visibility": [24000],
        },
    }


class WeatherSnapshotTests(unittest.TestCase):
    def test_successful_location_and_forecast_are_normalized(self) -> None:
        geocode_result = {
            "location": location(),
            "source_status": [{"source": "geocoder", "status": "ok"}],
        }
        forecast_result = {
            "forecast": forecast_payload(),
            "source_status": [{"source": "forecast", "status": "ok"}],
        }

        with patch.object(weather_snapshot, "geocode", return_value=geocode_result):
            with patch.object(
                weather_snapshot, "fetch_forecast", return_value=forecast_result
            ) as fetch_forecast:
                snapshot = weather_snapshot.build_snapshot("北京市朝阳区", days=1)

        fetch_forecast.assert_called_once_with(
            latitude=39.92,
            longitude=116.44,
            days=1,
            timezone_name="Asia/Shanghai",
            allow_insecure_tls=False,
        )
        self.assertFalse(snapshot["requires_disambiguation"])
        self.assertEqual(snapshot["location"]["timezone"], "Asia/Shanghai")
        self.assertEqual(snapshot["timezone"], "Asia/Shanghai")
        self.assertEqual(snapshot["units"]["temperature"], "°C")
        self.assertEqual(snapshot["daily"][0]["temperature_2m_max_c"], 31.0)
        self.assertEqual(snapshot["hourly"][0]["cloud_cover_pct"], 90)
        self.assertEqual([item["status"] for item in snapshot["source_status"]], ["ok", "ok"])

    def test_forecast_failure_keeps_location_and_status(self) -> None:
        geocode_result = {
            "location": location(),
            "source_status": [{"source": "geocoder", "status": "ok"}],
        }
        forecast_result = {
            "forecast": None,
            "source_status": [
                {
                    "source": "forecast",
                    "status": "failed",
                    "reason": "provider unavailable",
                }
            ],
        }

        with patch.object(weather_snapshot, "geocode", return_value=geocode_result):
            with patch.object(
                weather_snapshot, "fetch_forecast", return_value=forecast_result
            ):
                snapshot = weather_snapshot.build_snapshot("北京市朝阳区", days=1)

        self.assertEqual(snapshot["location"]["name"], "Chaoyang District")
        self.assertEqual(snapshot["daily"], [])
        self.assertEqual(snapshot["hourly"], [])
        self.assertEqual([item["status"] for item in snapshot["source_status"]], ["ok", "failed"])
        self.assertIn("Forecast was not returned", snapshot["notes"][-1])

    def test_coordinate_input_successfully_fetches_forecast(self) -> None:
        forecast_result = {
            "forecast": forecast_payload(),
            "source_status": [{"source": "forecast", "status": "ok"}],
        }

        with patch.object(
            weather_snapshot, "fetch_forecast", return_value=forecast_result
        ) as fetch_forecast:
            snapshot = weather_snapshot.build_snapshot("39.9,116.4", days=1)

        fetch_forecast.assert_called_once_with(
            latitude=39.9,
            longitude=116.4,
            days=1,
            timezone_name="auto",
            allow_insecure_tls=False,
        )
        self.assertEqual(snapshot["location"]["match_confidence"], "high")
        self.assertEqual(snapshot["location"]["timezone"], "Asia/Shanghai")
        self.assertEqual(snapshot["daily"][0]["weather"], "overcast")

    def test_disambiguation_candidates_are_preserved(self) -> None:
        candidates = [
            {
                "name": "Chaoyang District",
                "latitude": 39.92,
                "longitude": 116.44,
                "country": "China",
                "admin1": "Beijing",
                "match_confidence": "medium",
            },
            {
                "name": "Chaoyang",
                "latitude": 41.58,
                "longitude": 120.45,
                "country": "China",
                "admin1": "Liaoning",
                "match_confidence": "medium",
            },
        ]
        geocode_result = {
            "location": None,
            "requires_disambiguation": True,
            "candidates": candidates,
            "source_status": [
                {
                    "source": "Open-Meteo Geocoding",
                    "data_type": "geocoding",
                    "status": "ambiguous",
                    "reason": "Top geocoding candidates are too close.",
                }
            ],
        }

        with patch.object(weather_snapshot, "geocode", return_value=geocode_result):
            with patch.object(weather_snapshot, "fetch_forecast") as fetch_forecast:
                snapshot = weather_snapshot.build_snapshot("朝阳")

        fetch_forecast.assert_not_called()
        self.assertIsNone(snapshot["location"])
        self.assertTrue(snapshot["requires_disambiguation"])
        self.assertEqual(snapshot["candidates"], candidates)
        self.assertEqual(snapshot["source_status"][0]["status"], "ambiguous")
        self.assertIn("Location was not resolved", snapshot["notes"][-1])


if __name__ == "__main__":
    unittest.main()
