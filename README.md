# Weather Briefing Analyst

[![skills.sh](https://skills.sh/b/zshzzz/weather-briefing-analyst)](https://skills.sh/zshzzz/weather-briefing-analyst)

English | [中文](README.zh-CN.md)

A configurable Codex / agent skill for weather briefing analysis. It turns a user-provided place or address into a practical near-term forecast by combining weather forecasts, observations, radar, satellite/cloud imagery where available, air-quality context, warnings, and travel advice.

This is designed for questions like:

- `北京市朝阳区未来几天天气怎么样，适合出门吗？`
- `帮我分析上海浦东明后天是否会下雨，给出通勤建议`
- `Use weather-briefing-analyst for a standard briefing on Beijing Chaoyang District`
- `Give me a deep weather briefing with radar and satellite context for Hangzhou West Lake`

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=zshzzz/weather-briefing-analyst&type=Date)](https://www.star-history.com/#zshzzz/weather-briefing-analyst&Date)

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

## Runtime Requirements

- Python 3.10 or newer.
- No third-party Python packages are required.
- Outbound HTTPS access to:
  - `geocoding-api.open-meteo.com`
  - `api.open-meteo.com`
- `shellcheck` is optional and is used only by local static checks.

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
│   ├── run_static_checks.py
│   ├── source_failure_cases.jsonl
│   ├── test_fetch_open_meteo.py
│   ├── test_geocode.py
│   ├── test_normalize_weather.py
│   ├── test_weather_snapshot.py
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

## Analysis Level Triggers

The skill normally infers the analysis level from the user's wording. Users can still explicitly request `quick`, `standard`, or `deep`.

- Quick: simple lookup questions such as `Will it rain in Guangzhou tomorrow?`, `明天成都最高温多少？`, or `快速看一下明后天要不要带伞`.
- Standard: practical decisions such as commute, clothing, travel, elderly/children planning, outdoor windows, or `北京朝阳区未来几天适合出门吗？`.
- Deep: meteorological diagnosis or imagery-driven questions such as radar, satellite/cloud imagery, thunderstorm timing, heavy-rain assessment, or `帮我看深圳今天下午云图和雷达，判断暴雨什么时候来`.

Example:

```text
User: 帮我看北京市朝阳区未来几天天气，适合出门吗？
Expected: infer standard level; run the bundled snapshot script first, then add official forecast, warnings, radar/AQI context when available.
```

```text
User: 明后天去环球影城会不会下雨，云图怎么看？
Expected: infer deep level; prefer the theme-park POI coordinate, run the bundled script for model data, then inspect valid radar/satellite/cloud imagery before making imagery claims.
```

## Data Snapshot Script

The bundled Open-Meteo snapshot script provides a deterministic starting point for agents:

```bash
python weather-briefing-analyst/scripts/weather_snapshot.py "39.9,116.4" --days 3
```

For normal single-location briefings, agents should use this script before falling back to raw `curl` or browser-only collection. The snapshot intentionally covers only Open-Meteo geocoding plus model forecasts; official warnings, radar, satellite/cloud imagery, AQI, and UV still need supplemental sources.

If the local Python CA store is broken and HTTPS requests fail with `CERTIFICATE_VERIFY_FAILED`, rerun with `--allow-insecure-tls` and treat that output as a lower-trust diagnostic source.

## Tests

Run local checks without live network access:

```bash
python3 tests/run_static_checks.py
```

This compiles bundled scripts, validates JSONL eval seeds, runs unit tests, and runs `shellcheck` when it is installed. GitHub Actions runs the same core checks on push and pull request.

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
