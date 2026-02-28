# OS Paper Hub — 项目知识库

## 项目是什么？

**OS Paper Hub** 是本地运行的「操作系统论文」知识库：管理已下载论文、从 ArXiv 搜索并下载、用本地 Ollama 做 AI 摘要与对话。

- **论文列表**：表格展示本地论文（标题、作者、年份），点击行打开 PDF 或详情
- **ArXiv 搜索**：在线搜索、下载入库
- **AI 摘要**：对单篇论文调用 Ollama 生成摘要
- **全站对话**：页面右下角固定入口，通用问答（无 PDF 上下文）
- **论文内对话**：在论文详情内，基于该论文 PDF 全文与 Ollama 对话（需已下载到本地）

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | SQLite |
| 前端 | 原生 HTML + CSS + JS（静态在 `app/static/`） |
| AI | 本地 Ollama（摘要、全站聊天、论文内聊天） |
| 论文 | ArXiv API、PDF 存储于 `papers/` |

---

## 运行与端口

- **默认端口**: 8001
- **启动**: `python -m app.main`（需先 `ollama serve` 才能用摘要/对话）
- **释放端口**: `lsof -ti:8001 | xargs kill -9`

---

## 数据流与 API

- **本地论文**: `GET /api/papers/`、`GET /api/papers/{id}`，数据来自 SQLite
- **下载**: `POST /api/papers/download` 从 ArXiv 拉取 PDF 并写入 DB 与 `papers/`
- **AI 摘要**: `GET /api/papers/{id}/summarize` 调 Ollama，结果可存 DB
- **全站对话**: `POST /api/chat`，无论文上下文
- **论文内对话**: `POST /api/papers/{id}/chat`，后端用 PDF 全文 + 用户问题调 Ollama
- **ArXiv 搜索**: `GET /api/search/?q=...`
- **元数据补全**: `POST /api/papers/enrich` 批量补全/规范化标题、作者、年份等

---

## 前端约定（与 AGENT.md 一致）

- 顶部两块：① 搜索 ArXiv ② 论文列表
- 论文列表：一行一条，标题 + 作者 + 年份；点击行优先新标签打开 PDF
- 全站聊天：固定右下角
- 不做推荐、不做收藏

---

## 元数据治理（概要）

- 优先从 ArXiv API 与 PDF 提取 `arxiv_id`/年份，再规则清洗标题、作者
- 支持 `metadata_source`、`metadata_confidence`，可做去重与「待完善」展示
- 详见 AGENT.md「元数据治理方案」

---

## 项目结构（关键）

```
week8/
├── app/
│   ├── main.py              # FastAPI 入口，端口 8001
│   ├── models.py            # Paper, Favorite
│   ├── database.py          # SQLite Session
│   ├── routers/             # papers, chat, search
│   ├── services/             # arxiv, ollama, pdf, paperswithcode
│   └── static/              # index.html, app.js
├── papers/                  # PDF 存储
├── data/                    # app.db
├── tests/
├── AGENT.md                 # 开发任务与约定
├── knowledge.md             # 本文件
└── plan.md                  # 需求与 API 设计
```

---

## 已知问题与调试

- **Ollama 未启动**：摘要/对话会失败，前端需明确提示
- **长问题/长上下文**：易触发 Ollama 超时，可提高 `OLLAMA_TIMEOUT_SECONDS` 或缩短提问
- **端口占用**：`lsof -ti:8001 | xargs kill -9`

更多见 **AGENT.md**（API 端点、测试要求、Ollama 排查）。
