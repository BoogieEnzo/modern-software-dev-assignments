# Week 3 学习型计划：OpenWeather MCP Server

## 1. 先理解这门作业在做什么
这次作业不是“做一个天气 App”，而是“做一个给大模型调用的工具服务”。

你要做的是一个 **MCP Server**。可以把它理解成：
- 大模型是“会说话的大脑”
- MCP Server 是“可被大脑调用的工具箱”
- OpenWeather 是“工具箱背后的真实数据来源”

当模型需要天气信息时，不是胡猜，而是通过 MCP 调用你提供的工具，再由你的工具去请求 OpenWeather，最后把结构化结果返回给模型。

## 2. 什么是 MCP（学生版）
MCP（Model Context Protocol）是一种约定，统一“模型如何调用外部能力”。

你在这个作业中会接触三个核心能力：
- `tools`：可执行函数（本次作业最核心）
- `resources`：可读取的数据资源（可选增强）
- `prompts`：可复用提示模板（可选增强）

最低通过线：把 `tools` 做好，至少 2 个。

## 3. 这次作业真正训练的能力
- 把“外部 API”封装成“稳定可调用的工具接口”
- 参数设计与输入校验（不是只跑通 happy path）
- 错误处理（超时、限流、空结果、上游异常）
- 工程化交付（README、运行方式、示例调用）

一句话：训练你从“会写脚本”升级到“能交付可用服务”。

## 4. 你的环境怎么用（Linux + Cursor + OpenCode + Codex CLI）
你现在的工具链足够完成作业。建议分工如下（不涉及具体写哪行代码）：
- `Cursor`：主编辑器，写文档、看目录结构、对照任务要求逐项检查。
- `Codex CLI`：执行命令、跑测试、快速改文件、做收尾验收。
- `OpenCode`：可作为第二个 AI 视角做 review 或补充说明。

重点不是“哪个工具最强”，而是你要能解释：你的 server 如何被模型调用、如何在失败时给出稳定反馈。

## 5. API 选型与范围（已确定 OpenWeather）
使用 OpenWeather 免费端点：
- `GET /geo/1.0/direct`：城市名 -> 经纬度
- `GET /data/2.5/weather`：当前天气
- `GET /data/2.5/forecast`：5 天 / 3 小时预报

环境变量：
- `OPENWEATHER_API_KEY`（必需）
- `OPENWEATHER_BASE_URL`（可选，默认 `https://api.openweathermap.org`）
- `REQUEST_TIMEOUT_SECONDS`（可选，默认 10）

## 6. 你要交付的 MCP 能力（功能蓝图）

### 6.1 必做 tools（至少 2 个）
1. `get_current_weather`
- 输入：`city`、可选 `country_code`、`units`
- 输出：当前温度、体感、湿度、风速、天气描述、观测时间

2. `get_weather_forecast`
- 输入：`city`、可选 `country_code`、`units`、`hours`
- 输出：未来若干小时天气序列（温度、降水概率、描述）

### 6.2 可选增强
- `resolve_city`：处理重名城市
- `weather://cities/{query}` 资源：缓存查询结果
- `weather_summary_prompt`：把预报整理成自然语言建议

## 7. 推荐目录结构（便于讲清楚你的工程设计）
```text
week3/
  server/
    main.py               # MCP server 入口（STDIO）
    tools.py              # tools 定义
    openweather_client.py # OpenWeather 请求封装
    models.py             # 输入输出模型
    errors.py             # 统一错误
    config.py             # 环境变量配置
    logging_config.py     # 日志配置（stderr）
  tests/
    test_tools.py
    test_client.py
  README.md
  plan.md
```

## 8. 学习导向实施步骤（按“先懂后做”）
1. 先画数据流：模型 -> MCP tool -> OpenWeather -> MCP -> 模型。
2. 明确两个 tool 的输入输出契约（字段、类型、边界）。
3. 再做请求封装：把 OpenWeather 调用统一放在 client 层。
4. 补齐异常路径：超时、429、城市不存在、5xx。
5. 写最小测试：至少覆盖 1 条成功 + 1 条失败路径/工具。
6. 最后写 README：让别人不问你就能跑起来并会调用。

## 9. 鲁棒性标准（老师看重）
- 超时：返回可读错误，不崩溃。
- 限流（429）：提示等待或重试策略。
- 空结果：明确说明“未找到城市”，而不是返回模糊空对象。
- 参数错误：在工具入口就拦截非法值。
- 日志规范：STDIO 模式下不要把日志打到 stdout。

## 10. 交付物检查清单（提交前自查）
- `week3/server/*`：源代码完整，结构清晰。
- `week3/README.md`：
  - 安装与运行步骤
  - 环境变量说明
  - MCP 客户端配置示例（至少一种）
  - 每个 tool 的参数和示例输出
- 你可以口头解释：
  - 为什么要先 geocoding 再查天气
  - 发生 429/超时时用户会看到什么
  - 你的设计如何满足“2+ tools + resilience”

## 11. 与评分标准对齐（你该把精力放哪）
- Functionality（35）：先确保 2 个工具真实可用。
- Reliability（20）：重点拿稳超时/限流/空结果处理。
- Developer Experience（20）：README 可直接复现。
- Code Quality（15）：分层清楚、命名清楚、逻辑不绕。
- Extra Credit（10）：最后有余力再做远程 HTTP 或鉴权。

## 12. 常见误区（提前避坑）
- 误区 1：只追求“能返回数据”，忽略异常路径。
- 误区 2：README 太简略，别人无法复现。
- 误区 3：日志输出污染 stdout，导致 MCP 通信异常。
- 误区 4：城市重名不处理，结果看似成功但语义错误。
