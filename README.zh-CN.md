# Weather Briefing Analyst

[![skills.sh](https://skills.sh/b/zshzzz/weather-briefing-analyst)](https://skills.sh/zshzzz/weather-briefing-analyst)

[English](README.md) | 中文

一个面向 Codex / 通用 agent skills 生态的天气研判 skill。用户输入城市、区县、地址、景点或坐标后，它会综合天气预报、实况、雷达、可用的卫星云图/云量资料、空气质量、预警和出行场景，给出未来几天更可操作的天气判断和出行建议。

适合这类问题：

- `北京市朝阳区未来几天天气怎么样，适合出门吗？`
- `帮我分析上海浦东明后天是否会下雨，给出通勤建议`
- `用标准版分析北京朝阳区未来几天天气`
- `用深度版看杭州西湖附近的雷达和云图形势`

## 安装

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

两个脚本都会把 `weather-briefing-analyst` 安装到目标 skills 目录。
如果目标位置已存在，默认会先创建带时间戳的备份；传入 `--force` 时才会不备份直接覆盖。

## 目录结构

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

## 功能

- 将城市、区县、地址、地标、路线点或坐标解析为预报位置。
- 根据用户问题自动推断分析等级，并允许用户覆盖：
  - 快速版：只查天气预报。
  - 标准版：天气预报 + 雷达/空气质量。
  - 深度版：天气预报 + 雷达 + 云图/天气形势。
- 提供确定性的 Open-Meteo 地理编码和预报采集脚本，作为标准化数据起点。
- 在可用时对比官方天气源和模型/API 预报。
- 仅在能拿到有效、当前的图像资料时使用雷达或卫星云图。
- 输出逐日预报表、分项置信度和具体出行建议。
- 明确说明不确定性、过期资料、不可访问数据源和非官方判断。

## 分析等级触发方式

skill 默认根据用户问题自动推断分析等级；用户也可以显式指定 `快速版`、`标准版` 或 `深度版`。

- 快速版：简单天气查询，例如 `广州明天会不会下雨？`、`明天成都最高温多少？`、`快速看一下明后天要不要带伞`。
- 标准版：出行、通勤、穿衣、老人儿童活动、户外窗口等决策问题，例如 `北京朝阳区未来几天适合出门吗？`。
- 深度版：需要雷达、卫星云图、雷暴时段、暴雨研判或天气形势诊断的问题，例如 `帮我看深圳今天下午云图和雷达，判断暴雨什么时候来`。

示例：

```text
用户：帮我看北京市朝阳区未来几天天气，适合出门吗？
预期：自动选择标准版；先运行内置快照脚本，再按可用性补充官方预报、预警、雷达和空气质量。
```

```text
用户：明后天去环球影城会不会下雨，云图怎么看？
预期：自动选择深度版；优先使用主题公园 POI 坐标，先运行内置脚本取得模式预报，再检查有效雷达/卫星云图后才能给出图像判断。
```

## 数据快照脚本

内置的 Open-Meteo 快照脚本可以给 agent 提供确定性的基础数据：

```bash
python weather-briefing-analyst/scripts/weather_snapshot.py "39.9,116.4" --days 3
```

对普通单点天气简报，agent 应先使用这个脚本，再视需要补充浏览器/API 查询，而不是直接用原始 `curl` 替代脚本。该快照脚本目前只覆盖 Open-Meteo 地理编码和模式预报；官方预警、雷达、卫星云图、AQI 和 UV 仍需额外来源。

如果本机 Python CA 证书环境异常，HTTPS 请求报 `CERTIFICATE_VERIFY_FAILED`，可以显式加上 `--allow-insecure-tls` 作为诊断降级；使用该参数时应把结果视为可信度较低的数据源。

## 测试

运行本地离线检查：

```bash
python3 tests/run_static_checks.py
```

该命令会编译内置脚本、校验 JSONL eval seeds、运行单元测试，并在本机安装了 `shellcheck` 时检查 shell 脚本。GitHub Actions 会在 push 和 pull request 时运行同类核心检查。

## 让 find skill 更容易搜到

对 skills.sh 和类似工具，关键做法是：

- 使用公开 GitHub 仓库，并包含有效的 `SKILL.md`。
- 在 front matter 中写清楚 `name` 和 `description`。
- README 覆盖 weather forecast、radar、satellite、cloud imagery、AQI、warnings、travel advice 等关键词。
- 添加 skills.sh badge。
- 使用 skills CLI 安装一次；如果遥测开启，安装数据可能帮助后续发现和排序。

索引通常不是实时的。发布后建议安装一次，并等待发现服务刷新。

## 安全说明

这个 skill 只提供出行决策支持，不替代官方预警。遇到强对流、暴雨、高温等高风险天气，应优先关注当地气象台和应急部门发布的信息。
