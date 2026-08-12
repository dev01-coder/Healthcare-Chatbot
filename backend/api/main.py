"""
Healthcare RAG Bot - FastAPI Backend
Run: uvicorn backend.api.main:app --reload --port 8000
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

from backend.config import settings
from backend.exceptions import HealthcareBotError, RetrievalError, ProviderError
from backend.pipeline.rag_chain import chat, stream_chat
from backend.retrieval.retriever import retriever
from backend.safety.emergency import detect_emergency

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Rate Limiting ──────────────────────────────────────────────
_rate_limits: dict = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 30  # requests per window per IP


def _check_rate_limit(client_ip: str):
    now = time.time()
    _rate_limits[client_ip] = [
        t for t in _rate_limits[client_ip] if now - t < RATE_LIMIT_WINDOW
    ]
    # Clean up empty entries to prevent memory leak
    if not _rate_limits[client_ip]:
        del _rate_limits[client_ip]
        return
    if len(_rate_limits[client_ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_MAX} requests per minute.",
        )
    _rate_limits[client_ip].append(now)


# ── Lifespan (replaces deprecated on_event) ────────────────────

@asynccontextmanager
async def lifespan(app):
    settings.log_config()
    warnings = settings.validate()
    for w in warnings:
        logger.warning(w)
    yield


# ── App setup ──────────────────────────────────────────────────
app = FastAPI(
    title="Healthcare RAG Chatbot API",
    description="AI-powered healthcare information assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response Models ────────────────────────────────────

class Message(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    history: Optional[List[Message]] = Field(default_factory=list)
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    emergency: Optional[dict] = None
    model: str
    docs_retrieved: int


class EmergencyCheckRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


# ── Exception handler ─────────────────────────────────────────

@app.exception_handler(HealthcareBotError)
async def healthcare_error_handler(request, exc):
    """Handle application-specific errors with proper HTTP responses."""
    if isinstance(exc, ProviderError):
        return JSONResponse(status_code=502, content={"detail": str(exc)})
    if isinstance(exc, RetrievalError):
        return JSONResponse(status_code=503, content={"detail": str(exc)})
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# ── Routes ─────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Healthcare RAG Chatbot API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        stats = retriever.get_stats()
        return {
            "status": "healthy",
            "vector_db": "connected",
            "total_documents": stats["total_documents"],
            "model": stats["model"],
            "llm_provider": settings.LLM_PROVIDER,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "message": "Run python scripts/build_index.py to set up the database",
        }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, req: Request):
    """Non-streaming chat endpoint."""
    _check_rate_limit(req.client.host)
    history = [{"role": m.role, "content": m.content} for m in request.history]

    try:
        result = await asyncio.to_thread(chat, request.message, history)
        return result
    except HealthcareBotError:
        raise
    except Exception as e:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, req: Request):
    """Streaming chat endpoint — returns Server-Sent Events."""
    _check_rate_limit(req.client.host)
    history = [{"role": m.role, "content": m.content} for m in request.history]

    return StreamingResponse(
        stream_chat(request.message, history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/emergency-check")
async def emergency_check(body: EmergencyCheckRequest):
    """Check if a message contains emergency signals."""
    result = detect_emergency(body.message)
    return {"emergency": result}


@app.get("/stats")
async def stats():
    """Return database statistics."""
    return retriever.get_stats()


# ── Question Suggestions (autocomplete) ──────────────────────

_suggest_cache: Optional[List[str]] = None


def _load_question_list() -> List[str]:
    """Load unique questions from processed documents (cached in memory)."""
    global _suggest_cache
    if _suggest_cache is not None:
        return _suggest_cache

    docs_path = Path("data/processed/all_documents.json")
    if not docs_path.exists():
        _suggest_cache = []
        return _suggest_cache

    try:
        with open(docs_path, encoding="utf-8") as f:
            docs = json.load(f)
        questions = list({d["question"] for d in docs if d.get("question")})
        questions.sort(key=str.lower)
        _suggest_cache = questions
        logger.info("Loaded %d unique questions for suggestions", len(questions))
    except Exception as e:
        logger.error("Failed to load question list: %s", e)
        _suggest_cache = []

    return _suggest_cache


@app.get("/api/suggest")
async def suggest(q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=10)):
    """Return question suggestions matching a prefix (case-insensitive)."""
    questions = _load_question_list()
    query_lower = q.lower()
    matches = [question for question in questions if query_lower in question.lower()]
    return {"suggestions": matches[:limit]}


# ── Run directly ───────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
