# Week 8 Plan: OS Paper Hub

## 项目目标
个人操作系统论文知识库 + AI 辅助理解。

---

## 核心功能

### 1. 内置20篇经典OS论文
- `papers/` 文件夹预置20篇经典论文PDF ✅ 已完成

### 2. ArXiv搜索下载
- 前端搜索ArXiv论文
- 点击下载 → 保存到本地
- 自动解析PDF元数据

### 3. AI摘要生成
- 本地Ollama生成摘要
- 存JSON，他人clone可直接查看

### 4. GitHub代码关联
- Papers with Code API 查询关联仓库

### 5. 基础功能
- 论文列表、详情、搜索、收藏

---

## 技术方案

**FastAPI + SQLite + 简单HTML**

| 功能 | 技术 |
|------|------|
| 后端 | FastAPI |
| 数据库 | SQLite |
| ArXiv | `arxiv` Python库 |
| Papers with Code | `paperswithcode-client` 库 |
| AI摘要 | Ollama API |
| PDF解析 | `pdfplumber` |
| 前端 | HTML + JS（嵌在后端） |

---

## Agent 任务分配

### Agent 1: 前端 👨‍🎨
- 任务：实现 HTML/CSS/JS 界面
- 职责：
  - 论文列表页面
  - 论文详情页面
  - ArXiv搜索界面
  - 收藏功能
- Category: `visual-engineering`

### Agent 2: 后端 🔧
- 任务：实现 FastAPI 服务
- 职责：
  - 数据库模型 (SQLAlchemy)
  - API路由 (papers, favorites, search)
  - ArXiv 集成
  - Papers with Code 集成
  - Ollama AI 摘要集成
- Category: `deep`

### Agent 3: 测试 🧪
- 任务：编写测试用例
- 职责：
  - API单元测试
  - 集成测试
  - 边界情况测试
- Category: `quick`

### Agent 4: QA Review ✅
- 任务：代码审查
- 职责：
  - 检查代码质量
  - 验证功能完整性
  - 确保符合最佳实践
- Category: `momus`

---

## 项目结构

```
week8/
├── papers/                    # 论文PDF (20篇已完成)
│   └── summaries/             # AI摘要JSON
├── app/
│   ├── main.py               # FastAPI入口
│   ├── models.py             # 数据库模型
│   ├── routers/              # API路由
│   │   ├── papers.py
│   │   └── favorites.py
│   ├── services/             # 业务逻辑
│   │   ├── arxiv.py          # ArXiv搜索下载
│   │   ├── paperswithcode.py # GitHub关联
│   │   ├── ollama.py         # AI摘要
│   │   └── pdf.py            # PDF解析
│   └── static/               # 前端HTML/JS
├── tests/                    # 测试用例
├── data/                     # SQLite数据库
├── requirements.txt
└── README.md
```

---

## API 设计

```
GET  /api/papers/              # 论文列表
GET  /api/papers/{id}          # 论文详情
POST /api/papers/download      # 从ArXiv下载论文
GET  /api/papers/{id}/summarize # AI摘要生成
GET  /api/papers/{id}/code     # GitHub关联仓库
GET  /api/search?q=            # 搜索ArXiv在线
POST /api/favorites/           # 收藏
GET  /api/favorites/           # 收藏列表
```

---

## 环境变量

```bash
# 可选: 设置 Ollama 模型 (默认: gemma3:1b)
export OLLAMA_MODEL=gemma3:1b
```

---

## 验证功能

### 1. 启动服务

服务已在运行中: http://localhost:8000

如果需要重启:
```bash
cd /home/fengde/Projects/modern-software-dev-assignments/week8
source .venv/bin/activate
export OLLAMA_MODEL=gemma3:1b  # 可选
python -m app.main
```

### 2. 浏览器验证

访问: **http://localhost:8000**

验证项目:
1. **论文列表** - 应显示20篇预置论文
2. **搜索ArXiv** - 输入关键词搜索，点击下载
3. **收藏功能** - 点击收藏按钮，切换到收藏Tab查看
4. **AI摘要** - 点击论文→查看详情→生成AI摘要 (需启动Ollama)
5. **GitHub关联** - 查看论文详情中的代码链接

### 3. API 验证

```bash
# 论文列表
curl http://localhost:8000/api/papers/

# 搜索ArXiv
curl "http://localhost:8000/api/search?q=distributed systems&max_results=5"

# 论文详情
curl http://localhost:8000/api/papers/1

# 收藏列表
curl http://localhost:8000/api/favorites/

# AI摘要 (需Ollama运行中)
curl http://localhost:8000/api/papers/1/summarize

# GitHub代码
curl http://localhost:8000/api/papers/1/code
```

### 4. Ollama 测试

确保Ollama运行中:
```bash
ollama list  # 查看可用模型
ollama run gemma3:1b "Hello"  # 测试模型
```

---

## 进度

- [x] 20篇论文下载 ✅
- [x] 前端开发 ✅
- [x] 后端开发 ✅ (已修复依赖问题)
- [x] 基础功能 ✅ (论文列表、搜索、收藏、AI摘要、GitHub关联)
- [ ] 测试编写
- [ ] QA Review

---

## 已知问题

1. PDF元数据提取 - 部分PDF标题显示不正常（PDF解析限制）
2. Ollama AI摘要需要本地运行Ollama服务
