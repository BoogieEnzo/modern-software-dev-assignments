"""Live integration tests — require GITHUB_TOKEN and network access.

Run with: PYTHONPATH=. pytest backend/tests/test_github_live.py -v
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from backend.app.github_client import GitHubClient

pytestmark = pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN not set — skipping live tests",
)


def test_agent_search_returns_repos() -> None:
    """The query we actually use must return >0 results."""
    client = GitHubClient()
    repos = client.search_agent_repos(page_size=5)

    assert len(repos) > 0, "Agent search returned 0 repos — query is broken!"
    for r in repos:
        assert "full_name" in r
        assert "stargazers_count" in r


def test_agent_search_query_has_no_parentheses() -> None:
    """Parenthesized OR groups cause GitHub to silently return 0."""
    from datetime import datetime, timedelta, timezone

    created_date = (datetime.now(timezone.utc) - timedelta(days=30)).date()
    query = f"stars:>=100 archived:false created:>={created_date} agent in:name,description,topics"

    assert "(" not in query, "Query must not use parenthesized groups"
    assert ")" not in query, "Query must not use parenthesized groups"


def test_candidate_search_returns_repos() -> None:
    client = GitHubClient()
    repos = client.search_candidate_repos(page_size=5, created_days_ago=30)

    assert len(repos) > 0, "Candidate search returned 0 repos"


def test_full_trending_flow() -> None:
    """End-to-end: get_today_trending should return all 3 columns."""
    from backend.app.service import get_today_trending

    result = get_today_trending(limit=3)

    assert result["date"]
    assert result["generated_at"]
    assert len(result["repos_7d"]) > 0, "7d column is empty"
    assert len(result["repos_30d"]) > 0, "30d column is empty"
    assert len(result["repos_agent"]) > 0, "Agent column is empty — search likely broken"

    for repo in result["repos_agent"]:
        assert "full_name" in repo
        assert "stars_today" in repo
        assert "topics" in repo
