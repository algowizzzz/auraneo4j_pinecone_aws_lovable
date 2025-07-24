"""
Master Synthesis Node - Multi-topic Answer Aggregation
Implements map-reduce pattern for complex multi-topic queries from langrgaph_agent_readme
"""

from agent.state import AgentState
from langchain_openai import ChatOpenAI
import os
import logging
import textwrap
from typing import List

logger = logging.getLogger(__name__)

# Initialize LLM for master synthesis
_llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.1, 
    streaming=True,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Master aggregation prompt from readme specifications
AGG_PROMPT = """\
Combine the section-wise answers into ONE coherent response.
Remove duplicates, keep logical order: Market Risk → Credit Risk → Operational Risk.
Preserve citations exactly as they are.

Section answers:
{pieces}

Write the merged answer (max 8 sentences):
"""

# Alternative comprehensive prompt for complex financial analysis
COMPREHENSIVE_AGG_PROMPT = """\
You are a senior financial analyst synthesizing multiple research findings.

Combine the following sub-topic analyses into a comprehensive, well-structured response:

{pieces}

Requirements:
1. Create a logical flow covering all topics
2. Remove any duplicate information
3. Preserve all citations [1], [2], etc.
4. Use professional financial language
5. Keep response concise but complete (≤ 6 sentences per topic)
6. Structure: Overview → Key Findings → Risk Assessment → Conclusion

Synthesized Analysis:
"""

def _organize_sub_summaries_by_topic(sub_summaries: List[str], sub_tasks: List[dict]) -> List[tuple[str, str]]:
    """
    Organize sub-summaries with their topics in logical order.
    Returns list of (topic, summary) tuples.
    """
    # Define logical order for financial topics
    topic_priority = {
        'market risk': 1,
        'credit risk': 2, 
        'operational risk': 3,
        'liquidity risk': 4,
        'regulatory risk': 5,
        'business strategy': 6,
        'financial performance': 7,
        'competitive position': 8
    }
    
    # Pair summaries with their topics
    topic_summary_pairs = []
    for i, summary in enumerate(sub_summaries):
        if i < len(sub_tasks):
            topic = sub_tasks[i].get('topic', f'Topic {i+1}')
        else:
            topic = f'Topic {i+1}'
        topic_summary_pairs.append((topic, summary))
    
    # Sort by priority (known topics first, then alphabetical)
    def sort_key(pair):
        topic = pair[0].lower()
        for key, priority in topic_priority.items():
            if key in topic:
                return priority
        return 999  # Unknown topics go last
    
    return sorted(topic_summary_pairs, key=sort_key)

def _extract_citations_from_summaries(summaries: List[str]) -> List[str]:
    """
    Extract all citations from sub-summaries and renumber them consecutively.
    Returns updated summaries and consolidated citation list.
    """
    import re
    
    all_citations = []
    citation_mapping = {}
    next_citation_num = 1
    
    updated_summaries = []
    
    for summary in summaries:
        # Find all citations like [1], [2], etc.
        citation_pattern = r'\[(\d+)\]'
        citations_in_summary = re.findall(citation_pattern, summary)
        
        updated_summary = summary
        
        # Replace citations with new consecutive numbers
        for old_citation in set(citations_in_summary):
            old_ref = f'[{old_citation}]'
            
            if old_ref not in citation_mapping:
                citation_mapping[old_ref] = f'[{next_citation_num}]'
                all_citations.append(f'[{next_citation_num}] Sub-topic analysis')
                next_citation_num += 1
            
            # Replace all instances in this summary
            updated_summary = updated_summary.replace(old_ref, citation_mapping[old_ref])
        
        updated_summaries.append(updated_summary)
    
    return updated_summaries, all_citations

def _detect_query_complexity(query: str, sub_tasks: List[dict]) -> str:
    """
    Detect the complexity and type of the multi-topic query to choose appropriate synthesis strategy.
    """
    query_lower = query.lower()
    
    # Risk analysis query
    risk_keywords = ['risk', 'risks', 'exposure', 'threat', 'vulnerability']
    if any(keyword in query_lower for keyword in risk_keywords):
        return 'risk_analysis'
    
    # Comparative analysis
    comparative_keywords = ['compare', 'comparison', 'versus', 'vs', 'difference', 'similar']
    if any(keyword in query_lower for keyword in comparative_keywords):
        return 'comparative'
    
    # Strategic analysis
    strategy_keywords = ['strategy', 'approach', 'outlook', 'position', 'competitive']
    if any(keyword in query_lower for keyword in strategy_keywords):
        return 'strategic'
    
    # Financial performance
    performance_keywords = ['performance', 'results', 'metrics', 'financial', 'revenue', 'profit']
    if any(keyword in query_lower for keyword in performance_keywords):
        return 'performance'
    
    # Default comprehensive analysis
    return 'comprehensive'

def master_synth(state: AgentState) -> AgentState:
    """
    Master synthesis node - aggregates multiple sub-topic analyses into coherent response.
    
    Features:
    - Intelligent topic ordering (Market Risk → Credit Risk → Operational Risk, etc.)
    - Citation consolidation and renumbering
    - Duplicate removal and logical flow
    - Query-type specific synthesis strategies
    - Professional financial language
    """
    try:
        sub_summaries = state.get("sub_summaries", [])
        sub_tasks = state.get("sub_tasks", [])
        query = state.get("query_raw", "")
        
        logger.info(f"Master synthesis processing {len(sub_summaries)} sub-topic summaries")
        
        if not sub_summaries:
            state["master_answer"] = "I don't have enough information to provide a comprehensive analysis."
            state["citations"] = []
            logger.warning("Master synthesis with no sub-summaries")
            return state
        
        # Organize summaries by topic in logical order
        organized_pairs = _organize_sub_summaries_by_topic(sub_summaries, sub_tasks)
        
        # Extract and consolidate citations
        just_summaries = [pair[1] for pair in organized_pairs]
        updated_summaries, consolidated_citations = _extract_citations_from_summaries(just_summaries)
        
        # Rebuild organized pairs with updated summaries
        final_organized = [(organized_pairs[i][0], updated_summaries[i]) for i in range(len(organized_pairs))]
        
        # Format pieces for LLM prompt
        pieces_text = ""
        for i, (topic, summary) in enumerate(final_organized, 1):
            pieces_text += f"({i}) {topic.title()}:\n{summary}\n\n"
        
        # Detect query complexity and choose synthesis strategy
        query_type = _detect_query_complexity(query, sub_tasks)
        
        # Choose appropriate prompt based on query complexity
        if len(sub_summaries) <= 3 and query_type in ['risk_analysis', 'comparative']:
            # Use simple aggregation for focused queries
            prompt = AGG_PROMPT.format(pieces=pieces_text)
        else:
            # Use comprehensive synthesis for complex queries
            prompt = COMPREHENSIVE_AGG_PROMPT.format(pieces=pieces_text)
        
        # Generate master synthesis
        try:
            response = _llm.invoke(prompt)
            master_answer = response.content.strip()
        except Exception as e:
            logger.error(f"LLM master synthesis failed: {e}")
            # Fallback: simple concatenation
            master_answer = _create_fallback_synthesis(final_organized)
        
        # Enhance with query context
        if query_type == 'risk_analysis':
            master_answer = f"Risk Analysis Summary:\n\n{master_answer}"
        elif query_type == 'comparative':
            master_answer = f"Comparative Analysis:\n\n{master_answer}"
        elif query_type == 'strategic':
            master_answer = f"Strategic Assessment:\n\n{master_answer}"
        elif query_type == 'performance':
            master_answer = f"Performance Analysis:\n\n{master_answer}"
        
        # Store results
        state["master_answer"] = master_answer
        state["citations"] = consolidated_citations
        
        # Calculate master synthesis confidence
        master_confidence = _calculate_master_confidence(master_answer, sub_summaries, consolidated_citations)
        
        if "confidence_scores" not in state:
            state["confidence_scores"] = {}
        state["confidence_scores"]["master_synthesis"] = master_confidence
        
        # Track tool usage
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("master_synth")
        
        logger.info(f"Master synthesis completed: {len(master_answer)} chars, {len(consolidated_citations)} citations, confidence: {master_confidence:.2f}")
        
    except Exception as e:
        logger.error(f"Master synthesis error: {e}")
        state["master_answer"] = "I encountered an error while consolidating the analysis."
        state["citations"] = []
        if "error_messages" not in state:
            state["error_messages"] = []
        state["error_messages"].append(f"Master synthesis error: {str(e)}")
    
    return state

def _create_fallback_synthesis(organized_pairs: List[tuple[str, str]]) -> str:
    """
    Create a simple fallback synthesis when LLM fails.
    """
    fallback_parts = []
    
    for topic, summary in organized_pairs:
        fallback_parts.append(f"**{topic.title()}**: {summary}")
    
    return "\n\n".join(fallback_parts)

def _calculate_master_confidence(answer: str, sub_summaries: List[str], citations: List[str]) -> float:
    """
    Calculate confidence for master synthesis.
    """
    factors = []
    
    # Factor 1: Coverage of sub-topics
    coverage_score = min(1.0, len(sub_summaries) / 3)  # Normalize based on expected sub-topics
    factors.append(coverage_score)
    
    # Factor 2: Answer comprehensiveness
    if len(answer) < 200:
        factors.append(0.5)
    elif len(answer) > 500:
        factors.append(0.9)
    else:
        factors.append(0.7)
    
    # Factor 3: Citation consolidation
    citation_score = min(1.0, len(citations) / len(sub_summaries)) if sub_summaries else 0.0
    factors.append(citation_score)
    
    # Factor 4: Structural quality (has sections, logical flow)
    structure_indicators = ['risk', 'analysis', 'assessment', 'summary', 'conclusion']
    structure_count = sum(1 for indicator in structure_indicators if indicator.lower() in answer.lower())
    structure_score = min(1.0, structure_count / 3)
    factors.append(structure_score)
    
    return sum(factors) / len(factors)

def get_master_synthesis_summary(state: AgentState) -> dict:
    """
    Get summary of master synthesis results for debugging/monitoring.
    """
    return {
        "master_answer_length": len(state.get("master_answer", "")),
        "sub_topics_processed": len(state.get("sub_summaries", [])),
        "total_citations": len(state.get("citations", [])),
        "master_confidence": state.get("confidence_scores", {}).get("master_synthesis", 0.0),
        "synthesis_method": "llm_aggregation"
    }