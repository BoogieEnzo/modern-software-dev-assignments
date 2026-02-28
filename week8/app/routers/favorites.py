"""Favorites API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Favorite, Paper
from ..schemas import FavoriteResponse, FavoriteCreate

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("/", response_model=List[FavoriteResponse])
def list_favorites(db: Session = Depends(get_db)):
    """List all favorites."""
    favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
    return favorites


@router.post("/", response_model=FavoriteResponse)
def create_favorite(favorite: FavoriteCreate, db: Session = Depends(get_db)):
    """Add a paper to favorites."""
    # Check if paper exists
    paper = db.get(Paper, favorite.paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check if already favorited
    existing = db.query(Favorite).filter(Favorite.paper_id == favorite.paper_id).first()

    if existing:
        return FavoriteResponse.model_validate(existing)

    # Create favorite
    fav = Favorite(paper_id=favorite.paper_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)

    return FavoriteResponse.model_validate(fav)


@router.delete("/{favorite_id}")
def delete_favorite(favorite_id: int, db: Session = Depends(get_db)):
    """Remove a paper from favorites."""
    fav = db.get(Favorite, favorite_id)
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(fav)
    db.commit()

    return {"message": "Favorite removed"}
