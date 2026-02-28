"""Station-wide chat API (no paper context)."""

from fastapi import APIRouter, HTTPException

from ..schemas import ChatRequest, ChatResponse
from ..services import OllamaService

router = APIRouter(prefix="/api", tags=["chat"])
ollama_service = OllamaService()


@router.post("/chat", response_model=ChatResponse)
def station_chat(req: ChatRequest):
    """Chat with Ollama, no paper context."""
    if not ollama_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Please start Ollama to enable chat.",
        )
    reply = ollama_service.chat(req.message, context=None)
    if reply is None:
        raise HTTPException(status_code=503, detail="Ollama failed to respond.")
    return ChatResponse(reply=reply)
