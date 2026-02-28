"""Search API router."""

from fastapi import APIRouter, HTTPException
from typing import List

from ..services import ArxivService

router = APIRouter(prefix="/api/search", tags=["search"])
arxiv_service = ArxivService()


@router.get("/", response_model=List[dict])
def search_arxiv(q: str, max_results: int = 10):
    """Search ArXiv for papers."""
    if not q:
        return []

    try:
        results = arxiv_service.search(q, max_results=max_results)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")
