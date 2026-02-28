"""Tests for AI Summary (Ollama) API."""

from unittest.mock import patch

from app.models import Paper


def test_summarize_paper_not_found(client, test_db):
    """Test summarizing non-existent paper."""
    response = client.get("/api/papers/99999/summarize")
    assert response.status_code == 404


@patch("app.routers.papers.ollama_service.is_available")
def test_summarize_paper_ollama_unavailable(mock_is_available, client, test_db):
    """Test summarize endpoint returns clear error when Ollama is unavailable."""
    mock_is_available.return_value = False
    paper = Paper(title="Test Paper", abstract="A short abstract", pdf_path="/test/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.get(f"/api/papers/{paper.id}/summarize")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "Ollama is not running" in data["error"]


@patch("app.routers.papers.ollama_service.generate_summary")
@patch("app.routers.papers.ollama_service.is_available")
def test_summarize_paper_with_ollama_available(mock_is_available, mock_generate_summary, client, test_db):
    """Test summarizing paper when Ollama is available."""
    # Create paper with abstract
    paper = Paper(
        title="Test Paper",
        abstract="This is a test abstract about distributed systems.",
        pdf_path="/test/paper.pdf",
    )
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    # Mock Ollama response
    mock_is_available.return_value = True
    mock_generate_summary.return_value = "This is an AI-generated summary of the paper."

    response = client.get(f"/api/papers/{paper.id}/summarize")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["summary"] == "This is an AI-generated summary of the paper."


@patch("app.routers.papers.ollama_service.generate_summary")
@patch("app.routers.papers.ollama_service.is_available")
def test_summarize_paper_generation_failure(mock_is_available, mock_generate_summary, client, test_db):
    """Test summarize endpoint reports generation failure."""
    paper = Paper(
        title="Test Paper",
        abstract="This is a test abstract.",
        pdf_path="/test/paper.pdf",
    )
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    mock_is_available.return_value = True
    mock_generate_summary.return_value = None

    response = client.get(f"/api/papers/{paper.id}/summarize")
    assert response.status_code == 200
    assert response.json() == {"error": "Failed to generate summary"}


def test_code_endpoint_paper_not_found(client, test_db):
    """Test getting code for non-existent paper."""
    response = client.get("/api/papers/99999/code")
    assert response.status_code == 404
