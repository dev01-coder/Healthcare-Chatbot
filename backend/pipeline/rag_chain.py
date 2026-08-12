"""
Healthcare RAG Pipeline - Multi-Provider Support
Supports: Groq (free), Gemini (free), Ollama (local/free), Anthropic (paid)
Change LLM_PROVIDER in .env to switch between them.
"""

import json
import logging
from typing import List, Dict, AsyncIterator

from backend.config import settings
from backend.exceptions import ProviderError
from backend.retrieval.retriever import retriever
from backend.safety.emergency import detect_emergency, get_disclaimer, is_advice_query

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are MediAssist, a healthcare information assistant.

RULES:
1. ONLY answer questions about clinical health topics: symptoms, diseases, conditions, medications, treatments, diagnostics, wellness, nutrition, mental health, and first aid.
2. DECLINE questions about: medical billing, insurance, coding (ICD/CPT), prior authorization, revenue cycle management, hospital administration, legal or financial matters. For these, respond with: "I'm designed to help with clinical health questions only. For billing or insurance inquiries, please contact your healthcare provider or insurance company."
3. Answer using the provided medical context as your primary source.
4. If the context doesn't fully answer, you may use your general medical knowledge to supplement.
5. Be concise: 2-3 sentences maximum. Do not exceed 100 words.
6. Start directly with the answer. No introductions like "Based on the context..." or "According to..."
7. Do NOT repeat the question back.
8. If you're unsure or the question is outside clinical health scope, say: "I'm not sure about that. Please consult a healthcare provider."
9. NEVER make up specific medical dosages or treatment plans.
10. End every answer with: "Consult a healthcare provider for personalized advice."

FORMAT:
- Direct answer first
- Bullet points only for lists (symptoms, steps)
- Simple language anyone can understand
- For emergencies: "Call your local emergency number immediately."
"""


# ── Configure Gemini once at import time ───────────────────────
_gemini_configured = False

def _ensure_gemini_configured():
    global _gemini_configured
    if not _gemini_configured and settings.LLM_PROVIDER == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_configured = True


def build_prompt(query: str, docs: List[Dict]) -> str:
    """Build the RAG prompt with retrieved context."""
    if not docs:
        context = "No specific medical documents found for this query. Use your general medical knowledge to answer."
    else:
        parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.get("source", "Medical Database")
            score = doc.get("score", 0)
            parts.append(f"[Source {i}: {source} | relevance: {score:.3f}]\n{doc['text'][:400]}")
        context = "\n\n---\n\n".join(parts)

    return (
        f"MEDICAL CONTEXT:\n{context}\n\n---\n\n"
        f"USER QUESTION: {query}\n\n"
        "Answer the question using the context above as primary source. "
        "If the context is insufficient, you may use your general medical knowledge. "
        "ANSWER IN 2-3 SENTENCES MAXIMUM. Do not exceed 100 words."
    )


# ── Groq (free) ───────────────────────────────────────────────

def _chat_groq(prompt: str, history: List[Dict]) -> str:
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages,
        max_tokens=settings.MAX_TOKENS
    )
    return resp.choices[0].message.content or ""


async def _stream_groq(prompt: str, history: List[Dict]):
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": prompt})
    stream = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages,
        max_tokens=settings.MAX_TOKENS,
        stream=True
    )
    for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        if text:
            yield f"data: {json.dumps({'type': 'text', 'data': text})}\n\n"


# ── Google Gemini (free) ──────────────────────────────────────

def _chat_gemini(prompt: str, history: List[Dict]) -> str:
    import google.generativeai as genai
    _ensure_gemini_configured()
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT
    )
    chat_history = []
    for h in history[-6:]:
        role = "user" if h["role"] == "user" else "model"
        chat_history.append({"role": role, "parts": [h["content"]]})
    session = model.start_chat(history=chat_history)
    response = session.send_message(prompt)
    return response.text or ""


async def _stream_gemini(prompt: str, history: List[Dict]):
    import google.generativeai as genai
    _ensure_gemini_configured()
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT
    )
    chat_history = []
    for h in history[-6:]:
        role = "user" if h["role"] == "user" else "model"
        chat_history.append({"role": role, "parts": [h["content"]]})
    session = model.start_chat(history=chat_history)
    response = session.send_message(prompt, stream=True)
    for chunk in response:
        if chunk.text:
            yield f"data: {json.dumps({'type': 'text', 'data': chunk.text})}\n\n"


# ── Ollama (fully local, no API key) ─────────────────────────

def _chat_ollama(prompt: str, history: List[Dict]) -> str:
    import ollama
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": prompt})
    resp = ollama.chat(
        model=settings.OLLAMA_MODEL,
        messages=messages
    )
    return resp["message"]["content"] or ""


async def _stream_ollama(prompt: str, history: List[Dict]):
    import ollama
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": prompt})
    stream = ollama.chat(
        model=settings.OLLAMA_MODEL,
        messages=messages,
        stream=True
    )
    for chunk in stream:
        text = chunk["message"]["content"]
        if text:
            yield f"data: {json.dumps({'type': 'text', 'data': text})}\n\n"


# ── Anthropic Claude (paid, fallback) ────────────────────────

def _chat_anthropic(prompt: str, history: List[Dict]) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    messages = []
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": prompt})
    resp = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=settings.MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages
    )
    return resp.content[0].text if resp.content else ""


async def _stream_anthropic(prompt: str, history: List[Dict]):
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    messages = []
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": prompt})
    with client.messages.stream(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=settings.MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {json.dumps({'type': 'text', 'data': text})}\n\n"


# ── Provider router ───────────────────────────────────────────

CHAT_FN = {
    "groq":      _chat_groq,
    "gemini":    _chat_gemini,
    "ollama":    _chat_ollama,
    "anthropic": _chat_anthropic,
}

STREAM_FN = {
    "groq":      _stream_groq,
    "gemini":    _stream_gemini,
    "ollama":    _stream_ollama,
    "anthropic": _stream_anthropic,
}


# ── Public API ────────────────────────────────────────────────

def chat(query: str, history: List[Dict] = None) -> Dict:
    """Non-streaming chat — returns full answer + sources + emergency info."""
    emergency = detect_emergency(query)
    docs = retriever.retrieve(query)
    prompt = build_prompt(query, docs)

    fn = CHAT_FN.get(settings.LLM_PROVIDER)
    if not fn:
        raise ProviderError(
            f"Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}'. "
            f"Choose: groq, gemini, ollama, anthropic"
        )

    try:
        answer = fn(prompt, history or [])
    except ProviderError:
        raise
    except Exception as e:
        logger.error("LLM call failed (%s): %s", settings.LLM_PROVIDER, e)
        raise ProviderError(f"LLM provider '{settings.LLM_PROVIDER}' failed: {e}") from e

    sources = list({(d["source"], d["category"]) for d in docs})

    return {
        "answer": answer + (get_disclaimer() if is_advice_query(query) else ""),
        "sources": [{"name": s[0], "category": s[1]} for s in sources[:3]],
        "emergency": emergency,
        "model": settings.LLM_PROVIDER,
        "docs_retrieved": len(docs),
    }


async def stream_chat(query: str, history: List[Dict] = None) -> AsyncIterator[str]:
    """Streaming chat — yields SSE chunks."""
    emergency = detect_emergency(query)
    if emergency:
        yield f"data: {json.dumps({'type': 'emergency', 'data': emergency})}\n\n"

    docs = retriever.retrieve(query)
    sources = list({(d["source"], d["category"]) for d in docs})
    yield f"data: {json.dumps({'type': 'sources', 'data': [{'name': s[0], 'category': s[1]} for s in sources[:3]]})}\n\n"

    prompt = build_prompt(query, docs)
    fn = STREAM_FN.get(settings.LLM_PROVIDER)
    if not fn:
        raise ProviderError(
            f"Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}'"
        )

    try:
        async for chunk in fn(prompt, history or []):
            yield chunk
    except ProviderError:
        raise
    except Exception as e:
        logger.error("LLM stream failed (%s): %s", settings.LLM_PROVIDER, e)
        raise ProviderError(f"LLM stream failed: {e}") from e

    if is_advice_query(query):
        yield f"data: {json.dumps({'type': 'text', 'data': get_disclaimer()})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
