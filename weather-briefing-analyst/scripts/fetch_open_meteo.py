#!/usr/bin/env python3
"""Fetch hourly and daily forecast data from Open-Meteo."""

from __future__ import annotations

import argparse
import json
import ssl
import time
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
MAX_RESPONSE_BYTES = 5_000_000


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_json(
    url: str,
    timeout: int,
    allow_insecure_tls: bool = False,
    retries: int = 2,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> dict[str, Any]:
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(url, timeout=timeout, context=context) as response:
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise RuntimeError("response exceeded maximum size")
                payload = json.loads(body.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise RuntimeError("response JSON was not an object")
                return payload
        except Exception as exc:  # noqa: BLE001 - retry and surface final error.
            last_error = exc
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(str(last_error))


def validate_request(latitude: float, longitude: float, days: int) -> None:
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    if not 1 <= days <= 16:
        raise ValueError("days must be between 1 and 16")


def validate_series_lengths(series: dict[str, Any], label: str) -> None:
    times = series.get("time")
    if not isinstance(times, list) or not times:
        raise RuntimeError(f"Open-Meteo response missing non-empty {label}.time")

    expected = len(times)
    for key, values in series.items():
        if key == "time":
            continue
        if isinstance(values, list) and len(values) != expected:
            raise RuntimeError(
                f"Open-Meteo response has inconsistent {label}.{key} length"
            )


def validate_forecast_payload(payload: dict[str, Any]) -> None:
    if payload.get("error"):
        raise RuntimeError(str(payload.get("reason") or "Open-Meteo error"))

    hourly = payload.get("hourly")
    daily = payload.get("daily")
    if not isinstance(hourly, dict):
        raise RuntimeError("Open-Meteo response missing hourly object")
    if not isinstance(daily, dict):
        raise RuntimeError("Open-Meteo response missing daily object")

    validate_series_lengths(hourly, "hourly")
    validate_series_lengths(daily, "daily")


def fetch_forecast(
    latitude: float,
    longitude: float,
    days: int = 5,
    timezone_name: str = "auto",
    timeout: int = 20,
    allow_insecure_tls: bool = False,
) -> dict[str, Any]:
    validate_request(latitude, longitude, days)
    accessed_at = now_utc()
    params = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(HOURLY_FIELDS),
            "daily": ",".join(DAILY_FIELDS),
            "timezone": timezone_name or "auto",
            "forecast_days": days,
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        }
    )
    url = f"{FORECAST_URL}?{params}"

    try:
        payload = fetch_json(url, timeout, allow_insecure_tls=allow_insecure_tls)
        validate_forecast_payload(payload)
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

    forecast_valid_from = None
    daily_time = payload.get("daily", {}).get("time")
    hourly_time = payload.get("hourly", {}).get("time")
    if hourly_time:
        forecast_valid_from = hourly_time[0]
    elif daily_time:
        forecast_valid_from = daily_time[0]

    return {
        "forecast": payload,
        "source_status": [
            {
                "source": "Open-Meteo Forecast",
                "data_type": "forecast",
                "status": "ok",
                "forecast_valid_from": forecast_valid_from,
                "provider_generated_at": None,
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
