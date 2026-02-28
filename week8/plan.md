# Week 8 Plan: OS Paper Hub (Current Scope)

## 项目目标
做一个本地运行的 OS 论文站：本地论文列表 + ArXiv 搜索下载 + AI 摘要 + 聊天问答。

---

## 当前需求基线（以此为准）

1. 顶部只保留两个入口：`搜索 ArXiv`（前）和 `论文列表`（后）。
2. 不做推荐，不做收藏，前端不展示任何 favorites/recommendation 入口。
3. `论文列表` 用表格一行一条展示：标题、作者、年份。
4. 点击论文行优先在新标签页直接打开 PDF；无本地 PDF 时才退化为详情弹窗。
5. 搜索结果包含年份列，下载按钮体积小（视觉弱化）。
6. 全站聊天固定在页面右下角。
7. 论文内聊天基于本地 PDF 全文（先下载到本地才可用）。
8. AI 摘要和聊天必须有加载态与页面内错误提示（尤其 Ollama 未启动）。
9. 端口固定 `8001`，并支持 Mac -> Linux SSH 隧道访问。

---

## API 设计（当前）

```text
GET  /api/papers/                # 本地论文列表
GET  /api/papers/{id}            # 论文详情
POST /api/papers/download        # ArXiv 下载并入库
GET  /api/papers/{id}/summarize  # 生成/保存 AI 摘要
GET  /api/papers/{id}/code       # 查论文相关代码仓库
GET  /api/search/?q=&max_results=# ArXiv 搜索
POST /api/chat                   # 全站聊天（无论文上下文）
POST /api/papers/{id}/chat       # 论文聊天（PDF 全文上下文）
```

---

## 非功能约束

- 启动服务不能被初始扫描长时间阻塞（后台线程扫描 `papers/`）。
- 前端静态资源避免缓存污染（版本戳 + no-cache 头）。
- `loadPapers` 请求超时要有明确错误文案与重试按钮。

---

## 启动与验证

### 1) 服务启动

```bash
cd /home/fengde/Projects/modern-software-dev-assignments/week8
source .venv/bin/activate
export OLLAMA_MODEL=gemma3:1b   # 可选
python -m app.main
```

访问：`http://localhost:8001`

### 2) Ollama 检查与启动

```bash
ss -tlnp | rg 11434
curl -s http://localhost:11434/api/tags
```

未运行时：

```bash
ollama serve
# 或
nohup ollama serve > /tmp/ollama.log 2>&1 &
```

### 3) SSH 隧道（Mac 浏览器访问 Linux）

```bash
ssh -L 8001:localhost:8001 fengde@<服务器IP>
```

Mac 浏览器访问：`http://localhost:8001`

---

## 测试计划（当前）

后端必须覆盖：

1. 论文接口：空列表、详情不存在、下载成功/重复/失败、代码关联成功/空/不存在。
2. 搜索接口：空查询、正常查询、异常 500、参数透传。
3. AI 摘要：论文不存在、Ollama 不可用、生成成功、生成失败。
4. 全站聊天：成功、Ollama 不可用、Ollama 无回复。
5. 论文聊天：论文不存在、无 PDF、PDF 文件缺失、Ollama 不可用、PDF 提取失败、无回复、成功。
6. 扫描逻辑：从文件名提取年份、跳过重复 PDF。

---

## 已知限制

1. PDF 元数据提取受 PDF 文本质量影响，标题/作者可能不完整。
2. AI 功能依赖本机 Ollama 服务与模型可用性。
