"""
LangGraph State Definition for SEC Query Reasoning Agent
Based on specifications from langrgaph_agent_readme
"""

from typing_extensions import TypedDict, NotRequired, Literal, List, Dict, Any

class RetrievalHit(TypedDict):
    """Individual retrieval result from any source"""
    section_id: str
    text: str
    score: float
    source: Literal["cypher", "hybrid", "rag"]
    metadata: NotRequired[Dict[str, Any]]

class SubTask(TypedDict):
    """Sub-task for multi-topic queries"""
    topic: str
    metadata: Dict[str, Any]
    suggested_route: Literal["cypher", "hybrid", "rag"]

class AgentState(TypedDict, total=False):
    """
    Complete state for SEC Graph LangGraph Agent
    Tracks all information across the routing state machine
    """
    
    # === Input & Planning ===
    query_raw: str                          # Original user query
    metadata: Dict[str, Any]                # Extracted {company, year, quarter, doc_type}
    route: str                              # Current route: "cypher", "hybrid", "rag", "multi"
    fallback: List[str]                     # Ordered list of backup routes
    sub_tasks: List[SubTask]                # For multi-topic queries
    
    # === Retrieval Results ===
    retrievals: List[RetrievalHit]          # Current retrieval results
    valid: bool                             # Whether current retrievals pass validation
    
    # === Multi-topic Processing ===
    sub_summaries: List[str]                # List of text answers (one per sub-task)
    
    # === Final Output ===
    final_answer: str                       # Single-topic synthesized answer
    master_answer: str                      # Multi-topic aggregated answer
    citations: List[str]                    # Source citations
    
    # === Debugging & Tracing ===
    tools_used: NotRequired[List[str]]      # Track which nodes were executed
    confidence_scores: NotRequired[Dict[str, float]]  # Quality scores by node
    error_messages: NotRequired[List[str]]  # Any errors encountered