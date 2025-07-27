"""
Enhanced AgentState for Iterative Planner (v2)
Tracks conversation history, accumulated chunks, critique cycles, and planner decisions
"""

from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict, NotRequired
from datetime import datetime

from .models.metadata import (
    StandardizedMetadata, 
    ProgressiveStats, 
    ConversationEntry, 
    CritiqueResult, 
    UserClarificationRequest
)


class RetrievalChunk(TypedDict):
    """Individual chunk retrieved from any retrieval method"""
    chunk_id: str
    text: str
    score: float
    source: str  # "cypher", "rag", "hybrid"
    metadata: Dict[str, Any]
    retrieved_at: str  # timestamp


class PlannerDecision(TypedDict):
    """Single decision made by the planner"""
    decision_type: str  # "mode_selection", "metadata_discovery", "query_refinement", "completion"
    decision: str
    reasoning: str
    timestamp: str
    iteration: int


class AgentStateV2(TypedDict, total=False):
    """
    Enhanced state for the Iterative Planner system.
    Maintains complete history and context for intelligent planning decisions.
    """
    
    # === Core Query Info ===
    query_raw: str                                  # Original user query
    query_processed: Optional[str]                  # Processed/cleaned query
    current_query: Optional[str]                    # Current iteration's query (may be refined)
    
    # === Planning & Metadata ===
    plan: Optional[Dict[str, Any]]                  # Current plan from planner
    plan_metadata: StandardizedMetadata             # Structured metadata following standard model
    metadata_locked: bool                          # Whether metadata discovery is complete
    
    # === Mode & Routing ===
    planner_mode: Optional[str]                     # "semantic" or "structured"
    route: Optional[str]                           # Current route: "cypher", "rag", "hybrid"
    fallback_routes: List[str]                     # Backup routes if current fails
    attempted_routes_current_iteration: List[str]  # Routes tried in current iteration
    
    # === Iterative State ===
    iteration_count: int                           # Current iteration number
    max_iterations: int                            # Maximum allowed iterations
    is_complete: bool                              # Whether planner considers task complete
    completion_reason: Optional[str]               # Why the planner completed
    
    # === Retrieval & Content ===
    accumulated_chunks: List[RetrievalChunk]       # All chunks retrieved across iterations
    current_skip: int                              # For pagination in retrieval
    batch_size: int                                # Chunks to retrieve per iteration
    max_total_chunks: int                          # Maximum total chunks allowed
    
    # === Synthesis & Critique ===
    synthesis_history: List[str]                   # All synthesis attempts
    last_synthesis: Optional[str]                  # Most recent synthesis
    critique_history: List[CritiqueResult]         # All critique results
    last_critique: Optional[CritiqueResult]        # Most recent critique
    
    # === Conversation & Clarification ===
    conversation_history: List[ConversationEntry]  # Full conversation history
    pending_clarification: Optional[UserClarificationRequest]  # Active clarification request
    clarification_responses: List[str]             # User responses to clarifications
    
    # === Decision Tracking ===
    planner_decisions: List[PlannerDecision]       # All decisions made by planner
    adaptive_refinements: List[str]                # Query refinements based on critique
    
    # === Performance & Stats ===
    progressive_stats: ProgressiveStats            # Performance tracking
    execution_time: float                          # Total execution time
    
    # === Final Output ===
    final_answer: Optional[str]                    # Final synthesized answer
    citations: List[str]                           # Source citations
    data_coverage_summary: Optional[str]           # Summary of data analyzed
    
    # === Error Handling ===
    error_messages: List[str]                      # Any errors encountered
    warnings: List[str]                            # Non-fatal warnings
    
    # === Debugging ===
    tools_used: List[str]                          # Track which tools/nodes were executed
    debug_info: NotRequired[Dict[str, Any]]        # Additional debug information


class AgentStateManager:
    """
    Helper class to manage AgentStateV2 operations
    """
    
    @staticmethod
    def create_initial_state(query: str) -> AgentStateV2:
        """Create a new initial state for a query"""
        timestamp = datetime.now().isoformat()
        
        return AgentStateV2(
            query_raw=query,
            query_processed=None,
            current_query=query,
            plan=None,
            plan_metadata={},
            metadata_locked=False,
            planner_mode=None,
            route=None,
            fallback_routes=[],
            attempted_routes_current_iteration=[],
            iteration_count=0,
            max_iterations=10,  # Default max iterations
            is_complete=False,
            completion_reason=None,
            accumulated_chunks=[],
            current_skip=0,
            batch_size=50,  # Default batch size
            max_total_chunks=500,  # Default max chunks
            synthesis_history=[],
            last_synthesis=None,
            critique_history=[],
            last_critique=None,
            conversation_history=[
                ConversationEntry(
                    role="user",
                    content=query,
                    timestamp=timestamp
                )
            ],
            pending_clarification=None,
            clarification_responses=[],
            planner_decisions=[],
            adaptive_refinements=[],
            progressive_stats=ProgressiveStats(
                chunks_processed=0,
                batches_processed=0,
                reading_complete=False,
                iterations_completed=0,
                max_chunks_reached=False,
                critique_cycles=0
            ),
            execution_time=0.0,
            final_answer=None,
            citations=[],
            data_coverage_summary=None,
            error_messages=[],
            warnings=[],
            tools_used=[]
        )
    
    @staticmethod
    def add_planner_decision(
        state: AgentStateV2, 
        decision_type: str, 
        decision: str, 
        reasoning: str
    ) -> None:
        """Add a planner decision to the state"""
        decision_entry = PlannerDecision(
            decision_type=decision_type,
            decision=decision,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat(),
            iteration=state["iteration_count"]
        )
        state["planner_decisions"].append(decision_entry)
    
    @staticmethod
    def add_retrieval_chunks(
        state: AgentStateV2, 
        chunks: List[Dict[str, Any]], 
        source: str
    ) -> None:
        """Add retrieved chunks to accumulated chunks"""
        timestamp = datetime.now().isoformat()
        
        for chunk in chunks:
            retrieval_chunk = RetrievalChunk(
                chunk_id=chunk.get("id", f"{source}_{len(state['accumulated_chunks'])}"),
                text=chunk.get("text", ""),
                score=chunk.get("score", 0.0),
                source=source,
                metadata=chunk.get("metadata", {}),
                retrieved_at=timestamp
            )
            state["accumulated_chunks"].append(retrieval_chunk)
        
        # Update stats
        state["progressive_stats"]["chunks_processed"] = len(state["accumulated_chunks"])
    
    @staticmethod
    def add_synthesis_and_critique(
        state: AgentStateV2, 
        synthesis: str, 
        critique: CritiqueResult
    ) -> None:
        """Add synthesis and critique results"""
        state["synthesis_history"].append(synthesis)
        state["last_synthesis"] = synthesis
        
        state["critique_history"].append(critique)
        state["last_critique"] = critique
        
        state["progressive_stats"]["critique_cycles"] += 1
    
    @staticmethod
    def mark_complete(
        state: AgentStateV2, 
        reason: str
    ) -> None:
        """Mark the agent state as complete"""
        state["is_complete"] = True
        state["completion_reason"] = reason
        state["progressive_stats"]["reading_complete"] = True
        state["progressive_stats"]["iterations_completed"] = state["iteration_count"]
    
    @staticmethod
    def increment_iteration(state: AgentStateV2) -> None:
        """Increment iteration count and update stats"""
        state["iteration_count"] += 1
        if state["iteration_count"] > 0:
            state["progressive_stats"]["batches_processed"] = state["iteration_count"]
        # Reset attempted routes for new iteration
        state["attempted_routes_current_iteration"] = []
    
    @staticmethod
    def is_at_limits(state: AgentStateV2) -> tuple[bool, str]:
        """Check if state has reached any limits"""
        if state["iteration_count"] >= state["max_iterations"]:
            return True, "Maximum iterations reached"
        
        if len(state["accumulated_chunks"]) >= state["max_total_chunks"]:
            state["progressive_stats"]["max_chunks_reached"] = True
            return True, "Maximum chunks reached"
        
        return False, ""
    
    @staticmethod
    def get_latest_chunks(state: AgentStateV2, n: int = 5) -> List[RetrievalChunk]:
        """Get the n most recently retrieved chunks"""
        return state["accumulated_chunks"][-n:] if state["accumulated_chunks"] else []
    
    @staticmethod
    def get_chunk_texts(state: AgentStateV2) -> List[str]:
        """Get all chunk texts for synthesis"""
        return [chunk["text"] for chunk in state["accumulated_chunks"]]