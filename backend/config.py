"""
Centralized configuration for MediAssist.
Loads environment variables once and validates them.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _int_env(key: str, default: int) -> int:
    """Read an integer environment variable with validation."""
    val = os.getenv(key, str(default))
    try:
        return int(val)
    except (ValueError, TypeError):
        logger.warning("Invalid %s=%r, using default %d", key, val, default)
        return default


class Settings:
    """Application settings loaded from environment variables."""

    # ── LLM Provider ─────────────────────────────
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").lower()
    MAX_TOKENS: int = _int_env("MAX_TOKENS", 1024)

    # ── Groq ─────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

    # ── Gemini ───────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    # ── Ollama ───────────────────────────────────
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

    # ── Anthropic ────────────────────────────────
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    # ── Retrieval ────────────────────────────────
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    TOP_K_RESULTS: int = _int_env("TOP_K_RESULTS", 8)

    # ── Server ───────────────────────────────────
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = _int_env("BACKEND_PORT", 8000)
    VITE_API_URL: str = os.getenv("VITE_API_URL", "http://localhost:8000")

    def validate(self) -> list[str]:
        """
        Validate configuration and return list of warnings.
        Does not raise — allows degraded mode with warnings.
        """
        warnings = []

        provider_keys = {
            "groq": ("GROQ_API_KEY", self.GROQ_API_KEY),
            "gemini": ("GEMINI_API_KEY", self.GEMINI_API_KEY),
            "ollama": (None, None),
            "anthropic": ("ANTHROPIC_API_KEY", self.ANTHROPIC_API_KEY),
        }

        if self.LLM_PROVIDER not in provider_keys:
            warnings.append(
                f"Unknown LLM_PROVIDER '{self.LLM_PROVIDER}'. "
                f"Valid options: {', '.join(provider_keys.keys())}"
            )
        elif self.LLM_PROVIDER != "ollama":
            key_name, key_value = provider_keys[self.LLM_PROVIDER]
            if not key_value or key_value.startswith("your_"):
                warnings.append(
                    f"{key_name} is not set. "
                    f"Get a free key at the provider's console website."
                )

        chroma_path = Path(self.CHROMA_DB_PATH)
        if not chroma_path.exists():
            warnings.append(
                f"ChromaDB not found at {self.CHROMA_DB_PATH}. "
                f"Run: python scripts/build_index.py"
            )

        return warnings

    def log_config(self):
        """Log current configuration (without exposing API keys)."""
        logger.info(f"LLM Provider: {self.LLM_PROVIDER}")
        logger.info(f"ChromaDB Path: {self.CHROMA_DB_PATH}")
        logger.info(f"Top-K Results: {self.TOP_K_RESULTS}")
        logger.info(f"Max Tokens: {self.MAX_TOKENS}")

        if self.LLM_PROVIDER == "groq":
            logger.info(f"Groq Model: {self.GROQ_MODEL}")
        elif self.LLM_PROVIDER == "gemini":
            logger.info(f"Gemini Model: {self.GEMINI_MODEL}")
        elif self.LLM_PROVIDER == "ollama":
            logger.info(f"Ollama Model: {self.OLLAMA_MODEL}")
        elif self.LLM_PROVIDER == "anthropic":
            logger.info(f"Anthropic Model: {self.ANTHROPIC_MODEL}")


# Singleton
settings = Settings()
