import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx


class GitHubClient:
    def __init__(self) -> None:
        self.base_url = "https://api.github.com"
        token = os.getenv("GITHUB_TOKEN")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "repo-trends-explorer",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.headers = headers

    def search_candidate_repos(
        self,
        page_size: int = 50,
        sort: str = "stars",
        order: str = "desc",
        page: int = 1,
        created_days_ago: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if created_days_ago:
            created_date = (datetime.now(timezone.utc) - timedelta(days=created_days_ago)).date()
            query = f"stars:>=200 archived:false created:>={created_date}"
        else:
            query = "stars:>=200 archived:false"
        url = f"{self.base_url}/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": page_size,
            "page": page,
        }
        with httpx.Client(timeout=15.0, headers=self.headers) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
        payload = response.json()
        return payload.get("items", [])

    def list_star_events(self, owner: str, repo: str, per_page: int = 100) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/repos/{owner}/{repo}/stargazers"
        headers = dict(self.headers)
        headers["Accept"] = "application/vnd.github.star+json"
        with httpx.Client(timeout=15.0, headers=headers) as client:
            first_resp = client.get(url, params={"per_page": per_page, "page": 1})
            first_resp.raise_for_status()

            last_page = _extract_last_page(first_resp.headers.get("Link", ""))
            if last_page <= 1:
                return first_resp.json()

            events: List[Dict[str, Any]] = []
            min_page = max(last_page - 2, 1)
            for page in range(last_page, min_page - 1, -1):
                resp = client.get(url, params={"per_page": per_page, "page": page})
                resp.raise_for_status()
                payload = resp.json()
                if not isinstance(payload, list):
                    continue
                events.extend(payload)
        return events


def _extract_last_page(link_header: str) -> int:
    if not link_header:
        return 1
    match = re.search(r"[?&]page=(\d+)>;\s*rel=\"last\"", link_header)
    if not match:
        return 1
    return int(match.group(1))


def parse_iso_datetime(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)


def compute_stars_ago(
    stars_today: int, star_events: List[Dict[str, Any]], days: int, now: Optional[datetime] = None
) -> int:
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time.timestamp() - (days * 24 * 60 * 60)

    recent_stars = 0
    for event in star_events:
        starred_at = event.get("starred_at")
        if not starred_at:
            continue
        event_dt = parse_iso_datetime(starred_at)
        if event_dt.timestamp() >= cutoff:
            recent_stars += 1

    stars_ago = max(stars_today - recent_stars, 0)
    return stars_ago


def compute_stars_7d_ago(
    stars_today: int, star_events: List[Dict[str, Any]], now: Optional[datetime] = None
) -> int:
    return compute_stars_ago(stars_today, star_events, 7, now)


def compute_stars_30d_ago(
    stars_today: int, star_events: List[Dict[str, Any]], now: Optional[datetime] = None
) -> int:
    return compute_stars_ago(stars_today, star_events, 30, now)


def is_sensitive_repo(repo: Dict[str, Any]) -> bool:
    text = " ".join(
        [
            repo.get("name", ""),
            repo.get("description") or "",
            " ".join(repo.get("topics", []) or []),
        ]
    ).lower()

    blocked_keywords = {
        "porn",
        "nsfw",
        "adult",
        "xxx",
        "hentai",
        "sex",
        "nude",
    }
    return any(keyword in text for keyword in blocked_keywords)
