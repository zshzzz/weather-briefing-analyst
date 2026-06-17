#!/usr/bin/env python3
"""Create a normalized weather snapshot for a place using bundled providers."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any

from fetch_open_meteo import fetch_forecast
from geocode import geocode
from normalize_weather import normalize_forecast


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_snapshot(
    query: str,
    days: int = 5,
    language: str = "zh",
    allow_insecure_tls: bool = False,
) -> dict[str, Any]:
    generated_at = now_utc()
    statuses: list[dict[str, Any]] = []

    geocode_result = geocode(
        query,
        language=language,
        allow_insecure_tls=allow_insecure_tls,
    )
    statuses.extend(geocode_result.get("source_status", []))
    location = geocode_result.get("location")

    snapshot: dict[str, Any] = {
        "location": location,
        "generated_at": generated_at,
        "daily": [],
        "hourly": [],
        "warnings": [],
        "source_status": statuses,
        "notes": [
            "This snapshot uses Open-Meteo geocoding and model forecast only.",
            "It does not include official warnings, radar, satellite/cloud imagery, AQI, or UV.",
        ],
    }

    if not location:
        snapshot["notes"].append("Location was not resolved; no forecast request was made.")
        return snapshot

    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if latitude is None or longitude is None:
        snapshot["source_status"].append(
            {
                "source": "weather_snapshot",
                "data_type": "forecast",
                "status": "failed",
                "accessed_at": generated_at,
                "reason": "Resolved location did not include latitude and longitude.",
                "fallback": "Ask the user for coordinates or use another geocoder.",
            }
        )
        return snapshot

    forecast_result = fetch_forecast(
        latitude=float(latitude),
        longitude=float(longitude),
        days=days,
        timezone_name=location.get("timezone") or "auto",
        allow_insecure_tls=allow_insecure_tls,
    )
    snapshot["source_status"].extend(forecast_result.get("source_status", []))

    forecast = forecast_result.get("forecast")
    if not forecast:
        snapshot["notes"].append("Forecast was not returned; source_status contains the failure.")
        return snapshot

    normalized = normalize_forecast(forecast)
    snapshot["location"]["timezone"] = normalized.get("timezone") or location.get("timezone")
    snapshot["timezone"] = normalized.get("timezone")
    snapshot["timezone_abbreviation"] = normalized.get("timezone_abbreviation")
    snapshot["utc_offset_seconds"] = normalized.get("utc_offset_seconds")
    snapshot["units"] = normalized.get("units")
    snapshot["daily"] = normalized.get("daily", [])
    snapshot["hourly"] = normalized.get("hourly", [])

    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Place name, address, or 'latitude,longitude'.")
    parser.add_argument("--days", type=int, default=5, help="Forecast days to request.")
    parser.add_argument("--language", default="zh", help="Open-Meteo geocoding language.")
    parser.add_argument(
        "--allow-insecure-tls",
        action="store_true",
        help="Disable TLS certificate verification for environments with broken CA stores.",
    )
    args = parser.parse_args()

    result = build_snapshot(
        args.query,
        days=args.days,
        language=args.language,
        allow_insecure_tls=args.allow_insecure_tls,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
