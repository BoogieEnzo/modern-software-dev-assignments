from fastapi import HTTPException

from backend.app import main
from backend.app.schemas import TrendingResponse
from backend.app.service import UpstreamFetchError


def test_today_endpoint_success(monkeypatch) -> None:
    def fake_get_today_trending(limit: int = 3):
        return {
            "date": "2026-02-27",
            "generated_at": "2026-02-27T12:00:00+00:00",
            "repos_7d": [
                {
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
            ],
            "repos_30d": [
                {
                    "full_name": "acme/repo-2",
                    "repo_url": "https://github.com/acme/repo-2",
                    "description": "desc",
                    "language": "Rust",
                    "stars_today": 2000,
                    "stars_7d_ago": 1800,
                    "stars_30d_ago": 1500,
                    "weekly_star_gain": 200,
                    "monthly_star_gain": 500,
                    "forks": 20,
                    "created_at": "2025-12-01",
                    "updated_at": "2026-02-27T12:00:00+00:00",
                    "reason": "值得关注",
                }
            ],
            "repos_agent": [
                {
                    "full_name": "agent/agent-os",
                    "repo_url": "https://github.com/agent/agent-os",
                    "description": "Agent OS",
                    "language": "Rust",
                    "stars_today": 500,
                    "forks": 50,
                    "created_at": "2026-02-01",
                    "topics": ["agent", "ai"],
                }
            ],
        }

    monkeypatch.setattr(main, "get_today_trending", fake_get_today_trending)

    payload = main.trending_today()
    assert isinstance(payload, TrendingResponse)
    assert payload.repos_7d[0].full_name == "acme/repo-1"
    assert payload.repos_agent[0].full_name == "agent/agent-os"


def test_today_endpoint_failure(monkeypatch) -> None:
    def fake_get_today_trending(limit: int = 3):
        raise UpstreamFetchError("boom")

    monkeypatch.setattr(main, "get_today_trending", fake_get_today_trending)

    try:
        main.trending_today()
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == "趋势数据加载失败"
