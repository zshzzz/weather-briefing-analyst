#!/usr/bin/env python3
"""Resolve a place query to a normalized location using Open-Meteo geocoding."""

from __future__ import annotations

import argparse
import json
import re
import ssl
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
COORD_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_json(url: str, timeout: int, allow_insecure_tls: bool = False) -> dict[str, Any]:
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    with urlopen(url, timeout=timeout, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def confidence_for(result: dict[str, Any], query: str) -> str:
    name = str(result.get("name", "")).lower()
    admin1 = str(result.get("admin1", "")).lower()
    admin2 = str(result.get("admin2", "")).lower()
    country = str(result.get("country", "")).lower()
    haystack = " ".join([name, admin1, admin2, country])
    normalized_query = query.lower().strip()

    if normalized_query and normalized_query in haystack:
        return "high"
    if result.get("population") or admin1 or admin2:
        return "medium"
    return "low"


def location_from_coordinates(query: str) -> dict[str, Any] | None:
    match = COORD_RE.match(query)
    if not match:
        return None

    latitude = float(match.group(1))
    longitude = float(match.group(2))
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("coordinates out of range")

    return {
        "query": query,
        "name": query,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto",
        "country": None,
        "admin1": None,
        "admin2": None,
        "admin3": None,
        "match_confidence": "high",
        "match_reason": "Input was parsed as latitude,longitude.",
        "candidates": [],
    }


def geocode(
    query: str,
    count: int = 5,
    language: str = "zh",
    timeout: int = 15,
    allow_insecure_tls: bool = False,
) -> dict[str, Any]:
    coordinate_location = location_from_coordinates(query)
    accessed_at = now_utc()
    if coordinate_location:
        return {
            "location": coordinate_location,
            "source_status": [
                {
                    "source": "coordinate-parser",
                    "data_type": "geocoding",
                    "status": "ok",
                    "source_time": accessed_at,
                    "accessed_at": accessed_at,
                    "notes": "Input parsed directly as coordinates.",
                }
            ],
        }

    params = urlencode(
        {
            "name": query,
            "count": count,
            "language": language,
            "format": "json",
        }
    )
    url = f"{GEOCODE_URL}?{params}"
    accessed_at = now_utc()

    try:
        payload = fetch_json(url, timeout, allow_insecure_tls=allow_insecure_tls)
    except Exception as exc:  # noqa: BLE001 - CLI should report provider failures.
        return {
            "location": None,
            "source_status": [
                {
                    "source": "Open-Meteo Geocoding",
                    "data_type": "geocoding",
                    "status": "failed",
                    "accessed_at": accessed_at,
                    "reason": str(exc),
                    "fallback": "Ask the agent to resolve the place by another source.",
                }
            ],
        }

    results = payload.get("results") or []
    if not results:
        return {
            "location": None,
            "source_status": [
                {
                    "source": "Open-Meteo Geocoding",
                    "data_type": "geocoding",
                    "status": "failed",
                    "accessed_at": accessed_at,
                    "reason": "No geocoding results returned.",
                    "fallback": "Ask the user for a more specific address or coordinate.",
                }
            ],
        }

    best = results[0]
    candidates = []
    for item in results[:count]:
        candidates.append(
            {
                "name": item.get("name"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "country": item.get("country"),
                "admin1": item.get("admin1"),
                "admin2": item.get("admin2"),
                "admin3": item.get("admin3"),
                "timezone": item.get("timezone"),
                "population": item.get("population"),
                "match_confidence": confidence_for(item, query),
            }
        )

    location = {
        "query": query,
        "name": best.get("name"),
        "latitude": best.get("latitude"),
        "longitude": best.get("longitude"),
        "timezone": best.get("timezone") or "auto",
        "country": best.get("country"),
        "admin1": best.get("admin1"),
        "admin2": best.get("admin2"),
        "admin3": best.get("admin3"),
        "match_confidence": confidence_for(best, query),
        "match_reason": "Selected the first Open-Meteo geocoding result.",
        "candidates": candidates,
    }

    return {
        "location": location,
        "source_status": [
            {
                "source": "Open-Meteo Geocoding",
                "data_type": "geocoding",
                "status": "ok",
                "source_time": None,
                "accessed_at": accessed_at,
                "notes": (
                    f"Returned {len(results)} candidate(s)."
                    + (" TLS verification was disabled by request." if allow_insecure_tls else "")
                ),
            }
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Place name, address, or 'latitude,longitude'.")
    parser.add_argument("--count", type=int, default=5, help="Maximum geocoding candidates.")
    parser.add_argument("--language", default="zh", help="Open-Meteo geocoding language.")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--allow-insecure-tls",
        action="store_true",
        help="Disable TLS certificate verification for environments with broken CA stores.",
    )
    args = parser.parse_args()

    result = geocode(
        args.query,
        count=args.count,
        language=args.language,
        timeout=args.timeout,
        allow_insecure_tls=args.allow_insecure_tls,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
