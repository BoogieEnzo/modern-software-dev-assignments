"""Papers API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import glob
import re

from ..database import get_db
from ..models import Paper
from ..schemas import (
    PaperResponse,
    ArxivSearchResult,
    DownloadRequest,
    ChatRequest,
    ChatResponse,
    EnrichRequest,
    EnrichResponse,
)
from ..services import ArxivService, PapersWithCodeService, OllamaService, PDFService

router = APIRouter(prefix="/api/papers", tags=["papers"])

# Initialize services
arxiv_service = ArxivService()
pwc_service = PapersWithCodeService()
ollama_service = OllamaService()
pdf_service = PDFService()

ARXIV_ID_RE = re.compile(r"\b\d{4}\.\d{4,5}(?:v\d+)?\b")


def _normalize_whitespace(text: str | None) -> str | None:
    if text is None:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned or None


def _normalize_title(text: str | None) -> str | None:
    if text is None:
        return None
    text = _normalize_whitespace(text)
    if text is None:
        return None
    # Keep DB-safe title length.
    return text[:500]


def _extract_arxiv_id_from_text(text: str | None) -> str | None:
    if not text:
        return None
    normal = ARXIV_ID_RE.search(text)
    if normal:
        return normal.group()
    reversed_text = text[::-1]
    reversed_match = ARXIV_ID_RE.search(reversed_text)
    if reversed_match:
        return reversed_match.group()
    return None


def _looks_low_quality_title(title: str | None) -> bool:
    title = _normalize_title(title)
    if not title:
        return True
    if ARXIV_ID_RE.fullmatch(title):
        return True
    if len(title) > 220:
        return True
    if "arXiv:" in title or "viXra" in title:
        return True
    return False


def _canonical_title_key(title: str | None) -> str | None:
    title = _normalize_title(title)
    if not title:
        return None
    key = re.sub(r"[^a-z0-9]+", "", title.lower())
    return key or None


@router.get("/", response_model=List[PaperResponse])
def list_papers(include_duplicates: bool = False, db: Session = Depends(get_db)):
    """List local papers; hide duplicates by default."""
    papers = db.query(Paper).order_by(Paper.created_at.desc()).all()
    result = []
    seen_keys: set[str] = set()
    for paper in papers:
        if not include_duplicates:
            dedupe_key = None
            if paper.arxiv_id:
                dedupe_key = f"arxiv:{paper.arxiv_id.lower()}"
            else:
                title_key = _canonical_title_key(paper.title)
                if title_key:
                    dedupe_key = f"title:{title_key}"
            if dedupe_key and dedupe_key in seen_keys:
                continue
            if dedupe_key:
                seen_keys.add(dedupe_key)
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


@router.post("/enrich", response_model=EnrichResponse)
def enrich_papers_metadata(request: EnrichRequest, db: Session = Depends(get_db)):
    """Enrich local paper metadata using arXiv IDs and normalization rules."""
    query = db.query(Paper).order_by(Paper.created_at.desc())
    if request.limit and request.limit > 0:
        papers = query.limit(request.limit).all()
    else:
        papers = query.all()

    processed = 0
    updated = 0
    skipped = 0
    failed = 0
    assigned_arxiv_ids = {p.arxiv_id for p in papers if p.arxiv_id}

    for paper in papers:
        processed += 1
        changed = False
        try:
            source_text = " ".join(
                [
                    paper.arxiv_id or "",
                    paper.title or "",
                    os.path.basename(paper.pdf_path or ""),
                ]
            )
            candidate_arxiv_id = _extract_arxiv_id_from_text(source_text)

            if candidate_arxiv_id and paper.arxiv_id != candidate_arxiv_id:
                if candidate_arxiv_id not in assigned_arxiv_ids:
                    paper.arxiv_id = candidate_arxiv_id
                    assigned_arxiv_ids.add(candidate_arxiv_id)
                    changed = True

            # Always apply lightweight normalization.
            norm_title = _normalize_title(paper.title)
            norm_authors = _normalize_whitespace(paper.authors)
            if norm_title and norm_title != paper.title:
                paper.title = norm_title
                changed = True
            if norm_authors != paper.authors:
                paper.authors = norm_authors
                changed = True

            if paper.arxiv_id:
                metadata = arxiv_service.get_metadata(paper.arxiv_id)
                if metadata:
                    if (not paper.title) or _looks_low_quality_title(paper.title):
                        if metadata.get("title"):
                            paper.title = _normalize_title(metadata["title"])
                            changed = True
                    if not paper.authors and metadata.get("authors"):
                        paper.authors = _normalize_whitespace(metadata["authors"])
                        changed = True
                    if not paper.abstract and metadata.get("abstract"):
                        paper.abstract = metadata["abstract"]
                        changed = True
                    if not paper.year and metadata.get("year"):
                        paper.year = metadata["year"]
                        changed = True

            if changed:
                db.commit()
                updated += 1
            else:
                skipped += 1
        except Exception:
            db.rollback()
            failed += 1

    return EnrichResponse(
        processed=processed,
        updated=updated,
        skipped=skipped,
        failed=failed,
    )


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
