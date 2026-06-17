from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "weather-briefing-analyst" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import geocode  # noqa: E402


class GeocodeTests(unittest.TestCase):
    def test_coordinates_are_parsed_without_network(self) -> None:
        result = geocode.geocode("39.9,116.4")

        self.assertEqual(result["location"]["latitude"], 39.9)
        self.assertEqual(result["location"]["longitude"], 116.4)
        self.assertEqual(result["location"]["match_confidence"], "high")

    def test_ambiguous_top_candidates_require_disambiguation(self) -> None:
        payload = {
            "results": [
                {
                    "name": "Chaoyang",
                    "latitude": 41.58,
                    "longitude": 120.45,
                    "country": "China",
                    "admin1": "Liaoning",
                    "population": 450000,
                },
                {
                    "name": "Chaoyang District",
                    "latitude": 39.92,
                    "longitude": 116.44,
                    "country": "China",
                    "admin1": "Beijing",
                    "population": 3500000,
                },
            ]
        }

        with patch.object(geocode, "fetch_json", return_value=payload):
            result = geocode.geocode("朝阳")

        self.assertIsNone(result["location"])
        self.assertTrue(result["requires_disambiguation"])
        self.assertEqual(result["source_status"][0]["status"], "ambiguous")

    def test_route_sentence_is_not_geocoded_as_one_place(self) -> None:
        result = geocode.geocode("周六从上海开车到杭州")

        self.assertIsNone(result["location"])
        self.assertTrue(result["requires_disambiguation"])
        self.assertIn("origin and destination", result["source_status"][0]["reason"])

    def test_invalid_count_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            geocode.geocode("北京", count=0)


if __name__ == "__main__":
    unittest.main()
