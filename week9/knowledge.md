# Repo Daily Brief - 项目知识库

本目录三份文档：**README.md**（运行/测试/环境）、**knowledge.md**（本文件：数据来源、API、推荐理由）、**AGENT.md**（开发任务线与已完成/待办）。

---

## 项目是什么？

**Repo Daily Brief** 是一个 GitHub 趋势仓库每日简报页面。

- 展示过去 7 天和 30 天 GitHub star 增长最快的仓库
- 第三列展示 Agent OS（AI Agent 相关）新兴项目
- 每天自动从 GitHub API 抓取数据并缓存到 SQLite
- 用户打开页面即可看到当日热门仓库推荐

---

## 页面展示

```
┌────────────────────────────────────────────────────────────────────────┐
│  📊 Repo Daily Brief                                                   │
│  日期 2026-02-28 · 更新于 2/28/2026, 3:48:43 AM                       │
├───────────────────────┬───────────────────────┬───────────────────────┤
│  🔥 7天热门增长       │  📈 30天热门增长      │  🤖 Agent OS 新兴项目  │
│  ─────────────────   │  ─────────────────    │  ─────────────────    │
│  1. xxx/yyy          │  1. xxx/yyy           │  1. agent/agent-os   │
│     语言: Go             │     语言: Python        │     语言: Rust         │
│     ⭐ 20000              │     ⭐ 26000             │     ⭐ 500              │
│     🔥 +272/7d            │     📈 +26000/30d       │     🍴 50              │
│                       │                        │  topics: [agent, ai]   │
│  2. xxx/yyy          │  2. xxx/yyy           │  2. xxx/yyy           │
│     语言: Python         │     语言: Go              │     语言: Python       │
│     ⭐ 26000              │     ⭐ 20000              │     ⭐ 300              │
│     🔥 +271/7d            │     📈 +20000/30d        │     💡 推荐理由        │
│     💡 推荐理由           │     💡 推荐理由          │                        │
│  3. xxx/yyy (Rust)   │  3. xxx/yyy (Rust)    │  3. xxx/yyy (Rust)   │
└───────────────────────┴───────────────────────┴───────────────────────┘
```

每个仓库卡片显示：
- 仓库名（链接到 GitHub）
- 描述
- 语言、当前 star 数、7天/30天增长、fork 数
- 创建日期
- **💡 推荐理由**（三列均有，规则模板生成，不调用任何 LLM）

Agent OS 额外显示：
- GitHub topics 标签

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | SQLite |
| 前端 | 原生 HTML + CSS + JS |
| 部署 | 本地运行 |

---

## 本地运行指南（Linux 服务器）

### 1. SSH 到服务器

```bash
ssh -L 8002:localhost:8002 fengde@100.90.186.53
```

或直接访问：
```
http://100.90.186.53:8002
```

### 2. 在服务器上启动服务

```bash
cd /home/fengde/Projects/modern-software-dev-assignments/week9
make run
```

服务启动后显示：
```
Uvicorn running on http://0.0.0.0:8002
```

### 3. 在 Mac 浏览器中访问

```
http://100.90.186.53:8002
```

或使用 SSH tunnel：
```bash
# 在 Mac 终端运行
ssh -L 8002:localhost:8002 fengde@100.90.186.53
# 然后打开浏览器访问
http://localhost:8002
```

### 其他命令

| 操作 | 命令 |
|------|------|
| 停止服务 | `Ctrl + C` |
| 终止端口占用 | `lsof -ti:8002 \| xargs kill -9` |
| 运行测试 | `make test` |
| 查看日志 | `tail -f /tmp/server.log` |
| 设置 GitHub Token | `export GITHUB_TOKEN=xxx` |

---

## 数据来源

- **GitHub REST API**: 搜索热门仓库 + 获取 star 事件时间线
- **搜索关键词**:
  - 7天/30天热门：按 star 数量排序
  - Agent OS（agent / agent operating system 相关项目）：查询用 `agent in:name,description,topics`（含 stars>=100、近 30 天创建）。
  - **踩坑**：GitHub 搜索的括号 OR 写法 `(A OR B OR C)` 会静默返回 0 结果；另外超过 5 个 OR/AND/NOT 会 422。所以改用单关键词 + `in:` 限定范围。
  - 若缓存里 `repos_agent` 为空，接口会尝试实时再拉一次并写回缓存，避免一直显示「暂无Agent相关项目」。
- **推荐理由**: 纯规则生成（不调用 LLM）。7d/30d 根据 `weekly_star_gain` / `monthly_star_gain` 阈值选模板（如「近7天暴涨 X 星」「近30天增长 X 星」）；Agent OS 根据 `stars_today` 与 topics（如 mcp、ai-agents）生成一句（如「TypeScript 热门 Agent 项目，短期冲上 5000 星，支持 MCP 协议」）。从缓存读出的旧 Agent 数据若缺 `reason`，接口会现场用 `build_agent_reason()` 回填。
- **缓存策略**: 当天数据存储在 SQLite，4小时自动刷新
- **30 天数据保留**: 超过 30 天的快照自动清理

---

## API 接口

```
GET /api/trending/today
```

返回：
```json
{
  "date": "2026-02-28",
  "generated_at": "2026-02-28T03:48:43.977042Z",
  "repos_7d": [...],
  "repos_30d": [...],
  "repos_agent": [...]
}
```

---

## 项目结构

```
week9/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 入口
│   │   ├── service.py        # 业务逻辑 + 后台刷新
│   │   ├── github_client.py   # GitHub API 调用
│   │   ├── db.py             # SQLite 数据库
│   │   └── schemas.py        # Pydantic 模型
│   └── tests/                 # 测试
├── frontend/
│   ├── index.html            # 页面（3列布局）
│   ├── app.js                # 前端逻辑
│   └── styles.css            # 样式
├── data/                     # SQLite 数据库文件
├── Makefile                  # 运行命令
└── requirements.txt          # Python 依赖
```

---

## 功能特性

1. **3 列布局**: 7天热门 | 30天热门 | Agent OS 新兴项目
2. **💡 推荐理由**: 三列均展示一句推荐理由，由后端规则模板生成（`build_reason` / `build_agent_reason`），无 LLM 调用；缓存中的 Agent 数据缺理由时会自动回填
3. **Rust 优先级**: 第 3 位优先展示 Rust 项目
4. **后台刷新**: 每 4 小时自动更新数据
5. **北京时间**: 显示北京时间
6. **响应式**: 支持桌面/平板/手机
7. **GitHub Token**: 设置后避免 API 限流

---

## 示例简报数据（2026-02-28）

| 列 | 示例仓库 |
|----|----------|
| 7天热门 | cloudflare/vinext, anthropics/financial-services-plugins, AlexsJones/llmfit |
| 30天热门 | HKUDS/nanobot, sipeed/picoclaw, zeroclaw-labs/zeroclaw |
| Agent OS 新兴项目 | 与 agent / AI agent / agent framework / **agent OS** / **agent operating system(s)** 等主题相关的近期仓库（如 agiresearch/AIOS、Agent-OS、zeroclaw 等） |

第三列「🤖 Agent OS 新兴项目」对应 API 的 `repos_agent`，每条也带 `reason` 推荐理由；若接口未返回或拉取失败，前端会显示「暂无Agent相关项目」或「加载中...」。

---

## 如何运行本项目（简要）

```bash
cd /home/fengde/Projects/modern-software-dev-assignments/week9
make run
```

浏览器访问：`http://localhost:8002` 或 `http://<服务器IP>:8002`。需 7d/30d 数据时请配置 `GITHUB_TOKEN`。**更新时间**为北京时间（API 返回 ISO +08:00，前端按 Asia/Shanghai 显示）。
