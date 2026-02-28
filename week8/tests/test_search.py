"""Tests for ArXiv Search API."""

import pytest
from unittest.mock import patch


@patch("app.routers.search.arxiv_service.search")
def test_search_arxiv_basic(mock_search, client):
    """Test basic ArXiv search."""
    mock_search.return_value = [
        {
            "title": "A Distributed System",
            "authors": "Alice",
            "abstract": "An abstract.",
            "arxiv_id": "1234.5678",
            "pdf_path": ""
        }
    ]
    response = client.get("/api/search/?q=distributed&max_results=5")
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list)
    assert len(results) > 0
    assert len(results) <= 5
    mock_search.assert_called_with("distributed", max_results=5)


@patch("app.routers.search.arxiv_service.search")
def test_search_arxiv_returns_valid_structure(mock_search, client):
    """Test that search returns valid paper structure."""
    mock_search.return_value = [
        {
            "title": "Kernel stuff",
            "authors": "Bob",
            "abstract": "Kernel abstract.",
            "arxiv_id": "2345.6789",
            "pdf_path": ""
        }
    ]
    response = client.get("/api/search/?q=kernel&max_results=3")
    assert response.status_code == 200

    results = response.json()
    if len(results) > 0:
        paper = results[0]
        assert "title" in paper
        assert "arxiv_id" in paper
        assert "authors" in paper
        assert "abstract" in paper


def test_search_arxiv_empty_query(client):
    """Test search with empty query."""
    response = client.get("/api/search/?q=")
    assert response.status_code == 200
    # Empty query should return empty list
    assert response.json() == []


@patch("app.routers.search.arxiv_service.search")
def test_search_arxiv_large_results(mock_search, client):
    """Test search with large max_results."""
    mock_search.return_value = [{"title": f"Paper {i}", "authors": "Author", "abstract": "Abstract", "arxiv_id": f"{i}", "pdf_path": ""} for i in range(20)]
    response = client.get("/api/search/?q=linux&max_results=20")
    assert response.status_code == 200

    results = response.json()
    assert len(results) <= 20


@patch("app.routers.search.arxiv_service.search")
def test_search_arxiv_returns_500_on_exception(mock_search, client):
    """Test search when service raises - API returns 500 with detail."""
    mock_search.side_effect = Exception("ArXiv timeout")
    response = client.get("/api/search/?q=linux&max_results=5")
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "Search failed" in response.json()["detail"]

