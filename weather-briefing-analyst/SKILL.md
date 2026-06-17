---
name: weather-briefing-analyst
description: Produce configurable weather briefings for a user-provided place or address, from quick forecast checks to multi-source analysis with radar/satellite/cloud imagery, air quality, warnings, and travel advice. Use this whenever the user asks for weather analysis, cloud-map or radar interpretation, near-term forecast confidence, commute/outdoor planning, packing advice, or "最近几天/未来几天" weather guidance for a city, district, address, attraction, route, or coordinate; infer quick/standard/deep analysis depth from the request when the user did not specify one, and only ask a follow-up when the place, scope, cost, or depth is genuinely ambiguous.
compatibility: Requires Python 3.10+ and outbound HTTPS access to Open-Meteo APIs. No third-party Python packages required.
---

# Weather Briefing Analyst

## Purpose

Create a forecaster-style briefing for a specific place. Treat the user's location as the anchor, then combine current observations, numerical forecasts, warnings, radar/satellite/cloud imagery, air quality, and terrain/urban context to estimate the next few days of weather and give practical travel advice.

This skill is for decision support, not official warnings. Prefer official meteorological agencies for warnings and nowcasting, and clearly label uncertainty.

## Analysis Level Selection

Infer the analysis level from the user's request. Do not force the user to choose a level before every briefing. Start by stating the inferred level in one short sentence, for example: "我按标准版分析，包含预报、实况、可用雷达和空气质量。"

Use these defaults:

- **快速版** for simple weather lookups: temperature, rain/no rain, umbrella check, "今明天天气", "会不会下雨", or quick forecast checks.
- **标准版** for decisions: commute, travel, clothing, outdoor activities, family/elderly/children planning, "未来几天是否适合出门", or location-specific practical advice.
- **深度版** for meteorological diagnosis: radar, satellite/cloud imagery, thunderstorm timing, heavy-rain assessment, severe convection, synoptic situation, or when the user asks for "云图", "雷达形势", "天气形势", "暴雨研判", or "全量分析".

Ask one concise follow-up before collecting live data only when:

- The location is too broad or ambiguous to resolve safely.
- The requested route/region is too large for a single briefing.
- The user explicitly wants to control analysis depth, speed, or data cost.
- Deep analysis would require unavailable, paid, login-only, or unusually slow data sources.

When asking, use these choices:

1. **快速版：只查天气预报**
   - Use one official forecast source and one model/API cross-check.
   - Include daily forecast, main risks, and simple travel advice.
   - Skip radar, satellite/cloud imagery, and detailed air quality unless severe weather is already indicated.

2. **标准版：天气预报 + 雷达/空气质量（推荐）**
   - Use official forecast, model/API cross-check, current observations, radar imagery when accessible, and AQI/UV if relevant.
   - This is the default for practical travel, commute, clothing, and outdoor guidance.

3. **深度版：天气预报 + 雷达 + 云图/天气形势**
   - Use all standard sources plus satellite/cloud imagery or other synoptic products when valid and accessible.
   - Use this for cloud-map interpretation, thunderstorm timing, outdoor event planning, severe-weather concern, or when the user explicitly asks for "云图", "雷达形势", "天气形势", or "全量分析".

If the user explicitly chooses a level, honor it unless the request cannot be answered at that level; in that case, explain the gap and ask whether to escalate or proceed with a limited answer.

## Core Workflow

1. **Resolve the place and level**
   - Convert the address/place into coordinates and an administrative location.
   - Record the geocoding confidence and matched administrative hierarchy when available.
   - For POIs such as scenic spots, airports, stations, resorts, campuses, or theme parks, prefer the POI coordinate over an administrative center.
   - If bundled scripts are available, inspect `scripts/` before using ad hoc API calls. Use `scripts/weather_snapshot.py` as the first deterministic data pass for single-point quick, standard, and deep briefings; supplement it with browser/API evidence only for sources the script does not cover.
   - Use `scripts/geocode.py` directly for coordinate, city, and district queries. If it returns `requires_disambiguation: true`, do not continue with the first candidate as if it were certain; ask a concise follow-up or use a POI/address-capable source.
   - If the place is broad, choose a representative point only when that is reasonable; state the choice and its limits.
   - For large districts/cities, mountainous scenic areas, coastal/island locations, or places with major elevation differences, flag microclimate or terrain sensitivity.
   - For route requests, split the route into origin and destination before geocoding; add a midpoint for longer trips when possible. Do not pass an entire route sentence into `geocode.py` as one place.
   - Preserve the user's local timezone and use absolute dates.
   - Record the selected or inferred analysis level and do not gather sources outside that level unless a warning signal requires escalation.

2. **Collect time-sensitive evidence**
   - Use live sources; do not rely on memory for current weather.
   - Gather at least two independent forecast sources when possible.
   - Prefer bundled deterministic scripts when available for geocoding and Open-Meteo forecast collection; use browser/API work as supplements when the scripts do not cover a needed source. Do not replace these scripts with raw `curl` unless the script is unavailable or has failed and the failure is disclosed.
   - For China locations, prioritize official sources such as China Meteorological Administration / local meteorological bureau pages, then supplement with global model APIs.
   - Include radar/satellite/cloud imagery only for levels that require it. If imagery cannot be accessed, say so and base the confidence rating on the remaining evidence.
   - Treat official warnings, observations, radar, satellite, and numerical forecasts as separate evidence types. Do not let one evidence type imply certainty for unrelated claims.
   - Read `references/data-sources.md` when choosing sources or building API/browser queries.

3. **Analyze like a briefing, not a lookup**
   - Compare model agreement on precipitation timing, temperature range, wind, humidity, visibility, and severe-weather signals.
   - Use radar/satellite/cloud imagery for short-range precipitation confidence, convective development, cloud movement, and clearing trends.
   - Check warnings, heat/cold stress, air quality, pollen/dust when relevant to travel.
   - Separate high-confidence signals from low-confidence signals by forecast element.

4. **Produce an actionable output**
   - Lead with the bottom line for the next 24-72 hours.
   - Provide a day-by-day table for the requested window, defaulting to 3-5 days.
   - Include travel/outdoor advice tied to timing: umbrella/raincoat, commute windows, clothing, sun/UV, air quality masks, flight/highway risks, elderly/child considerations.
   - Cite sources with links and timestamps. Say when the data was checked.

## Required Report Shape

Use this structure unless the user asks for a different format:

```markdown
**结论**
[2-4 sentences: most likely weather, biggest uncertainty, travel impact]

**地点与时效**
- 地点: [resolved place + coordinates if useful]
- 分析等级: [快速版/标准版/深度版]
- 数据检查时间: [absolute date/time + timezone]
- 预报窗口: [absolute dates]

**逐日预报**
| 日期 | 天气判断 | 温度 | 降水/风/能见度 | 置信度 | 出行建议 |
|---|---|---|---|---|---|

**分项置信度**
- 温度趋势: [高/中/低 + reason]
- 是否降雨: [高/中/低 + reason]
- 降雨开始时间: [高/中/低/不适用 + reason]
- 降雨量级: [高/中/低/不适用 + reason]
- 雷暴/强对流风险: [高/中/低/不适用 + reason]
- 风力影响: [高/中/低/不适用 + reason]

**云图/雷达/天气形势**
[include only if selected level includes imagery; summarize evidence and movement trends; state gaps]

**风险提示**
[warnings, AQI, heat/cold, thunderstorm, travel disruption risks]

**来源**
[links and source timestamps]
```

## Confidence Rules

- Report confidence by forecast element, not only as one overall score.
- **Temperature trend** is high confidence when model/API forecasts and official forecast ranges are close; lower it when terrain, coastal exposure, elevation, or urban heat-island effects are important.
- **Rain/no-rain** is high confidence when official forecasts, model precipitation probability, observations, and near-term radar are aligned. It is medium when forecasts agree but imagery is missing. It is low when sources disagree or convection dominates.
- **Rain start time** is usually lower confidence than rain/no-rain. Use time windows, especially beyond 12-24 hours.
- **Rain amount** is lower confidence when precipitation is convective, terrain-driven, or localized.
- **Thunderstorm/severe convection risk** should stay low or medium unless official warnings, radar trends, and short-term forecast signals all support it.
- **Wind impact** should consider gusts, coastal exposure, high bridges, open terrain, and travel mode.
- Treat official warnings as risk evidence, not proof that a specific timing or amount forecast is accurate.
- Radar mainly improves 0-6/12 hour precipitation confidence. Satellite/cloud imagery supports cloud-system movement and development trends, but should not be used alone for precise rainfall timing.

Never present a deterministic forecast for thunderstorms or short-lived convective rain. Use probability and timing windows.

## Source Discipline

- Always state the date/time each source was accessed.
- Prefer source timestamps from the page/API over only the access time.
- Avoid over-quoting page text; summarize.
- If a source is inaccessible, use another source and disclose the gap.
- Do not fabricate cloud-map or radar conclusions if imagery was not inspected.
- Do not infer satellite/cloud-map content from forecast cloud-cover variables alone. Label model cloud cover as model data, not inspected imagery.
- Treat pages that return contact pages, login prompts, commercial data notices, placeholder/loading images, or stale files as failed sources, not weak evidence.

## Common User Requests

- "快速看一下明后天会不会下雨" -> quick level.
- "帮我看北京市朝阳区未来几天天气，适合出门吗？" -> standard level.
- "明后天去环球影城会不会下雨，云图怎么看？" -> deep level.
- "给我分析一下杭州西湖附近这几天的天气和穿衣建议" -> standard level.
- "看一下这个地址未来三天通勤是否会受暴雨影响" -> standard level, escalate if severe-weather signals appear.
- "Give me a quick forecast check for Beijing Chaoyang District for the next two days." -> quick level.
- "Analyze whether I should carry an umbrella for my commute in Shanghai Pudong tomorrow." -> standard level.
- "Use radar and satellite/cloud imagery to brief thunderstorm risk near Hangzhou West Lake this weekend." -> deep level.
- "I am visiting Universal Beijing Resort tomorrow. Check rain timing, wind, heat, and travel advice." -> standard level.
- "Assess the next three days of weather for this address and tell me the best outdoor activity windows." -> standard level.
