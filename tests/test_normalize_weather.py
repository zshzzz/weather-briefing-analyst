from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "weather-briefing-analyst" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import normalize_weather  # noqa: E402


class NormalizeWeatherTests(unittest.TestCase):
    def test_units_are_read_from_provider_payload(self) -> None:
        forecast = {
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
            "daily": {"time": []},
            "hourly": {"time": []},
        }

        result = normalize_weather.normalize_forecast(forecast)

        self.assertEqual(result["units"]["temperature"], "°C")
        self.assertEqual(result["units"]["precipitation"], "mm")
        self.assertEqual(result["units"]["wind_speed"], "km/h")
        self.assertEqual(result["units"]["visibility"], "m")
        self.assertEqual(result["units"]["provider_hourly"]["temperature_2m"], "°C")


if __name__ == "__main__":
    unittest.main()
