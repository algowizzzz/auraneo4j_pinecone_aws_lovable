"""
SimpleChatPlanner - Enhanced Iterative Planner (Main Orchestrator)
Implements the core logic from the sprint plan for intelligent, adaptive query processing
"""

import logging
import time
from typing import Dict, Any, List

from ..state_v2 import AgentStateV2, AgentStateManager
from ..models.metadata import StandardizedMetadata, CritiqueResult
from ..utils.llm_helpers import (
    llm_extract_query_info,
    llm_synthesize,
    llm_critique,
    llm_generate_clarification,
    llm_refine_query,
    llm_detect_introspection,
    generate_data_inventory_response,
    generate_capabilities_response
)
from .retrieval_functions import (
    simplified_cypher,
    simplified_rag,
    simplified_hybrid,
    cypher_discover_metadata
)

logger = logging.getLogger(__name__)


class SimpleChatPlanner:
    """
    The Enhanced Iterative Planner - Central orchestrator for the entire agent.
    Manages iterative data discovery, adaptive retrieval, and user clarification loops.
    """
    
    def __init__(self):
        self.start_time = None
    
    def execute(self, state: AgentStateV2) -> AgentStateV2:
        """
        Main execution method - implements the complete iterative planning logic
        """
        self.start_time = time.time()
        logger.info(f"SimpleChatPlanner starting execution for query: {state['query_raw'][:100]}...")
        
        try:
            # Step 1: Check for introspection queries (short-circuit)
            if self._handle_introspection_query(state):
                return self._finalize_state(state)
            
            # Step 2: Initial query extraction and mode detection
            self._initial_extraction_and_mode_detection(state)
            
            # Step 3: Execute appropriate mode loop
            if state["planner_mode"] == "semantic":
                self._handle_semantic_mode(state)
            elif state["planner_mode"] == "structured":
                self._handle_structured_mode(state)
            else:
                # Fallback to semantic mode
                logger.warning("Unknown planner mode, defaulting to semantic")
                state["planner_mode"] = "semantic"
                self._handle_semantic_mode(state)
            
            # Step 4: Finalize and return
            return self._finalize_state(state)
            
        except Exception as e:
            logger.error(f"SimpleChatPlanner execution failed: {e}")
            state["error_messages"].append(f"Planner execution error: {str(e)}")
            AgentStateManager.mark_complete(state, f"Error: {str(e)}")
            return self._finalize_state(state)
    
    def _handle_introspection_query(self, state: AgentStateV2) -> bool:
        """
        Handle meta-queries about agent capabilities or data inventory
        Returns True if query was handled, False otherwise
        """
        if not llm_detect_introspection(state["query_raw"]):
            return False
        
        logger.info("Detected introspection query - short-circuiting to direct response")
        
        AgentStateManager.add_planner_decision(
            state, 
            "introspection_detection", 
            "introspection_query", 
            "Detected query about agent capabilities or data inventory"
        )
        
        query_lower = state["query_raw"].lower()
        
        # Determine sub-type of introspection query
        if any(kw in query_lower for kw in ['data', 'companies', 'years', 'documents', 'available']):
            response = generate_data_inventory_response()
        else:
            response = generate_capabilities_response()
        
        state["final_answer"] = response
        AgentStateManager.mark_complete(state, "Introspection query handled directly")
        
        return True
    
    def _initial_extraction_and_mode_detection(self, state: AgentStateV2) -> None:
        """
        Extract query information and detect planning mode (Semantic vs Structured)
        """
        logger.info("Performing initial query extraction and mode detection")
        
        # Extract structured information from query
        extraction_result = llm_extract_query_info(state["query_raw"])
        
        # Log extraction details
        AgentStateManager.add_planner_decision(
            state,
            "llm_extraction",
            f"extracted_entities",
            f"LLM extracted entities from query: companies={extraction_result.get('companies', [])}, years={extraction_result.get('years', [])}, quarters={extraction_result.get('quarters', [])}, doc_types={extraction_result.get('doc_types', [])}, regulatory_sections={extraction_result.get('regulatory_sections', [])}, text_contains={extraction_result.get('text_contains', [])}, intent={extraction_result.get('intent', 'unknown')}, reading_depth={extraction_result.get('reading_depth', 'normal')}"
        )
        
        # Convert to StandardizedMetadata format
        plan_metadata = StandardizedMetadata(
            companies=extraction_result.get("companies", []),
            years=extraction_result.get("years", []),
            quarters=extraction_result.get("quarters", []),
            doc_types=extraction_result.get("doc_types", []),
            regulatory_sections=extraction_result.get("regulatory_sections", []),
            text_contains=extraction_result.get("text_contains", [])
        )
        
        state["plan_metadata"] = plan_metadata
        
        # Mode detection logic
        has_entities = (
            plan_metadata.get("companies") or 
            plan_metadata.get("years") or 
            plan_metadata.get("regulatory_sections")
        )
        
        if has_entities:
            state["planner_mode"] = "structured"
            AgentStateManager.add_planner_decision(
                state,
                "mode_selection",
                "structured",
                f"Detected specific entities: {plan_metadata}"
            )
        else:
            state["planner_mode"] = "semantic"
            AgentStateManager.add_planner_decision(
                state,
                "mode_selection", 
                "semantic",
                "No specific entities detected, using broad semantic search"
            )
        
        # Set other plan parameters
        state["plan"] = {
            "reading_depth": extraction_result.get("reading_depth", "normal"),
            "max_chunks": self._determine_max_chunks(extraction_result.get("reading_depth", "normal")),
            "route": None  # Will be determined by mode-specific logic
        }
        
        logger.info(f"Mode detected: {state['planner_mode']}, Reading depth: {state['plan']['reading_depth']}")
    
    def _determine_max_chunks(self, reading_depth: str) -> int:
        """Determine maximum chunks based on reading depth"""
        depth_limits = {
            "quick": 100,
            "normal": 300,
            "deep": 500,
            "comprehensive": 800
        }
        return depth_limits.get(reading_depth, 300)
    
    def _handle_semantic_mode(self, state: AgentStateV2) -> None:
        """
        Handle semantic mode - progressive RAG expansion until satisfied
        """
        logger.info("Executing semantic mode - progressive RAG expansion")
        
        state["route"] = "rag"
        state["plan"]["route"] = "rag"
        
        AgentStateManager.add_planner_decision(
            state,
            "route_selection",
            "rag",
            "Semantic mode: using RAG for broad topic-based search"
        )
        
        # Progressive retrieval loop
        while not state["is_complete"] and not AgentStateManager.is_at_limits(state)[0]:
            AgentStateManager.increment_iteration(state)
            
            logger.info(f"Semantic mode iteration {state['iteration_count']}")
            
            # Determine batch size for this iteration (expanding search)
            current_skip = len(state["accumulated_chunks"])
            batch_size = min(state["batch_size"], state["plan"]["max_chunks"] - current_skip)
            
            # Log iteration details
            AgentStateManager.add_planner_decision(
                state,
                "iteration_control",
                f"semantic_iteration_{state['iteration_count']}",
                f"Starting semantic iteration {state['iteration_count']}. Current chunks: {current_skip}, Batch size: {batch_size}, Max chunks: {state['plan']['max_chunks']}"
            )
            
            if batch_size <= 0:
                AgentStateManager.add_planner_decision(
                    state,
                    "iteration_control",
                    "completion_by_max_chunks",
                    f"Reached maximum chunks limit in semantic mode ({current_skip}/{state['plan']['max_chunks']})"
                )
                AgentStateManager.mark_complete(state, "Reached maximum chunks in semantic mode")
                break
            
            # Track the current route as attempted (semantic mode uses rag)
            if "rag" not in state["attempted_routes_current_iteration"]:
                state["attempted_routes_current_iteration"].append("rag")
            
            # Retrieve batch
            chunks = simplified_rag(
                state["current_query"],
                state["plan_metadata"],
                limit=batch_size,
                skip=current_skip
            )
            
            if not chunks:
                # Try route fallback before giving up (semantic mode starts with rag)
                logger.info("RAG returned 0 chunks in semantic mode, trying fallback routes")
                # Temporarily set route to rag for fallback logic
                original_route = state["route"]
                state["route"] = "rag"
                chunks = self._try_route_fallback(state)
                
                if not chunks:
                    # All routes failed - generate helpful error message for semantic queries
                    state["route"] = original_route  # Restore original route
                    error_message = self._generate_semantic_availability_message(state["current_query"])
                    AgentStateManager.mark_complete(state, f"No semantic data found after trying all routes: {error_message}")
                    
                    # Provide a helpful response instead of empty answer
                    if not state.get("final_answer"):
                        state["final_answer"] = error_message
                    break
                # If fallback succeeded, chunks now contains results, continue with processing
            
            # Add to accumulated chunks (use actual route that succeeded)
            AgentStateManager.add_retrieval_chunks(state, chunks, state["route"])
            
            # Synthesize and critique
            self._synthesize_and_critique(state)
            
            # Check if critique indicates completion
            if state["last_critique"] and state["last_critique"]["is_complete"]:
                AgentStateManager.mark_complete(state, "Critique indicates sufficient coverage")
                break
        
        # Handle completion cases
        at_limits, limit_reason = AgentStateManager.is_at_limits(state)
        if at_limits and not state["is_complete"]:
            AgentStateManager.mark_complete(state, limit_reason)
    
    def _handle_structured_mode(self, state: AgentStateV2) -> None:
        """
        Handle structured mode - metadata discovery followed by progressive retrieval
        """
        logger.info("Executing structured mode - metadata discovery + progressive retrieval")
        
        # Phase 1: Iterative Metadata Discovery
        if not state["metadata_locked"]:
            self._iterative_metadata_discovery(state)
        
        # If we have a pending clarification, pause here
        if state["pending_clarification"]:
            logger.info("Metadata discovery requires user clarification - pausing execution")
            return
        
        # Phase 2: Progressive Retrieval with Adaptive Refinement
        self._progressive_retrieval(state)
    
    def _iterative_metadata_discovery(self, state: AgentStateV2) -> None:
        """
        Use Cypher to explore and lock down the correct documents
        """
        logger.info("Starting iterative metadata discovery")
        
        plan_metadata = state["plan_metadata"]
        
        # Discovery sequence: companies -> years -> quarters -> sections
        discoveries = {}
        
        # Discover available companies if we have partial company info
        if plan_metadata.get("companies"):
            primary_company = plan_metadata["companies"][0]
            available_years = cypher_discover_metadata(
                company=primary_company,
                discovery_type="years"
            )
            
            if available_years:
                discoveries["years"] = available_years
                
                # If we don't have years specified, this could be ambiguous
                if not plan_metadata.get("years"):
                    if len(available_years) > 3:  # Many years available
                        self._request_clarification(
                            state,
                            f"I found data for {primary_company} across multiple years: {available_years[:5]}...",
                            f"Multiple years available: {available_years}",
                            "Please specify which year(s) you're interested in, or I can analyze the most recent data."
                        )
                        return
                    else:
                        # Use most recent years automatically
                        recent_years = sorted(available_years, reverse=True)[:2]
                        plan_metadata["years"] = recent_years
                        logger.info(f"Auto-selected recent years: {recent_years}")
        
        # Discover sections if we have company and year
        if plan_metadata.get("companies") and plan_metadata.get("years"):
            primary_company = plan_metadata["companies"][0]
            primary_year = plan_metadata["years"][0]
            
            available_sections = cypher_discover_metadata(
                company=primary_company,
                year=primary_year,
                discovery_type="sections"
            )
            
            if available_sections:
                discoveries["sections"] = available_sections
        
        # Update state with discoveries
        state["plan_metadata"] = plan_metadata
        state["metadata_locked"] = True
        
        AgentStateManager.add_planner_decision(
            state,
            "metadata_discovery",
            f"locked_metadata",
            f"Completed metadata discovery: {discoveries}"
        )
        
        logger.info(f"Metadata discovery complete: {discoveries}")
    
    def _request_clarification(self, state: AgentStateV2, context: str, ambiguity: str, question: str) -> None:
        """
        Request clarification from user
        """
        clarification = llm_generate_clarification(context, ambiguity)
        clarification["question"] = question  # Override with our specific question
        
        state["pending_clarification"] = clarification
        
        AgentStateManager.add_planner_decision(
            state,
            "clarification_request",
            "pending_user_input",
            f"Requested clarification: {clarification['question']}"
        )
        
        logger.info(f"Requested user clarification: {clarification['question']}")
    
    def _progressive_retrieval(self, state: AgentStateV2) -> None:
        """
        Progressive retrieval with critique-driven adaptive refinement
        """
        logger.info("Starting progressive retrieval phase")
        
        # Determine best route for structured queries
        if state["plan_metadata"].get("regulatory_sections"):
            state["route"] = "hybrid"  # Sections need semantic + structural
        elif state["plan_metadata"].get("companies"):
            # RAG works best for all company queries with our current data structure
            state["route"] = "rag"  # Company queries work best with RAG
        else:
            state["route"] = "hybrid"  # Fallback to hybrid
        
        state["plan"]["route"] = state["route"]
        
        AgentStateManager.add_planner_decision(
            state,
            "route_selection",
            state["route"],
            f"Selected route for structured retrieval based on metadata: {state['plan_metadata']}"
        )
        
        # Progressive retrieval loop
        while not state["is_complete"] and not AgentStateManager.is_at_limits(state)[0]:
            AgentStateManager.increment_iteration(state)
            
            logger.info(f"Progressive retrieval iteration {state['iteration_count']}")
            
            # Retrieve batch using selected route
            batch_size = state["batch_size"]
            current_skip = state["current_skip"]
            
            # Track the current route as attempted
            if state["route"] not in state["attempted_routes_current_iteration"]:
                state["attempted_routes_current_iteration"].append(state["route"])
            
            if state["route"] == "cypher":
                chunks = simplified_cypher(
                    state["current_query"],
                    state["plan_metadata"],
                    limit=batch_size,
                    skip=current_skip
                )
            elif state["route"] == "rag":
                chunks = simplified_rag(
                    state["current_query"],
                    state["plan_metadata"],
                    limit=batch_size,
                    skip=current_skip
                )
            else:  # hybrid
                chunks = simplified_hybrid(
                    state["current_query"],
                    state["plan_metadata"],
                    limit=batch_size,
                    skip=current_skip
                )
            
            if not chunks:
                # Try route fallback before giving up
                logger.info(f"Route {state['route']} returned 0 chunks, trying fallback routes")
                
                # Log initial route failure
                AgentStateManager.add_planner_decision(
                    state,
                    "retrieval_execution",
                    f"route_failure_{state['route']}",
                    f"Route {state['route']} returned 0 chunks with query: '{state['current_query']}' and metadata: {state['plan_metadata']}. Attempting fallback routes."
                )
                
                chunks = self._try_route_fallback(state)
                
                if not chunks:
                    # All routes failed - generate helpful error message
                    metadata = state["plan_metadata"]
                    error_message = self._generate_data_availability_message(metadata, state["current_query"])
                    
                    # Log complete failure
                    AgentStateManager.add_planner_decision(
                        state,
                        "retrieval_execution",
                        "all_routes_failed",
                        f"All retrieval routes failed. Attempted routes: {state.get('attempted_routes_current_iteration', [])}. No data found for query: '{state['current_query']}'"
                    )
                    
                    AgentStateManager.mark_complete(state, f"No data found after trying all routes: {error_message}")
                    
                    # Provide a helpful response instead of empty answer
                    if not state.get("final_answer"):
                        state["final_answer"] = error_message
                    break
                # If fallback succeeded, chunks now contains results, continue with processing
            else:
                # Log successful retrieval
                AgentStateManager.add_planner_decision(
                    state,
                    "retrieval_execution",
                    f"route_success_{state['route']}",
                    f"Route {state['route']} successfully retrieved {len(chunks)} chunks with query: '{state['current_query']}'"
                )
            
            # Add to accumulated chunks
            AgentStateManager.add_retrieval_chunks(state, chunks, state["route"])
            
            # Synthesize and critique
            self._synthesize_and_critique(state)
            
            # ADAPTIVE REFINEMENT: Use critique to improve next query
            if (state["last_critique"] and 
                not state["last_critique"]["is_complete"] and 
                state["last_critique"]["missing_aspects"]):
                
                # Log refinement initiation
                AgentStateManager.add_planner_decision(
                    state,
                    "query_refinement",
                    "refinement_start", 
                    f"Critique indicates incomplete synthesis (quality: {state['last_critique'].get('synthesis_quality', 'unknown')}). Missing aspects identified: {state['last_critique']['missing_aspects']}. Attempting query refinement."
                )
                
                # Refine query based on missing aspects
                refined_query = llm_refine_query(
                    state["query_raw"], 
                    state["last_critique"]["missing_aspects"]
                )
                
                if refined_query != state["current_query"]:
                    old_query = state["current_query"]
                    state["current_query"] = refined_query
                    state["adaptive_refinements"].append(refined_query)
                    state["current_skip"] = 0  # Reset skip to re-search with better focus
                    
                    AgentStateManager.add_planner_decision(
                        state,
                        "query_refinement",
                        "refinement_applied",
                        f"Query refined from '{old_query}' to '{refined_query}'. Reset search pagination to re-search with improved focus. Missing aspects addressed: {state['last_critique']['missing_aspects']}"
                    )
                    
                    logger.info(f"Refined query: {refined_query}")
                else:
                    # If query can't be refined further, continue with pagination
                    AgentStateManager.add_planner_decision(
                        state,
                        "query_refinement",
                        "refinement_skipped",
                        f"LLM query refinement returned same query '{refined_query}'. Continuing with pagination instead (skip: {state['current_skip']} -> {state['current_skip'] + batch_size})"
                    )
                    state["current_skip"] += batch_size
            else:
                # Continue with pagination if critique doesn't suggest refinement
                completion_reason = "synthesis_complete" if state["last_critique"] and state["last_critique"]["is_complete"] else "no_missing_aspects"
                AgentStateManager.add_planner_decision(
                    state,
                    "iteration_control",
                    "continue_pagination",
                    f"No query refinement needed ({completion_reason}). Continuing with pagination (skip: {state['current_skip']} -> {state['current_skip'] + batch_size})"
                )
                state["current_skip"] += batch_size
            
            # Check if critique indicates completion
            if state["last_critique"] and state["last_critique"]["is_complete"]:
                AgentStateManager.add_planner_decision(
                    state,
                    "iteration_control",
                    "completion_by_critique",
                    f"Critique indicates synthesis is complete (quality: {state['last_critique'].get('synthesis_quality', 'unknown')}, confidence: {state['last_critique'].get('confidence_score', 0):.2f}). Stopping iteration loop after {state['iteration_count']} iterations with {len(state['accumulated_chunks'])} total chunks."
                )
                AgentStateManager.mark_complete(state, "Critique indicates comprehensive coverage")
                break
        
        # Handle completion cases
        at_limits, limit_reason = AgentStateManager.is_at_limits(state)
        if at_limits and not state["is_complete"]:
            AgentStateManager.add_planner_decision(
                state,
                "iteration_control",
                "completion_by_limits",
                f"Reached system limits: {limit_reason}. Completed {state['iteration_count']} iterations with {len(state['accumulated_chunks'])} total chunks."
            )
            AgentStateManager.mark_complete(state, limit_reason)
    
    def _synthesize_and_critique(self, state: AgentStateV2) -> None:
        """
        Synthesize current chunks and critique the result
        """
        # Get all chunk texts for synthesis
        chunk_texts = AgentStateManager.get_chunk_texts(state)
        
        if not chunk_texts:
            logger.warning("No chunks available for synthesis")
            return
        
        # Log synthesis initiation
        AgentStateManager.add_planner_decision(
            state,
            "synthesis_process",
            "synthesis_start",
            f"Starting synthesis with {len(chunk_texts)} chunks ({sum(len(text) for text in chunk_texts)} total characters) for query: '{state['query_raw']}'"
        )
        
        # Synthesize
        synthesis = llm_synthesize(chunk_texts, state["query_raw"])
        
        # Log synthesis completion
        AgentStateManager.add_planner_decision(
            state,
            "synthesis_process",
            "synthesis_complete",
            f"Synthesis generated: {len(synthesis)} characters. Preview: '{synthesis[:150]}...'" if len(synthesis) > 150 else f"Synthesis generated: '{synthesis}'"
        )
        
        # Critique
        critique = llm_critique(
            synthesis,
            state["query_raw"],
            state["plan"].get("reading_depth", "normal")
        )
        
        # Log detailed critique results
        AgentStateManager.add_planner_decision(
            state,
            "critique_analysis",
            f"critique_result_{critique.get('synthesis_quality', 'unknown')}",
            f"Critique assessment: Quality={critique.get('synthesis_quality', 'unknown')}, Complete={critique.get('is_complete', False)}, Confidence={critique.get('confidence_score', 0):.2f}, Missing aspects={critique.get('missing_aspects', [])}, Improvement suggestions={critique.get('improvement_suggestions', [])}"
        )
        
        # Update state
        AgentStateManager.add_synthesis_and_critique(state, synthesis, critique)
        
        logger.info(f"Synthesis complete. Critique: {critique['synthesis_quality']}, "
                   f"Complete: {critique['is_complete']}, "
                   f"Missing: {critique['missing_aspects']}")
    
    def _finalize_state(self, state: AgentStateV2) -> AgentStateV2:
        """
        Finalize the state before returning
        """
        # Calculate execution time
        if self.start_time:
            state["execution_time"] = time.time() - self.start_time
        
        # Set final answer if not already set
        if not state.get("final_answer") and state.get("last_synthesis"):
            state["final_answer"] = state["last_synthesis"]
        
        # Generate data coverage summary
        if state["accumulated_chunks"]:
            stats = state["progressive_stats"]
            coverage_summary = (
                f"Analysis based on {stats['chunks_processed']} text sections "
                f"across {stats['batches_processed']} retrieval batches. "
            )
            
            if not stats.get("reading_complete", True):
                coverage_summary += (
                    "Analysis was stopped due to reaching maximum depth limits. "
                    "Additional details may exist in the source documents."
                )
            
            state["data_coverage_summary"] = coverage_summary
        
        # Add tool tracking
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("SimpleChatPlanner")
        
        logger.info(f"SimpleChatPlanner execution complete. "
                   f"Time: {state.get('execution_time', 0):.2f}s, "
                   f"Chunks: {len(state['accumulated_chunks'])}, "
                   f"Iterations: {state['iteration_count']}")
        
        return state
    
    def _generate_data_availability_message(self, metadata: Dict[str, Any], query: str) -> str:
        """Generate helpful message about data availability for structured queries"""
        
        companies = metadata.get("companies", [])
        years = metadata.get("years", [])
        sections = metadata.get("regulatory_sections", [])
        
        message_parts = []
        message_parts.append("I couldn't find the specific data you requested.")
        
        # Provide specific feedback about what was searched
        if companies:
            message_parts.append(f"I searched for data about {', '.join(companies)}")
        
        if years:
            message_parts.append(f"for the year(s) {', '.join(map(str, years))}")
        
        if sections:
            message_parts.append(f"in sections related to {', '.join(sections)}")
        
        # Add suggestions
        message_parts.append("\nHere are some things to try:")
        message_parts.append("• Check if the company ticker is correct (e.g., 'BAC' for Bank of America)")
        message_parts.append("• Try a different year (I have data primarily for 2024-2025)")
        message_parts.append("• Use a more general query (e.g., 'BAC financial highlights')")
        message_parts.append("• Ask 'what data do you have available?' to see what's accessible")
        
        return " ".join(message_parts)
    
    def _generate_semantic_availability_message(self, query: str) -> str:
        """Generate helpful message about data availability for semantic queries"""
        
        message_parts = []
        message_parts.append("I couldn't find relevant content for your query using semantic search.")
        
        # Add suggestions for semantic queries
        message_parts.append("\nHere are some things to try:")
        message_parts.append("• Try more specific terms (e.g., 'credit risk management' instead of 'risks')")
        message_parts.append("• Include company names if you're looking for specific information")
        message_parts.append("• Try broader topics (e.g., 'banking regulations' or 'financial performance')")
        message_parts.append("• Ask 'what data do you have available?' to see what's accessible")
        
        return " ".join(message_parts)
    
    def _try_route_fallback(self, state: AgentStateV2) -> List[Dict[str, Any]]:
        """
        Try fallback routes when current route returns no chunks.
        Returns chunks from successful fallback route or empty list if all fail.
        """
        current_route = state["route"]
        
        # Define fallback sequence
        route_fallback_map = {
            "cypher": ["rag", "hybrid"],
            "rag": ["hybrid", "cypher"],
            "hybrid": ["cypher", "rag"]
        }
        
        fallback_routes = route_fallback_map.get(current_route, [])
        
        for fallback_route in fallback_routes:
            # Check if we've already tried this route in current iteration
            if fallback_route in state["attempted_routes_current_iteration"]:
                continue
            
            logger.info(f"Trying fallback route: {current_route} -> {fallback_route}")
            
            # Mark this route as attempted
            state["attempted_routes_current_iteration"].append(fallback_route)
            
            # Try the fallback route
            batch_size = state["batch_size"]
            current_skip = state["current_skip"]
            
            if fallback_route == "cypher":
                chunks = simplified_cypher(
                    state["current_query"],
                    state["plan_metadata"],
                    limit=batch_size,
                    skip=current_skip
                )
            elif fallback_route == "rag":
                chunks = simplified_rag(
                    state["current_query"],
                    state["plan_metadata"],
                    limit=batch_size,
                    skip=current_skip
                )
            else:  # hybrid
                chunks = simplified_hybrid(
                    state["current_query"],
                    state["plan_metadata"],
                    limit=batch_size,
                    skip=current_skip
                )
            
            if chunks:
                # Success! Update the route and log the decision
                old_route = state["route"]
                state["route"] = fallback_route
                
                AgentStateManager.add_planner_decision(
                    state,
                    "route_fallback",
                    fallback_route,
                    f"Fallback from {old_route} to {fallback_route} - found {len(chunks)} chunks"
                )
                
                logger.info(f"Route fallback successful: {old_route} -> {fallback_route}, found {len(chunks)} chunks")
                return chunks
            else:
                logger.info(f"Route fallback {fallback_route} also returned 0 chunks")
        
        # All routes failed
        logger.warning(f"All route fallbacks failed for route {current_route}")
        return []


def simple_chat_planner(state: AgentStateV2) -> AgentStateV2:
    """
    LangGraph node wrapper for SimpleChatPlanner
    """
    planner = SimpleChatPlanner()
    return planner.execute(state)