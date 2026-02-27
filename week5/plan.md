# Week 5 学习计划：Agentic Development with Warp

---

## 第一部分：第一性原理 - 你需要做什么（Manager 视角）

### 1.1 核心概念理解

**什么是 Agentic Development？**
- 不是让 AI 一次性写完所有代码
- 而是把你自己变成**指挥官**，把任务分解给多个 AI Agent
- 每个 Agent 做独立的事情，最后你整合验证

**为什么用 Warp？**
- Warp 是一个 AI 增强的终端
- 核心能力：**多 Tab + AI 集成**
- 你可以同时开多个 Tab，每个 Tab 跑一个 AI Agent
- 类似"你有多个员工同时工作"

### 1.2 你的角色：Human Manager

```
你（Manager）
    │
    ├── Agent A (Task 9 - 数据库索引)
    │           └── 任务：给数据库加索引
    │
    ├── Agent B (Task 4 - 批量操作)
    │           └── 任务：筛选 + 批量完成
    │
    └── Agent C (测试验证)
                    └── 任务：写测试，确保不坏
```

**你需要做：**
1. **分解任务** - 把大任务拆成独立的小任务
2. **分配任务** - 告诉每个 Agent 做什么（给 prompt）
3. **整合结果** - 把各 Agent 的产出合并
4. **验证** - 运行测试确保一切正常

### 1.3 本次选定的任务组合

**选定的组合：A（数据库专项）**

| 任务 | 难度 | 做什么 |
|------|------|--------|
| **Task 9** | ⭐⭐ | 数据库索引优化 |
| **Task 4** | ⭐⭐ | 筛选 + 批量操作 |

**Task 9 - 数据库索引**：
```
现在：查 "标题包含 X 的笔记" → 慢（一行一行读）
加了索引：→ 快（像书的目录，直接翻到那一页）
```

**Task 4 - 筛选 + 批量**：
```
筛选：只显示"已完成"的任务
批量：一次选 5 个任务，点"全部完成"
```

**目标：每个任务都要实现两种自动化方式**
| 方式 | 要求 | 做什么 |
|------|------|--------|
| **Warp Drive** | 至少一个 | 创建可重用的 prompt/规则 |
| **Multi-agent** | 至少一个 | 多 Agent 并行工作 |

### 1.4 你不需要做前端

本次任务**纯后端 + 数据库**，不涉及：
- React
- 前端页面
- UI 组件

只需要：
- Python 后端 API
- SQLAlchemy 模型
- 数据库优化
- 测试

---

## 第二部分：AI Agent 协调指南（给 Sisyphus / AI 用）

### 2.1 Agent 类型选择

| Agent 类型 | 用途 | 场景 |
|------------|------|------|
| `deep` | 深度开发 | 数据库索引、复杂查询 |
| `quick` | 简单任务 | 小修复、格式调整 |
| `ultrabrain` | 硬核问题 | 性能优化、复杂逻辑 |

### 2.2 技能加载

对于纯数据库任务，不需要特殊技能：

```python
task(
    category="deep",
    load_skills=[],  # 不需要前端技能
    prompt="..."
)
```

### 2.3 Multi-Agent 并行模式

**Task 9 + Task 4 可以并行执行：**

```python
# Agent A: Task 9 - 索引优化
task(
    category="deep",
    prompt="在 week5/backend/ 实现 Task 9: 数据库索引..."
)

# Agent B: Task 4 - 批量操作
task(
    category="deep", 
    prompt="在 week5/backend/ 实现 Task 4: 筛选 + 批量..."
)
```

两个 Agent **完全独立**，可以同时启动。

**验证阶段**：等两个都完成后，再运行测试。

### 2.4 Prompt 模板

**后端 Agent Prompt（数据库任务）：**

```
TASK: 实现 Task [编号] - [任务名]

## 具体要求
[从 TASKS.md 复制具体要求]

## EXPECTED OUTCOME
- [ ] 修改文件：backend/app/models.py
- [ ] 修改文件：backend/app/schemas.py  
- [ ] 修改文件：backend/app/routers/[xxx].py
- [ ] 添加测试：backend/tests/test_[xxx].py

## MUST DO
- 遵循现有代码风格（week5/backend/app/）
- 使用 SQLAlchemy 2.0 模式
- 添加类型提示
- 现有测试必须继续通过

## MUST NOT DO
- 不要修改前端文件
- 不要删除现有功能

## CONTEXT
- 现有模型：Note, ActionItem
- 现有路由：/notes/, /action-items/
- 数据库：SQLite
```

### 2.5 验证清单

每个 Agent 完成后的检查项：

- [ ] `lsp_diagnostics` 无错误
- [ ] `make lint` 通过
- [ ] `make test` 通过
- [ ] 手动测试 API 正常

---

## 第三部分：实际操作指南

### 3.1 快速开始

```bash
# 1. 进入 week5 目录
cd week5

# 2. 运行现有测试，确保基础正常
make test

# 3. 启动 Agent 执行任务
# Task 9 + Task 4 可以并行
```

### 3.2 任务执行顺序

**阶段 1：Task 9 - 数据库索引**
- 修改 models.py 加索引
- 测试查询性能

**阶段 2：Task 4 - 筛选 + 批量**
- 添加筛选 API
- 添加批量完成 API
- 测试事务回滚

**阶段 3：验证**
- make test
- make lint

### 3.3 整合验证命令

```bash
# 格式化 + lint
make format
make lint

# 测试
make test

# 运行
make run

# 访问
# http://localhost:8000/docs
```

---

## 附录：常用命令速查

| 命令 | 作用 |
|------|------|
| `make run` | 启动服务 |
| `make test` | 运行测试 |
| `make format` | 代码格式化 |
| `make lint` | 代码检查 |
| `PYTHONPATH=. pytest -v` | 详细测试输出 |
