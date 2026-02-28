import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from .db import load_today_snapshot, save_snapshot
from .github_client import (
    GitHubClient,
    compute_stars_30d_ago,
    compute_stars_7d_ago,
    is_sensitive_repo,
    parse_iso_datetime,
)


class UpstreamFetchError(Exception):
    pass


def build_reason(repo: Dict[str, Any], weekly_star_gain: int, monthly_star_gain: int) -> str:
    language = repo.get("language") or "该技术栈"

    if weekly_star_gain > 50:
        return f"🔥 近7天暴涨{weekly_star_gain}星！{language}领域新星值得关注！"
    elif weekly_star_gain > 20:
        return f"近7天增长{weekly_star_gain}星，{language}生态近期讨论度高"
    elif monthly_star_gain > 100:
        return f"近30天增长{monthly_star_gain}星，{language}社区持续关注"
    elif monthly_star_gain > 30:
        return f"近30天增长{monthly_star_gain}星，{language}社区持续关注"
    else:
        stars_today = int(repo.get("stargazers_count", 0))
        return f"累计{stars_today}星，{language}社区关注度高"


def _eligible(repo: Dict[str, Any]) -> bool:
    if repo.get("private"):
        return False
    if repo.get("archived"):
        return False
    if is_sensitive_repo(repo):
        return False
    if int(repo.get("stargazers_count", 0)) < 200:
        return False
    return True


def _ensure_rust_in_position(ranked: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if limit < 3 or len(ranked) < 3:
        return ranked

    if ranked[2].get("language") == "Rust":
        return ranked

    for i in range(3, len(ranked)):
        if ranked[i].get("language") == "Rust":
            ranked[2], ranked[i] = ranked[i], ranked[2]
            break

    return ranked


def get_today_trending(limit: int = 5) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    today_str = now.date().isoformat()

    cached = load_today_snapshot(today_str)
    if cached:
        return {
            "date": cached["date"],
            "generated_at": cached["generated_at"],
            "repos_7d": cached["repos_7d"][:limit],
            "repos_30d": cached["repos_30d"][:limit],
        }

    client = GitHubClient()
    start_ts = time.monotonic()
    max_duration_sec = 25.0

    try:
        pools = []
        for days in [30, 90, 180, 365]:
            pools.extend(
                client.search_candidate_repos(
                    page_size=100, sort="stars", order="desc", created_days_ago=days
                )
            )
        pools.extend(client.search_candidate_repos(page_size=100, sort="stars", order="desc"))
    except Exception as exc:
        save_snapshot(today_str, [], [], status="error", error_msg=str(exc))
        raise UpstreamFetchError("failed to fetch GitHub repositories") from exc

    deduped: Dict[str, Dict[str, Any]] = {}
    for repo in pools:
        full_name = repo.get("full_name")
        if full_name:
            deduped[full_name] = repo
    candidates = list(deduped.values())

    ranked_7d: List[Dict[str, Any]] = []
    ranked_30d: List[Dict[str, Any]] = []
    processed = 0

    for repo in candidates:
        if time.monotonic() - start_ts > max_duration_sec:
            break
        if not _eligible(repo):
            continue

        owner = repo["owner"]["login"]
        name = repo["name"]
        stars_today = int(repo["stargazers_count"])

        try:
            events = client.list_star_events(owner, name, per_page=100)
        except Exception:
            continue

        created_at = parse_iso_datetime(repo["created_at"])
        days_since_creation = (now - created_at).days

        if days_since_creation < 7:
            stars_7d_ago = 0
            stars_30d_ago = 0
        elif days_since_creation < 30:
            stars_7d_ago = compute_stars_7d_ago(
                stars_today=stars_today, star_events=events, now=now
            )
            stars_30d_ago = 0
        else:
            stars_7d_ago = compute_stars_7d_ago(
                stars_today=stars_today, star_events=events, now=now
            )
            stars_30d_ago = compute_stars_30d_ago(
                stars_today=stars_today, star_events=events, now=now
            )

        weekly_gain = max(stars_today - stars_7d_ago, 0)
        monthly_gain = max(stars_today - stars_30d_ago, 0)

        repo_data = {
            "full_name": repo["full_name"],
            "repo_url": repo["html_url"],
            "description": repo.get("description"),
            "language": repo.get("language"),
            "stars_today": stars_today,
            "stars_7d_ago": stars_7d_ago,
            "stars_30d_ago": stars_30d_ago,
            "weekly_star_gain": weekly_gain,
            "monthly_star_gain": monthly_gain,
            "forks": int(repo.get("forks_count", 0)),
            "created_at": created_at.strftime("%Y-%m-%d"),
            "updated_at": parse_iso_datetime(repo["updated_at"]),
            "reason": build_reason(repo, weekly_gain, monthly_gain),
        }

        ranked_7d.append(repo_data)
        ranked_30d.append(repo_data)

        processed += 1
        if processed >= 50:
            break

    ranked_7d.sort(
        key=lambda item: (
            item["weekly_star_gain"],
            item["updated_at"],
            item["stars_today"],
        ),
        reverse=True,
    )

    ranked_30d.sort(
        key=lambda item: (
            item["monthly_star_gain"],
            item["updated_at"],
            item["stars_today"],
        ),
        reverse=True,
    )

    ranked_7d = _ensure_rust_in_position(ranked_7d, limit)
    ranked_30d = _ensure_rust_in_position(ranked_30d, limit)

    for item in ranked_7d[:limit]:
        if isinstance(item["updated_at"], datetime):
            item["updated_at"] = item["updated_at"].isoformat()

    for item in ranked_30d[:limit]:
        if isinstance(item["updated_at"], datetime):
            item["updated_at"] = item["updated_at"].isoformat()

    if not ranked_7d and not ranked_30d:
        save_snapshot(
            today_str, [], [], status="error", error_msg="no ranked repositories available"
        )
        raise UpstreamFetchError("no ranked repositories available")

    result = {
        "date": now.date().isoformat(),
        "generated_at": now.isoformat(),
        "repos_7d": ranked_7d[:limit],
        "repos_30d": ranked_30d[:limit],
    }
    save_snapshot(today_str, ranked_7d[:limit], ranked_30d[:limit], status="success")

    return result
