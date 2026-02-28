# Assignments for CS146S: The Modern Software Developer

This is the home of the assignments for [CS146S: The Modern Software Developer](https://themodernsoftware.dev), taught at Stanford University fall 2025.

## What’s in this repo

Each `week*/` directory is a self-contained assignment (many are small full‑stack apps: FastAPI + SQLite + vanilla frontend).

- **Week 9**: Repo Daily Brief (GitHub trends + Agent OS column) — see `week9/README.md`
- **Week 8**: OS Paper Hub (papers + ArXiv + Ollama summary/chat) — see `week8/README.md`

Quick navigation:

- `week9/README.md`, `week9/knowledge.md`, `week9/AGENT.md`
- `week8/README.md`, `week8/knowledge.md`, `week8/AGENT.md`
- `AGENTS.md` (repo-wide agent/dev guidance)

Other weeks (entrypoints vary; check each folder):

- `week1/README.md`
- `week2/README.md`
- `week3/README.md`
- `week5/README.md`
- `week7/README.md`

## Repo Setup

Recommended: Python 3.12+ in a clean environment (some weeks may have additional per-week requirements; follow that week’s `README.md`).

1. Install Anaconda
   - Download and install: [Anaconda Individual Edition](https://www.anaconda.com/download)
   - Open a new terminal so `conda` is on your `PATH`.

2. Create and activate a Conda environment (Python 3.12+)
   ```bash
   conda create -n cs146s python=3.12 -y
   conda activate cs146s
   ```

3. Install Poetry
   ```bash
   curl -sSL https://install.python-poetry.org | python -
   ```

4. Install project dependencies with Poetry (inside the activated Conda env)
   From the repository root:
   ```bash
   poetry install --no-interaction
   ```

## Run / Test (by week)

Most weeks have their own `Makefile` and `README.md`. Typical patterns:

- **Week 5 / 7** (FastAPI demo apps):
  - Run: `cd week5 && make run` or `cd week7 && make run` (usually `http://localhost:8000`)
  - Test: `cd week5 && make test` / `cd week7 && make test`
- **Week 8** (OS Paper Hub):
  - Run: follow `week8/README.md` (default `http://localhost:8001`)
  - Test: `PYTHONPATH=. .venv/bin/python -m pytest tests/ -v`
- **Week 9** (Repo Daily Brief):
  - Run: `cd week9 && pip install -r requirements.txt && make run` (default `http://localhost:8002`)
  - Test: `cd week9 && make test`
