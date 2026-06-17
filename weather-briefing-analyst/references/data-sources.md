# Data Sources And Query Guidance

Use this reference when building a weather briefing. Source availability changes, so verify live pages and APIs each time.

## Provider matrix

Use this matrix before improvising sources.

| Source | Data type | Coverage | Freshness | Structured | Fallback |
|---|---|---|---|---|---|
| Open-Meteo | Model forecast, geocoding | Global | Hourly to daily | JSON | MET Norway or another public model/API |
| MET Norway | Model forecast | Global | Hourly to daily | JSON | Open-Meteo, NOAA/GFS-derived public products |
| China Meteorological Administration / National Meteorological Center | Official warnings, forecast, radar/satellite products | Mainland China | Product-dependent | Mixed webpage/image/API | Provincial/city meteorological bureau, public radar/map layer |
| Provincial/city meteorological bureaus | Local warnings, forecast, observations | Local China | Product-dependent | Mixed webpage/image/API | CMA/NMC, model/API cross-check |
| Official environmental monitoring pages | AQI and pollutants | Local/national | Hourly or daily | Mixed | Reputable AQI aggregator, with disclosure |
| Public transport/road/airport authorities | Travel disruption | Local/route-specific | Event-dependent | Mixed | Omit unless requested or severe weather risk is relevant |

Every collected source should produce a `source_status` note:

```json
{
  "source": "Open-Meteo",
  "data_type": "forecast",
  "status": "ok",
  "source_time": "2026-06-17T15:00:00+08:00",
  "accessed_at": "2026-06-17T15:03:00+08:00",
  "notes": "Hourly and daily model forecast returned"
}
```

When a source fails, keep the failure explicit:

```json
{
  "source": "Official satellite page",
  "data_type": "satellite",
  "status": "failed",
  "reason": "Returned commercial contact page instead of current imagery",
  "fallback": "Skipped satellite interpretation and lowered cloud-trend confidence"
}
```

## Preferred source order

Select sources according to the analysis level in `SKILL.md`; do not collect full radar/satellite data for quick mode.

1. **Official warnings and local observations**
   - National or local meteorological agencies.
   - For mainland China: China Meteorological Administration, provincial/city meteorological bureaus, National Meteorological Center, official radar/satellite pages when accessible.
   - Look for warning signals, station observations, short-term nowcasts, radar mosaics, satellite cloud maps, and forecast discussion pages.

2. **Forecast model/API cross-check**
   - Open-Meteo for free global forecast variables and geocoding.
   - MET Norway, ECMWF-derived public products, NOAA/NCEP/GFS-based products, or other accessible model viewers.
   - Use model data to compare precipitation timing, temperature range, wind, humidity, cloud cover, and visibility proxies.

3. **Radar/satellite/cloud imagery**
   - Prefer official radar and satellite imagery with timestamps.
   - If official imagery is not accessible, use reputable public map layers or model viewers. State the provider and timestamp.
   - For short-term precipitation, radar is more important than daily forecast icons.
   - For cloud-cover trends, satellite loops are more useful than a static image.
   - Do not use `https://d1.weather.com.cn/satellite2015/JC_YT_DL_WXZXCSYT_4B.html` as evidence if it returns the WeatherDT commercial-contact page instead of image metadata. Treat that response as a failed source and either use the public satellite page through a browser or skip satellite imagery with disclosure.

4. **Impact layers**
   - Air quality: official environmental monitoring pages when available, or reputable AQI aggregators.
   - Travel disruption: official transport advisories only if the user asks about flights, rail, highway, or route-specific risk.

## Useful Open-Meteo fields

For a coordinate-based cross-check, request hourly and daily fields such as:

```text
hourly=temperature_2m,relative_humidity_2m,precipitation,precipitation_probability,rain,showers,weather_code,cloud_cover,wind_speed_10m,wind_gusts_10m,visibility
daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max
timezone=auto
forecast_days=5
```

Use geocoding first when the user's input is an address or district:

```text
https://geocoding-api.open-meteo.com/v1/search?name=<place>&count=5&language=zh&format=json
```

Then forecast:

```text
https://api.open-meteo.com/v1/forecast?latitude=<lat>&longitude=<lon>&hourly=...&daily=...&timezone=auto&forecast_days=5
```

If bundled scripts are available, prefer:

```bash
python weather-briefing-analyst/scripts/weather_snapshot.py "北京朝阳区" --days 5
```

The script output is a normalized starting point. It does not replace official warnings, radar, satellite/cloud imagery, or AQI sources when the selected analysis level requires them.

If a local Python environment has a broken CA certificate store and Open-Meteo HTTPS requests fail with `CERTIFICATE_VERIFY_FAILED`, the scripts support `--allow-insecure-tls` as an explicit last-resort diagnostic option. When used, treat the source as less trustworthy and mention that TLS verification was disabled.

## Source validation

Before using a source as evidence, verify it contains weather data, a forecast, an image, or a source timestamp. Reject the source if it matches any of these patterns:

- Contact/commercial-cooperation pages such as WeatherDT notices.
- Placeholder images such as `loading.jpg`.
- Empty API responses, for example `{"msg":"success","code":0,"data":""}`.
- Static home pages that list products but not current weather content.
- Image files without an interpretable timestamp when time sensitivity matters.

When rejecting a source, do not mention its raw failed file unless useful for debugging. Say "卫星云图接口未返回可用云图数据" or similar, then continue with valid radar/model/forecast sources.

## Level-specific source sets

**快速版**
- Official daily forecast page or agency forecast.
- One model/API cross-check.
- Current observation if available.
- No radar or satellite/cloud imagery unless official warnings or the user explicitly asks.

**标准版**
- Everything in quick mode.
- Radar image or radar mosaic if relevant and accessible.
- AQI/UV when travel, outdoor activity, heat, haze, or respiratory sensitivity is relevant.
- If radar is unavailable, disclose it and keep precipitation timing confidence conservative.

**深度版**
- Everything in standard mode.
- Satellite/cloud imagery only if valid image data or a browser-rendered product can be inspected.
- Forecast discussion, warning bulletins, or synoptic products when available.
- If satellite/cloud imagery is unavailable, do not write a cloud-map interpretation. Use model cloud-cover fields only as model evidence.

## Analysis checklist

- Does observed weather match the first forecast period?
- Are multiple forecasts aligned on precipitation timing?
- Do radar echoes or satellite clouds support the next 0-12 hour forecast?
- Are warnings active or likely from model signals?
- Are wind gusts, visibility, heat index, AQI, or thunderstorm risk relevant to travel?
- Is the advice specific enough to act on by morning/afternoon/evening?

## Output safeguards

- Use "较可能", "可能", "不确定" for uncertain precipitation or convection.
- Use exact dates, not only "today/tomorrow".
- Do not imply official authority. For severe weather, tell the user to follow local meteorological bureau alerts.
