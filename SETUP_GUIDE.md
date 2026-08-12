# MediAssist — Complete Setup Guide (Windows Laptop)

## Prerequisites

### 1. Python 3.11 (64-bit)
- Download: https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
- During install: CHECK "Add Python to PATH"

### 2. Node.js 20 LTS
- Download: https://nodejs.org/dist/v20.17.0/node-v20.17.0-x64.msi
- Install with default settings

### 3. LLM API Key (choose one)

| Provider | Free? | Sign Up URL | Key Prefix |
|---|---|---|---|
| Groq (Recommended) | Yes, 14,400 req/day | https://console.groq.com | `gsk_` |
| Google Gemini | Yes, 1M tokens/day | https://aistudio.google.com/apikey | `AI` |
| Ollama | Yes, unlimited, offline | https://ollama.com | None needed |
| Anthropic | Limited trial | https://console.anthropic.com | `sk-ant-` |

---

## Installation Steps

### Step 1: Extract the ZIP

Extract `healthcare_bot.zip` to a folder like `C:\Projects\healthcare_bot`

### Step 2: Open Command Prompt

```bash
cd C:\Projects\healthcare_bot
```

### Step 3: Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal.

### Step 4: Install Python packages

```bash
pip install -r requirements.txt
```

Takes 3-5 minutes on first run.

### Step 5: Configure your API key

```bash
copy .env.example .env
notepad .env
```

Set your chosen provider in `.env`:

**Option A — Groq (fastest, recommended):**
```
LLM_PROVIDER=groq
GROQ_API_KEY=paste_your_key_here
```

**Option B — Gemini:**
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=paste_your_key_here
```

**Option C — Ollama (fully offline):**
```
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

**Option D — Anthropic:**
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=paste_your_key_here
```

### Step 6: Download datasets

```bash
python scripts/download_data.py
```

### Step 7: Process data

```bash
python scripts/process_data.py
```

### Step 8: Build the vector index

```bash
python scripts/build_index.py
```

First time downloads the embedding model (~90MB). Takes 2-4 minutes.

### Step 9: Install frontend packages

```bash
cd frontend
npm install
cd ..
```

---

## Running the App

You need TWO terminal windows open at the same time.

### Terminal 1 — Backend

```bash
venv\Scripts\activate
uvicorn backend.api.main:app --reload --port 8000
```

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

### Then open:

```
http://localhost:5173
```

---

## Disk Space

| Component | Size |
|---|---|
| Python venv | ~1.5 GB |
| Embedding model | ~90 MB |
| Vector database | ~50 MB |
| Downloaded datasets | ~50 MB |
| Node modules | ~200 MB |
| **Total** | **~2 GB** |

---

## Troubleshooting

### "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

### "Collection not found" or vector DB errors

```bash
python scripts/build_index.py
```

### Frontend shows "Backend not reachable"

- Make sure the backend terminal is running
- Check: http://localhost:8000/health
- Check that `VITE_API_URL` in `frontend/.env` matches your backend URL

### Slow responses

- Normal on first query (model loads into memory)
- Subsequent queries are faster
- Try Groq for fastest responses

### API key error

- Check your `.env` file has the correct key
- Make sure `LLM_PROVIDER` matches the key you set
- Groq keys start with `gsk_`, Anthropic keys with `sk-ant-`

### Corrupted ZIP extraction

If you see a `{backend/` directory, delete it:
```bash
rmdir /s /q "{backend"
```

### Port already in use

```bash
# Find process on port 8000
netstat -ano | findstr :8000
# Kill it (replace PID)
taskkill /PID <PID> /F
```

---

## Adding More Medical Data

1. Put PDF or CSV files in `data/raw/`
2. Edit `scripts/process_data.py` to load them
3. Run `python scripts/process_data.py`
4. Run `python scripts/build_index.py`

---

## Quick Start (After First Setup)

Every time you want to run the app:

```bash
# Terminal 1
venv\Scripts\activate
uvicorn backend.api.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Then go to http://localhost:5173
