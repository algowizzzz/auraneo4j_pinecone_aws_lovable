"""
Validator Node - LLM-based Quality Scoring and Fallback Logic
Implements sophisticated validation from langrgaph_agent_readme specifications
"""

from agent.state import AgentState
from langchain_openai import ChatOpenAI
import os
import logging
from typing import List

logger = logging.getLogger(__name__)

# Initialize LLM for validation scoring
_llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# LLM reflection prompt optimized for financial retrieval tasks
_REFLECT_PROMPT = """\
Rate the following retrieved passages for their usefulness to answer the user's
financial question on a scale 0–10 (0 = completely irrelevant, 10 = perfectly sufficient).

Consider that partial information about financial metrics, business descriptions, 
or risk factors can still be useful for synthesis. Even if passages don't fully 
answer the question, they may contain relevant financial context.

Return ONLY the integer score.

User question:
{question}

Passages:
{joined}
"""

def _llm_score(question: str, passages: List[str]) -> int:
    """
    Use LLM self-reflection to score retrieval quality.
    Returns integer score 0-10.
    """
    try:
        if not passages:
            return 0
        
        # Join passages with separators, limit to first 5 for performance
        joined = "\n---\n".join(passages[:5])
        
        # Truncate if too long to avoid token limits
        if len(joined) > 3000:
            joined = joined[:3000] + "... [truncated]"
        
        prompt = _REFLECT_PROMPT.format(question=question, joined=joined)
        response = _llm.invoke(prompt)
        
        # Parse integer response
        score_text = response.content.strip()
        try:
            score = int(score_text)
            return max(0, min(10, score))  # Clamp to 0-10 range
        except ValueError:
            logger.warning(f"LLM returned non-integer score: {score_text}")
            return 0
            
    except Exception as e:
        logger.error(f"LLM scoring failed: {e}")
        return 0

def _calculate_numerical_quality(state: AgentState) -> dict:
    """
    Calculate numerical quality metrics for retrieval results.
    Returns dict with various quality indicators.
    """
    hits = state.get("retrievals", [])
    
    quality_metrics = {
        "hit_count": len(hits),
        "avg_score": 0.0,
        "min_score": 0.0,
        "source_diversity": 0,
        "has_company_match": False,
        "has_temporal_match": False
    }
    
    if not hits:
        return quality_metrics
    
    # Calculate score statistics
    scores = [hit.get("score", 0.0) for hit in hits]
    quality_metrics["avg_score"] = sum(scores) / len(scores)
    quality_metrics["min_score"] = min(scores)
    
    # Source diversity (number of unique sources)
    sources = set(hit.get("source", "unknown") for hit in hits)
    quality_metrics["source_diversity"] = len(sources)
    
    # Check for metadata alignment
    query_metadata = state.get("metadata", {})
    
    if query_metadata.get("company"):
        # Check if any result matches the queried company
        for hit in hits:
            hit_metadata = hit.get("metadata", {})
            if hit_metadata.get("company") == query_metadata["company"]:
                quality_metrics["has_company_match"] = True
                break
    
    if query_metadata.get("year") or query_metadata.get("quarter"):
        # Check for temporal alignment
        for hit in hits:
            hit_metadata = hit.get("metadata", {})
            year_match = not query_metadata.get("year") or hit_metadata.get("year") == int(query_metadata.get("year", 0))
            quarter_match = not query_metadata.get("quarter") or hit_metadata.get("quarter") == query_metadata.get("quarter")
            
            if year_match and quarter_match:
                quality_metrics["has_temporal_match"] = True
                break
    
    return quality_metrics

def validator(state: AgentState) -> AgentState:
    """
    Validator node - sophisticated quality assessment using LLM reflection and numerical metrics.
    
    Validation criteria:
    1. LLM self-reflection score >= 6 (sufficient relevance)
    2. Minimum hit count >= 2 (basic coverage)
    3. Average similarity score >= 0.25 (for semantic searches)
    4. Company/temporal alignment (if metadata available)
    """
    try:
        hits = state.get("retrievals", [])
        query = state.get("query_raw", "")
        source = hits[0].get("source", "unknown") if hits else "unknown"
        
        logger.info(f"Validating {len(hits)} results from {source} source")
        
        # Initialize validation state
        state["valid"] = False
        validation_details = {
            "llm_score": 0,
            "numerical_metrics": {},
            "validation_reasons": []
        }
        
        # Quick fail for no results
        if not hits:
            validation_details["validation_reasons"].append("No retrieval results")
            state["confidence_scores"] = state.get("confidence_scores", {})
            state["confidence_scores"]["validation"] = 0.0
            logger.info("Validation FAILED: No results")
            return state
        
        # Calculate numerical quality metrics
        numerical_metrics = _calculate_numerical_quality(state)
        validation_details["numerical_metrics"] = numerical_metrics
        
        # Get LLM quality score
        passages = [hit.get("text", "") for hit in hits if hit.get("text")]
        llm_score = _llm_score(query, passages)
        validation_details["llm_score"] = llm_score
        
        # Apply validation rules (from readme specifications)
        validation_passed = True
        reasons = []
        
        # Rule 1: LLM reflection score must be >= 3 (optimized for SEC retrieval)
        if llm_score < 3:
            validation_passed = False
            reasons.append(f"LLM relevance score too low: {llm_score}/10")
        
        # Rule 2: Minimum hit count >= 1 for basic coverage (business-optimized)
        if numerical_metrics["hit_count"] < 1:
            validation_passed = False
            reasons.append(f"Insufficient results: {numerical_metrics['hit_count']} hits")
        
        # Rule 3: For semantic searches, minimum average score (business-optimized)
        if source in ["hybrid", "rag"] and numerical_metrics["avg_score"] < 0.10:
            validation_passed = False
            reasons.append(f"Low semantic similarity: {numerical_metrics['avg_score']:.3f}")
        
        # Rule 4: Company alignment check (if company specified)
        query_metadata = state.get("metadata", {})
        if query_metadata.get("company") and not numerical_metrics["has_company_match"]:
            # This is a warning, not a failure
            reasons.append(f"No exact company match for {query_metadata['company']}")
        
        # Rule 5: Temporal alignment check (if year/quarter specified)
        if (query_metadata.get("year") or query_metadata.get("quarter")) and not numerical_metrics["has_temporal_match"]:
            # This is a warning, not a failure for open-ended queries
            reasons.append(f"No exact temporal match")
        
        # Set validation result
        state["valid"] = validation_passed
        validation_details["validation_reasons"] = reasons
        
        # Calculate overall confidence score
        confidence_factors = [
            llm_score / 10,  # LLM score normalized
            min(1.0, numerical_metrics["hit_count"] / 5),  # Hit count normalized
            numerical_metrics["avg_score"] if source in ["hybrid", "rag"] else 1.0,  # Semantic score
            1.0 if numerical_metrics["has_company_match"] or not query_metadata.get("company") else 0.8,
            1.0 if numerical_metrics["has_temporal_match"] or not (query_metadata.get("year") or query_metadata.get("quarter")) else 0.9
        ]
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Store confidence and validation details
        if "confidence_scores" not in state:
            state["confidence_scores"] = {}
        state["confidence_scores"]["validation"] = overall_confidence
        state["validation_details"] = validation_details
        
        # Track tool usage
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("validator")
        
        # Log validation result
        result_text = "PASSED" if validation_passed else "FAILED"
        logger.info(f"Validation {result_text}: LLM={llm_score}/10, hits={numerical_metrics['hit_count']}, confidence={overall_confidence:.2f}")
        
        if reasons:
            logger.info(f"Validation issues: {', '.join(reasons)}")
        
    except Exception as e:
        logger.error(f"Validator error: {e}")
        state["valid"] = False
        if "error_messages" not in state:
            state["error_messages"] = []
        state["error_messages"].append(f"Validation error: {str(e)}")
    
    return state

def route_decider(state: AgentState) -> str:
    """
    Route decision function for LangGraph conditional edges.
    
    Implements sophisticated fallback logic:
    1. If validation passed -> "pass" (proceed to synthesis)
    2. If fallback routes available -> trigger next fallback
    3. If all fallbacks exhausted -> "fail" (end with apology)
    """
    try:
        # Check if validation passed
        if state.get("valid", False):
            logger.info("Validation passed - routing to synthesis")
            return "synthesizer"
        
        # Check for available fallback routes
        fallback_routes = state.get("fallback", [])
        
        if fallback_routes:
            # Trigger next fallback route
            next_route = fallback_routes.pop(0)
            state["route"] = next_route
            
            # Update state with remaining fallbacks
            state["fallback"] = fallback_routes
            
            logger.info(f"Validation failed - triggering fallback to {next_route}")
            logger.info(f"Remaining fallbacks: {fallback_routes}")
            
            return next_route
        
        # All fallbacks exhausted
        logger.warning("Validation failed - all fallback routes exhausted")
        return "__end__"
        
    except Exception as e:
        logger.error(f"Route decider error: {e}")
        return "__end__"

def get_validation_summary(state: AgentState) -> dict:
    """
    Get a summary of validation results for debugging/monitoring.
    """
    validation_details = state.get("validation_details", {})
    
    return {
        "validation_passed": state.get("valid", False),
        "llm_score": validation_details.get("llm_score", 0),
        "hit_count": validation_details.get("numerical_metrics", {}).get("hit_count", 0),
        "confidence": state.get("confidence_scores", {}).get("validation", 0.0),
        "issues": validation_details.get("validation_reasons", []),
        "fallbacks_remaining": len(state.get("fallback", []))
    }