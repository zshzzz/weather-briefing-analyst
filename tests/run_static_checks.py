#!/usr/bin/env python3
"""Run local static checks that do not require network access."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    run([sys.executable, "-m", "compileall", "weather-briefing-analyst/scripts"])
    run([sys.executable, "tests/validate_jsonl.py"])
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests"])

    shellcheck = shutil.which("shellcheck")
    if shellcheck:
        run([shellcheck, "scripts/install-codex.sh", "scripts/install-claude-code.sh"])
    else:
        print("shellcheck not found; skipping shell script lint.")


if __name__ == "__main__":
    main()
