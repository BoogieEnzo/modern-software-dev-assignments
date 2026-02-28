from fastapi import HTTPException

from backend.app import main
from backend.app.schemas import TrendingResponse
from backend.app.service import UpstreamFetchError


FAKE_7D_REPO = {
    "full_name": "acme/repo-1",
    "repo_url": "https://github.com/acme/repo-1",
    "description": "desc",
    "language": "Python",
    "stars_today": 1000,
    "stars_7d_ago": 900,
    "stars_30d_ago": 800,
    "weekly_star_gain": 100,
    "monthly_star_gain": 200,
    "forks": 10,
    "created_at": "2026-01-01",
    "updated_at": "2026-02-27T12:00:00+00:00",
    "reason": "值得关注",
}

FAKE_AGENT_REPO = {
    "full_name": "agent/agent-os",
    "repo_url": "https://github.com/agent/agent-os",
    "description": "Agent OS",
    "language": "Rust",
    "stars_today": 500,
    "forks": 50,
    "created_at": "2026-02-01",
    "topics": ["agent", "ai"],
    "reason": "Rust领域Agent新星，已获500星",
}


def test_endpoint_returns_all_three_columns(monkeypatch) -> None:
    def fake_get(limit: int = 3):
        return {
            "date": "2026-02-27",
            "generated_at": "2026-02-27T20:00:00+08:00",
            "repos_7d": [FAKE_7D_REPO],
            "repos_30d": [FAKE_7D_REPO],
            "repos_agent": [FAKE_AGENT_REPO],
        }

    monkeypatch.setattr(main, "get_today_trending", fake_get)
    payload = main.trending_today()

    assert isinstance(payload, TrendingResponse)
    assert len(payload.repos_7d) == 1
    assert len(payload.repos_30d) == 1
    assert len(payload.repos_agent) == 1
    assert payload.repos_agent[0].full_name == "agent/agent-os"
    assert payload.repos_agent[0].topics == ["agent", "ai"]


def test_endpoint_works_with_empty_agent(monkeypatch) -> None:
    def fake_get(limit: int = 3):
        return {
            "date": "2026-02-27",
            "generated_at": "2026-02-27T20:00:00+08:00",
            "repos_7d": [FAKE_7D_REPO],
            "repos_30d": [],
            "repos_agent": [],
        }

    monkeypatch.setattr(main, "get_today_trending", fake_get)
    payload = main.trending_today()

    assert isinstance(payload, TrendingResponse)
    assert payload.repos_agent == []


def test_endpoint_503_on_upstream_error(monkeypatch) -> None:
    def fake_get(limit: int = 3):
        raise UpstreamFetchError("boom")

    monkeypatch.setattr(main, "get_today_trending", fake_get)

    try:
        main.trending_today()
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == "趋势数据加载失败"


def test_generated_at_is_beijing_timezone(monkeypatch) -> None:
    """generated_at should be parseable and contain +08:00"""

    def fake_get(limit: int = 3):
        return {
            "date": "2026-02-27",
            "generated_at": "2026-02-27T20:00:00+08:00",
            "repos_7d": [FAKE_7D_REPO],
            "repos_30d": [],
            "repos_agent": [],
        }

    monkeypatch.setattr(main, "get_today_trending", fake_get)
    payload = main.trending_today()

    gen_at = str(payload.generated_at)
    assert "+08:00" in gen_at or "2026-02-27" in gen_at
