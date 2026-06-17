#!/usr/bin/env python3
"""Normalize raw Open-Meteo forecast payloads into a stable briefing shape."""

from __future__ import annotations

import argparse
import json
from typing import Any


WEATHER_CODES = {
    0: "clear",
    1: "mainly_clear",
    2: "partly_cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing_rime_fog",
    51: "light_drizzle",
    53: "moderate_drizzle",
    55: "dense_drizzle",
    56: "light_freezing_drizzle",
    57: "dense_freezing_drizzle",
    61: "slight_rain",
    63: "moderate_rain",
    65: "heavy_rain",
    66: "light_freezing_rain",
    67: "heavy_freezing_rain",
    71: "slight_snow",
    73: "moderate_snow",
    75: "heavy_snow",
    77: "snow_grains",
    80: "slight_rain_showers",
    81: "moderate_rain_showers",
    82: "violent_rain_showers",
    85: "slight_snow_showers",
    86: "heavy_snow_showers",
    95: "thunderstorm",
    96: "thunderstorm_with_slight_hail",
    99: "thunderstorm_with_heavy_hail",
}


def pick(series: dict[str, list[Any]], key: str, index: int) -> Any:
    values = series.get(key) or []
    if index >= len(values):
        return None
    return values[index]


def normalize_daily(daily: dict[str, list[Any]]) -> list[dict[str, Any]]:
    days = daily.get("time") or []
    normalized = []
    for index, day in enumerate(days):
        code = pick(daily, "weather_code", index)
        normalized.append(
            {
                "date": day,
                "weather_code": code,
                "weather": WEATHER_CODES.get(code, "unknown"),
                "temperature_2m_max_c": pick(daily, "temperature_2m_max", index),
                "temperature_2m_min_c": pick(daily, "temperature_2m_min", index),
                "precipitation_sum_mm": pick(daily, "precipitation_sum", index),
                "precipitation_probability_max_pct": pick(
                    daily, "precipitation_probability_max", index
                ),
                "wind_speed_10m_max_kmh": pick(daily, "wind_speed_10m_max", index),
                "wind_gusts_10m_max_kmh": pick(daily, "wind_gusts_10m_max", index),
            }
        )
    return normalized


def normalize_hourly(hourly: dict[str, list[Any]]) -> list[dict[str, Any]]:
    hours = hourly.get("time") or []
    normalized = []
    for index, hour in enumerate(hours):
        code = pick(hourly, "weather_code", index)
        normalized.append(
            {
                "time": hour,
                "weather_code": code,
                "weather": WEATHER_CODES.get(code, "unknown"),
                "temperature_2m_c": pick(hourly, "temperature_2m", index),
                "relative_humidity_2m_pct": pick(hourly, "relative_humidity_2m", index),
                "precipitation_mm": pick(hourly, "precipitation", index),
                "precipitation_probability_pct": pick(
                    hourly, "precipitation_probability", index
                ),
                "rain_mm": pick(hourly, "rain", index),
                "showers_mm": pick(hourly, "showers", index),
                "cloud_cover_pct": pick(hourly, "cloud_cover", index),
                "wind_speed_10m_kmh": pick(hourly, "wind_speed_10m", index),
                "wind_gusts_10m_kmh": pick(hourly, "wind_gusts_10m", index),
                "visibility_m": pick(hourly, "visibility", index),
            }
        )
    return normalized


def normalize_forecast(forecast: dict[str, Any]) -> dict[str, Any]:
    hourly_units = forecast.get("hourly_units") or {}
    daily_units = forecast.get("daily_units") or {}
    return {
        "timezone": forecast.get("timezone"),
        "timezone_abbreviation": forecast.get("timezone_abbreviation"),
        "utc_offset_seconds": forecast.get("utc_offset_seconds"),
        "latitude": forecast.get("latitude"),
        "longitude": forecast.get("longitude"),
        "elevation_m": forecast.get("elevation"),
        "units": {
            "temperature": daily_units.get("temperature_2m_max")
            or hourly_units.get("temperature_2m"),
            "precipitation": daily_units.get("precipitation_sum")
            or hourly_units.get("precipitation"),
            "wind_speed": daily_units.get("wind_speed_10m_max")
            or hourly_units.get("wind_speed_10m"),
            "visibility": hourly_units.get("visibility"),
            "provider_hourly": hourly_units,
            "provider_daily": daily_units,
        },
        "daily": normalize_daily(forecast.get("daily") or {}),
        "hourly": normalize_hourly(forecast.get("hourly") or {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("forecast_json", help="Path to raw Open-Meteo forecast JSON.")
    args = parser.parse_args()

    with open(args.forecast_json, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    forecast = payload.get("forecast", payload)
    result = normalize_forecast(forecast)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
