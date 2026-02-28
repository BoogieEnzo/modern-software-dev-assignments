# AGENTS.md — Week 8 (OS Paper Hub)

## 项目身份

- **名称**: OS Paper Hub (操作系统论文知识库)
- **技术栈**: FastAPI + SQLite + Vanilla JS
- **Python**: 3.12
- **入口**: `python -m app.main` (默认端口 8001，访问 http://localhost:8001)

---

## 运行命令

```bash
# 激活环境
cd /home/fengde/Projects/modern-software-dev-assignments/week8
source .venv/bin/activate

# 启动服务 (可选: 设置Ollama模型)
export OLLAMA_MODEL=gemma3:1b
python -m app.main

# 运行测试 (必须用本目录 .venv，否则缺 arxiv 等依赖)
PYTHONPATH=. .venv/bin/python -m pytest tests/ -v
```

### 远程开发 (SSH 隧道，Mac 浏览器访问 Linux 上的 week8)

| 步骤 | 位置 | 操作 |
|-----|------|------|
| 1. 启动服务 | Linux 服务器 | `cd week8 && source .venv/bin/activate && python -m app.main` |
| 2. 建隧道 | Mac 终端 | `ssh -L 8001:localhost:8001 fengde@<服务器IP>`，保持登录 |
| 3. 访问 | Mac Chrome | 打开 `http://localhost:8001` |
| 4. 跑测试 | Linux 服务器 | 另开 SSH，`cd week8 && PYTHONPATH=. .venv/bin/python -m pytest tests/ -v` |

---

## 项目结构 (关键路径)

| 路径 | 用途 |
|------|------|
| `app/main.py` | FastAPI 入口, 路由注册, 静态文件挂载 |
| `app/models.py` | SQLAlchemy 模型 (Paper, Favorite) |
| `app/schemas.py` | Pydantic 响应模型 |
| `app/database.py` | 数据库连接, SessionLocal, get_db |
| `app/routers/papers.py` | 论文 CRUD, 下载, AI摘要, GitHub关联 |
| `app/routers/chat.py` | 全站聊天接口 |
| `app/routers/search.py` | ArXiv 在线搜索 |
| `app/services/arxiv.py` | ArXiv API 封装 |
| `app/services/paperswithcode.py` | GitHub 仓库查询 |
| `app/services/ollama.py` | 本地 AI 摘要/聊天 |
| `app/services/pdf.py` | PDF 元数据/全文提取 |
| `app/static/index.html` | 前端页面 |
| `app/static/app.js` | 前端逻辑 |
| `papers/` | 论文 PDF 存储目录 |
| `tests/` | 测试文件 |

---

## 前端 / 产品方案（约定）

- **顶部仅两块、不糅杂**：① 搜索 ArXiv（在前） ② 论文列表。
- **搜索**：单独一块，一个干净的搜索框 + 搜索按钮（或回车即搜），仅做 ArXiv 搜索，不与其他筛选/Tab 混在一起。
- **论文列表**：展示本地所有论文；**一行一条**，不用卡片；每行仅：**标题 + 作者 + 年份**。
- **去掉**：推荐、收藏（彻底去掉，前端不展示收藏与推荐相关入口）。

### 修改计划（UI 与交互）

| 项 | 约定 |
|----|------|
| 论文列表标题 | 不显示「本地论文」等字样，直接展示表格。 |
| 论文列表展示 | 一行一条：标题、作者、年份；数据来自 `GET /api/papers/`（DB 中已有摘要/元数据，不实时读 PDF 生成）。 |
| 点击行为 | 论文列表：点击行**在新标签页打开该论文 PDF**（`target="_blank"`）；无 PDF 时再打开详情弹窗。 |
| 搜索 ArXiv 结果 | 表格列：标题、作者、**年份**（由 `published` 取）、操作；**下载按钮**使用小号样式（如 `.btn-download`），高度与体积偏小。 |
| 全站对话 | 固定于页面**右下角**（如 `position: fixed; right/bottom`），不占主内容区。 |

---

## Ollama 与 AI 功能

- **运行位置**：Ollama 与 week8 后端同机（Linux 服务器）。本机未跑 Ollama 则摘要/对话不可用。
- **谁启动谁**：Ollama 与 week8 是**两个独立进程**。执行 `python -m app.main` **不会**自动启动 Ollama；需在本机先运行 `ollama serve`（或由系统/其他方式常驻），week8 再连 `localhost:11434` 调用。若 11434 已被占用，说明 Ollama 已在跑，无需再执行 `ollama serve`。
- **启动方式（在服务器上执行）**：
  ```bash
  ollama serve          # 前台
  nohup ollama serve > /tmp/ollama.log 2>&1 &   # 后台
  ollama list           # 检查是否在跑、已有模型（如 gemma3:1b）
  ```
- **默认模型**：`OLLAMA_MODEL=gemma3:1b`（与 `ollama list` 中一致即可）。
- **AI 摘要交互**：点击「生成AI摘要」后须有**加载中**（如按钮禁用/转圈或「生成中…」）；若失败（含 Ollama 未启动），**在页面上明确展示错误信息**（例如「Ollama 未启动，请在服务器执行 ollama serve」），不依赖弹窗。

---

## 对话功能方案（约定）

- **两处对话**：
  1. **全站对话**：固定在页面右下角（不依赖当前选中论文）。用户输入、后端调 Ollama 回复；无 PDF 上下文，可做通用问答。
  2. **论文内对话**：用户**点进某篇论文详情**后，在该详情内再提供对话区。此处对话**基于该论文 PDF 全文**：后端用本地 Ollama 读取该论文已下载的 PDF 全文（先抽取正文再送 Ollama），再根据用户问题回答。**前提**：该论文已下载到本地（有 `pdf_path` 且文件存在），否则提示先下载。
- **实现要点**：论文内对话需 **PDF 全文抽取**（如 pdfplumber）；后端提供「带 PDF 上下文的 chat」接口（例如 `POST /api/papers/{id}/chat`），请求体含用户消息，后端拼 prompt（论文全文 + 用户问题）调 Ollama 生成回复。全站对话可用单独接口（如 `POST /api/chat`）无论文上下文。

---

## 代码规范

### SQLAlchemy 2.0
```python
# 查询用 select(), 获取用 scalars().all()
from sqlalchemy import select
rows = db.execute(select(Paper)).scalars().all()

# 主键获取用 db.get()
paper = db.get(Paper, paper_id)
```

### Pydantic v2
```python
# 用 model_validate() 不是 parse_obj()
paper_dict = PaperResponse.model_validate(paper)

# 用 from_attributes = True
class Config:
    from_attributes = True
```

### 导入顺序
1. 标准库
2. 第三方包
3. 本地相对导入 (`from ..models import ...`)

---

## API 端点

| Method | Path | 功能 |
|--------|------|------|
| GET | `/api/papers/` | 论文列表 |
| GET | `/api/papers/{id}` | 论文详情 |
| POST | `/api/papers/download` | 从ArXiv下载 |
| GET | `/api/papers/{id}/summarize` | AI摘要 |
| GET | `/api/papers/{id}/code` | GitHub仓库 |
| GET | `/api/search/?q=` | ArXiv在线搜索 |
| POST | `/api/chat` | 全站对话（无论文上下文，Ollama） |
| POST | `/api/papers/{id}/chat` | 论文内对话（基于该论文 PDF 全文，需已下载到本地） |

---

## 测试现状与要求

### 当前测试基线（按现需求）
- `test_papers.py`: 列表/详情/下载/代码关联/扫描逻辑。
- `test_search.py`: 空查询、正常查询、异常返回、参数透传。
- `test_ai_summary.py`: 404、Ollama 不可用、生成成功、生成失败。
- `test_chat.py`: 全站聊天与论文聊天的成功和关键错误分支。

### 丢弃策略（删除无效测试）
删除或改写以下测试：
1. 依赖旧需求（favorites/recommendation）的测试。
2. 断言过弱的测试（例如“summary 或 error 都算通过”）。
3. 与现接口行为不一致的断言（如错误字段写成 `error` 而不是 `detail`）。

### 必须覆盖的关键错误分支
1. `/api/chat`: Ollama 不可用、Ollama 无回复。
2. `/api/papers/{id}/chat`: 无论文、无 pdf_path、文件不存在、文本提取失败、Ollama 不可用、Ollama 无回复。
3. `/api/papers/{id}/summarize`: 论文不存在、Ollama 不可用、生成失败。
4. `/api/papers/download`: 重复下载不触发外部下载、外部下载异常返回 500。

---

## 已知问题

1. **Ollama 依赖**: AI摘要需要本地运行 `ollama serve`
2. **PDF 元数据**: 部分PDF标题解析不完整 (PDF解析库限制)
3. **ArXiv API**: 网络不稳定时可能超时

---

## 调试提示

```bash
# 端口占用 (默认 8001)
lsof -ti:8001 | xargs kill -9

# 重置数据库
rm data/app.db
python -m app.main  # 自动重建

# 查看API文档
curl http://localhost:8001/docs
```
