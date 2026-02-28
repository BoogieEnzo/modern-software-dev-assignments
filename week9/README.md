# Week9 Repo Daily Brief

GitHub 趋势仓库每日简报：三列展示 **7 天热门增长**、**30 天热门增长**、**Agent OS 新兴项目**，每张卡片带 💡 推荐理由（规则模板生成，无 LLM）。

## 运行

```bash
cd week9
pip install -r requirements.txt
make run
```

浏览器打开: http://localhost:8002

## 远程开发 (SSH + 浏览器)

服务绑定 `0.0.0.0:8002`，可从 Mac 直接访问服务器 IP，或用 SSH 隧道：

| 操作 | 命令 |
|------|------|
| 启动服务 | `make run` |
| 查看本机 IP | `hostname -I \| awk '{print $1}'` |
| 访问 | `http://<服务器IP>:8002` 或隧道后 `http://localhost:8002` |
| 隧道 (Mac) | `ssh -L 8002:localhost:8002 fengde@<服务器IP>` |
| 释放端口 | `lsof -ti:8002 \| xargs kill -9` |

## 测试

```bash
make test
# 或
PYTHONPATH=. pytest backend/tests/ -v
```

## 环境变量

- **GITHUB_TOKEN**（可选，建议设置以避免 API 限流）

## 文档

- **knowledge.md** — 项目知识库（数据来源、API、推荐理由、缓存策略）
- **AGENT.md** — 开发任务线与已完成/待办
