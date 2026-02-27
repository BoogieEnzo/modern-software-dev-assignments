# Week 4 — The Autonomous Coding Agent IRL (OpenCode Edition)

> ***We recommend reading this entire document before getting started.***

This week, your task is to build at least **2 automations** within the context of this repository using any combination of the following **OpenCode** features:


- Custom slash commands (checked into `.opencode/commands/*.md`)

- `AGENTS.md` files for repository or context guidance

- Custom Agents / SubAgents (role-specialized agents working together, defined in `.opencode/agents/*.md` or `opencode.json`)

- MCP servers integrated into OpenCode

Your automations should meaningfully improve a developer workflow – for example, by streamlining tests, documentation, refactors, or data-related tasks. You will then use the automations you create to expand upon the starter application found in `week4/`.


## Learn about OpenCode
To gain a deeper understanding of OpenCode and explore your automation options, please read through the following resources:

1. **Custom Commands docs:** [open-code.ai/docs/en/commands](https://open-code.ai/docs/en/commands)

2. **Agents (SubAgents) docs:** [open-code.ai/docs/en/agents](https://open-code.ai/docs/en/agents)

3. **AGENTS.md (Rules) docs:** [open-code.ai/docs/en/rules](https://open-code.ai/docs/en/rules)

4. **MCP Servers docs:** [open-code.ai/docs/en/mcp-servers](https://open-code.ai/docs/en/mcp-servers)

5. **OpenCode CLI docs:** [open-code.ai/docs/en/cli](https://open-code.ai/docs/en/cli)

## Explore the Starter Application
Minimal full‑stack starter application designed to be a **"developer's command center"**. 
- FastAPI backend with SQLite (SQLAlchemy)
- Static frontend (no Node toolchain needed)
- Minimal tests (pytest)
- Pre-commit (black + ruff)
- Tasks to practice agent-driven workflows

Use this application as your playground to experiment with the OpenCode automations you build.

### Structure

```
backend/                # FastAPI app
frontend/               # Static UI served by FastAPI
data/                   # SQLite DB + seed
docs/                   # TASKS for agent-driven workflows
```

### Quickstart

1) Activate your environment.

```bash
# Option A: Use .venv (recommended)
source .venv/bin/activate

# Option B: Use conda (if installed)
conda activate cs146s
```

2) (Optional) Install pre-commit hooks

```bash
pre-commit install
```

3) Run the app

```bash
cd week4
make run
```

3) Run the app (from `week4/` directory)

```bash
make run
```

4) Open `http://localhost:8000` for the frontend and `http://localhost:8000/docs` for the API docs.

5) Play around with the starter application to get a feel for its current features and functionality.


### Testing
Run the tests (from `week4/` directory)
```bash
make test
```

### Formatting/Linting
```bash
make format
make lint
```

## Part I: Build Your Automation (Choose 2 or more)
Now that you're familiar with the starter application, your next step is to build automations to enhance or extend it. Below are several automation options you can choose from. You can mix and match across categories.

As you build your automations, document your changes in the `writeup.md` file. Leave the *"How you used the automation to enhance the starter application"* section empty for now - you will be returning to this in Part II of the assignment.

### A) OpenCode custom slash commands
Custom commands let you create reusable prompts as Markdown files inside `.opencode/commands/`. OpenCode exposes these via `/` in the TUI.

Each command file supports **frontmatter** (to set `description`, `agent`, `model`, etc.) and a **prompt template body** with special placeholders like `$ARGUMENTS`, `$1`/`$2`, shell output injection via `` !`command` ``, and file references via `@path/to/file`.

- Example 1: Test runner with coverage
  - Name: `tests.md`
  - Intent: Run `pytest -q backend/tests --maxfail=1 -x` and, if green, run coverage.
  - Inputs: Optional marker or path via `$ARGUMENTS`.
  - Output: Summarize failures and suggest next steps.
  - Usage: `/tests` or `/tests backend/tests/test_notes.py`

```markdown
---
description: Run tests with coverage and summarize results
agent: build
---

Run the following test command:
!`pytest -q backend/tests --maxfail=1 -x $ARGUMENTS`

If all tests pass, run coverage:
!`pytest --cov=backend/app backend/tests`

Summarize failures (if any) and suggest next steps.
```

- Example 2: Docs sync
  - Name: `docs-sync.md`
  - Intent: Read `/openapi.json`, update `docs/API.md`, and list route deltas.
  - Output: Diff-like summary and TODOs.
- Example 3: Refactor harness
  - Name: `refactor-module.md`
  - Intent: Rename a module (e.g., `services/extract.py` → `services/parser.py`), update imports, run lint/tests.
  - Output: A checklist of modified files and verification steps.

>*Tips: Keep commands focused, use `$ARGUMENTS` for flexibility, and prefer idempotent steps. Use shell output injection (`` !`command` ``) to include live project state in prompts.*

### B) `AGENTS.md` guidance files
The `AGENTS.md` file is automatically read when starting an OpenCode session, allowing you to provide repository-specific instructions, context, or guidance that influence the agent's behavior. Create an `AGENTS.md` in the repo root (and optionally in `week4/` subfolders) to guide OpenCode's behavior.

You can also bootstrap one with the `/init` command inside OpenCode, which scans your project and generates an initial `AGENTS.md` for you.

> Note: OpenCode also supports Claude Code's `CLAUDE.md` as a fallback, but the native convention is `AGENTS.md`.

- Example 1: Code navigation and entry points
  - Include: How to run the app, where routers live (`backend/app/routers`), where tests live, how the DB is seeded.
- Example 2: Style and safety guardrails
  - Include: Tooling expectations (black/ruff), safe commands to run, commands to avoid, and lint/test gates.
- Example 3: Workflow snippets
  - Include: "When asked to add an endpoint, first write a failing test, then implement, then run pre-commit."

> *Tips: Iterate on `AGENTS.md` like a prompt, keep it concise and actionable, and document custom tools/scripts you expect OpenCode to use. You can also reference additional instruction files via `opencode.json`'s `instructions` field.*

### C) Custom Agents / SubAgents (role-specialized)

OpenCode supports **primary agents** (Build, Plan) and **subagents** (General, Explore) out of the box. You can create your own custom agents as Markdown files in `.opencode/agents/` or configure them in `opencode.json`. Each agent has its own system prompt, tool permissions, and model setting.

Design two or more cooperating agents, each responsible for a distinct step in a single workflow.

- Example 1: TestAgent + CodeAgent
  - Create `.opencode/agents/test-agent.md` (subagent, read-only + bash for running tests) and use the default Build agent for code changes.
  - Flow: `/test-agent` writes/updates tests → Build agent implements code to pass tests → `@test-agent` verifies.
- Example 2: DocsAgent + CodeAgent
  - Create `.opencode/agents/docs-agent.md` (subagent, write access only to `docs/`)
  - Flow: Build agent adds a new API route → `@docs-agent` updates `API.md` and `TASKS.md` and checks drift against `/openapi.json`.
- Example 3: DBAgent + RefactorAgent
  - Flow: DBAgent proposes a schema change (adjust `data/seed.sql`) → RefactorAgent updates models/schemas/routers and fixes lints.

Example agent definition (`.opencode/agents/test-agent.md`):

```markdown
---
description: Writes and runs tests, verifies code changes
mode: subagent
tools:
  write: true
  edit: true
  bash: true
---

You are a test-driven development specialist. Your responsibilities:
- Write pytest test cases for new features before implementation
- Run tests and report results clearly
- Never modify application code, only test files
```

>*Tips: Use `@agent-name` to invoke subagents in your messages. Switch between primary agents with Tab. Set tool permissions carefully — e.g., a review agent should have `write: false`.*

### D) MCP Servers (bonus option)

MCP (Model Context Protocol) servers add external tools to OpenCode. Configure them in `opencode.json` under the `mcp` section, or use `opencode mcp add` to add them interactively. Once configured, MCP tools are automatically available to all agents.

Example `opencode.json` snippet:

```json
{
  "mcp": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "data/dev.db"]
    }
  }
}
```

>*Tips: Browse the MCP server ecosystem at [modelcontextprotocol.io/servers](https://modelcontextprotocol.io/servers) for servers relevant to your workflow (GitHub, databases, search, etc.).*

## Part II: Put Your Automations to Work 
Now that you've built 2+ automations, let's put them to use! In the `writeup.md` under section *"How you used the automation to enhance the starter application"*, describe how you leveraged each automation to improve or extend the app's functionality.

e.g. If you implemented the custom slash command `/tests`, explain how you used it to interact with and test the starter application.


## Deliverables
1) Two or more automations, which may include:
   - Slash commands in `.opencode/commands/*.md`
   - `AGENTS.md` files (project root and/or subdirectories)
   - Custom Agent definitions in `.opencode/agents/*.md` or `opencode.json`
   - MCP server configuration in `opencode.json`

2) A write-up `writeup.md` under `week4/` that includes:
  - Design inspiration (e.g. cite the OpenCode docs for commands/agents/rules)
  - Design of each automation, including goals, inputs/outputs, steps
  - How to run it (exact commands), expected outputs, and rollback/safety notes
  - Before vs. after (i.e. manual workflow vs. automated workflow)
  - How you used the automation to enhance the starter application

## Useful OpenCode Commands

| Command | Description |
|---|---|
| `opencode` | Launch TUI (default) |
| `opencode run "message"` | Run a one-shot prompt |
| `/init` | Generate an initial `AGENTS.md` for your project |
| `/command-name` | Run a custom slash command |
| `@agent-name` | Invoke a subagent by name |
| `Tab` | Switch between primary agents (Build ↔ Plan) |
| `opencode agent list` | List available agents |
| `opencode agent create` | Interactively create a new agent |
| `opencode mcp add` | Add an MCP server |
| `opencode mcp list` | List configured MCP servers |


## SUBMISSION INSTRUCTIONS
1. Make sure you have all changes pushed to your remote repository for grading.
2. **Make sure you've added both brentju and febielin as collaborators on your assignment repository.**
2. Submit via Gradescope. 
