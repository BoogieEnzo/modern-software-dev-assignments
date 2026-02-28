from datetime import datetime, timezone
import time
from typing import Any, Dict, List

from .github_client import GitHubClient, compute_stars_7d_ago, is_sensitive_repo, parse_iso_datetime


class UpstreamFetchError(Exception):
    pass


def build_reason(repo: Dict[str, Any], weekly_star_gain: int) -> str:
    language = repo.get("language") or "该技术栈"
    updated_at = parse_iso_datetime(repo["updated_at"]).strftime("%Y-%m-%d")
    if weekly_star_gain <= 0:
        stars_today = int(repo.get("stargazers_count", 0))
        return f"本周新增较少，但累计{stars_today}星，{language}社区关注度仍高，且最近在{updated_at}持续更新。"
    return f"近7天增长{weekly_star_gain}星，{language}生态近期讨论度高，且最近在{updated_at}仍有更新。"


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


def get_today_trending(limit: int = 3) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    client = GitHubClient()
    start_ts = time.monotonic()
    # Keep API responsive for frontend brief loading.
    max_duration_sec = 12.0

    try:
        updated_pool = client.search_candidate_repos(page_size=100, sort="updated", order="desc", page=1)
        stars_pool = client.search_candidate_repos(page_size=100, sort="stars", order="desc", page=1)
    except Exception as exc:
        raise UpstreamFetchError("failed to fetch GitHub repositories") from exc

    deduped: Dict[str, Dict[str, Any]] = {}
    for repo in updated_pool + stars_pool:
        full_name = repo.get("full_name")
        if full_name:
            deduped[full_name] = repo
    candidates = list(deduped.values())

    ranked: List[Dict[str, Any]] = []

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
            # Skip noisy candidates if individual star timeline fetch fails.
            continue

        created_at = parse_iso_datetime(repo["created_at"])
        if (now - created_at).days < 7:
            stars_7d_ago = 0
        else:
            stars_7d_ago = compute_stars_7d_ago(stars_today=stars_today, star_events=events, now=now)

        weekly_gain = max(stars_today - stars_7d_ago, 0)
        ranked.append(
            {
                "full_name": repo["full_name"],
                "repo_url": repo["html_url"],
                "description": repo.get("description"),
                "language": repo.get("language"),
                "stars_today": stars_today,
                "stars_7d_ago": stars_7d_ago,
                "weekly_star_gain": weekly_gain,
                "forks": int(repo.get("forks_count", 0)),
                "updated_at": parse_iso_datetime(repo["updated_at"]),
                "reason": build_reason(repo, weekly_gain),
            }
        )
        # Early stop once we have enough scored options to rank top N.
        if len(ranked) >= 40:
            break

    ranked.sort(
        key=lambda item: (
            item["weekly_star_gain"],
            item["updated_at"],
            item["stars_today"],
        ),
        reverse=True,
    )

    if not ranked:
        raise UpstreamFetchError("no ranked repositories available")

    return {
        "date": now.date().isoformat(),
        "generated_at": now,
        "repos": ranked[:limit],
    }
