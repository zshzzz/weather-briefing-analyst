#!/usr/bin/env python3
"""Fetch hourly and daily forecast data from Open-Meteo."""

from __future__ import annotations

import argparse
import json
import ssl
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "precipitation_probability",
    "rain",
    "showers",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_gusts_10m",
    "visibility",
]
DAILY_FIELDS = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_json(url: str, timeout: int, allow_insecure_tls: bool = False) -> dict[str, Any]:
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    with urlopen(url, timeout=timeout, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_forecast(
    latitude: float,
    longitude: float,
    days: int = 5,
    timezone_name: str = "auto",
    timeout: int = 20,
    allow_insecure_tls: bool = False,
) -> dict[str, Any]:
    accessed_at = now_utc()
    params = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(HOURLY_FIELDS),
            "daily": ",".join(DAILY_FIELDS),
            "timezone": timezone_name or "auto",
            "forecast_days": days,
        }
    )
    url = f"{FORECAST_URL}?{params}"

    try:
        payload = fetch_json(url, timeout, allow_insecure_tls=allow_insecure_tls)
    except Exception as exc:  # noqa: BLE001 - CLI should report provider failures.
        return {
            "forecast": None,
            "source_status": [
                {
                    "source": "Open-Meteo Forecast",
                    "data_type": "forecast",
                    "status": "failed",
                    "accessed_at": accessed_at,
                    "reason": str(exc),
                    "fallback": "Use another model/API source or official forecast page.",
                }
            ],
        }

    source_time = None
    daily_time = payload.get("daily", {}).get("time")
    hourly_time = payload.get("hourly", {}).get("time")
    if hourly_time:
        source_time = hourly_time[0]
    elif daily_time:
        source_time = daily_time[0]

    return {
        "forecast": payload,
        "source_status": [
            {
                "source": "Open-Meteo Forecast",
                "data_type": "forecast",
                "status": "ok",
                "source_time": source_time,
                "accessed_at": accessed_at,
                "notes": (
                    "Hourly and daily model forecast returned."
                    + (" TLS verification was disabled by request." if allow_insecure_tls else "")
                ),
            }
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--days", type=int, default=5)
    parser.add_argument("--timezone", default="auto")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument(
        "--allow-insecure-tls",
        action="store_true",
        help="Disable TLS certificate verification for environments with broken CA stores.",
    )
    args = parser.parse_args()

    result = fetch_forecast(
        latitude=args.latitude,
        longitude=args.longitude,
        days=args.days,
        timezone_name=args.timezone,
        timeout=args.timeout,
        allow_insecure_tls=args.allow_insecure_tls,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
