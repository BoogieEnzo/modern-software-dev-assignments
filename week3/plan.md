# Week 3 计划：OpenWeather MCP Server

---

## 第一部分：给学生看的“大图景说明”

这一周你要做的，不是一个给人用的天气 App，而是一个 **给大模型用的“天气工具箱”**：

- 大模型：会说话、会推理，但自己不会上网查天气。
- 你的 MCP Server：是一个“天气工具箱”，大模型可以调用它。
- OpenWeather API：是真实天气数据的来源。

**完整链路长这样：**

> 用户跟模型说话 → 模型决定调用 `get_current_weather` 等工具 →  
> 工具在你的 MCP Server 里运行 → 去请求 OpenWeather →  
> 把整理好的结果返回给模型 → 模型再用自然语言告诉用户。

你要交付的是：

1. **一个 MCP Server**（可以先做成本机 STDIO 版，后面有力气再考虑 HTTP 版）。
2. **至少两个天气相关的 MCP tools**，比如：
   - `get_current_weather`：查当前天气。
   - `get_weather_forecast`：查未来一段时间的预报。
3. **清晰的 README**，让别人知道：
   - 怎么装依赖、怎么配置 `OPENWEATHER_API_KEY`。
   - 怎么启动 server。
   - MCP 客户端（Claude Desktop / Cursor）要如何配置才能调用这些 tools。

你真正要学会的能力是三件事：

- 会把一个外部 HTTP API（OpenWeather）**封装成稳定、可重试的工具接口**。
- 会处理坏情况：城市不存在、网络超时、被限流、上游 5xx。
- 会写一份别人看得懂、能按照步骤复现的 README。

**如果你只看这一部分，大概需要记住的事情：**

1. 我做的是“给模型用的天气工具箱”，不是手机 App。
2. 我需要至少 2 个 tool：一个查当前天气，一个查未来预报。
3. 我必须考虑异常情况，并在 README 里教别人怎么跑起来。

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

推荐目录（允许调整命名，但保持分层思想）：

```text
week3/
  server/
    main.py               # MCP server 入口（STDIO，后续可扩展 HTTP）
    tools.py              # MCP tools 实现（调用 client 层）
    openweather_client.py # OpenWeather 请求封装（HTTP 调用、重试、错误分类）
    models.py             # Pydantic 数据模型：工具入参/出参、上游响应抽象
    errors.py             # 自定义异常类型（超时、限流、城市未找到等）
    config.py             # 读取环境变量，集中配置
    logging_config.py     # 日志到 stderr 的统一配置
  tests/
    test_tools.py         # 针对 tools 的单测（可用 mock 上游）
    test_client.py        # 针对 client 行为的单测（超时、429 等）
  README.md               # 对外文档
  plan.md                 # 本文件
```

### 5. 实施步骤（Agent 视角）

1. **初始化工程**
   - 在 `week3/` 下创建 `server/`、`tests/`、`README.md`。
   - 选择 Python 作为实现语言，引入 MCP Python SDK（或符合作业要求的最小 JSON-RPC 实现）。

2. **配置与模型**
   - 在 `config.py` 中读取并验证必要环境变量。
   - 在 `models.py` 中用类型模型定义：
     - 工具入参模型（两个 tools）。
     - 工具输出模型（统一字段名，便于文档化）。
     - 对 OpenWeather 响应做最小必要抽象，避免在业务层直接操作原始 JSON。

3. **OpenWeather client 封装**
   - 在 `openweather_client.py` 中实现：
     - `geocode_city(city, country_code)`。
     - `fetch_current_weather(lat, lon, units)`。
     - `fetch_forecast(lat, lon, units)`。
   - 增加：
     - 超时设置（使用 `REQUEST_TIMEOUT_SECONDS`）。
     - 对 4xx/5xx 的分类：
       - 429：专门映射为 `RateLimitError`。
       - 404 / 空结果：映射为 `CityNotFoundError` 或类似。
   - 所有错误统一抛出自定义异常，交给上层 tools 处理为可读信息。

4. **Tools 实现**
   - 在 `tools.py` 中：
     - 注册两个 tools 的元数据（名称、描述、参数 schema）。
     - 在 handler 中调用 client 层：
       - 先 geocoding，处理重名/空结果。
       - 再拉天气/预报，并按模型定义组装输出。
     - 捕获 client 抛出的异常，转换为：
       - 清晰错误信息字符串。
       - 简洁的错误码（如 `rate_limit`, `city_not_found`, `timeout`）。

5. **MCP Server 入口**
   - 在 `main.py` 中：
     - 按 MCP STDIO quickstart 要求，注册 tools，并启动事件循环。
     - 确保日志全部通过 `logging` 输出到 stderr，不污染 stdout。
   - 若有时间，再增加一个简单 HTTP endpoint：
     - 使用 FastAPI/Flask 暴露一个 JSON-RPC 兼容接口，实现 Remote HTTP 模式。

6. **测试与自验**
   - 在 `tests/test_client.py` 中：
     - mock OpenWeather 响应，覆盖：
       - 正常城市返回。
       - 空数组（城市不存在）。
       - 429 限流。
       - 5xx 上游错误。
   - 在 `tests/test_tools.py` 中：
     - mock client，验证 tools 在成功/失败时的输出结构和错误信息。

7. **README 编写**
   - 描述：
     - 依赖安装步骤（例如 `pip install -r requirements.txt` 或 `uv` 流程）。
     - 必需/可选环境变量及默认值。
     - 启动 MCP Server 的命令。
     - 至少一个 MCP 客户端的配置示例（Claude Desktop / Cursor / inspector）。
     - 两个主要 tools 的参数说明和示例输入输出。

### 6. 鲁棒性与评分对齐（Agent 需要保证）

- **鲁棒性标准：**
  - 超时：工具返回“请求 OpenWeather 超时，请稍后重试”之类的可读信息，不崩溃。
  - 限流：识别 429，提示用户稍后重试或减小频率。
  - 空结果：对城市名无法解析时，明确返回“未找到该城市，请检查拼写或加上国家代码”。
  - 参数错误：在 tools 入参层面做简单校验（例如 `hours > 0` 且不超过某个上限）。
  - 日志：不往 stdout 打杂，所有 debug/info/error 走 stderr。

- **与评分标准的映射：**
  - Functionality（35）：确保两个工具全流程跑通，参数清晰。
  - Reliability（20）：通过错误分类、超时配置、限流处理来拿分。
  - Developer Experience（20）：README 可复现、目录结构清楚。
  - Code Quality（15）：分层、命名、类型标注基本到位。
  - Extra Credit（10）：有余力再做 HTTP MCP 或鉴权（如 API key 校验）。
