# Weather Briefing Analyst

[![skills.sh](https://skills.sh/b/zshzzz/weather-briefing-analyst)](https://skills.sh/zshzzz/weather-briefing-analyst)

English | [中文](#中文)

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

Both scripts overwrite an existing `weather-briefing-analyst` skill at the target location.

## Skill Layout

```text
weather-briefing-analyst/
├── README.md
├── LICENSE
├── .gitignore
├── scripts/
│   ├── install-codex.sh
│   └── install-claude-code.sh
└── weather-briefing-analyst/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    └── references/
        └── data-sources.md
```

## Capabilities

- Resolves a city, district, address, landmark, route point, or coordinate into a forecast location.
- Offers configurable depth before collecting data:
  - Quick: weather forecast only.
  - Standard: forecast plus radar and air-quality context.
  - Deep: forecast plus radar, satellite/cloud imagery, and broader weather-pattern analysis.
- Compares official weather sources and model/API forecasts.
- Uses radar or satellite/cloud imagery only when valid current imagery is accessible.
- Produces day-by-day forecast tables with confidence levels and travel advice.
- Clearly labels uncertainty, stale imagery, inaccessible sources, and non-official guidance.

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

## 中文

一个面向 Codex / 通用 agent skills 生态的天气研判 skill。用户输入城市、区县、地址、景点或坐标后，它会综合天气预报、实况、雷达、可用的卫星云图/云量资料、空气质量、预警和出行场景，给出未来几天更可操作的天气判断和出行建议。

适合这类问题：

- `北京市朝阳区未来几天天气怎么样，适合出门吗？`
- `帮我分析上海浦东明后天是否会下雨，给出通勤建议`
- `用标准版分析北京朝阳区未来几天天气`
- `用深度版看杭州西湖附近的雷达和云图形势`

### 安装

通过 skills CLI 从 GitHub 安装：

```bash
npx skills add https://github.com/zshzzz/weather-briefing-analyst --skill weather-briefing-analyst
```

如果你的 skills 客户端支持仓库简写：

```bash
npx skills add zshzzz/weather-briefing-analyst --skill weather-briefing-analyst
```

安装到本机 Codex：

```bash
./scripts/install-codex.sh
```

安装到本机 Claude Code：

```bash
./scripts/install-claude-code.sh
```

两个脚本都会直接覆盖目标位置已有的 `weather-briefing-analyst` skill。

### 功能

- 将城市、区县、地址、地标、路线点或坐标解析为预报位置。
- 开始分析前提供分级选择：
  - 快速版：只查天气预报。
  - 标准版：天气预报 + 雷达/空气质量。
  - 深度版：天气预报 + 雷达 + 云图/天气形势。
- 对比官方天气源和模型/API 预报。
- 仅在能拿到有效、当前的图像资料时使用雷达或卫星云图。
- 输出逐日预报表、置信度和具体出行建议。
- 明确说明不确定性、过期资料、不可访问数据源和非官方判断。

### 让 find skill 更容易搜到

对 skills.sh 和类似工具，关键做法是：

- 使用公开 GitHub 仓库，并包含有效的 `SKILL.md`。
- 在 front matter 中写清楚 `name` 和 `description`。
- README 覆盖 weather forecast、radar、satellite、cloud imagery、AQI、warnings、travel advice 等关键词。
- 添加 skills.sh badge。
- 使用 skills CLI 安装一次；如果遥测开启，安装数据可能帮助后续发现和排序。

索引通常不是实时的。发布后建议安装一次，并等待发现服务刷新。

### 安全说明

这个 skill 只提供出行决策支持，不替代官方预警。遇到强对流、暴雨、高温等高风险天气，应优先关注当地气象台和应急部门发布的信息。
