"""Tests for Favorites API."""

import pytest
from app.models import Paper, Favorite


def test_list_favorites_empty(client, test_db):
    """Test listing favorites when empty."""
    response = client.get("/api/favorites/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_favorites_with_data(client, test_db):
    """Test listing favorites with data."""
    # Create paper and favorite
    paper = Paper(title="Test Paper", pdf_path="/test/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    fav = Favorite(paper_id=paper.id)
    test_db.add(fav)
    test_db.commit()

    response = client.get("/api/favorites/")
    assert response.status_code == 200

    favorites = response.json()
    assert len(favorites) == 1
    assert favorites[0]["paper"]["title"] == "Test Paper"


def test_create_favorite(client, test_db):
    """Test adding a paper to favorites."""
    paper = Paper(title="Test Paper", pdf_path="/test/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.post("/api/favorites/", json={"paper_id": paper.id})
    assert response.status_code == 200

    favorites = test_db.query(Favorite).all()
    assert len(favorites) == 1


def test_create_favorite_duplicate(client, test_db):
    """Test adding same paper to favorites twice."""
    paper = Paper(title="Test Paper", pdf_path="/test/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    # Add first time
    client.post("/api/favorites/", json={"paper_id": paper.id})

    # Add second time - should not create duplicate
    response = client.post("/api/favorites/", json={"paper_id": paper.id})
    assert response.status_code == 200

    favorites = test_db.query(Favorite).filter(Favorite.paper_id == paper.id).all()
    assert len(favorites) == 1


def test_create_favorite_paper_not_found(client, test_db):
    """Test adding non-existent paper to favorites."""
    response = client.post("/api/favorites/", json={"paper_id": 99999})
    assert response.status_code == 404


def test_delete_favorite(client, test_db):
    """Test removing a paper from favorites."""
    paper = Paper(title="Test Paper", pdf_path="/test/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    fav = Favorite(paper_id=paper.id)
    test_db.add(fav)
    test_db.commit()
    test_db.refresh(fav)

    # Delete
    response = client.delete(f"/api/favorites/{fav.id}")
    assert response.status_code == 200

    # Verify deleted
    favorites = test_db.query(Favorite).all()
    assert len(favorites) == 0


def test_delete_favorite_not_found(client, test_db):
    """Test deleting non-existent favorite."""
    response = client.delete("/api/favorites/99999")
    assert response.status_code == 404
