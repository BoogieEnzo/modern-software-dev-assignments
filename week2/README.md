## 项目概览

一个简单的“行动项（Action Items）提取”小应用：

- 前端：`frontend/index.html`，原生 HTML + JS。
- 后端：FastAPI（`app/main.py`、`app/routers/*`），SQLite（`app/db.py`）。
- 抽取逻辑：规则版 `extract_action_items` 和 LLM 版 `extract_action_items_llm`（`app/services/extract.py`）。

---

## 安装与运行

在仓库根目录（不是 `week2/`）：

```bash
conda activate cs146s
poetry install --no-interaction
```

准备 Ollama（任选合适模型）：

```bash
ollama serve
ollama run llama3.1:8b
# 可选：指定用于 LLM 抽取的模型名
export OLLAMA_ACTION_MODEL="llama3.1:8b"
```

启动后端：

```bash
cd week2
poetry run uvicorn app.main:app --reload --port 8000
```

浏览器访问：`http://localhost:8000/`

---

## 主要接口（API）

所有路径默认前缀为 `http://localhost:8000`。

- `GET /`
  - 返回前端页面。

- `POST /notes`
  - 创建笔记，body：`{ "content": "..." }`

- `GET /notes`
  - 列出所有笔记。

- `GET /notes/{note_id}`
  - 获取指定笔记。

- `POST /action-items/extract`
  - 使用规则版提取行动项。
  - body：`{ "text": "...", "save_note": true|false }`

- `POST /action-items/extract-llm`
  - 使用 LLM 版提取行动项（通过 Ollama）。
  - body 同上。

- `GET /action-items`
  - 列出所有行动项，可选 `?note_id=...` 过滤。

- `POST /action-items/{id}/done`
  - 更新某个行动项的完成状态，body：`{ "done": true|false }`

---

## 前端按钮行为（简要）

- **Extract** → `POST /action-items/extract`
- **Extract LLM** → `POST /action-items/extract-llm`
- **List Notes** → `GET /notes`
- 勾选行动项复选框 → `POST /action-items/{id}/done`

---

## 运行测试

在 `week2/` 目录下：

```bash
poetry run pytest
```

或只跑提取函数的测试：

```bash
poetry run pytest tests/test_extract.py
```

