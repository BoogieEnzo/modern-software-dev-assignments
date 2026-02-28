"""FastAPI main application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from .database import engine, SessionLocal
from .models import Base
from .routers import papers_router, favorites_router, search_router
from .routers.papers import scan_papers_folder


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler."""
    # Startup
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # papers is in the same directory as app/
        papers_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "papers")
        papers_dir = os.path.abspath(papers_dir)
        if os.path.exists(papers_dir):
            scan_papers_folder(papers_dir, db)
    finally:
        db.close()
    
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

# Include routers
app.include_router(papers_router)
app.include_router(favorites_router)
app.include_router(search_router)

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
