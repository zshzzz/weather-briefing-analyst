#!/usr/bin/env python3
"""Validate lightweight JSONL eval seed files."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
REQUIRED_KEYS = {"id", "prompt", "expected"}


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_number}: invalid JSON: {exc}")
                continue

            if not isinstance(item, dict):
                errors.append(f"{path}:{line_number}: line must be a JSON object")
                continue

            missing = REQUIRED_KEYS - item.keys()
            if missing:
                errors.append(
                    f"{path}:{line_number}: missing required key(s): {sorted(missing)}"
                )

            for key in REQUIRED_KEYS & item.keys():
                if not isinstance(item[key], str) or not item[key].strip():
                    errors.append(f"{path}:{line_number}: {key} must be a non-empty string")

            case_id = item.get("id")
            if isinstance(case_id, str):
                if case_id in seen_ids:
                    errors.append(f"{path}:{line_number}: duplicate id {case_id!r}")
                seen_ids.add(case_id)

    return errors


def main() -> None:
    errors: list[str] = []
    for path in sorted(TESTS_DIR.glob("*.jsonl")):
        errors.extend(validate_file(path))

    if errors:
        raise SystemExit("\n".join(errors))

    print("JSONL eval seeds are valid.")


if __name__ == "__main__":
    main()
