# Week 7 学习计划：四分支 + 多 Agent 并行（全程 Cursor 托管）

---

## 第一部分：总体目标（Manager 视角）

**本周目标**：在一个更复杂的后端代码库上，完成 4 个独立任务，每个任务：
- 在 **单独 Git 分支** 上开发
- 用 **Cursor（一个 1-shot prompt）驱动 AI 开发**
- **代码审查、测试编写与执行尽量交给 Cursor 完成**
- 在 GitHub 上开 **单独 PR**，仅做最小化人工检查（是否能跑通、是否大致符合题意）

任务来自 `week7/docs/TASKS.md`：
- **Task 1**：Add more endpoints and validations
- **Task 2**：Extend extraction logic
- **Task 3**：Add a new model and relationships
- **Task 4**：Improve tests for pagination and sorting

你的角色依然是 **Human Manager**，但偏“自动化运营”：
1. **分解任务** → 4 个相对独立的后端子任务  
2. **分配任务** → 4 个 Cursor 会话（4 个“Agent”），各管一个分支  
3. **整合结果** → 通过 4 个 PR 合入 `master`  
4. **验证** → 尽量通过 Cursor 自动生成/运行测试，人工只在明显异常时介入

---

## 第二部分：Git 分支与并行策略

### 2.1 分支规划（每个任务一个分支）

建议的分支命名：
- **Task 1**：`week7-task1-endpoints-validation`
- **Task 2**：`week7-task2-extract-logic`
- **Task 3**：`week7-task3-new-models`
- **Task 4**：`week7-task4-tests-pagination-sorting`

从 `master` 出发创建 4 个分支（可以按需、非一次性全开）：

```bash
# 确保在 master 且是最新
git checkout master

# Task 1
git checkout -b week7-task1-endpoints-validation

# Task 2
git checkout master
git checkout -b week7-task2-extract-logic

# Task 3
git checkout master
git checkout -b week7-task3-new-models

# Task 4
git checkout master
git checkout -b week7-task4-tests-pagination-sorting
```

并行的含义：
- 逻辑上：4 个分支彼此独立，互不干扰
- 实际操作上：你可以在 4 个分支之间 **来回切换**，或者用 `git worktree` 在需要时把分支 checkout 到不同目录（可选）

### 2.2 每个分支的标准工作流（Cursor 托管版）

以 **Task 1 分支** 为例，其它任务完全照搬：

```bash
# 1. 切到对应分支
git checkout week7-task1-endpoints-validation

# 2. 使用 Cursor，一次性写清楚 Task 1 的需求和约束，发 1-shot prompt
#    → 让 AI 完成主代码改动（包括必要的测试代码）

# 3. 让 Cursor 生成并建议测试命令（例如 make test 或 pytest ...）
#    → 直接在终端执行这些命令，把是否通过交给 AI 分析

# 4. 对 AI 生成的 diff 只做快速扫一眼（不做逐行深度人工 review）

# 5. 提交本分支
git add .
git commit -m "Week7 Task 1: add endpoints and validations"

# 6. 推到远程
git push -u origin week7-task1-endpoints-validation
```

然后去 GitHub：
- 从 `week7-task1-endpoints-validation` → `master` 开一个 PR  
- 在 PR 描述里简单写：问题、方案、Cursor 帮你跑过的测试命令与结果（可由 Cursor 总结）  
- 不强制使用 Graphite，所有 review 反馈以 Cursor 的建议为主

其它 3 个任务分支按同样流程执行即可。

---

## 第三部分：Cursor 多 Agent 并行策略

### 3.1 将 4 个任务映射到 4 个 Cursor 会话

建议你在 Cursor 里开 **4 个独立聊天/会话标签页**，人为地当成 4 个“Agent”：

- **Agent A（Task 1）**
  - 分支：`week7-task1-endpoints-validation`
  - 负责：新增/扩展 API endpoint，输入校验、错误处理
- **Agent B（Task 2）**
  - 分支：`week7-task2-extract-logic`
  - 负责：改进 action item 提取逻辑，加入更丰富的 pattern / heuristic
- **Agent C（Task 3）**
  - 分支：`week7-task3-new-models`
  - 负责：新增数据库模型，配置关系（FK / relationship），更新相关 API 与 schema
- **Agent D（Task 4）**
  - 分支：`week7-task4-tests-pagination-sorting`
  - 负责：为分页、排序相关功能补齐/加强测试用例

你在终端中切换分支时，对应在 Cursor 里也让当前会话“绑定”到那个分支进行开发。

### 3.2 每个 Agent 的 1-shot Prompt 模板

你可以对每个任务，用类似下面的英文/中英 prompt（示例以 Task 1 为例）：

```text
TASK: Implement Week7 Task 1 - Add more endpoints and validations for the week7 backend.

CONTEXT:
- Codebase: week7/ (FastAPI + SQLite / SQLAlchemy 风格，参考课程说明)
- Goal: Add/extend API endpoints and add proper input validation & error handling.
- Keep style consistent with existing code (type hints, Pydantic models, SQLAlchemy 2.0 patterns).

REQUIREMENTS:
- Identify where the current endpoints and schemas live.
- Add or extend endpoints to support the new behavior as described in TASKS.md.
- Add input validation with Pydantic schemas.
- Use proper HTTPException status codes and error messages.
- Update or add tests to cover the new endpoints and validation cases.

MUST:
- Do not break existing tests.
- Maintain clear, readable code and good naming.
- Keep changes scoped to this task only.

OUTPUT:
- List which files you will modify.
- Then propose concrete code changes.
```

对 Task 2/3/4，只需要替换 `TASK` 和 `Goal` 段落，约束保持一致（类型提示、测试、错误处理等）。

---

## 第四部分：Review 策略（全程依赖 Cursor）

### 4.1 Review 目标

总体目标：**把深入的逻辑检查和测试建议交给 Cursor，自己只做 sanity check**：
- Cursor 负责：找潜在 bug、边界条件、风格问题、测试覆盖不足等  
- 你负责：看一下改动有没有明显违背题目要求、有没有一眼能看出的离谱错误

### 4.2 每个 Task 的自动化 Review 流程

对每个分支：
- 在 Cursor 里用“请作为严谨的 code reviewer 审查本分支 diff”这类 prompt，让它指出问题并给出修改建议  
- 让 Cursor 自动生成/修改测试用例，覆盖它认为的关键路径和边界情况  
- 让 Cursor 给出推荐的测试命令（例如 `make test` / `PYTHONPATH=. pytest ...`），在终端执行，并把失败信息交回给 Cursor 让它修

---

## 第五部分：收尾与提交

1. 所有 4 个 PR 合入 `master`（可以自审后自行 merge）  
2. 在 `week7/writeup.md` 中（如需要）：
   - 列出 4 个 PR 链接和简要说明  
   - 简要记录 Cursor 在每个任务中的主要 review 建议和你是否采纳  
3. 确认：
   - `make test` 全通过  
   - 远程 `master` 已 push 到 GitHub  
4. 在 Gradescope 提交，并确保已添加课程助教为 GitHub 合作者。

