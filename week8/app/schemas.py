"""Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PaperBase(BaseModel):
    title: str
    authors: Optional[str] = None
    abstract: Optional[str] = None
    arxiv_id: Optional[str] = None
    pdf_path: Optional[str] = None
    summary: Optional[str] = None
    github_repo: Optional[str] = None
    year: Optional[int] = None


class PaperCreate(PaperBase):
    pass


class PaperResponse(PaperBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_favorite: bool = False

    class Config:
        from_attributes = True


class FavoriteCreate(BaseModel):
    paper_id: int


class FavoriteResponse(BaseModel):
    id: int
    paper_id: int
    created_at: datetime
    paper: Optional[PaperResponse] = None

    class Config:
        from_attributes = True


class ArxivSearchResult(BaseModel):
    arxiv_id: str
    title: str
    authors: str
    abstract: str
    published: str


class DownloadRequest(BaseModel):
    arxiv_id: str
