# Week 3 计划：OpenWeather MCP Server

---

## 第一部分：整体架构与关键认知

### 你在做什么

你在做一个 **MCP Server**——一个"给大模型调用的工具服务"，不是给人用的天气 App。

**MCP 架构一句话**：MCP 是一套协议，规定了"AI 客户端如何发现和调用外部工具"。你写的 server 就是按这套协议暴露工具。

**完整调用链**：

```
用户在 OpenCode 里说话
  → OpenCode 把消息发给大模型
    → 模型看到有 get_current_weather 这个 MCP tool 可用
      → 模型决定调用它，传入参数 {"city": "Beijing"}
        → OpenCode 按 STDIO 协议把调用请求发给你的 MCP Server 进程
          → 你的 server 拿着参数去请求 OpenWeather API
            → OpenWeather 返回 JSON
          → 你的 server 整理成结构化结果，通过 STDIO 返回
        → OpenCode 把结果交给模型
      → 模型用自然语言回答用户
```

### 三个角色各自干什么

| 角色 | 是什么 | 职责 |
|---|---|---|
| OpenCode | MCP 客户端 | 发现你注册的 MCP server，把模型的 tool call 转发过去 |
| 你的 MCP Server | STDIO 进程 | 接收 tool call → 调 OpenWeather → 返回结构化结果 |
| OpenWeather | 外部 HTTP API | 提供真实天气数据，需要 API key |

### STDIO 模式怎么运作

- OpenCode 启动你的 server 作为**子进程**。
- 通信方式：OpenCode 往你的进程 **stdin** 写 JSON-RPC 请求，从 **stdout** 读响应。
- 所以你的代码**绝对不能往 stdout 打日志**（`print()` 会破坏协议），日志必须走 stderr。

### 你要交付什么

1. **MCP Server 代码**（`week3/server/`），至少 2 个 tools。
2. **README**，让别人能装依赖、配好 key、跑起来、知道怎么在客户端里注册。
3. **鲁棒性**：城市不存在、超时、限流、上游挂了——都要返回可读错误，不能崩。

### 环境实操要点

- **API key 谁提供**：你自己去 openweathermap.org 注册免费账号，拿到 key。免费层包含 Current Weather、5 Day Forecast、Geocoding 三个端点，够用。
- **Python 环境**：Ubuntu 系统只有 `python3`，没有 `python`。必须用虚拟环境装依赖（PEP 668 禁止全局 pip install）：
  ```bash
  cd week3 && uv venv .venv && source .venv/bin/activate && uv pip install "mcp[cli]" httpx
  ```
- **`__init__.py`**：`week3/` 和 `week3/server/` 各需要一个空的 `__init__.py`，否则 `python -m week3.server.main` 报 ModuleNotFoundError。
- **OpenCode 注册 MCP**：配置文件在 `~/.opencode/opencode.json`，关键是 `command` 用 venv Python 绝对路径 + `PYTHONPATH` 指向项目根：
  ```json
  {
    "mcp": {
      "openweather": {
        "type": "local",
        "command": [
          "/absolute/path/to/week3/.venv/bin/python",
          "-m", "week3.server.main"
        ],
        "enabled": true,
        "environment": {
          "OPENWEATHER_API_KEY": "<your-key>",
          "PYTHONPATH": "/absolute/path/to/project-root"
        }
      }
    }
  }
  ```

---

## 第二部分：给 AI Agent 的详细实施计划

### 1. 目标与边界

- 目标：基于 OpenWeather，交付一个 MCP Server，暴露至少 2 个可用的天气工具，满足课程对功能性、鲁棒性和文档的要求。
- 范围：优先实现本地 STDIO MCP；有余力时，再尝试 HTTP 版本或云端部署（Vercel / Cloudflare 等）。

### 2. 外部 API 设计（OpenWeather）

使用 OpenWeather 免费端点：

- `GET /geo/1.0/direct`：城市名 → 经纬度（用于先 geocoding）。
- `GET /data/2.5/weather`：当前天气。
- `GET /data/2.5/forecast`：5 天 / 3 小时预报。

关键环境变量：

- `OPENWEATHER_API_KEY`（必需）。
- `OPENWEATHER_BASE_URL`（可选，默认 `https://api.openweathermap.org`）。
- `REQUEST_TIMEOUT_SECONDS`（可选，默认 `10`）。

### 3. MCP 能力设计

#### 3.1 必做 tools

1. `get_current_weather`
   - 输入参数：
     - `city: string`（必填）。
     - `country_code?: string`（可选，ISO 3166-1 alpha-2，如 `CN`、`US`）。
     - `units?: string`（可选，`standard` / `metric` / `imperial`，默认 `metric`）。
   - 行为：
     - 调用 geocoding 端点获取经纬度。
     - 用经纬度请求当前天气。
     - 返回结构化对象：温度、体感温度、湿度、风速、天气描述、观测时间、城市名。

2. `get_weather_forecast`
   - 输入参数：
     - `city: string`（必填）。
     - `country_code?: string`。
     - `units?: string`。
     - `hours?: int`（可选，控制返回未来多少小时的数据，如 6/12/24，默认 12）。
   - 行为：
     - 同样先 geocoding。
     - 调用 forecast 端点，按 3 小时间隔的列表。
     - 按 `hours` 截断，返回时间序列：每个时间点的温度、降水概率（如果可用）、天气描述。

### 4. 代码结构规划

```text
week3/
  server/
    __init__.py
    main.py               # MCP server 入口（STDIO）
    openweather_client.py # OpenWeather 请求封装（HTTP 调用、重试、错误分类）
    models.py             # 数据模型：工具出参、上游响应抽象
    errors.py             # 自定义异常类型（超时、限流、城市未找到等）
    config.py             # 读取环境变量，集中配置
    logging_config.py     # 日志到 stderr 的统一配置
  __init__.py
  tests/
    test_tools.py
    test_client.py
  README.md
  plan.md
```

### 5. 实施步骤（Agent 视角）

1. **初始化工程**
   - 在 `week3/` 下创建 `server/`、`tests/`、`README.md`。
   - 选择 Python 作为实现语言，引入 MCP Python SDK。

2. **配置与模型**
   - 在 `config.py` 中读取并验证必要环境变量。
   - 在 `models.py` 中定义工具输出模型和对 OpenWeather 响应的最小抽象。

3. **OpenWeather client 封装**
   - 在 `openweather_client.py` 中实现 `geocode_city`、`fetch_current_weather`、`fetch_forecast`。
   - 超时设置、429 映射为 `RateLimitError`、空结果映射为 `CityNotFoundError`。

4. **Tools 实现**
   - 在 `main.py` 中用 `@mcp.tool()` 注册两个工具。
   - 捕获 client 层异常，转换为可读错误信息。

5. **MCP Server 入口**
   - `main.py` 末尾 `mcp.run()` 启动 STDIO 循环。
   - 日志全部走 stderr。

6. **测试**
   - mock OpenWeather 响应，覆盖：正常返回、城市不存在、429、5xx。

7. **README**
   - 依赖安装、环境变量、启动命令、OpenCode 配置示例、两个工具的参数和返回结构。

### 6. 鲁棒性与评分对齐

- **鲁棒性标准：**
  - 超时：返回可读错误，不崩溃。
  - 限流（429）：提示稍后重试。
  - 空结果：明确返回"未找到该城市"。
  - 参数错误：入口校验。
  - 日志：不污染 stdout。

- **与评分标准的映射：**
  - Functionality（35）：确保两个工具全流程跑通，参数清晰。
  - Reliability（20）：错误分类、超时配置、限流处理。
  - Developer Experience（20）：README 可复现、目录结构清楚。
  - Code Quality（15）：分层、命名、类型标注。
  - Extra Credit（10）：有余力再做 HTTP MCP 或鉴权。
