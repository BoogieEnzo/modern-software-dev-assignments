from fastapi import HTTPException

from backend.app import main
from backend.app.schemas import TrendingResponse
from backend.app.service import UpstreamFetchError


def test_today_endpoint_success(monkeypatch) -> None:
    def fake_get_today_trending(limit: int = 3):
        return {
            "date": "2026-02-27",
            "generated_at": "2026-02-27T12:00:00+00:00",
            "repos": [
                {
                    "full_name": "acme/repo-1",
                    "repo_url": "https://github.com/acme/repo-1",
                    "description": "desc",
                    "language": "Python",
                    "stars_today": 1000,
                    "stars_7d_ago": 900,
                    "weekly_star_gain": 100,
                    "forks": 10,
                    "updated_at": "2026-02-27T12:00:00+00:00",
                    "reason": "值得关注",
                }
            ],
        }

    monkeypatch.setattr(main, "get_today_trending", fake_get_today_trending)

    payload = main.trending_today()
    assert isinstance(payload, TrendingResponse)
    assert payload.repos[0].full_name == "acme/repo-1"


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
