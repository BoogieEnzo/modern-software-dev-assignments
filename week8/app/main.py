"""FastAPI main application."""

import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from .database import engine, SessionLocal
from .models import Base
from .routers import papers_router, search_router, chat_router
from .routers.papers import scan_papers_folder


def _scan_papers_background():
    """Run scan_papers_folder in a background thread so server can accept requests immediately."""
    papers_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "papers")
    papers_dir = os.path.abspath(papers_dir)
    if not os.path.exists(papers_dir):
        return
    db = SessionLocal()
    try:
        scan_papers_folder(papers_dir, db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler."""
    Base.metadata.create_all(bind=engine)
    # Scan papers in background so first request is not blocked (scan can be slow with many PDFs)
    t = threading.Thread(target=_scan_papers_background, daemon=True)
    t.start()
    yield


# Create FastAPI app
app = FastAPI(
    title="OS Paper Hub",
    description="Personal OS论文知识库 + AI辅助理解",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_static_cache_in_dev(request: Request, call_next):
    """Avoid stale JS/CSS during local development."""
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Include routers
app.include_router(papers_router)
app.include_router(search_router)
app.include_router(chat_router)

# Get directories - papers is at week8/papers (same level as app/)
APP_DIR = os.path.dirname(os.path.abspath(__file__))  # app/
BASE_DIR = os.path.dirname(APP_DIR)  # week8/
static_dir = os.path.join(APP_DIR, "static")
papers_dir = os.path.join(BASE_DIR, "papers")

print(f"Static dir: {static_dir}, exists: {os.path.exists(static_dir)}")
print(f"Papers dir: {papers_dir}, exists: {os.path.exists(papers_dir)}")

# Mount static files
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount papers directory for PDF access
if os.path.exists(papers_dir):
    app.mount("/papers", StaticFiles(directory=papers_dir), name="papers")

# Finally mount SPA for all other routes (must be last)
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "OS Paper Hub API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
