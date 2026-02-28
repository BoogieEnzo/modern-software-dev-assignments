import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

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


REFRESH_INTERVAL_HOURS = 4

_background_thread: Optional[threading.Thread] = None
_refresh_in_progress = False


def _background_refresh():
    """后台定时刷新任务（每4小时）"""
    global _refresh_in_progress

    while True:
        try:
            time.sleep(REFRESH_INTERVAL_HOURS * 3600)

            if _refresh_in_progress:
                print("[Background] Refresh in progress, skipping...")
                continue

            _refresh_in_progress = True
            print(f"[Background] Starting refresh at {datetime.now()}")

            _do_fetch_and_save()
            print("[Background] Refresh completed")

        except Exception as e:
            print(f"[Background] Error: {e}")
        finally:
            _refresh_in_progress = False


def _do_fetch_and_save(limit: int = 5):
    """执行抓取并保存"""
    now = datetime.now(timezone.utc)
    today_str = now.date().isoformat()

    client = GitHubClient()
    start_ts = time.monotonic()
    max_duration_sec = 90.0

    pools = []
    for days in [30, 90, 180, 365]:
        pools.extend(
            client.search_candidate_repos(
                page_size=50, sort="stars", order="desc", created_days_ago=days
            )
        )
    pools.extend(client.search_candidate_repos(page_size=50, sort="stars", order="desc"))

    deduped = {}
    for repo in pools:
        fn = repo.get("full_name")
        if fn:
            deduped[fn] = repo
    candidates = list(deduped.values())

    ranked_7d, ranked_30d = _process_candidates(
        candidates, now, client, start_ts, max_duration_sec, limit
    )

    # Fetch Agent OS related repos
    agent_repos = _fetch_agent_repos(client, limit)

    if ranked_7d or ranked_30d:
        save_snapshot(
            today_str, ranked_7d[:limit], ranked_30d[:limit], agent_repos, status="success"
        )
        print(
            f"[Background] Saved: 7d={len(ranked_7d)}, 30d={len(ranked_30d)}, agent={len(agent_repos)}"
        )


def _fetch_agent_repos(client: GitHubClient, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch Agent OS related repositories (created in past 30 days)"""
    try:
        repos = client.search_agent_repos(page_size=30, sort="stars", order="desc")
    except Exception as e:
        print(f"[Agent] Failed to fetch agent repos: {e}")
        return []

    agent_list = []
    for repo in repos[: limit * 2]:  # Fetch more to filter
        if repo.get("private") or repo.get("archived"):
            continue
        if is_sensitive_repo(repo):
            continue

        created_at = parse_iso_datetime(repo["created_at"])
        agent_data = {
            "full_name": repo["full_name"],
            "repo_url": repo["html_url"],
            "description": repo.get("description"),
            "language": repo.get("language"),
            "stars_today": int(repo["stargazers_count"]),
            "forks": int(repo.get("forks_count", 0)),
            "created_at": created_at.strftime("%Y-%m-%d"),
            "topics": repo.get("topics", []) or [],
            "reason": build_agent_reason(repo),
        }
        agent_list.append(agent_data)

        if len(agent_list) >= limit:
            break

    # Ensure Rust is in position 3 if available
    agent_list = _ensure_rust_in_agent(agent_list, limit)

    return agent_list


def _ensure_rust_in_agent(ranked: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Ensure Rust repo is in position 3 for agent repos"""
    if limit < 3 or len(ranked) < 3:
        return ranked
    if ranked[2].get("language") == "Rust":
        return ranked
    for i in range(3, len(ranked)):
        if ranked[i].get("language") == "Rust":
            ranked[2], ranked[i] = ranked[i], ranked[2]
            break
    return ranked


def _process_candidates(candidates, now, client, start_ts, max_duration_sec, limit):
    """处理候选仓库"""
    ranked_7d = []
    ranked_30d = []
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
        days_since = (now - created_at).days

        if days_since < 7:
            stars_7d_ago, stars_30d_ago = 0, 0
        elif days_since < 30:
            stars_7d_ago = compute_stars_7d_ago(stars_today, events, now)
            stars_30d_ago = 0
        else:
            stars_7d_ago = compute_stars_7d_ago(stars_today, events, now)
            stars_30d_ago = compute_stars_30d_ago(stars_today, events, now)

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
        key=lambda x: (x["weekly_star_gain"], x["updated_at"], x["stars_today"]), reverse=True
    )
    ranked_30d.sort(
        key=lambda x: (x["monthly_star_gain"], x["updated_at"], x["stars_today"]), reverse=True
    )

    ranked_7d = _ensure_rust_in_position(ranked_7d, limit)
    ranked_30d = _ensure_rust_in_position(ranked_30d, limit)

    for item in ranked_7d[:limit]:
        if isinstance(item["updated_at"], datetime):
            item["updated_at"] = item["updated_at"].isoformat()
    for item in ranked_30d[:limit]:
        if isinstance(item["updated_at"], datetime):
            item["updated_at"] = item["updated_at"].isoformat()

    return ranked_7d, ranked_30d


def start_background_refresh():
    """启动后台刷新线程"""
    global _background_thread
    if _background_thread is None or not _background_thread.is_alive():
        _background_thread = threading.Thread(target=_background_refresh, daemon=True)
        _background_thread.start()
        print("[Background] Started auto-refresh thread (every 4 hours)")


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


def build_agent_reason(repo: Dict[str, Any]) -> str:
    """Generate recommendation reason for Agent OS repos based on available metrics."""
    language = repo.get("language") or "该技术栈"
    stars = int(repo.get("stargazers_count") or repo.get("stars_today") or 0)
    topics = repo.get("topics") or []

    topic_highlights = {
        "mcp": "支持MCP协议",
        "ai-agents": "AI Agent框架",
        "agent-framework": "Agent基础设施",
        "llm": "LLM驱动",
        "operating-system": "Agent操作系统",
        "openclaw": "OpenClaw生态",
        "claude-code": "Claude Code生态",
        "claude-skills": "Claude Skills集成",
    }
    matched = [v for k, v in topic_highlights.items() if k in topics]
    tag = f"，{matched[0]}" if matched else ""

    if stars > 10000:
        return f"🔥 {language}新兴Agent项目，累计{stars}星{tag}，社区高度关注！"
    elif stars > 3000:
        return f"🔥 {language}热门Agent项目，短期冲上{stars}星{tag}，值得关注！"
    elif stars > 500:
        return f"{language}领域Agent新星，已获{stars}星{tag}"
    else:
        return f"{language}新兴Agent项目{tag}，潜力值得关注"


def _eligible(repo: Dict[str, Any]) -> bool:
    if repo.get("private") or repo.get("archived"):
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
    start_background_refresh()

    now_utc = datetime.now(timezone.utc)
    today_str = now_utc.date().isoformat()

    cached = load_today_snapshot(today_str)
    if cached:
        generated_at_utc = cached["generated_at"]
        if isinstance(generated_at_utc, str):
            generated_at_utc = datetime.fromisoformat(generated_at_utc.replace("Z", "+00:00"))
        if getattr(generated_at_utc, "tzinfo", None) is None:
            generated_at_utc = generated_at_utc.replace(tzinfo=timezone.utc)

        beijing_tz = timezone(timedelta(hours=8))
        generated_at_beijing = generated_at_utc.astimezone(beijing_tz)

        # Return ISO with +08:00 so frontend can show 北京时间 correctly
        repos_agent = cached.get("repos_agent", [])[:limit]
        # Backfill reason for agent repos saved before we added the field
        for r in repos_agent:
            if not r.get("reason"):
                r["reason"] = build_agent_reason(r)
        if not repos_agent:
            try:
                client = GitHubClient()
                repos_agent = _fetch_agent_repos(client, limit)
                if repos_agent:
                    save_snapshot(
                        today_str,
                        cached.get("repos_7d") or [],
                        cached.get("repos_30d") or [],
                        repos_agent,
                        status="success",
                    )
            except Exception:
                pass

        return {
            "date": cached["date"],
            "generated_at": generated_at_beijing.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "generated_at_utc": str(cached["generated_at"]),
            "repos_7d": cached["repos_7d"][:limit] if cached.get("repos_7d") else [],
            "repos_30d": cached["repos_30d"][:limit] if cached.get("repos_30d") else [],
            "repos_agent": repos_agent,
        }

    # 懒加载：没有缓存时立即抓取
    client = GitHubClient()
    start_ts = time.monotonic()
    max_duration_sec = 90.0

    try:
        pools = []
        for days in [30, 90, 180, 365]:
            pools.extend(
                client.search_candidate_repos(
                    page_size=50, sort="stars", order="desc", created_days_ago=days
                )
            )
        pools.extend(client.search_candidate_repos(page_size=50, sort="stars", order="desc"))
    except Exception as exc:
        save_snapshot(today_str, [], [], [], status="error", error_msg=str(exc))
        raise UpstreamFetchError("failed to fetch GitHub repositories") from exc

    deduped = {}
    for repo in pools:
        fn = repo.get("full_name")
        if fn:
            deduped[fn] = repo
    candidates = list(deduped.values())

    ranked_7d, ranked_30d = _process_candidates(
        candidates, now_utc, client, start_ts, max_duration_sec, limit
    )

    # Fetch Agent OS related repos
    agent_repos = _fetch_agent_repos(client, limit)

    if not ranked_7d and not ranked_30d:
        save_snapshot(
            today_str, [], [], [], status="error", error_msg="no ranked repositories available"
        )
        raise UpstreamFetchError("no ranked repositories available")

    beijing_tz = timezone(timedelta(hours=8))
    generated_at_beijing = now_utc.astimezone(beijing_tz)

    result = {
        "date": today_str,
        "generated_at": generated_at_beijing.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "generated_at_utc": now_utc.isoformat(),
        "repos_7d": ranked_7d[:limit],
        "repos_30d": ranked_30d[:limit],
        "repos_agent": agent_repos,
    }
    save_snapshot(today_str, ranked_7d[:limit], ranked_30d[:limit], agent_repos, status="success")

    return result
