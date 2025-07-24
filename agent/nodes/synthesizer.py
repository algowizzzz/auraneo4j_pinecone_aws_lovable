"""
Synthesizer Node - Single-topic Answer Generation
Implements financial domain-optimized synthesis from langrgaph_agent_readme
"""

from agent.state import AgentState
from langchain_openai import ChatOpenAI
import os
import logging
import textwrap
from typing import List

logger = logging.getLogger(__name__)

# Initialize LLM for synthesis
_llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.1, 
    streaming=True,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Financial domain-optimized prompt from readme specifications
SYNTH_PROMPT = """\
You are FinAnswer, a cautious financial analyst AI.
Answer the user's question ONLY from the provided passages.
If the answer is not fully supported, say "I don't have enough information."
Use *concise professional language* (≤ 4 sentences).
Add bracketed numeric citations like [1], [3] pointing to the passages.

User question:
{question}

Passages:
{context}
"""

def _prepare_context_with_citations(retrievals: List[dict]) -> tuple[str, List[str]]:
    """
    Prepare context chunks with citation numbers and return citation list.
    Returns (formatted_context, citation_list)
    """
    context_chunks = []
    citations = []
    
    for i, hit in enumerate(retrievals, 1):
        text = hit.get("text", "")
        source_info = hit.get("metadata", {})
        
        # Truncate very long text
        if len(text) > 800:
            text = text[:800] + "..."
        
        # Format context chunk with citation number
        context_chunks.append(f"[{i}] {text}")
        
        # Build citation info
        citation_parts = []
        if source_info.get("company"):
            citation_parts.append(source_info["company"])
        if source_info.get("year"):
            citation_parts.append(str(source_info["year"]))
        if source_info.get("quarter"):
            citation_parts.append(source_info["quarter"])
        if source_info.get("section_name"):
            citation_parts.append(source_info["section_name"])
        
        citation = f"[{i}] " + " ".join(citation_parts) if citation_parts else f"[{i}] SEC Filing"
        citations.append(citation)
    
    formatted_context = "\n\n".join(context_chunks)
    return formatted_context, citations

def _enhance_answer_with_financial_context(answer: str, retrievals: List[dict], query: str) -> str:
    """
    Enhance the answer with financial context and SEC-specific formatting.
    """
    # Check if answer is too generic or insufficient
    generic_indicators = [
        "i don't have enough information",
        "insufficient information", 
        "cannot determine",
        "not provided in the passages"
    ]
    
    is_generic = any(indicator in answer.lower() for indicator in generic_indicators)
    
    if is_generic and retrievals:
        # Try to extract some useful information even if incomplete
        companies = set()
        years = set()
        quarters = set()
        
        for hit in retrievals:
            metadata = hit.get("metadata", {})
            if metadata.get("company"):
                companies.add(metadata["company"])
            if metadata.get("year"):
                years.add(str(metadata["year"]))
            if metadata.get("quarter"):
                quarters.add(metadata["quarter"])
        
        context_info = []
        if companies:
            context_info.append(f"Companies: {', '.join(sorted(companies))}")
        if years:
            context_info.append(f"Years: {', '.join(sorted(years))}")
        if quarters:
            context_info.append(f"Quarters: {', '.join(sorted(quarters))}")
        
        if context_info:
            answer += f"\n\nAvailable data covers: {'; '.join(context_info)}."
    
    return answer

def synthesizer(state: AgentState) -> AgentState:
    """
    Synthesizer node - generates concise, well-cited answers from retrieval results.
    
    Features:
    - Financial domain expertise
    - Proper citation formatting
    - Cautious approach (admits when information insufficient)
    - SEC-specific context enhancement
    """
    try:
        retrievals = state.get("retrievals", [])
        query = state.get("query_raw", "")
        
        logger.info(f"Synthesizing answer from {len(retrievals)} retrieval results")
        
        if not retrievals:
            # No results to synthesize from
            state["final_answer"] = "I don't have enough information to answer your question. No relevant documents were found."
            state["citations"] = []
            logger.warning("Synthesis with no retrieval results")
            return state
        
        # Prepare context and citations
        context, citations = _prepare_context_with_citations(retrievals)
        
        # Generate answer using LLM
        prompt = SYNTH_PROMPT.format(question=query, context=context)
        
        try:
            response = _llm.invoke(prompt)
            raw_answer = response.content.strip()
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            raw_answer = "I encountered an error while analyzing the information."
        
        # Enhance answer with financial context
        enhanced_answer = _enhance_answer_with_financial_context(raw_answer, retrievals, query)
        
        # Store results
        state["final_answer"] = enhanced_answer
        state["citations"] = citations
        
        # Track synthesis quality metrics
        if "confidence_scores" not in state:
            state["confidence_scores"] = {}
        
        # Calculate synthesis confidence based on various factors
        synthesis_confidence = _calculate_synthesis_confidence(enhanced_answer, retrievals, citations)
        state["confidence_scores"]["synthesis"] = synthesis_confidence
        
        # Track tool usage
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("synthesizer")
        
        logger.info(f"Synthesis completed: {len(enhanced_answer)} chars, {len(citations)} citations, confidence: {synthesis_confidence:.2f}")
        
    except Exception as e:
        logger.error(f"Synthesizer error: {e}")
        state["final_answer"] = "I encountered an error while processing your question."
        state["citations"] = []
        if "error_messages" not in state:
            state["error_messages"] = []
        state["error_messages"].append(f"Synthesis error: {str(e)}")
    
    return state

def _calculate_synthesis_confidence(answer: str, retrievals: List[dict], citations: List[str]) -> float:
    """
    Calculate confidence score for the synthesized answer.
    """
    factors = []
    
    # Factor 1: Answer length and completeness
    if "don't have enough information" in answer.lower():
        factors.append(0.3)  # Low confidence for insufficient info
    elif len(answer) < 50:
        factors.append(0.5)  # Low confidence for very short answers
    elif len(answer) > 100:
        factors.append(0.9)  # High confidence for substantial answers
    else:
        factors.append(0.7)  # Medium confidence
    
    # Factor 2: Citation usage
    citation_count = len([cite for cite in citations if cite])
    if citation_count >= 3:
        factors.append(0.9)
    elif citation_count >= 2:
        factors.append(0.8)
    elif citation_count >= 1:
        factors.append(0.6)
    else:
        factors.append(0.3)
    
    # Factor 3: Retrieval quality
    if retrievals:
        avg_retrieval_score = sum(hit.get("score", 0.5) for hit in retrievals) / len(retrievals)
        factors.append(min(1.0, avg_retrieval_score))
    else:
        factors.append(0.0)
    
    # Factor 4: Answer specificity (contains numbers, specific terms)
    specificity_indicators = ['$', '%', 'billion', 'million', 'ratio', 'Q1', 'Q2', 'Q3', 'Q4', '2024', '2025']
    specificity_count = sum(1 for indicator in specificity_indicators if indicator in answer)
    specificity_score = min(1.0, specificity_count / 3)
    factors.append(specificity_score)
    
    return sum(factors) / len(factors)

def get_synthesis_summary(state: AgentState) -> dict:
    """
    Get a summary of synthesis results for debugging/monitoring.
    """
    return {
        "answer_length": len(state.get("final_answer", "")),
        "citation_count": len(state.get("citations", [])),
        "synthesis_confidence": state.get("confidence_scores", {}).get("synthesis", 0.0),
        "has_answer": bool(state.get("final_answer")),
        "source_count": len(state.get("retrievals", []))
    }