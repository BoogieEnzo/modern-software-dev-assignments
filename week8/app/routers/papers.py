"""Papers API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import glob
import re

from ..database import get_db
from ..models import Paper
from ..schemas import PaperResponse, ArxivSearchResult, DownloadRequest, ChatRequest, ChatResponse
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
    result = []
    for paper in papers:
        paper_dict = PaperResponse.model_validate(paper)
        paper_dict.is_favorite = False
        result.append(paper_dict)
    return result


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    """Get paper by ID."""
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    response = PaperResponse.model_validate(paper)
    response.is_favorite = False
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


@router.post("/{paper_id}/chat", response_model=ChatResponse)
def paper_chat(paper_id: int, req: ChatRequest, db: Session = Depends(get_db)):
    """Chat about a paper using its full PDF text. Paper must be downloaded locally."""
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if not paper.pdf_path:
        raise HTTPException(
            status_code=400,
            detail="Paper has no local PDF. Download the paper first.",
        )
    if not os.path.exists(paper.pdf_path):
        raise HTTPException(
            status_code=400,
            detail="PDF file not found. Download the paper first.",
        )
    if not ollama_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Please start Ollama to enable chat.",
        )
    full_text = pdf_service.extract_full_text(paper.pdf_path)
    if not full_text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF.",
        )
    reply = ollama_service.chat(req.message, context=full_text)
    if reply is None:
        raise HTTPException(status_code=503, detail="Ollama failed to respond.")
    return ChatResponse(reply=reply)


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
        db.commit()  # commit per paper so SQLite write lock is released quickly; GET /api/papers/ can return without waiting
