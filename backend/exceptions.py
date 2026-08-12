"""
Custom exceptions for MediAssist.
Provides structured error handling across all modules.
"""


class HealthcareBotError(Exception):
    """Base exception for all healthcare bot errors."""
    pass


class RetrievalError(HealthcareBotError):
    """Raised when document retrieval fails."""
    pass


class ProviderError(HealthcareBotError):
    """Raised when the LLM provider fails or is misconfigured."""
    pass
