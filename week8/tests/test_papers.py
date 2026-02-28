"""Tests for Papers API."""

from unittest.mock import patch

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
    assert papers[0]["is_favorite"] is False


def test_list_papers_hides_duplicates_by_default(client, test_db):
    """List endpoint should hide duplicates unless include_duplicates=true."""
    p1 = Paper(
        title="Analysis of Docker Security",
        authors="Author A",
        pdf_path="/tmp/a1.pdf",
        arxiv_id=None,
        year=2014,
    )
    p2 = Paper(
        title="Analysis of Docker Security",
        authors="Author B",
        pdf_path="/tmp/a2.pdf",
        arxiv_id=None,
        year=2014,
    )
    test_db.add(p1)
    test_db.add(p2)
    test_db.commit()

    response = client.get("/api/papers/")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response_all = client.get("/api/papers/?include_duplicates=true")
    assert response_all.status_code == 200
    assert len(response_all.json()) == 2


def test_list_papers_hides_noisy_rows_by_default(client, test_db):
    """Noisy OCR-like rows should be hidden unless include_noisy=true."""
    noisy = Paper(
        title="Analysis of Docker Security ThanhBui AaltoUniversitySchoolofScience thanh.bui@aalto.fi Abstract",
        authors=None,
        pdf_path="/tmp/noisy.pdf",
        year=None,
    )
    clean = Paper(
        title="Analysis of Docker Security",
        authors="Thanh Bui",
        pdf_path="/tmp/clean.pdf",
        year=2015,
    )
    test_db.add(noisy)
    test_db.add(clean)
    test_db.commit()

    response = client.get("/api/papers/")
    assert response.status_code == 200
    papers = response.json()
    assert len(papers) == 1
    assert papers[0]["title"] == "Analysis of Docker Security"

    response_all = client.get("/api/papers/?include_noisy=true")
    assert response_all.status_code == 200
    assert len(response_all.json()) == 2


def test_get_paper_by_id(client, test_db):
    """Test getting a specific paper by ID."""
    paper = Paper(title="Test Paper", authors="Test Author", pdf_path="/test/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.get(f"/api/papers/{paper.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Paper"
    assert response.json()["is_favorite"] is False


def test_get_paper_not_found(client, test_db):
    """Test getting a non-existent paper."""
    response = client.get("/api/papers/99999")
    assert response.status_code == 404


@patch("app.routers.papers.arxiv_service.download")
def test_download_paper_success(mock_download, client, test_db):
    """Test downloading a paper from ArXiv."""
    mock_download.return_value = {
        "arxiv_id": "2401.12345",
        "title": "Test OS Paper",
        "authors": "Alice, Bob",
        "abstract": "An abstract.",
        "pdf_path": "/papers/2401.12345.pdf",
        "year": 2024,
    }
    response = client.post("/api/papers/download", json={"arxiv_id": "2401.12345"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test OS Paper"
    assert data["arxiv_id"] == "2401.12345"
    mock_download.assert_called_once_with("2401.12345")


def test_download_paper_duplicate(client, test_db):
    """Test download when paper with same arxiv_id already exists."""
    paper = Paper(
        title="Existing Paper",
        authors="Author",
        pdf_path="/test/existing.pdf",
        arxiv_id="2401.99999",
    )
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    with patch("app.routers.papers.arxiv_service.download") as mock_download:
        response = client.post("/api/papers/download", json={"arxiv_id": "2401.99999"})
    assert response.status_code == 200
    assert response.json()["id"] == paper.id
    assert response.json()["title"] == "Existing Paper"
    mock_download.assert_not_called()


@patch("app.routers.papers.arxiv_service.download")
def test_download_paper_failure(mock_download, client, test_db):
    """Test download when ArXiv fails."""
    mock_download.side_effect = Exception("Network error")
    response = client.post("/api/papers/download", json={"arxiv_id": "2401.00000"})
    assert response.status_code == 500
    assert "Failed to download" in response.json()["detail"]


@patch("app.routers.papers.pwc_service.get_repo")
def test_get_code_returns_repo(mock_get_repo, client, test_db):
    """Test GET /api/papers/{id}/code when repo is found."""
    mock_get_repo.return_value = "https://github.com/example/os-paper"
    paper = Paper(title="Some Kernel Paper", pdf_path="/test/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.get(f"/api/papers/{paper.id}/code")
    assert response.status_code == 200
    assert response.json()["repo"] == "https://github.com/example/os-paper"


@patch("app.routers.papers.pwc_service.get_repo")
def test_get_code_returns_none(mock_get_repo, client, test_db):
    """Test GET /api/papers/{id}/code when no repo found."""
    mock_get_repo.return_value = None
    paper = Paper(title="Obscure Paper", pdf_path="/test/paper.pdf")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.get(f"/api/papers/{paper.id}/code")
    assert response.status_code == 200
    assert response.json()["repo"] is None


@patch("app.routers.papers.pwc_service.get_repo")
def test_get_code_uses_cached_repo(mock_get_repo, client, test_db):
    """If paper already has github_repo, endpoint should not call external service."""
    paper = Paper(
        title="Cached Repo Paper",
        pdf_path="/test/paper.pdf",
        github_repo="https://github.com/example/cached",
    )
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    response = client.get(f"/api/papers/{paper.id}/code")
    assert response.status_code == 200
    assert response.json()["repo"] == "https://github.com/example/cached"
    mock_get_repo.assert_not_called()


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


@patch("app.routers.papers.pdf_service.extract_metadata")
@patch("app.routers.papers.glob.glob")
def test_scan_papers_folder_skips_existing(mock_glob, mock_extract, client, test_db):
    """scan_papers_folder should skip PDF paths already in DB."""
    from app.routers.papers import scan_papers_folder

    existing = Paper(title="Existing", pdf_path="/fake/papers/2024_test2.pdf")
    test_db.add(existing)
    test_db.commit()

    mock_glob.return_value = ["/fake/papers/2023_test1.pdf", "/fake/papers/2024_test2.pdf"]
    mock_extract.return_value = {"title": "Mocked Title", "authors": "A", "abstract": "B"}

    scan_papers_folder("/fake/papers", test_db)

    papers = test_db.query(Paper).all()
    assert len(papers) == 2


@patch("app.routers.papers.arxiv_service.get_metadata")
def test_enrich_papers_metadata_from_filename_arxiv_id(mock_get_metadata, client, test_db):
    """POST /api/papers/enrich should fill fields from arXiv metadata."""
    mock_get_metadata.return_value = {
        "arxiv_id": "2502.11708v1",
        "title": "Clean Linux Kernel Title",
        "authors": "Alice, Bob",
        "abstract": "Kernel paper abstract",
        "year": 2025,
    }
    paper = Paper(
        title="2502.11708v1",
        authors=None,
        abstract=None,
        arxiv_id=None,
        pdf_path="/tmp/2502.11708v1.pdf",
        year=None,
    )
    test_db.add(paper)
    test_db.commit()

    response = client.post("/api/papers/enrich", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["processed"] == 1
    assert payload["updated"] == 1
    assert payload["failed"] == 0

    test_db.refresh(paper)
    assert paper.arxiv_id == "2502.11708v1"
    assert paper.title == "Clean Linux Kernel Title"
    assert paper.authors == "Alice, Bob"
    assert paper.year == 2025


@patch("app.routers.papers.arxiv_service.get_metadata")
def test_enrich_papers_metadata_extracts_reversed_arxiv_id(mock_get_metadata, client, test_db):
    """POST /api/papers/enrich should recover arXiv IDs from reversed strings."""
    mock_get_metadata.return_value = {
        "arxiv_id": "1410.0846v1",
        "title": "Recovered Title",
        "authors": "Recovered Author",
        "abstract": "Recovered abstract",
        "year": 2014,
    }
    paper = Paper(
        title="4102 tcO 2 ]ES.sc[ 1v6480.0141:viXra",
        authors=None,
        abstract=None,
        arxiv_id=None,
        pdf_path="/tmp/noisy.pdf",
        year=None,
    )
    test_db.add(paper)
    test_db.commit()

    response = client.post("/api/papers/enrich", json={})
    assert response.status_code == 200
    test_db.refresh(paper)
    assert paper.arxiv_id == "1410.0846v1"
    assert paper.title == "Recovered Title"
    assert paper.authors == "Recovered Author"
    assert paper.year == 2014


@patch("app.routers.papers.arxiv_service.get_metadata")
def test_enrich_papers_metadata_skips_arxiv_id_conflict(mock_get_metadata, client, test_db):
    """POST /api/papers/enrich should not overwrite to duplicate arXiv IDs."""
    mock_get_metadata.return_value = {
        "arxiv_id": "2502.11708v1",
        "title": "Some Title",
        "authors": "Some Author",
        "abstract": "Some abstract",
        "year": 2025,
    }
    paper_a = Paper(
        title="A",
        authors="A",
        abstract="A",
        arxiv_id="2502.11708v1",
        pdf_path="/tmp/a.pdf",
        year=2025,
    )
    paper_b = Paper(
        title="B",
        authors=None,
        abstract=None,
        arxiv_id=None,
        pdf_path="/tmp/2502.11708v1.pdf",
        year=None,
    )
    test_db.add(paper_a)
    test_db.add(paper_b)
    test_db.commit()

    response = client.post("/api/papers/enrich", json={})
    assert response.status_code == 200
    test_db.refresh(paper_b)
    assert paper_b.arxiv_id is None
