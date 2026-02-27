# AGENTS.md — Week 4

This AGENTS.md is specific to week4/. The root AGENTS.md has general project info.

---

## Week 4 Focus

This week is about building OpenCode automations:
- Custom slash commands (`.opencode/commands/`)
- AGENTS.md files
- Custom agents (`.opencode/agents/`)
- MCP servers (optional)

---

## Development Commands

```bash
cd week4

# Run app
make run

# Run tests
make all test

# Run single test
PYTHONPATH=. pytest backend/tests/test_notes.py::test_create_and_list_notes

# Format + lint
make format
make lint
```

---

## App Features

- Notes CRUD: Create, list, search, get by ID
- Action Items: Create, list, mark complete

---

## Testing

Write tests first, then implement. Use the `client` fixture from `conftest.py`:

```python
def test_example(client):
    r = client.get("/notes/")
    assert r.status_code == 200
```

---

## Automation Examples to Build

1. `/tests` - Run pytest with coverage
2. `/lint` - Run ruff check + black format

See `.opencode/commands/` for implementation.
