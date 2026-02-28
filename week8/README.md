# Week8 OS Paper Hub

操作系统论文知识库：本地论文列表 + ArXiv 搜索下载 + AI 摘要（Ollama）+ 全站/论文内对话。

## 运行

```bash
cd week8
source .venv/bin/activate

# 可选：设置 Ollama 模型与超时（AI 摘要/对话依赖本地 Ollama）
export OLLAMA_MODEL=gemma3:1b
export OLLAMA_TIMEOUT_SECONDS=300

python -m app.main
```

浏览器打开: http://localhost:8001

## 远程开发 (SSH 隧道)

| 步骤 | 操作 |
|------|------|
| 1. 服务器 | `cd week8 && source .venv/bin/activate && python -m app.main` |
| 2. Mac 隧道 | `ssh -L 8001:localhost:8001 fengde@<服务器IP>` |
| 3. 访问 | Mac 浏览器打开 `http://localhost:8001` |

## 测试

```bash
cd week8
PYTHONPATH=. .venv/bin/python -m pytest tests/ -v
```

## 环境变量

- **OLLAMA_MODEL** — 本地 Ollama 模型名（默认 gemma3:1b）
- **OLLAMA_TIMEOUT_SECONDS** — Ollama 请求超时（默认 300）

## 文档

- **AGENT.md** — 项目身份、运行命令、API、前端约定、Ollama 说明、测试与调试
- **knowledge.md** — 项目知识库（需求基线、数据流、元数据治理）
- **plan.md** — 需求与 API 设计
