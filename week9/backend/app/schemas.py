from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TrendingRepo(BaseModel):
    full_name: str
    repo_url: str
    description: Optional[str]
    language: Optional[str]
    stars_today: int
    stars_7d_ago: int
    stars_30d_ago: int
    weekly_star_gain: int
    monthly_star_gain: int
    forks: int
    created_at: str
    updated_at: datetime
    reason: str


class AgentRepo(BaseModel):
    """Simplified repo schema for Agent OS related repos (recently created)"""

    full_name: str
    repo_url: str
    description: Optional[str]
    language: Optional[str]
    stars_today: int
    forks: int
    created_at: str
    topics: List[str] = []


class TrendingResponse(BaseModel):
    date: str
    generated_at: datetime
    repos_7d: List[TrendingRepo]
    repos_30d: List[TrendingRepo]
    repos_agent: List[AgentRepo] = []
