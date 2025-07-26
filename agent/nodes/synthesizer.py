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

# Business-focused synthesizer prompt for SEC Graph LangGraph Agent
SYNTH_PROMPT = """\
You are the Synthesizer component of the SEC Graph LangGraph Agent, tasked with generating actionable business insights from validated data retrieved from SEC filings and related financial sources. Your role is to analyze the input data, identify key patterns and trends, and produce a concise, coherent, and business-relevant response that directly addresses the user's query.

**Key Instructions:**
1. **Analyze Retrieved Data**: Review all data chunks to identify relevant financial metrics, qualitative insights, and patterns. Prioritize data with high confidence scores.

2. **Synthesize Insights**: Generate 3-5 key business insights that directly address the query's objective. Ensure insights are actionable, specific, and aligned with the query's business value.

3. **Structure Response**: 
   - Start with a direct answer to the main question
   - Provide 3-5 specific, actionable insights
   - Include comparative analysis when relevant
   - Use professional financial language
   - Keep response concise but comprehensive (150-300 words)

4. **Citations**: Include bracketed numeric citations [1], [2], etc. pointing to the source passages.

5. **Business Focus**: Tailor insights for executive decision-making, focusing on:
   - Risk assessment and mitigation strategies
   - Competitive positioning and market dynamics
   - Financial performance and operational efficiency
   - Regulatory compliance and governance
   - Strategic opportunities and threats

6. **CRITICAL - No Placeholder Values**: NEVER use placeholder values like "XX billion", "$XX million", "XX%", or similar patterns. When specific numerical values are not available in the retrieved data, state "specific figures were not found in the available data" or describe the information qualitatively without using placeholders.

**Only if you truly have insufficient data should you indicate limitations, but always try to provide what insights you can from the available information.**

User Question: {question}

Retrieved Data:
{context}

Provide actionable business insights:"""

def _prepare_context_with_citations(retrievals: List[dict]) -> tuple[str, List[str]]:
    """
    Prepare context chunks with citation numbers and return citation list.
    Updated for chunked data structure.
    Returns (formatted_context, citation_list)
    """
    context_chunks = []
    citations = []
    seen_sources = {}  # Track unique sources for better citation
    
    for i, hit in enumerate(retrievals, 1):
        text = hit.get("text", "")
        source_info = hit.get("metadata", {})
        
        # Truncate very long text
        if len(text) > 800:
            text = text[:800] + "..."
        
        # Format context chunk with citation number
        context_chunks.append(f"[{i}] {text}")
        
        # Build citation info with source file attribution
        citation_parts = []
        if source_info.get("company"):
            citation_parts.append(source_info["company"])
        if source_info.get("year"):
            citation_parts.append(str(source_info["year"]))
        if source_info.get("quarter"):
            citation_parts.append(source_info["quarter"])
        if source_info.get("section_name"):
            citation_parts.append(source_info["section_name"])
            
        # Use source_filename for citation (the original file, not chunk_id)
        source_file = source_info.get("source_filename", "Unknown Source")
        
        # Check if this is from a chunked source
        chunk_info = ""
        if source_info.get("chunk_index") is not None:
            total_chunks = source_info.get("total_chunks", 1)
            if total_chunks > 1:
                chunk_info = f" (Part {source_info['chunk_index'] + 1}/{total_chunks})"
        
        # Build final citation
        base_citation = " ".join(citation_parts) if citation_parts else "SEC Filing"
        citation = f"[{i}] {base_citation}{chunk_info}"
        
        # Track unique sources for summary
        if source_file not in seen_sources:
            seen_sources[source_file] = {"indices": [], "chunks": 0}
        seen_sources[source_file]["indices"].append(i)
        seen_sources[source_file]["chunks"] += 1
        
        citations.append(citation)
    
    formatted_context = "\n\n".join(context_chunks)
    return formatted_context, citations

def _enhance_answer_with_financial_context(answer: str, retrievals: List[dict], query: str) -> str:
    """
    Enhance the answer with financial context and SEC-specific formatting.
    Focus on providing business value from available data.
    """
    # Extract metadata for context regardless of answer content
    companies = set()
    years = set()
    quarters = set()
    source_files = set()
    total_chunks = 0
    
    for hit in retrievals:
        metadata = hit.get("metadata", {})
        if metadata.get("company"):
            companies.add(metadata["company"])
        if metadata.get("year"):
            years.add(str(metadata["year"]))
        if metadata.get("quarter"):
            quarters.add(metadata["quarter"])
        if metadata.get("source_filename"):
            source_files.add(metadata["source_filename"])
        total_chunks += 1
    
    # Always add data coverage information for transparency
    context_info = []
    if companies:
        context_info.append(f"Companies: {', '.join(sorted(companies))}")
    if years:
        context_info.append(f"Years: {', '.join(sorted(years))}")
    if quarters:
        context_info.append(f"Quarters: {', '.join(sorted(quarters))}")
    
    # Add source information
    unique_sources = len(source_files)
    if unique_sources > 0:
        context_info.append(f"Sources: {unique_sources} document(s), {total_chunks} text sections")
    
    if context_info:
        answer += f"\n\n**Data Coverage**: {'; '.join(context_info)}."
    
    return answer

def synthesizer(state: AgentState) -> AgentState:
    """
    Synthesizer node - generates actionable business insights from retrieval results.
    
    Features:
    - Business-focused analysis and insights
    - Proper citation formatting  
    - Proactive approach (maximizes value from available data)
    - SEC-specific financial context
    """
    try:
        retrievals = state.get("retrievals", [])
        query = state.get("query_raw", "")
        
        logger.info(f"Synthesizing business insights from {len(retrievals)} retrieval results")
        
        if not retrievals:
            # No results to synthesize from
            state["final_answer"] = "No relevant documents were found to answer your question. Please try a different query or check if the requested companies/time periods are available in our database."
            state["citations"] = []
            logger.warning("Synthesis with no retrieval results")
            return state
        
        # Prepare context and citations
        context, citations = _prepare_context_with_citations(retrievals)
        
        # Generate answer using LLM with business-focused prompt
        prompt = SYNTH_PROMPT.format(question=query, context=context)
        
        try:
            response = _llm.invoke(prompt)
            raw_answer = response.content.strip()
            logger.info(f"Generated business insights: {len(raw_answer)} characters")
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            raw_answer = "I encountered an error while analyzing the retrieved information, but I can confirm relevant data was found."
        
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