# AGENTS.md — Modern Software Dev Assignments

This file provides context for AI agents working in this repository.

---

## Project Overview

- **Course**: CS146S: The Modern Software Developer (Stanford)
- **Stack**: FastAPI + SQLite (SQLAlchemy) + vanilla frontend
- **Python**: 3.10+
- **Active Week**: Week 4 (and others: week5, week6, week8)

---

## Running the Application

### Activate Environment

```bash
# Option 1: Use existing .venv (recommended)
source .venv/bin/activate

# Option 2: Conda (if installed)
conda activate cs146s
```

### Development Commands (from week4/ directory)

| Command | Description |
|---------|-------------|
| `make run` | Start FastAPI server at http://localhost:8000 |
| `make test` | Run all tests |
| `make format` | Run black + ruff --fix |
| `make lint` | Run ruff check |
| `make seed` | Seed database with initial data |

### Run Single Test

```bash
PYTHONPATH=. pytest backend/tests/test_notes.py::test_create_and_list_notes
```

### Test Patterns

```bash
# Run tests matching a keyword
PYTHONPATH=. pytest -k "notes"

# Run with verbose output
PYTHONPATH=. pytest -v backend/tests/

# Stop on first failure
PYTHONPATH=. pytest -x backend/tests/
```

---

## Code Style Guidelines

### Formatting

- **Line length**: 100 characters (enforced by black)
- **Formatter**: Black (auto-run via `make format`)
- **Linter**: Ruff (E, F, I, UP, B rules)

### Import Order

```python
# 1. Standard library
import os
from pathlib import Path
from typing import Optional

# 2. Third-party packages
from fastapi import FastAPI
from sqlalchemy import select

# 3. Local imports (relative)
from ..db import get_db
from ..models import Note
```

### Type Hints

- Always use type hints for function signatures
- Use modern syntax: `list[X]`, `dict[K, V]` (Python 3.9+)
- Use `Optional[X]` instead of `X | None` for compatibility

```python
# Good
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRead:
    ...

# Avoid
def get_note(note_id, db):
    ...
```

### Pydantic Models

- Use Pydantic v2 syntax
- Use `model_validate()` not `parse_obj()`
- Use `from_attributes = True` for ORM compatibility

```python
class NoteRead(BaseModel):
    id: int
    title: str
    content: str

    class Config:
        from_attributes = True
```

### SQLAlchemy 2.0 Patterns

- Use `select()` function, not query methods
- Use `scalars().all()` for fetching
- Use `db.get(Model, id)` for getting by primary key

```python
# Good (SQLAlchemy 2.0)
rows = db.execute(select(Note)).scalars().all()
note = db.get(Note, note_id)

# Avoid (old style)
rows = db.query(Note).all()
note = db.query(Note).filter_by(id=note_id).first()
```

### Error Handling

- Use `HTTPException` for API errors with proper status codes
- Always rollback on database exceptions

```python
from fastapi import HTTPException

@app.get("/notes/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteRead.model_validate(note)
```

### Naming Conventions

- **Files**: snake_case (e.g., `notes.py`, `action_items.py`)
- **Classes**: PascalCase (e.g., `Note`, `ActionItem`)
- **Functions/variables**: snake_case (e.g., `get_note()`, `note_id`)
- **Constants**: UPPER_SNAKE_CASE
- **Routes**: kebab-case in URL paths (`/action-items/`)

---

## Project Structure

```
week4/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── db.py            # Database connection + seed
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── routers/         # API route handlers
│   │   │   ├── notes.py
│   │   │   └── action_items.py
│   │   └── services/        # Business logic
│   │       └── extract.py
│   └── tests/
│       ├── conftest.py      # Pytest fixtures
│       ├── test_notes.py
│       ├── test_action_items.py
│       └── test_extract.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── data/
│   ├── app.db               # SQLite database
│   └── seed.sql             # Initial data
├── docs/
│   └── TASKS.md             # Agent-driven workflow tasks
├── Makefile
└── pre-commit-config.yaml
```

---

## Pre-commit Hooks

Install with:

```bash
pre-commit install
```

Runs on every commit:
- Black (formatting)
- Ruff (linting + fix)
- End-of-file fixer
- Trailing whitespace remover

---

## Database

- **Path**: `week4/data/app.db` (SQLite)
- **Seed**: Auto-seeded on first run via `data/seed.sql`
- **Manual seed**: `make seed`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serve frontend |
| GET | `/notes/` | List all notes |
| POST | `/notes/` | Create note |
| GET | `/notes/search/?q=` | Search notes |
| GET | `/notes/{id}` | Get single note |
| GET | `/action-items/` | List action items |
| POST | `/action-items/` | Create action item |
| PUT | `/action-items/{id}/complete` | Mark complete |

---

## Useful Patterns

### Adding a New Route

1. Create router file in `backend/app/routers/`
2. Import and include in `main.py`
3. Write test first, then implement

### Adding a New Model

1. Add class in `backend/app/models.py`
2. Add corresponding schema in `backend/app/schemas.py`
3. Run `make test` to verify

### Testing

- Use `TestClient` from FastAPI
- Override database with temporary file (see `conftest.py`)
- Always test both success and error cases

---

## Troubleshooting

### Port already in use

```bash
lsof -ti:8000 | xargs kill -9
```

### Reset database

```bash
rm week4/data/app.db
make run  #会自动重新seed
```

### Reinstall dependencies

```bash
poetry install
```
