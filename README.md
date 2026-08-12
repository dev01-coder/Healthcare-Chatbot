# MediAssist — Healthcare RAG Chatbot

A production-ready, lightweight Healthcare RAG (Retrieval-Augmented Generation) chatbot
built to run on a laptop with limited resources (30GB space, 64-bit).

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Designed & Developed by Ozair Ilyas**

---

## Table of Contents

- [System Requirements](#system-requirements)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
  - [System Architecture](#system-architecture)
  - [Data Pipeline](#data-pipeline)
  - [Request Lifecycle](#request-lifecycle)
- [Key Design Decisions](#key-design-decisions)
- [Quick Start](#quick-start)
- [LLM Provider Options](#llm-provider-options)
- [Performance](#performance)
- [Security](#security)
- [Medical Disclaimer](#medical-disclaimer)

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.9+ | 3.12 |
| Node.js | 18+ | 20+ |
| RAM | 4 GB | 8 GB |
| Storage | ~5 GB | ~10 GB |
| OS | Windows 10/11 64-bit | Windows 11 |

---

## Project Structure

```
healthcare_bot/
│
├── backend/                          # FastAPI REST API
│   ├── config.py                     #   Centralized env-var configuration
│   ├── exceptions.py                 #   Custom exception hierarchy
│   ├── api/
│   │   └── main.py                   #   Routes, middleware, rate limiter
│   ├── pipeline/
│   │   └── rag_chain.py              #   LLM provider router + RAG prompt builder
│   ├── retrieval/
│   │   └── retriever.py              #   Hybrid search: ChromaDB vector + BM25 keyword
│   └── safety/
│       └── emergency.py              #   Emergency detection + medical disclaimers
│
├── scripts/                          # Offline data pipeline
│   ├── download_data.py              #   Fetch MedQuAD (47K Q&A) + sample data
│   ├── process_data.py               #   Clean, chunk, merge into JSON
│   └── build_index.py                #   Create ChromaDB vector index
│
├── frontend/                         # React + Vite + Tailwind CSS
│   └── src/
│       ├── App.jsx                   #   Main chat UI shell
│       ├── utils/api.js              #   API client with SSE streaming
│       └── components/
│           ├── ChatHeader.jsx        #     Header bar + settings
│           ├── ChatInput.jsx         #     Input field + autocomplete
│           ├── MessageList.jsx       #     Scrollable message container
│           ├── MessageBubble.jsx     #     Individual message renderer
│           ├── MessageActions.jsx    #     Copy / regenerate actions
│           ├── EmptyState.jsx        #     Hero screen (first question)
│           ├── EmergencyAlert.jsx    #     Emergency banner
│           ├── SourceBadges.jsx      #     Source citation chips
│           ├── NeuralBackground.jsx  #     Animated background
│           └── Toast.jsx             #     Toast notification system
│
├── tests/                            # 28 unit tests
│   ├── test_api.py                   #   API endpoint tests
│   ├── test_emergency.py             #   Emergency detection tests
│   └── test_retriever.py             #   Retrieval logic tests
│
├── .env.example                      # Environment config template
├── requirements.txt                  # Python dependencies
├── start_windows.bat                 # One-click Windows launcher
└── SETUP_GUIDE.md                    # Detailed setup walkthrough
```

---

## Architecture

### System Architecture

The diagram below shows the complete runtime architecture — from the user's browser
through the API, safety checks, retrieval pipeline, and LLM provider.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER  (Browser :5173)                              │
│                                                                            │
│   ┌────────────┐  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐   │
│   │ ChatInput  │  │ MessageList │  │ EmergencyAlert│  │ SourceBadges  │   │
│   │  ├─ input  │  │  ├─ Bubble  │  │  (banner)    │  │  (citations) │   │
│   │  └─ suggest│  │  └─ Actions │  └──────────────┘  └───────────────┘   │
│   └─────┬──────┘  └──────┬──────┘                                        │
│         └────────────────┴───────────┐                                    │
│                                     │                                     │
│              React + Tailwind CSS    │  Vite Dev Server                    │
└─────────────────────────────────────┼─────────────────────────────────────┘
                                      │
                          REST / SSE  │  (fetch + EventSource)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND  (uvicorn :8000)                        │
│                                                                            │
│   ┌──────────────┐  ┌──────────┐  ┌────────────────┐  ┌───────────────┐  │
│   │ Rate Limiter │  │   CORS   │  │ Exception      │  │ Lifespan      │  │
│   │ 30 req/min   │  │ middleware│  │ Handler        │  │ (startup)     │  │
│   └──────┬───────┘  └──────────┘  └────────────────┘  └───────────────┘  │
│          ▼                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                        RAG PIPELINE                                  │  │
│   │                                                                      │  │
│   │   ┌─────────────────┐                                                │  │
│   │   │ 1. Emergency    │  Regex pattern matching                       │  │
│   │   │    Detection    │  7 categories: cardiac, stroke, breathing,    │  │
│   │   │                 │  suicide, overdose, unconscious, bleeding     │  │
│   │   └────────┬────────┘                                                │  │
│   │            │                                                         │  │
│   │   ┌────────▼────────────────────────────────────────────────────┐    │  │
│   │   │ 2. Hybrid Retriever                                        │    │  │
│   │   │                                                            │    │  │
│   │   │   ┌─────────────┐         ┌──────────────────┐            │    │  │
│   │   │   │ Synonym     │         │ Query Expander    │            │    │  │
│   │   │   │ Expansion   │────────▶│ (40+ medical      │            │    │  │
│   │   │   │ (dict)      │         │  term mappings)   │            │    │  │
│   │   │   └─────────────┘         └────────┬─────────┘            │    │  │
│   │   │                                    │                       │    │  │
│   │   │                    ┌───────────────┼───────────────┐       │    │  │
│   │   │                    ▼               ▼               ▼       │    │  │
│   │   │          ┌──────────────┐ ┌────────────┐ ┌────────────┐   │    │  │
│   │   │          │  ChromaDB    │ │   BM25     │ │  (Future:  │   │    │  │
│   │   │          │  Vector      │ │  Keyword   │ │  Web/API)  │   │    │  │
│   │   │          │  Search      │ │  Search    │ │            │   │    │  │
│   │   │          │  (semantic)  │ │ (lexical)  │ │            │   │    │  │
│   │   │          └──────┬───────┘ └─────┬──────┘ └────────────┘   │    │  │
│   │   │                 └───────┬───────┘                          │    │  │
│   │   │                         ▼                                  │    │  │
│   │   │              ┌─────────────────────┐                      │    │  │
│   │   │              │  Reciprocal Rank    │                      │    │  │
│   │   │              │  Fusion (RRF)       │  k=60               │    │  │
│   │   │              │  Score Combiner     │                      │    │  │
│   │   │              └──────────┬──────────┘                      │    │  │
│   │   │                         │                                  │    │  │
│   │   │              ┌──────────▼──────────┐                      │    │  │
│   │   │              │  Score Threshold    │  min=0.002           │    │  │
│   │   │              │  Filter (top-k=8)   │                      │    │  │
│   │   │              └──────────┬──────────┘                      │    │  │
│   │   └─────────────────────────┼────────────────────────────────┘    │  │
│   │                             │                                      │  │
│   │   ┌─────────────────────────▼──────────────────────────────────┐  │  │
│   │   │ 3. Prompt Builder                                          │  │  │
│   │   │    System prompt + Retrieved context + User question        │  │  │
│   │   └─────────────────────────┬──────────────────────────────────┘  │  │
│   │                             │                                      │  │
│   │   ┌─────────────────────────▼──────────────────────────────────┐  │  │
│   │   │ 4. LLM Provider Router                                     │  │  │
│   │   │                                                            │  │  │
│   │   │    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐     │  │  │
│   │   │    │  Groq   │ │ Gemini  │ │ Ollama  │ │ Anthropic │     │  │  │
│   │   │    │  (free) │ │ (free)  │ │ (local) │ │  (paid)   │     │  │  │
│   │   │    └─────────┘ └─────────┘ └─────────┘ └───────────┘     │  │  │
│   │   │                                                            │  │  │
│   │   │    All providers support: sync + streaming (SSE)           │  │  │
│   │   └─────────────────────────┬──────────────────────────────────┘  │  │
│   │                             │                                      │  │
│   │   ┌─────────────────────────▼──────────────────────────────────┐  │  │
│   │   │ 5. Safety Layer                                             │  │  │
│   │   │    ├─ Emergency alert (if detected)                         │  │  │
│   │   │    ├─ Medical disclaimer (on advice queries)                │  │  │
│   │   │    └─ Scope check (decline billing/insurance questions)     │  │  │
│   │   └────────────────────────────────────────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │ STORAGE                                                          │  │
│   │   ├─ ChromaDB (data/chroma_db/)     27,229 vector embeddings    │  │
│   │   ├─ BM25 Index (in-memory)         30K docs capped             │  │
│   │   └─ all_documents.json (data/processed/)  source of truth      │  │
│   └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Pipeline

The offline pipeline downloads, processes, and indexes medical data before the
app can serve queries. Run once after setup.

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│                  │       │                  │       │                  │
│  download_data   │──────▶│  process_data    │──────▶│  build_index     │
│                  │       │                  │       │                  │
│  ─ HuggingFace   │       │  ─ Deduplicate   │       │  ─ Embed texts   │
│    MedQuAD       │       │  ─ Chunk (500w)  │       │    (MiniLM)      │
│    (47K Q&A)     │       │  ─ Merge JSON    │       │  ─ Store in      │
│  ─ Sample data   │       │  ─ Strip HTML    │       │    ChromaDB      │
│    (35 docs)     │       │  ─ Normalize     │       │  ─ Build BM25    │
│                  │       │                  │       │    in-memory     │
└──────────────────┘       └──────────────────┘       └──────────────────┘
       │                          │                          │
       ▼                          ▼                          ▼
  data/raw/                data/processed/             data/chroma_db/
  ├─ medquad.csv           └─ all_documents.json       └─ sqlite + parquet
  └─ sample_data/              (27,229 docs)             (vector index)
```

### Request Lifecycle

A single chat message flows through these steps:

```
User types "What are symptoms of diabetes?"
    │
    ▼
[1] Frontend sends POST /chat/stream  { message, history }
    │
    ▼
[2] Rate Limiter checks IP (30 req/min)
    │
    ▼
[3] Emergency Detection  →  No emergency found
    │
    ▼
[4] Query Expansion      →  "symptoms of diabetes" + "hyperglycemia blood sugar"
    │
    ▼
[5] Hybrid Retrieval
    ├─ ChromaDB vector search (top-8 semantic matches)
    └─ BM25 keyword search  (top-8 lexical matches)
    │
    ▼
[6] Reciprocal Rank Fusion  →  Combined + deduplicated ranked list
    │
    ▼
[7] Score Threshold Filter  →  6 relevant documents pass
    │
    ▼
[8] Prompt Builder
    ├─ System prompt (rules + scope)
    ├─ Retrieved context (6 docs with sources)
    └─ User question
    │
    ▼
[9] LLM Provider (Groq)  →  Streams answer token by token
    │
    ▼
[10] Safety Layer
    ├─ Advice query detected?  →  Yes  →  Append disclaimer
    └─ Emergency detected?     →  No   →  Skip
    │
    ▼
[11] SSE chunks sent to frontend:
     { type: "sources",  data: [...] }
     { type: "text",     data: "Symptoms include..." }
     { type: "text",     data: "..." }
     { type: "done" }
    │
    ▼
[12] Frontend renders answer with source badges
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Hybrid retrieval (vector + BM25)** | Vector search catches semantic meaning ("heart attack" ↔ "myocardial infarction"). BM25 catches exact medical terms and abbreviations. RRF combines both rankings without score normalization issues. |
| **Lazy initialization** | ChromaDB + BM25 index loads on first query, not at startup. Reduces cold-start from ~5s to ~0ms. |
| **Multi-provider LLM** | 4 providers (Groq, Gemini, Ollama, Anthropic) with a single `LLM_PROVIDER` env var. Groq is default — free tier with 14K req/day and fastest inference. |
| **SSE streaming** | First token appears in ~300ms instead of waiting for the full 2-3 sentence answer. Uses `text/event-stream` with JSON chunks. |
| **Emergency detection (regex)** | 7 life-threatening categories detected via compiled regex patterns. No LLM call needed — instant response with emergency resources. Runs before retrieval to ensure safety. |
| **Conditional disclaimer** | Medical disclaimer appended only on advice-seeking queries ("should I take...", "what treatment..."). Reduces noise on informational queries. |
| **Scope restriction** | System prompt explicitly declines billing, insurance, and administrative questions. Returns a helpful redirect message. |
| **30K BM25 cap** | BM25 index capped at 30K documents to stay under 4GB RAM. Vector search handles the full 27K+ docs via ChromaDB's optimized storage. |
| **Custom exception hierarchy** | `HealthcareBotError` → `ProviderError` / `RetrievalError`. FastAPI exception handler maps each to the correct HTTP status (502/503/500). |

---

## Quick Start

### Step 1: Install dependencies

```bash
# Python
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### Step 2: Configure API key

```bash
copy .env.example .env
# Edit .env and set your API key (Groq recommended — free)
```

### Step 3: Download and index data

```bash
python scripts/download_data.py    # ~2 min first run (47K Q&A from NIH)
python scripts/process_data.py     # ~30 sec
python scripts/build_index.py      # ~5 min (vector embeddings)
```

### Step 4: Start the app

```bash
# Terminal 1: Backend
uvicorn backend.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Step 5: Open browser

```
http://localhost:5173
```

---

## LLM Provider Options

| Provider | Free Limit | Speed | Quality | Internet? |
|----------|-----------|-------|---------|-----------|
| **Groq** | 14,400 req/day | Fastest | Very Good | Yes |
| **Gemini** | 1M tokens/day | Fast | Excellent | Yes |
| **Ollama** | Unlimited | Medium | Good | No (local) |
| **Anthropic** | Limited trial | Fast | Best | Yes |

Set `LLM_PROVIDER` in your `.env` file to switch between providers.

### Groq (Recommended)

```bash
# Get free key at: https://console.groq.com
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
```

### Google Gemini

```bash
# Get free key at: https://aistudio.google.com/apikey
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

### Ollama (Fully Offline)

```bash
# Install from: https://ollama.com
# Then run: ollama pull llama3.2
LLM_PROVIDER=ollama
```

### Anthropic Claude (Paid)

```bash
# Get key at: https://console.anthropic.com
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
```

---

## Performance

| Metric | Value |
|--------|-------|
| First token latency | ~300 ms (Groq) |
| Full answer (2-3 sentences) | ~1.5 s |
| Retrieval latency | ~80 ms (ChromaDB + BM25) |
| Index size (27K docs) | ~1.2 GB on disk |
| Peak RAM usage | ~3.5 GB |
| Concurrent connections | 30 req/min per IP (rate limited) |

---

## Security

| Measure | Implementation |
|---------|---------------|
| **Rate limiting** | 30 requests per minute per IP. Sliding window with automatic cleanup of stale entries. Returns HTTP 429. |
| **Input validation** | Pydantic models enforce `min_length=1`, `max_length=2000` on all chat inputs. |
| **CORS** | Whitelist: `localhost:5173`, `localhost:3000`, `localhost:5174`. Credentials and all methods allowed. |
| **Exception handling** | Custom `HealthcareBotError` hierarchy. Provider failures → 502, retrieval failures → 503, unknown → 500. No stack traces leaked. |
| **Emergency detection** | 7 life-threatening categories detected before LLM call. Instant response with emergency resources — no delay. |
| **API keys** | Stored in `.env` (gitignored). Never logged or exposed in API responses. |
| **No secrets in code** | `.env.example` contains placeholder values only. Real keys never committed. |

---

## Medical Disclaimer

This chatbot is for informational purposes only.
It is NOT a substitute for professional medical advice, diagnosis, or treatment.
Always consult a qualified healthcare provider.

---

**Designed & Developed by Ozair Ilyas** · [MIT License](LICENSE)
