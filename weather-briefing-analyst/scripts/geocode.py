#!/usr/bin/env python3
"""Resolve a place query to a normalized location using Open-Meteo geocoding."""

from __future__ import annotations

import argparse
import json
import re
import ssl
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
MAX_RESPONSE_BYTES = 2_000_000
COORD_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")
ROUTE_PATTERNS = [
    re.compile(r"从\s*(.+?)\s*(?:到|至)\s*(.+)"),
    re.compile(r"(.+?)\s*(?:->|→)\s*(.+)"),
    re.compile(r"\bfrom\s+(.+?)\s+to\s+(.+)", re.IGNORECASE),
]
POI_OR_ADDRESS_HINTS = (
    "路",
    "街",
    "号",
    "大道",
    "景区",
    "风景区",
    "机场",
    "火车站",
    "高铁站",
    "车站",
    "乐园",
    "环球影城",
    "度假区",
    "广场",
    "外滩",
    "公园",
    "大学",
    "校区",
    "医院",
    "酒店",
)


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
                if payload.get("error"):
                    raise RuntimeError(str(payload.get("reason") or "Open-Meteo error"))
                return payload
        except Exception as exc:  # noqa: BLE001 - retry and surface final error.
            last_error = exc
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(str(last_error))


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


def looks_like_route(query: str) -> bool:
    normalized = query.strip()
    return any(pattern.search(normalized) for pattern in ROUTE_PATTERNS)


def looks_like_poi_or_address(query: str) -> bool:
    normalized = query.strip().lower()
    return any(hint.lower() in normalized for hint in POI_OR_ADDRESS_HINTS)


def result_identity(result: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(result.get("name") or "").lower(),
        str(result.get("admin1") or "").lower(),
        str(result.get("admin2") or "").lower(),
        str(result.get("country") or "").lower(),
    )


def score_result(result: dict[str, Any], query: str) -> int:
    normalized_query = query.lower().strip()
    name = str(result.get("name", "")).lower()
    admin1 = str(result.get("admin1", "")).lower()
    admin2 = str(result.get("admin2", "")).lower()
    admin3 = str(result.get("admin3", "")).lower()
    country = str(result.get("country", "")).lower()
    haystack = " ".join([name, admin1, admin2, admin3, country])

    score = 0
    if normalized_query:
        if normalized_query == name:
            score += 100
        elif normalized_query in name:
            score += 70
        elif normalized_query in haystack:
            score += 35

    if result.get("population"):
        score += 10
    if result.get("admin1"):
        score += 8
    if result.get("admin2"):
        score += 5
    if result.get("country_code") == "CN" or country in {"china", "中国"}:
        score += 3
    return score


def top_candidates_are_ambiguous(candidates: list[dict[str, Any]], query: str) -> bool:
    if not candidates:
        return False

    if len(candidates) == 1:
        return looks_like_poi_or_address(query) and confidence_for(candidates[0], query) != "high"

    scored = [(score_result(item, query), result_identity(item), item) for item in candidates]
    scored.sort(key=lambda item: item[0], reverse=True)
    top_score, top_identity, _top = scored[0]
    second_score, second_identity, _second = scored[1]

    if top_identity == second_identity:
        return False

    if top_score < 45:
        return True

    if top_score - second_score <= 8:
        return True

    # Short administrative names such as "朝阳" often match multiple places.
    compact = re.sub(r"\s+", "", query)
    if len(compact) <= 4 and second_score >= 35:
        return True

    if looks_like_poi_or_address(query) and confidence_for(scored[0][2], query) != "high":
        return True

    return False


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
    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= count <= 20:
        raise ValueError("count must be between 1 and 20")

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

    if looks_like_route(query):
        return {
            "location": None,
            "requires_disambiguation": True,
            "candidates": [],
            "source_status": [
                {
                    "source": "route-parser",
                    "data_type": "geocoding",
                    "status": "failed",
                    "accessed_at": accessed_at,
                    "reason": "Route-like input should be split into origin and destination before geocoding.",
                    "fallback": "Resolve origin and destination separately; add a midpoint for longer routes.",
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

    sorted_results = sorted(results, key=lambda item: score_result(item, query), reverse=True)
    best = sorted_results[0]
    candidates = []
    for item in sorted_results[:count]:
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
                "match_score": score_result(item, query),
            }
        )

    if top_candidates_are_ambiguous(sorted_results[:count], query):
        return {
            "location": None,
            "requires_disambiguation": True,
            "candidates": candidates,
            "source_status": [
                {
                    "source": "Open-Meteo Geocoding",
                    "data_type": "geocoding",
                    "status": "ambiguous",
                    "source_time": None,
                    "accessed_at": accessed_at,
                    "reason": "Top geocoding candidates are too close or the query looks like a POI/address not safely resolved by this provider.",
                    "fallback": "Ask for a more specific place or use a POI/address-capable geocoder before requesting the forecast.",
                }
            ],
        }

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
        "match_score": score_result(best, query),
        "match_reason": "Selected the highest-scored Open-Meteo geocoding result.",
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
