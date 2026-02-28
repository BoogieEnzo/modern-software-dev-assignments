# Repo Daily Brief - 项目知识库

## 项目是什么？

**Repo Daily Brief** 是一个 GitHub 趋势仓库每日简报页面。

- 展示过去 7 天和 30 天 GitHub star 增长最快的仓库
- 每天自动从 GitHub API 抓取数据并缓存到 SQLite
- 用户打开页面即可看到当日热门仓库推荐

---

## 页面展示

```
┌─────────────────────────────────────────────────────────┐
│  📊 Repo Daily Brief                                    │
│  日期 2026-02-28 · 更新于 2/28/2026, 3:48:43 AM        │
├──────────────────────────┬──────────────────────────────┤
│  🔥 7天热门增长          │  📈 30天热门增长            │
│  ─────────────────────   │  ─────────────────────      │
│  1. xxx/yyy              │  1. xxx/yyy                │
│     语言: Go              │     语言: Python            │
│     ⭐ 20000             │     ⭐ 26000               │
│     🔥 +272/7d           │     📈 +26000/30d         │
│                          │                              │
│  2. xxx/yyy              │  2. xxx/yyy                │
│     语言: Python          │     语言: Go                │
│     ⭐ 26000             │     ⭐ 20000               │
│     🔥 +271/7d           │     📈 +20000/30d         │
│                          │                              │
│  3. xxx/yyy  (Rust)      │  3. xxx/yyy  (Rust)       │
│     语言: Rust            │     语言: Rust              │
│     ⭐ 20000             │     ⭐ 19000               │
│     🔥 +150/7d           │     📈 +18000/30d         │
└──────────────────────────┴──────────────────────────────┘
```

每个仓库卡片显示：
- 仓库名（链接到 GitHub）
- 描述
- 语言、当前 star 数、7天/30天增长、fork 数
- 创建日期
- 推荐理由

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
- **缓存策略**: 当天数据存储在 SQLite，次日自动刷新
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
  "repos_30d": [...]
}
```

---

## 项目结构

```
week9/
├── backend/
│   ├── app/
│   │   ├── main.py       # FastAPI 入口
│   │   ├── service.py   # 业务逻辑
│   │   ├── github_client.py  # GitHub API 调用
│   │   ├── db.py         # SQLite 数据库
│   │   └── schemas.py    # Pydantic 模型
│   └── tests/            # 测试
├── frontend/
│   ├── index.html        # 页面
│   ├── app.js            # 前端逻辑
│   └── styles.css        # 样式
├── data/                 # SQLite 数据库文件
├── Makefile              # 运行命令
└── requirements.txt      # Python 依赖
```
