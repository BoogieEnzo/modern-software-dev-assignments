# Week 2 Write-up
Tip: To preview this markdown file
- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

---

## Learning Notes / 学习笔记

### Environment Setup

- **不需要 conda**：项目使用 Poetry 管理依赖，直接用 `poetry install` 和 `poetry run` 即可
- 启动服务：`poetry run uvicorn week2.app.main:app --reload`

### Remote Development: SSH Port Forwarding

代码在 Linux 服务器上，Mac 本地浏览器测试需要 SSH 端口转发：

```bash
ssh -L 8000:localhost:8000 fengde@100.90.186.53
```

- `-L 8000:localhost:8000` 将 Mac 本地 8000 端口流量通过 SSH 隧道转发到 Linux 服务器的 localhost:8000
- 连接后保持终端窗口打开，Mac 浏览器访问 http://127.0.0.1:8000/ 即可测试
- 如果在已有 SSH 会话中动态添加：按 `回车` → `~C` → 输入 `-L 8000:localhost:8000`

### Testing Methods

1. **Unit Tests (TODO 2)**：`poetry run pytest week2/tests/ -v`，不需要浏览器
2. **Browser Manual Testing (TODO 4)**：通过 SSH 端口转发 + 浏览器验证前端按钮功能

### Action Item Extractor: Input Formats

heuristic 提取器能识别的格式：
- Bullet list: `- item`, `* item`, `• item`
- Numbered list: `1. item`
- Keyword prefix: `todo:`, `action:`, `next:`
- Checkbox: `[ ]`, `[todo]`
- Imperative verbs: add, create, implement, fix, update, write, check, verify, refactor, document, design, investigate

---

## INSTRUCTIONS

Fill out all of the `TODO`s in this file.

## SUBMISSION DETAILS

Name: **TODO** \
SUNet ID: **TODO** \
Citations: **TODO**

This assignment took me about **TODO** hours to do. 


## YOUR RESPONSES
For each exercise, please include what prompts you used to generate the answer, in addition to the location of the generated response. Make sure to clearly add comments in your code documenting which parts are generated.

### Exercise 1: Scaffold a New Feature
Prompt: 
```
Analyze extract_action_items() in week2/app/services/extract.py. Implement an LLM-powered alternative extract_action_items_llm() using Ollama, with structured JSON output. Refer to https://ollama.com/blog/structured-outputs.
``` 

What was done:

在 `week2/app/services/extract.py` 中新增了 `extract_action_items_llm()` 函数（lines 112-162）：
- 用 Ollama `chat()` 调用本地 LLM，通过 system prompt 要求模型返回 JSON 数组
- 辅助函数 `_parse_llm_json_array()` 从 LLM 输出中提取 JSON（容错处理多余文字）
- 结果去重（大小写不敏感）
- 解析失败时 fallback 到 heuristic 提取器
- 模型名通过环境变量 `OLLAMA_ACTION_MODEL` 配置，默认 `gemma3:1b`

Generated Code Snippets:
```
week2/app/services/extract.py (lines 92-163, Cursor 生成)
```

### Exercise 2: Add Unit Tests
Prompt: 
```
@week2/assignment.md:48-51 do this（指向 TODO 2 的要求：为 extract_action_items_llm() 编写覆盖多种输入的单元测试）
``` 

What was done:

在 `week2/tests/test_extract.py` 中编写了 21 个测试，分为 3 组：

1. **TestExtractActionItems** (4 tests) — 测试 heuristic 提取器
   - bullet list / checkbox 输入
   - keyword prefix 输入 (`todo:`, `action:`, `next:`)
   - 空输入返回空列表
   - 重复项去重

2. **TestParseLlmJsonArray** (6 tests) — 测试 JSON 解析辅助函数
   - 正常 JSON 数组、带多余文字的 JSON、空数组
   - 过滤空字符串、非法 JSON 抛异常、非数组抛异常

3. **TestExtractActionItemsLlm** (11 tests) — 测试 LLM 提取器
   - bullet list / keyword prefix / numbered list / 混合格式输入
   - 空输入和纯空白不调用模型
   - LLM 返回空数组、重复项去重
   - LLM 输出带多余文字仍能解析
   - LLM 输出不合法时 fallback 到 heuristic
   - 环境变量 `OLLAMA_ACTION_MODEL` 控制模型名

关键：所有 LLM 测试用 `@patch` mock 了 Ollama 调用，不需要真实模型，测试秒级完成。

运行方式：`poetry run pytest week2/tests/test_extract.py -v`

Generated Code Snippets:
```
week2/tests/test_extract.py (lines 1-199, 全部由 Cursor 生成)
```

### Exercise 3: Refactor Existing Code for Clarity
Prompt: 
```
TODO
``` 

Generated/Modified Code Snippets:
```
TODO: List all modified code files with the relevant line numbers. (We anticipate there may be multiple scattered changes here – just produce as comprehensive of a list as you can.)
```


### Exercise 4: Use Agentic Mode to Automate a Small Task
Prompt: 
```
1. Integrate extract_action_items_llm as a new endpoint POST /action-items/extract-llm. Add an "Extract LLM" button in the frontend that calls this endpoint.
2. Add a GET /notes endpoint to retrieve all notes. Add a "List Notes" button in the frontend that fetches and displays them.
``` 

What was done:

**后端**：
- `week2/app/routers/action_items.py` (lines 29-42)：新增 `POST /action-items/extract-llm` 端点，调用 `extract_action_items_llm()`
- `week2/app/routers/notes.py` (lines 27-33)：新增 `GET /notes` 端点，返回所有笔记

**前端**：
- `week2/frontend/index.html` (line 27)：新增 "Extract LLM" 按钮，点击调用 `/action-items/extract-llm`
- `week2/frontend/index.html` (line 28)：新增 "List Notes" 按钮，点击调用 `GET /notes` 并展示笔记列表

Generated Code Snippets:
```
week2/app/routers/action_items.py (lines 29-42, Cursor 生成)
week2/app/routers/notes.py (lines 27-33, Cursor 生成)
week2/frontend/index.html (lines 27-28, 76-97, Cursor 生成)
```


### Exercise 5: Generate a README from the Codebase
Prompt: 
```
Analyze the week2 codebase and generate a well-structured README.md including: project overview, setup and run instructions, API endpoints and functionality, and how to run tests.
``` 

What was done:

生成了 `week2/README.md`，包含：
- 项目概览（前端、后端、提取逻辑）
- 安装与运行步骤（Poetry + Ollama + uvicorn）
- 完整 API 端点文档（8 个端点，含请求 body 格式）
- 前端按钮行为说明
- 测试运行方式

Generated Code Snippets:
```
week2/README.md (lines 1-95, 全部由 Cursor 生成)
```


## SUBMISSION INSTRUCTIONS
1. Hit a `Command (⌘) + F` (or `Ctrl + F`) to find any remaining `TODO`s in this file. If no results are found, congratulations – you've completed all required fields. 
2. Make sure you have all changes pushed to your remote repository for grading.
3. Submit via Gradescope. 