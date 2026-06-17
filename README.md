# Weather Briefing Analyst

[![skills.sh](https://skills.sh/b/zshzzz/weather-briefing-analyst)](https://skills.sh/zshzzz/weather-briefing-analyst)

English | [中文](README.zh-CN.md)

A configurable Codex / agent skill for weather briefing analysis. It turns a user-provided place or address into a practical near-term forecast by combining weather forecasts, observations, radar, satellite/cloud imagery where available, air-quality context, warnings, and travel advice.

This is designed for questions like:

- `北京市朝阳区未来几天天气怎么样，适合出门吗？`
- `帮我分析上海浦东明后天是否会下雨，给出通勤建议`
- `Use weather-briefing-analyst for a standard briefing on Beijing Chaoyang District`
- `Give me a deep weather briefing with radar and satellite context for Hangzhou West Lake`

## Install

Install from GitHub with the skills CLI:

```bash
npx skills add https://github.com/zshzzz/weather-briefing-analyst --skill weather-briefing-analyst
```

If your skills client supports shorthand repositories:

```bash
npx skills add zshzzz/weather-briefing-analyst --skill weather-briefing-analyst
```

Install locally for Codex:

```bash
./scripts/install-codex.sh
```

Install locally for Claude Code:

```bash
./scripts/install-claude-code.sh
```

Both scripts install `weather-briefing-analyst` to the target skills directory.
If the target already exists, they create a timestamped backup first. Pass `--force` to replace without a backup.

## Skill Layout

```text
weather-briefing-analyst/
├── README.md
├── README.zh-CN.md
├── LICENSE
├── .gitignore
├── scripts/
│   ├── install-codex.sh
│   └── install-claude-code.sh
├── tests/
│   ├── hallucination_cases.jsonl
│   ├── location_cases.jsonl
│   ├── mode_selection_cases.jsonl
│   ├── source_failure_cases.jsonl
│   └── trigger_cases.jsonl
└── weather-briefing-analyst/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── scripts/
    │   ├── fetch_open_meteo.py
    │   ├── geocode.py
    │   ├── normalize_weather.py
    │   └── weather_snapshot.py
    └── references/
        └── data-sources.md
```

## Capabilities

- Resolves a city, district, address, landmark, route point, or coordinate into a forecast location.
- Infers an analysis depth from the request and lets the user override it:
  - Quick: weather forecast only.
  - Standard: forecast plus radar and air-quality context.
  - Deep: forecast plus radar, satellite/cloud imagery, and broader weather-pattern analysis.
- Provides deterministic Open-Meteo geocoding and forecast scripts as a normalized starting point.
- Compares official weather sources and model/API forecasts when available.
- Uses radar or satellite/cloud imagery only when valid current imagery is accessible.
- Produces day-by-day forecast tables, per-element confidence, and travel advice.
- Clearly labels uncertainty, stale imagery, inaccessible sources, and non-official guidance.

## Data Snapshot Script

The bundled Open-Meteo snapshot script provides a deterministic starting point for agents:

```bash
python weather-briefing-analyst/scripts/weather_snapshot.py "39.9,116.4" --days 3
```

If the local Python CA store is broken and HTTPS requests fail with `CERTIFICATE_VERIFY_FAILED`, rerun with `--allow-insecure-tls` and treat that output as a lower-trust diagnostic source.

## Discoverability Notes

For skills.sh and similar find-skill tools, the most important signals are:

- A public GitHub repository with a valid `SKILL.md`.
- A descriptive skill `name` and `description` in the front matter.
- Clear repository README keywords such as weather forecast, radar, satellite, cloud imagery, AQI, warnings, and travel advice.
- A skills.sh badge linking to the repository page.
- Installation through the skills CLI, which may contribute anonymous install telemetry when enabled.

Indexing is not always immediate. After publishing, install the skill once through the CLI and give the crawler or discovery service time to refresh.

## Safety

This skill provides decision support, not official warnings. For severe weather, users should follow local meteorological bureau alerts and official emergency guidance.
