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
    weekly_star_gain: int
    forks: int
    updated_at: datetime
    reason: str


class TrendingResponse(BaseModel):
    date: str
    generated_at: datetime
    repos: List[TrendingRepo]
