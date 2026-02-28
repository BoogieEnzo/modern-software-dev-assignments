import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.app.github_client import compute_stars_7d_ago, is_sensitive_repo
from backend.app.service import (
    _eligible,
    _ensure_rust_in_position,
    _fetch_agent_repos,
    build_agent_reason,
    build_reason,
)


def test_compute_stars_7d_ago_counts_recent_stars() -> None:
    now = datetime(2026, 2, 27, tzinfo=timezone.utc)
    events = [
        {"starred_at": (now - timedelta(days=1)).isoformat()},
        {"starred_at": (now - timedelta(days=3)).isoformat()},
        {"starred_at": (now - timedelta(days=8)).isoformat()},
    ]
    stars_7d_ago = compute_stars_7d_ago(stars_today=100, star_events=events, now=now)
    assert stars_7d_ago == 98


def test_sensitive_repo_filter() -> None:
    assert is_sensitive_repo({"name": "ok", "description": "a nsfw toolkit", "topics": []}) is True
    assert is_sensitive_repo({"name": "good", "description": "agent OS", "topics": []}) is False


def test_build_reason_includes_gain() -> None:
    repo = {"language": "Python", "updated_at": "2026-02-26T12:00:00Z"}
    reason = build_reason(repo, weekly_star_gain=321, monthly_star_gain=500)
    assert "321" in reason
    assert "Python" in reason


def test_build_agent_reason_includes_language_and_stars() -> None:
    repo = {"language": "TypeScript", "stargazers_count": 5000, "topics": ["mcp", "ai-agents"]}
    reason = build_agent_reason(repo)
    assert "TypeScript" in reason
    assert "5000" in reason
    assert "MCP" in reason or "Agent" in reason


def test_eligible_filters_private_and_low_stars() -> None:
    assert _eligible({"private": True, "stargazers_count": 999}) is False
    assert _eligible({"archived": True, "stargazers_count": 999}) is False
    assert _eligible({"stargazers_count": 50}) is False
    assert _eligible({"name": "ok", "description": "ok", "stargazers_count": 500}) is True


def test_ensure_rust_in_position_3() -> None:
    repos = [
        {"language": "Python", "name": "a"},
        {"language": "Go", "name": "b"},
        {"language": "TypeScript", "name": "c"},
        {"language": "Rust", "name": "d"},
    ]
    result = _ensure_rust_in_position(repos, limit=3)
    assert result[2]["language"] == "Rust"
    assert result[2]["name"] == "d"


def test_ensure_rust_noop_when_already_at_3() -> None:
    repos = [
        {"language": "Python", "name": "a"},
        {"language": "Go", "name": "b"},
        {"language": "Rust", "name": "c"},
    ]
    result = _ensure_rust_in_position(repos, limit=3)
    assert result[2]["name"] == "c"


def test_fetch_agent_repos_parses_github_response() -> None:
    fake_repos = [
        {
            "full_name": "org/agent-x",
            "html_url": "https://github.com/org/agent-x",
            "description": "An agent framework",
            "language": "Python",
            "stargazers_count": 500,
            "forks_count": 30,
            "created_at": "2026-02-10T00:00:00Z",
            "topics": ["agent", "ai"],
            "private": False,
            "archived": False,
            "name": "agent-x",
        },
        {
            "full_name": "org/tool-y",
            "html_url": "https://github.com/org/tool-y",
            "description": "Tool use framework",
            "language": "Rust",
            "stargazers_count": 300,
            "forks_count": 10,
            "created_at": "2026-02-15T00:00:00Z",
            "topics": ["tool-use"],
            "private": False,
            "archived": False,
            "name": "tool-y",
        },
    ]
    mock_client = MagicMock()
    mock_client.search_agent_repos.return_value = fake_repos

    result = _fetch_agent_repos(mock_client, limit=5)

    assert len(result) == 2
    assert result[0]["full_name"] == "org/agent-x"
    assert result[0]["stars_today"] == 500
    assert result[0]["topics"] == ["agent", "ai"]
    assert "reason" in result[0]
    assert result[0]["reason"]
    assert "Python" in result[0]["reason"] or "500" in result[0]["reason"]
    assert result[1]["full_name"] == "org/tool-y"
    assert "reason" in result[1]


def test_fetch_agent_repos_returns_empty_on_failure() -> None:
    mock_client = MagicMock()
    mock_client.search_agent_repos.side_effect = Exception("422 boom")

    result = _fetch_agent_repos(mock_client, limit=5)
    assert result == []


def test_fetch_agent_repos_filters_sensitive() -> None:
    fake_repos = [
        {
            "full_name": "org/nsfw-agent",
            "html_url": "https://github.com/org/nsfw-agent",
            "description": "nsfw content",
            "language": "Python",
            "stargazers_count": 999,
            "forks_count": 10,
            "created_at": "2026-02-10T00:00:00Z",
            "topics": [],
            "private": False,
            "archived": False,
            "name": "nsfw-agent",
        },
    ]
    mock_client = MagicMock()
    mock_client.search_agent_repos.return_value = fake_repos

    result = _fetch_agent_repos(mock_client, limit=5)
    assert result == []


# -- DB roundtrip test --

def test_db_save_and_load_roundtrip() -> None:
    from backend.app import db as db_module

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        test_engine = create_engine(f"sqlite:///{test_db_path}")
        test_session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

        original_engine = db_module.engine
        original_session = db_module.SessionLocal
        db_module.engine = test_engine
        db_module.SessionLocal = test_session

        try:
            repos_7d = [{"full_name": "a/b", "stars_today": 100}]
            repos_30d = [{"full_name": "c/d", "stars_today": 200}]
            repos_agent = [{"full_name": "e/f", "stars_today": 50}]

            db_module.save_snapshot("2026-02-28", repos_7d, repos_30d, repos_agent)
            loaded = db_module.load_today_snapshot("2026-02-28")

            assert loaded is not None
            assert loaded["date"] == "2026-02-28"
            assert loaded["repos_7d"] == repos_7d
            assert loaded["repos_30d"] == repos_30d
            assert loaded["repos_agent"] == repos_agent

            assert db_module.load_today_snapshot("2099-01-01") is None
        finally:
            db_module.engine = original_engine
            db_module.SessionLocal = original_session


# -- dotenv loading test --

def test_dotenv_loads_github_token() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return  # skip if no .env

    from dotenv import load_dotenv

    load_dotenv(env_path)
    import os

    token = os.getenv("GITHUB_TOKEN", "")
    assert token, f".env exists at {env_path} but GITHUB_TOKEN is empty"
    assert token.startswith("ghp_") or token.startswith("github_pat_"), (
        f"Token format unexpected: {token[:10]}..."
    )
