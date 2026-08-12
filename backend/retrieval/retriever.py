"""
Healthcare RAG - Hybrid Retrieval Engine
Combines vector (semantic) search + BM25 (keyword) search
using Reciprocal Rank Fusion (RRF) for score combination.
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict

from backend.config import settings
from backend.exceptions import RetrievalError

logger = logging.getLogger(__name__)

# Medical synonym expansion dictionary
MEDICAL_SYNONYMS = {
    "heart attack": "myocardial infarction cardiac arrest",
    "high blood pressure": "hypertension elevated bp",
    "low blood pressure": "hypotension",
    "sugar": "diabetes glucose blood sugar",
    "bp": "blood pressure hypertension",
    "tb": "tuberculosis",
    "fit": "seizure epilepsy convulsion",
    "stroke": "cerebrovascular accident brain attack",
    "kidney": "renal nephrology",
    "liver": "hepatic hepatitis",
    "stomach": "gastric gastrointestinal abdomen",
    "fever": "pyrexia high temperature",
    "cold": "upper respiratory infection rhinitis",
    "flu": "influenza viral fever",
    "cancer": "malignancy tumor oncology carcinoma",
    "pain killer": "analgesic painkiller nsaid",
    "allergy": "allergic reaction hypersensitivity",
    "mental health": "psychiatry psychology depression anxiety",
    "stress": "anxiety depression mental health",
    "chest hurt": "chest pain angina",
    "head hurt": "headache migraine cephalgia",
    "throw up": "vomit emesis nausea",
    "throwing up": "vomiting emesis",
    "runny nose": "rhinorrhea nasal discharge",
    "skin rash": "dermatitis eczema eruption",
    "ear pain": "otalgia earache",
    "eye pain": "ophthalmalgia ocular pain",
    "back pain": "lumbago dorsalgia backache",
    "joint pain": "arthralgia",
    "muscle pain": "myalgia",
    "can't sleep": "insomnia sleep disorder",
    "heart burn": "GERD acid reflux pyrosis",
    "dizzy": "vertigo lightheadedness dizziness",
    "swollen": "edema inflammation swelling",
    "bleeding": "hemorrhage blood loss",
    "infection": "sepsis contagion pathogen",
    "antibiotic": "antimicrobial antibacterial",
    "vitamin": "supplement nutrient",
    "diabetes": "hyperglycemia blood sugar",
    "sore throat": "pharyngitis tonsillitis",
    "cough": "tussis expectoration",
    "weight loss": "cachexia emaciation",
    "weight gain": "obesity overweight",
    "anxiety": "nervousness worry panic",
    "depression": "major depressive disorder sadness",
    "rash": "exanthem dermatitis",
    "vomiting": "emesis puking",
    "diarrhea": "loose stools gastroenteritis",
    "constipation": "obstipation infrequent stools",
    "fatigue": "tiredness exhaustion lethargy",
    "shortness of breath": "dyspnea breathlessness",
    "chest pain": "angina thoracalgia",
    "abdominal pain": "stomach ache belly pain",
    "numbness": "paresthesia tingling",
    "weakness": "asthenia frailty",
    "swelling": "edema tumefaction",
    "itching": "pruritus",
    "burning": "causalgia stinging",
    "blurred vision": "visual impairment",
    "ringing in ears": "tinnitus",
}

# Pattern for splitting medical text into tokens
_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*")

# RRF constant (higher k = less weight on rank)
_RRF_K = 60


def tokenize(text: str) -> List[str]:
    """
    Tokenize text for BM25. Handles medical terms with hyphens
    (e.g., "co-morbidity", "β-blocker") better than plain .split().
    """
    return [t.lower() for t in _TOKEN_PATTERN.findall(text)]


def expand_query(query: str) -> str:
    """Expand medical query with synonyms for better retrieval."""
    expanded = query
    query_lower = query.lower()

    for term, expansion in MEDICAL_SYNONYMS.items():
        if term in query_lower:
            expanded += " " + expansion

    return expanded


def _reciprocal_rank_fusion(result_lists: List[List[Dict]], k: int = _RRF_K) -> List[Dict]:
    """
    Combine multiple ranked result lists using Reciprocal Rank Fusion.
    
    RRF score = sum(1 / (k + rank_i)) for each list where doc appears.
    k=60 is the standard constant from the original RRF paper.
    """
    doc_scores: Dict[str, float] = {}
    doc_data: Dict[str, Dict] = {}

    for result_list in result_lists:
        for rank, doc in enumerate(result_list, start=1):
            # Use first 100 chars as dedup key
            key = doc["text"][:100]
            rrf_score = 1.0 / (k + rank)

            if key in doc_scores:
                doc_scores[key] += rrf_score
            else:
                doc_scores[key] = rrf_score
                doc_data[key] = doc

    # Sort by fused RRF score
    sorted_keys = sorted(doc_scores.keys(), key=lambda k: doc_scores[k], reverse=True)

    results = []
    for key in sorted_keys:
        doc = doc_data[key].copy()
        doc["score"] = doc_scores[key]
        results.append(doc)

    return results


class HealthcareRetriever:
    """Hybrid retriever combining ChromaDB + BM25."""

    def __init__(self):
        self._chroma_client = None
        self._collection = None
        self._bm25 = None
        self._all_docs = None
        self._initialized = False

    def _init(self):
        """Lazy initialization to avoid slow startup."""
        if self._initialized:
            return

        try:
            import chromadb
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            embedding_fn = DefaultEmbeddingFunction()

            self._chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
            self._collection = self._chroma_client.get_collection(
                name="healthcare_docs",
                embedding_function=embedding_fn
            )

            self._init_bm25()
            self._initialized = True
            logger.info(
                "Retriever initialized: %d documents loaded",
                self._collection.count()
            )

        except Exception as e:
            logger.error("Retriever init failed: %s", e)
            raise RetrievalError(
                f"Failed to initialize retriever: {e}. "
                "Run: python scripts/build_index.py"
            ) from e

    def _init_bm25(self):
        """Initialize BM25 index from processed documents."""
        from rank_bm25 import BM25Okapi

        docs_path = Path(__file__).parent.parent.parent / "data" / "processed" / "all_documents.json"
        if not docs_path.exists():
            logger.warning("all_documents.json not found — BM25 disabled")
            return

        with open(docs_path, encoding="utf-8") as f:
            all_docs = json.load(f)

        # Cap BM25 at 30K docs to save memory (vector search handles the rest)
        MAX_BM25_DOCS = 30000
        if len(all_docs) > MAX_BM25_DOCS:
            logger.info("Capping BM25 to %d docs (total: %d)", MAX_BM25_DOCS, len(all_docs))
            all_docs = all_docs[:MAX_BM25_DOCS]

        self._all_docs = all_docs
        tokenized = [tokenize(doc["text"]) for doc in self._all_docs]
        self._bm25 = BM25Okapi(tokenized)
        logger.info("BM25 index built: %d documents", len(self._all_docs))

    def _vector_search(self, query: str, n: int) -> List[Dict]:
        """Search using semantic embeddings."""
        results = self._collection.query(
            query_texts=[query],
            n_results=min(n, self._collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        docs = []
        for text, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            docs.append({
                "text": text,
                "source": meta.get("source", "Unknown"),
                "category": meta.get("category", "general"),
                "method": "vector"
            })

        return docs

    def _bm25_search(self, query: str, n: int) -> List[Dict]:
        """Search using BM25 keyword matching."""
        if not self._bm25 or not self._all_docs:
            return []

        tokenized_query = tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]

        docs = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = self._all_docs[idx]
                docs.append({
                    "text": doc["text"],
                    "source": doc.get("source", "Unknown"),
                    "category": doc.get("category", "general"),
                    "method": "bm25"
                })

        return docs

    def retrieve(self, query: str, n: int = None) -> List[Dict]:
        """
        Main retrieval function using hybrid search with RRF.
        Returns top-k most relevant documents above score threshold.
        """
        self._init()
        n = n if n is not None else settings.TOP_K_RESULTS

        expanded_query = expand_query(query)

        vector_results = self._vector_search(expanded_query, n=n)
        bm25_results = self._bm25_search(expanded_query, n=n)

        # Use Reciprocal Rank Fusion instead of naive score concatenation
        combined = _reciprocal_rank_fusion([vector_results, bm25_results])

        # Filter out low-relevance results (score threshold)
        MIN_SCORE = 0.002
        filtered = [d for d in combined if d.get("score", 0) >= MIN_SCORE]

        logger.debug(
            "Retrieved %d docs (vector=%d, bm25=%d, after filter=%d) for query: %s",
            len(filtered[:n]), len(vector_results), len(bm25_results), len(filtered), query[:80]
        )

        return filtered[:n]

    def get_stats(self) -> Dict:
        """Return index statistics."""
        self._init()
        return {
            "total_documents": self._collection.count(),
            "db_path": settings.CHROMA_DB_PATH,
            "model": "all-MiniLM-L6-v2"
        }


# Singleton instance
retriever = HealthcareRetriever()
