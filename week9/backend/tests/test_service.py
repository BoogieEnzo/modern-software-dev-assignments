from datetime import datetime, timedelta, timezone

from backend.app.github_client import compute_stars_7d_ago, is_sensitive_repo
from backend.app.service import build_reason


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
    repo = {
        "name": "some-project",
        "description": "a nsfw toolkit",
        "topics": ["ai"],
    }
    assert is_sensitive_repo(repo) is True


def test_build_reason_includes_gain() -> None:
    repo = {"language": "Python", "updated_at": "2026-02-26T12:00:00Z"}
    reason = build_reason(repo, weekly_star_gain=321, monthly_star_gain=500)
    assert "321" in reason
    assert "Python" in reason
