"""
Healthcare RAG Bot - Vector Index Builder
Creates ChromaDB index from processed documents.
Run: python scripts/build_index.py
"""

import json
import os
import time
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

PROCESSED_DIR = Path("data/processed")
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
BATCH_SIZE = 200  # Larger batches for faster indexing with 50K+ docs


def build_index():
    print("=" * 60)
    print("Healthcare RAG Bot - Index Builder")
    print("=" * 60)

    # Load processed documents
    docs_path = PROCESSED_DIR / "all_documents.json"
    if not docs_path.exists():
        print("No processed documents found!")
        print("   Run: python scripts/process_data.py first")
        return

    print("Loading processed documents...")
    with open(docs_path, encoding="utf-8") as f:
        docs = json.load(f)

    print(f"   {len(docs)} documents loaded")

    # Setup ChromaDB + embeddings
    print("\nSetting up vector database...")
    print("   (First run downloads embedding model ~90MB — please wait)")

    import chromadb
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    # Uses onnxruntime (~30MB) — no torch/sentence-transformers needed
    embedding_fn = DefaultEmbeddingFunction()

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Delete existing collection to rebuild
    try:
        client.delete_collection("healthcare_docs")
        print("   Deleted old index")
    except Exception:
        pass

    collection = client.create_collection(
        name="healthcare_docs",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # Index in batches
    print(f"\nBuilding index in batches of {BATCH_SIZE}...")

    texts = [d["text"] for d in docs]
    ids = [f"doc_{i}" for i in range(len(docs))]
    metadatas = [
        {
            "source": d.get("source", "Unknown"),
            "category": d.get("category", "general"),
            "question": d.get("question", "")[:200]  # Truncate for metadata
        }
        for d in docs
    ]

    total_batches = (len(docs) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in tqdm(range(0, len(docs), BATCH_SIZE), total=total_batches, desc="Indexing"):
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_ids = ids[i:i + BATCH_SIZE]
        batch_meta = metadatas[i:i + BATCH_SIZE]

        collection.add(
            documents=batch_texts,
            ids=batch_ids,
            metadatas=batch_meta
        )
        time.sleep(0.05)  # Small delay to prevent memory spikes

    count = collection.count()
    print(f"\nIndex built successfully!")
    print(f"   Total documents indexed: {count}")
    print(f"   Database saved at: {CHROMA_PATH}")
    print("\nNext steps:")
    print("   1. Start backend:  cd backend && uvicorn api.main:app --reload")
    print("   2. Start frontend: cd frontend && npm run dev")
    print("=" * 60)


if __name__ == "__main__":
    build_index()
