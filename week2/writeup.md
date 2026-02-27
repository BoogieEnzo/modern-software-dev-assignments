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

### Bug Fix: Ollama Model Name

- `week2/app/services/extract.py` 第 136 行默认模型从 `llama3.1:8b` 改为 `gemma3:1b`（因已删除大模型节省内存）
- 环境变量 `OLLAMA_ACTION_MODEL` 可覆盖默认值

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
TODO
``` 

Generated Code Snippets:
```
TODO: List all modified code files with the relevant line numbers.
```

### Exercise 2: Add Unit Tests
Prompt: 
```
TODO
``` 

Generated Code Snippets:
```
TODO: List all modified code files with the relevant line numbers.
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
TODO
``` 

Generated Code Snippets:
```
TODO: List all modified code files with the relevant line numbers.
```


### Exercise 5: Generate a README from the Codebase
Prompt: 
```
TODO
``` 

Generated Code Snippets:
```
TODO: List all modified code files with the relevant line numbers.
```


## SUBMISSION INSTRUCTIONS
1. Hit a `Command (⌘) + F` (or `Ctrl + F`) to find any remaining `TODO`s in this file. If no results are found, congratulations – you've completed all required fields. 
2. Make sure you have all changes pushed to your remote repository for grading.
3. Submit via Gradescope. 