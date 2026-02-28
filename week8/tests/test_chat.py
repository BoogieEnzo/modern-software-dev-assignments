"""Tests for Chat API (station-wide and paper-scoped)."""

from unittest.mock import patch

from app.models import Paper


# ---- Station chat POST /api/chat ----
@patch("app.routers.chat.ollama_service.chat")
@patch("app.routers.chat.ollama_service.is_available")
def test_station_chat_success(mock_available, mock_chat, client):
    """POST /api/chat returns Ollama reply when available."""
    mock_available.return_value = True
    mock_chat.return_value = "Hello! How can I help?"
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["reply"] == "Hello! How can I help?"
    mock_chat.assert_called_once_with("Hello", context=None)


@patch("app.routers.chat.ollama_service.is_available")
def test_station_chat_ollama_unavailable(mock_available, client):
    """POST /api/chat returns 503 when Ollama not running."""
    mock_available.return_value = False
    response = client.post("/api/chat", json={"message": "Hi"})
    assert response.status_code == 503
    assert "detail" in response.json()


# ---- Paper chat POST /api/papers/{id}/chat ----
@patch("app.routers.papers.ollama_service.chat")
@patch("app.routers.papers.ollama_service.is_available")
@patch("app.routers.papers.pdf_service.extract_full_text")
@patch("app.routers.papers.os.path.exists")
def test_paper_chat_success(mock_exists, mock_extract, mock_available, mock_chat, client, test_db):
    """POST /api/papers/{id}/chat returns reply when PDF exists and Ollama available."""
    mock_exists.return_value = True
    mock_extract.return_value = "Full paper text about kernels."
    mock_available.return_value = True
    mock_chat.return_value = "This paper discusses kernel design."
    paper = Paper(
        title="Kernel Paper",
        pdf_path="/real/path/paper.pdf",
    )
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.post(
        f"/api/papers/{paper.id}/chat",
        json={"message": "What is this paper about?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "This paper discusses kernel design."
    mock_extract.assert_called_once_with("/real/path/paper.pdf")
    mock_chat.assert_called_once()
    call_args = mock_chat.call_args
    assert "What is this paper about?" in call_args[0][0]
    assert "Full paper text about kernels." in call_args[1]["context"]


def test_paper_chat_paper_not_found(client, test_db):
    """POST /api/papers/99999/chat returns 404."""
    response = client.post(
        "/api/papers/99999/chat",
        json={"message": "What?"},
    )
    assert response.status_code == 404


@patch("app.routers.papers.pdf_service.extract_full_text")
def test_paper_chat_no_pdf_or_not_downloaded(mock_extract, client, test_db):
    """POST /api/papers/{id}/chat returns 400 when paper has no local PDF."""
    paper = Paper(title="No PDF", pdf_path=None)
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.post(
        f"/api/papers/{paper.id}/chat",
        json={"message": "What?"},
    )
    assert response.status_code == 400
    mock_extract.assert_not_called()


@patch("app.routers.papers.ollama_service.is_available")
@patch("app.routers.papers.os.path.exists")
def test_paper_chat_ollama_unavailable(mock_exists, mock_available, client, test_db):
    """POST /api/papers/{id}/chat returns 503 when Ollama is unavailable."""
    mock_exists.return_value = True
    mock_available.return_value = False
    paper = Paper(title="Kernel Paper", pdf_path="/real/path/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.post(
        f"/api/papers/{paper.id}/chat",
        json={"message": "What is this paper about?"},
    )
    assert response.status_code == 503
    assert "Ollama is not running" in response.json()["detail"]


@patch("app.routers.papers.ollama_service.is_available")
@patch("app.routers.papers.pdf_service.extract_full_text")
@patch("app.routers.papers.os.path.exists")
def test_paper_chat_extract_text_failed(mock_exists, mock_extract, mock_available, client, test_db):
    """POST /api/papers/{id}/chat returns 400 when PDF text extraction fails."""
    mock_exists.return_value = True
    mock_available.return_value = True
    mock_extract.return_value = None
    paper = Paper(title="Kernel Paper", pdf_path="/real/path/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.post(
        f"/api/papers/{paper.id}/chat",
        json={"message": "What is this paper about?"},
    )
    assert response.status_code == 400
    assert "Could not extract text from PDF." in response.json()["detail"]


@patch("app.routers.papers.ollama_service.chat")
@patch("app.routers.papers.ollama_service.is_available")
@patch("app.routers.papers.pdf_service.extract_full_text")
@patch("app.routers.papers.os.path.exists")
def test_paper_chat_ollama_no_reply(mock_exists, mock_extract, mock_available, mock_chat, client, test_db):
    """POST /api/papers/{id}/chat returns 503 when Ollama returns no reply."""
    mock_exists.return_value = True
    mock_available.return_value = True
    mock_extract.return_value = "Full paper text"
    mock_chat.return_value = None
    paper = Paper(title="Kernel Paper", pdf_path="/real/path/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.post(
        f"/api/papers/{paper.id}/chat",
        json={"message": "What is this paper about?"},
    )
    assert response.status_code == 503
    assert "Ollama failed to respond." in response.json()["detail"]
