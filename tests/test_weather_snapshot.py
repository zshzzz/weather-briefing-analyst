from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "weather-briefing-analyst" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import weather_snapshot  # noqa: E402


class WeatherSnapshotTests(unittest.TestCase):
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
