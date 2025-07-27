"""
Standardized Metadata Model for Enhanced Iterative Planner
Provides a single source of truth for metadata structure across all components
"""

from typing import List, Optional
from typing_extensions import TypedDict


class StandardizedMetadata(TypedDict, total=False):
    """
    A standardized metadata structure for the entire agent.
    All fields are optional to allow for progressive discovery.
    """
    companies: Optional[List[str]]
    years: Optional[List[int]]
    quarters: Optional[List[str]]
    doc_types: Optional[List[str]]
    regulatory_sections: Optional[List[str]]
    text_contains: Optional[List[str]]


class ProgressiveStats(TypedDict, total=False):
    """
    Statistics tracking for progressive retrieval loops
    """
    chunks_processed: int
    batches_processed: int
    reading_complete: bool
    iterations_completed: int
    max_chunks_reached: bool
    critique_cycles: int


class ConversationEntry(TypedDict):
    """
    Single entry in conversation history
    """
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str


class CritiqueResult(TypedDict):
    """
    Result from LLM critique of synthesis
    """
    is_complete: bool
    confidence_score: float
    missing_aspects: List[str]
    improvement_suggestions: List[str]
    synthesis_quality: str  # "poor", "fair", "good", "excellent"


class UserClarificationRequest(TypedDict):
    """
    Request for user clarification
    """
    question: str
    options: Optional[List[str]]
    context: str
    request_type: str  # "disambiguation", "confirmation", "additional_info"