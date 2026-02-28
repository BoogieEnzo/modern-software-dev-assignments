from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .schemas import TrendingResponse
from .service import UpstreamFetchError, get_today_trending

app = FastAPI(title="Repo Trends Explorer")

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/api/trending/today", response_model=TrendingResponse)
def trending_today() -> TrendingResponse:
    try:
        payload = get_today_trending(limit=3)
    except UpstreamFetchError as exc:
        raise HTTPException(status_code=503, detail="趋势数据加载失败") from exc

    return TrendingResponse.model_validate(payload)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
