## Week 3 – OpenWeather MCP Server

### 概览

这个目录包含一个基于 OpenWeather 的 MCP Server，实现了两个工具：

- `get_current_weather`：查询指定城市的当前天气。
- `get_weather_forecast`：查询指定城市未来若干小时的天气预报。

它采用 **STDIO MCP 模式**，可以被支持 MCP 的客户端（例如 Claude Desktop、Cursor、OpenCode 等）调用。

### 环境准备

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)（推荐）

```bash
cd week3
uv venv .venv
source .venv/bin/activate
uv pip install "mcp[cli]" httpx
```

### 环境变量

| 变量 | 必需 | 默认值 | 说明 |
|---|---|---|---|
| `OPENWEATHER_API_KEY` | 是 | — | 在 openweathermap.org 免费注册获取 |
| `OPENWEATHER_BASE_URL` | 否 | `https://api.openweathermap.org` | API 基础地址 |
| `REQUEST_TIMEOUT_SECONDS` | 否 | `10` | HTTP 请求超时秒数 |

### 启动 MCP Server（手动测试）

在仓库根目录下执行：

```bash
source week3/.venv/bin/activate
OPENWEATHER_API_KEY="你的key" python -m week3.server.main
```

### 在 OpenCode 中使用

编辑 `~/.opencode/opencode.json`，在 `mcp` 字段中添加：

```json
{
  "mcp": {
    "openweather": {
      "type": "local",
      "command": [
        "/absolute/path/to/week3/.venv/bin/python",
        "-m",
        "week3.server.main"
      ],
      "enabled": true,
      "environment": {
        "OPENWEATHER_API_KEY": "你的key",
        "PYTHONPATH": "/absolute/path/to/modern-software-dev-assignments"
      }
    }
  }
}
```

重启 OpenCode 后，在聊天中说"查一下北京的天气"即可触发工具调用。

### 工具说明

#### `get_current_weather`

- **参数**
  - `city` (string, 必填)：城市名称，例如 `"Beijing"`、`"San Francisco"`。
  - `country_code` (string, 可选)：国家代码，ISO 3166-1 alpha-2，例如 `"CN"`、`"US"`。
  - `units` (string, 可选)：单位系统，`"standard"` / `"metric"` / `"imperial"`，默认 `"metric"`。

- **返回示例（结构）**

```json
{
  "city": "Beijing, CN",
  "temperature": 26.5,
  "feels_like": 27.0,
  "humidity": 60,
  "wind_speed": 3.5,
  "description": "clear sky",
  "observed_at": "2025-06-01T12:34:56+00:00"
}
```

#### `get_weather_forecast`

- **参数**
  - `city` (string, 必填)
  - `country_code` (string, 可选)
  - `units` (string, 可选)
  - `hours` (int, 可选)：大致需要的预报时长，按 3 小时为步长，默认 12，最大 120。

- **返回示例（结构）**

```json
{
  "city": "Beijing, CN",
  "entries": [
    {
      "time": "2025-06-01T15:00:00+00:00",
      "temperature": 25.0,
      "description": "few clouds",
      "probability_of_precipitation": 0.1
    }
  ]
}
```

### 错误与鲁棒性行为

- 如果 `OPENWEATHER_API_KEY` 未配置：工具会返回提示，要求先设置环境变量。
- 如果城市无法解析：工具会返回“未找到该城市，请检查拼写或加上国家代码”等信息。
- 如果触发 OpenWeather 限流（429）：工具会提示稍后重试。
- 请求超时或上游 5xx：会被统一映射为可读错误信息，而不是让 server 崩溃。

