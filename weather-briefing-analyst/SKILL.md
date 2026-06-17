---
name: weather-briefing-analyst
description: Produce configurable weather briefings for a user-provided place or address, from quick forecast checks to multi-source analysis with radar/satellite/cloud imagery, air quality, warnings, and travel advice. Use this whenever the user asks for weather analysis, cloud-map or radar interpretation, near-term forecast confidence, commute/outdoor planning, packing advice, or "最近几天/未来几天" weather guidance for a city, district, address, attraction, route, or coordinate; start by offering analysis depth choices when the user has not already specified the depth.
---

# Weather Briefing Analyst

## Purpose

Create a forecaster-style briefing for a specific place. Treat the user's location as the anchor, then combine current observations, numerical forecasts, warnings, radar/satellite/cloud imagery, air quality, and terrain/urban context to estimate the next few days of weather and give practical travel advice.

This skill is for decision support, not official warnings. Prefer official meteorological agencies for warnings and nowcasting, and clearly label uncertainty.

## Analysis Levels

Before collecting live data, determine the depth. If the user did not specify a depth, ask one short question and offer these choices:

1. **快速版：只查天气预报**
   - Use one official forecast source and one model/API cross-check.
   - Include daily forecast, main risks, and simple travel advice.
   - Skip radar, satellite/cloud imagery, and detailed air quality unless severe weather is already indicated.

2. **标准版：天气预报 + 雷达/空气质量（推荐）**
   - Use official forecast, model/API cross-check, current observations, radar imagery when accessible, and AQI/UV if relevant.
   - This is the default if the user says "帮我分析", "出行建议", "未来几天", or wants a practical answer without requesting deep meteorological detail.

3. **深度版：天气预报 + 雷达 + 云图/天气形势**
   - Use all standard sources plus satellite/cloud imagery or other synoptic products when valid and accessible.
   - Use this for cloud-map interpretation, thunderstorm timing, outdoor event planning, severe-weather concern, or when the user explicitly asks for "云图", "雷达形势", "天气形势", or "全量分析".

If the user already specified the depth or asks for urgent advice, do not pause for a question; proceed with the closest level and state which level was used.

## Core Workflow

1. **Resolve the place and level**
   - Convert the address/place into coordinates and an administrative location.
   - If the place is broad, choose a representative point and state that choice.
   - Preserve the user's local timezone and use absolute dates.
   - Record the selected analysis level and do not gather sources outside that level unless a warning signal requires escalation.

2. **Collect time-sensitive evidence**
   - Use live sources; do not rely on memory for current weather.
   - Gather at least two independent forecast sources when possible.
   - For China locations, prioritize official sources such as China Meteorological Administration / local meteorological bureau pages, then supplement with global model APIs.
   - Include radar/satellite/cloud imagery only for levels that require it. If imagery cannot be accessed, say so and base the confidence rating on the remaining evidence.
   - Read `references/data-sources.md` when choosing sources or building API/browser queries.

3. **Analyze like a briefing, not a lookup**
   - Compare model agreement on precipitation timing, temperature range, wind, humidity, visibility, and severe-weather signals.
   - Use radar/satellite/cloud imagery for short-range precipitation confidence, convective development, cloud movement, and clearing trends.
   - Check warnings, heat/cold stress, air quality, pollen/dust when relevant to travel.
   - Separate high-confidence signals from low-confidence signals.

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

**云图/雷达/天气形势**
[include only if selected level includes imagery; summarize evidence and movement trends; state gaps]

**风险提示**
[warnings, AQI, heat/cold, thunderstorm, travel disruption risks]

**来源**
[links and source timestamps]
```

## Confidence Rules

- **High**: official warning/observation agrees with at least one forecast source; radar/satellite supports near-term trend.
- **Medium**: forecast sources broadly agree, but imagery is unavailable or timing differs by a few hours.
- **Low**: sources disagree, convective precipitation dominates, location is mountainous/coastal/urban microclimate-sensitive, or imagery is stale/unavailable.

Never present a deterministic forecast for thunderstorms or short-lived convective rain. Use probability and timing windows.

## Source Discipline

- Always state the date/time each source was accessed.
- Prefer source timestamps from the page/API over only the access time.
- Avoid over-quoting page text; summarize.
- If a source is inaccessible, use another source and disclose the gap.
- Do not fabricate cloud-map or radar conclusions if imagery was not inspected.
- Treat pages that return contact pages, login prompts, commercial data notices, placeholder/loading images, or stale files as failed sources, not weak evidence.

## Common User Requests

- "帮我看北京市朝阳区未来几天天气，适合出门吗？" -> ask level choice if not urgent; otherwise use standard level.
- "快速看一下明后天会不会下雨" -> quick level.
- "明后天去环球影城会不会下雨，云图怎么看？"
- "给我分析一下杭州西湖附近这几天的天气和穿衣建议"
- "看一下这个地址未来三天通勤是否会受暴雨影响"
- "Give me a quick forecast check for Beijing Chaoyang District for the next two days." -> quick level.
- "Analyze whether I should carry an umbrella for my commute in Shanghai Pudong tomorrow." -> standard level.
- "Use radar and satellite/cloud imagery to brief thunderstorm risk near Hangzhou West Lake this weekend." -> deep level.
- "I am visiting Universal Beijing Resort tomorrow. Check rain timing, wind, heat, and travel advice." -> standard level, escalate to deep if radar/cloud imagery is requested.
- "Assess the next three days of weather for this address and tell me the best outdoor activity windows." -> ask level choice if not urgent; otherwise use standard level.
