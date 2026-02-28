"""Tests for Papers API."""

import os
import pytest
from app.models import Paper


def test_list_papers_empty(client, test_db):
    """Test listing papers when database is empty."""
    response = client.get("/api/papers/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_papers_with_data(client, test_db):
    """Test listing papers with data in database."""
    # Add a test paper
    paper = Paper(
        title="Test Paper",
        authors="Test Author",
        abstract="Test abstract",
        pdf_path="/test/paper.pdf",
        year=2024,
    )
    test_db.add(paper)
    test_db.commit()

    response = client.get("/api/papers/")
    assert response.status_code == 200
    papers = response.json()
    assert len(papers) == 1
    assert papers[0]["title"] == "Test Paper"


def test_get_paper_by_id(client, test_db):
    """Test getting a specific paper by ID."""
    paper = Paper(title="Test Paper", authors="Test Author", pdf_path="/test/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.get(f"/api/papers/{paper.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Paper"


def test_get_paper_not_found(client, test_db):
    """Test getting a non-existent paper."""
    response = client.get("/api/papers/99999")
    assert response.status_code == 404


def test_paper_with_favorite(client, test_db):
    """Test paper favorite status."""
    from app.models import Favorite

    paper = Paper(title="Test Paper", pdf_path="/test/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    # Add to favorites
    fav = Favorite(paper_id=paper.id)
    test_db.add(fav)
    test_db.commit()

    response = client.get(f"/api/papers/{paper.id}")
    assert response.status_code == 200
    assert response.json()["is_favorite"] == True


from unittest.mock import patch

@patch("app.routers.papers.pdf_service.extract_metadata")
@patch("app.routers.papers.glob.glob")
def test_scan_papers_folder(mock_glob, mock_extract, client, test_db):
    """Test scanning papers folder."""
    from app.routers.papers import scan_papers_folder

    mock_glob.return_value = ["/fake/papers/2023_test1.pdf", "/fake/papers/2024_test2.pdf"]
    mock_extract.return_value = {
        "title": "Mocked Title",
        "authors": "Mocked Author",
        "abstract": "Mocked abstract"
    }

    scan_papers_folder("/fake/papers", test_db)

    papers = test_db.query(Paper).all()
    # Should have scanned mocked papers
    assert len(papers) == 2
    assert papers[0].year == 2023
    assert papers[1].year == 2024
