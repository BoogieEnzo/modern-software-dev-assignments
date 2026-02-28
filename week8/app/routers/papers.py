"""Papers API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import glob
import re
import glob

from ..database import get_db
from ..models import Paper, Favorite
from ..schemas import PaperResponse, ArxivSearchResult, DownloadRequest
from ..services import ArxivService, PapersWithCodeService, OllamaService, PDFService

router = APIRouter(prefix="/api/papers", tags=["papers"])

# Initialize services
arxiv_service = ArxivService()
pwc_service = PapersWithCodeService()
ollama_service = OllamaService()
pdf_service = PDFService()


@router.get("/", response_model=List[PaperResponse])
def list_papers(db: Session = Depends(get_db)):
    """List all papers."""
    papers = db.query(Paper).order_by(Paper.created_at.desc()).all()

    # Check favorites
    favorite_ids = {f.paper_id for f in db.query(Favorite).all()}

    result = []
    for paper in papers:
        paper_dict = PaperResponse.model_validate(paper)
        paper_dict.is_favorite = paper.id in favorite_ids
        result.append(paper_dict)

    return result


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    """Get paper by ID."""
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    response = PaperResponse.model_validate(paper)
    favorite = db.query(Favorite).filter(Favorite.paper_id == paper_id).first()
    response.is_favorite = favorite is not None

    return response


@router.get("/{paper_id}/summarize")
def summarize_paper(paper_id: int, db: Session = Depends(get_db)):
    """Generate AI summary for a paper."""
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check if Ollama is available
    if not ollama_service.is_available():
        return {"error": "Ollama is not running. Please start Ollama to enable AI summaries."}

    # Generate summary
    summary = ollama_service.generate_summary(paper.title, paper.abstract or "")

    if summary:
        paper.summary = summary
        db.commit()
        return {"summary": summary}

    return {"error": "Failed to generate summary"}


@router.get("/{paper_id}/code")
def get_code(paper_id: int, db: Session = Depends(get_db)):
    """Get GitHub repository for a paper."""
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # If already has repo, return it
    if paper.github_repo:
        return {"repo": paper.github_repo}

    # Try to find repo
    repo = pwc_service.get_repo(paper.title)

    if repo:
        paper.github_repo = repo
        db.commit()
        return {"repo": repo}

    return {"repo": None}


@router.post("/download")
def download_paper(request: DownloadRequest, db: Session = Depends(get_db)):
    """Download a paper from ArXiv."""
    # Check if already exists
    existing = db.query(Paper).filter(Paper.arxiv_id == request.arxiv_id).first()
    if existing:
        return PaperResponse.model_validate(existing)

    # Download from ArXiv
    try:
        paper_data = arxiv_service.download(request.arxiv_id)

        # Create paper record
        paper = Paper(
            title=paper_data["title"],
            authors=paper_data["authors"],
            abstract=paper_data["abstract"],
            arxiv_id=paper_data["arxiv_id"],
            pdf_path=paper_data["pdf_path"],
            year=paper_data.get("year"),
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

        return PaperResponse.model_validate(paper)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download: {str(e)}")


def scan_papers_folder(papers_dir: str, db: Session):
    """Scan papers folder and add to database."""
    pdf_files = glob.glob(os.path.join(papers_dir, "*.pdf"))

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)

        # Check if already in DB
        existing = db.query(Paper).filter(Paper.pdf_path == pdf_path).first()
        if existing:
            continue

        # Extract metadata
        metadata = pdf_service.extract_metadata(pdf_path)

        # Extract year from filename if possible
        year = None
        match = re.search(r"(19|20)\d{2}", filename)
        if match:
            year = int(match.group())

        paper = Paper(
            title=metadata.get("title", filename.replace(".pdf", ""))
            if metadata
            else filename.replace(".pdf", ""),
            authors=metadata.get("authors") if metadata else None,
            abstract=metadata.get("abstract") if metadata else None,
            pdf_path=pdf_path,
            year=year,
        )
        db.add(paper)

    db.commit()
