"""
LLM Helper Functions for Enhanced Iterative Planner
Provides structured extraction, synthesis, critique, and clarification functions
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI

from ..models.metadata import StandardizedMetadata, CritiqueResult, UserClarificationRequest

logger = logging.getLogger(__name__)

# Initialize LLM
_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# System prompts
EXTRACTION_PROMPT = """
You are an expert SEC filing query analyzer. Extract structured information from user queries.

Your task is to produce a JSON object with:
- intent: "factual_query" | "semantic_query" | "introspection_query" 
- companies: List of company tickers (e.g., ["BAC", "JPM"])
- years: List of years (e.g., [2024, 2025])
- quarters: List of quarters (e.g., ["Q1", "Q4"])  
- doc_types: List of document types (e.g., ["10-K", "10-Q"])
- regulatory_sections: List of sections (e.g., ["item_1A", "item_7"])
- text_contains: List of key terms to search for
- reading_depth: "quick" | "normal" | "deep" | "comprehensive"

Classification rules:
- introspection_query: Questions about the agent's capabilities or available data
- factual_query: Specific facts, numbers, or well-defined information requests
- semantic_query: Open-ended questions requiring broad search

Company normalization:
- "Bank of America" -> "BAC"
- "JPMorgan" or "JPMorgan Chase" -> "JPM"  
- "Goldman Sachs" -> "GS"
- "Wells Fargo" -> "WFC"
- "Morgan Stanley" -> "MS"

Return only valid JSON, no markdown.
"""

SYNTHESIS_PROMPT = """
You are an expert financial analyst synthesizing information from SEC filings.

Your task: Create a comprehensive, well-structured answer based on the provided text chunks.

Guidelines:
1. Directly answer the user's question
2. Use specific data points and quotes when available
3. Structure your response clearly with headers if appropriate
4. Maintain professional, analytical tone
5. Focus on the most relevant information
6. If comparing multiple entities, structure comparisons clearly

User Query: {question}

Text Chunks:
{chunks}

Provide a thorough, professional analysis:
"""

CRITIQUE_PROMPT = """
You are a quality assessor for financial research. Evaluate the completeness and quality of a synthesis.

Your task: Assess whether the synthesis adequately answers the user's question.

Return a JSON object with:
- is_complete: boolean (true if synthesis fully answers the question)
- confidence_score: float 0-1 (confidence in the synthesis quality)
- missing_aspects: list of strings (what important aspects are missing)
- improvement_suggestions: list of strings (specific ways to improve)
- synthesis_quality: "poor" | "fair" | "good" | "excellent"

Evaluation criteria:
- Completeness: Does it fully address the query?
- Accuracy: Are facts and figures correct?
- Depth: Is the analysis thorough for the requested reading depth?
- Clarity: Is the answer well-structured and understandable?

User Query: {question}
Reading Depth Required: {reading_depth}
Current Synthesis: {synthesis}

Return only valid JSON:
"""

CLARIFICATION_PROMPT = """
You are a helpful research assistant that asks clarifying questions when encountering ambiguous data.

Your task: Generate a clear, helpful question to resolve ambiguity in the user's request.

Guidelines:
1. Be specific about the ambiguity found
2. Provide clear options when possible
3. Explain why clarification is needed
4. Keep the question concise and professional

Context: {context}
Ambiguity Details: {ambiguity_details}

Generate a clarification request as JSON:
{
  "question": "Clear, specific question for the user",
  "options": ["option1", "option2", ...] (if applicable),
  "context": "Brief explanation of why clarification is needed",
  "request_type": "disambiguation" | "confirmation" | "additional_info"
}

Return only valid JSON:
"""


def llm_extract_query_info(query: str) -> Dict[str, Any]:
    """
    Extract structured information from user query using LLM
    
    Args:
        query: Raw user query
        
    Returns:
        Structured metadata dictionary
    """
    try:
        prompt = EXTRACTION_PROMPT + f"\n\nUser Query: {query}"
        response = _llm.invoke(prompt)
        result_text = response.content.strip()
        
        # Clean markdown if present
        if result_text.startswith("```"):
            result_text = result_text.split('\n', 1)[1]
        if result_text.endswith("```"):
            result_text = result_text.rsplit('\n', 1)[0]
        
        return json.loads(result_text)
        
    except json.JSONDecodeError as e:
        logger.warning(f"LLM extraction returned invalid JSON: {result_text}")
        return {
            "intent": "semantic_query",
            "companies": [],
            "years": [],
            "quarters": [],
            "doc_types": [],
            "regulatory_sections": [],
            "text_contains": [],
            "reading_depth": "normal"
        }
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return {}


def llm_synthesize(chunks: List[str], question: str) -> str:
    """
    Synthesize answer from text chunks using LLM
    
    Args:
        chunks: List of text chunks to synthesize
        question: Original user question
        
    Returns:
        Synthesized answer
    """
    try:
        # Prepare chunks text
        chunks_text = "\n\n---\n\n".join(chunks)
        
        # Truncate if too long
        max_chunks_length = 15000  # Leave room for prompt
        if len(chunks_text) > max_chunks_length:
            chunks_text = chunks_text[:max_chunks_length] + "\n\n[... content truncated ...]"
        
        prompt = SYNTHESIS_PROMPT.format(
            question=question,
            chunks=chunks_text
        )
        
        response = _llm.invoke(prompt)
        return response.content.strip()
        
    except Exception as e:
        logger.error(f"LLM synthesis failed: {e}")
        return f"Error synthesizing answer: {str(e)}"


def llm_critique(synthesis: str, question: str, reading_depth: str = "normal") -> CritiqueResult:
    """
    Critique synthesis quality using LLM
    
    Args:
        synthesis: The synthesized answer to critique
        question: Original user question
        reading_depth: Required depth of analysis
        
    Returns:
        Critique result with completeness assessment
    """
    try:
        prompt = CRITIQUE_PROMPT.format(
            question=question,
            reading_depth=reading_depth,
            synthesis=synthesis
        )
        
        response = _llm.invoke(prompt)
        result_text = response.content.strip()
        
        # Clean markdown if present
        if result_text.startswith("```"):
            result_text = result_text.split('\n', 1)[1]
        if result_text.endswith("```"):
            result_text = result_text.rsplit('\n', 1)[0]
        
        critique_data = json.loads(result_text)
        
        return CritiqueResult(
            is_complete=critique_data.get("is_complete", False),
            confidence_score=critique_data.get("confidence_score", 0.0),
            missing_aspects=critique_data.get("missing_aspects", []),
            improvement_suggestions=critique_data.get("improvement_suggestions", []),
            synthesis_quality=critique_data.get("synthesis_quality", "fair")
        )
        
    except json.JSONDecodeError as e:
        logger.warning(f"LLM critique returned invalid JSON: {result_text}")
        return CritiqueResult(
            is_complete=False,
            confidence_score=0.5,
            missing_aspects=["Unable to assess completeness"],
            improvement_suggestions=["Review synthesis quality"],
            synthesis_quality="fair"
        )
    except Exception as e:
        logger.error(f"LLM critique failed: {e}")
        return CritiqueResult(
            is_complete=False,
            confidence_score=0.0,
            missing_aspects=[f"Critique error: {str(e)}"],
            improvement_suggestions=[],
            synthesis_quality="poor"
        )


def llm_generate_clarification(context: str, ambiguity_details: str) -> UserClarificationRequest:
    """
    Generate clarification question using LLM
    
    Args:
        context: Context about the query and discovered data
        ambiguity_details: Specific details about the ambiguity
        
    Returns:
        Clarification request for user
    """
    try:
        prompt = CLARIFICATION_PROMPT.format(
            context=context,
            ambiguity_details=ambiguity_details
        )
        
        response = _llm.invoke(prompt)
        result_text = response.content.strip()
        
        # Clean markdown if present
        if result_text.startswith("```"):
            result_text = result_text.split('\n', 1)[1]
        if result_text.endswith("```"):
            result_text = result_text.rsplit('\n', 1)[0]
        
        clarification_data = json.loads(result_text)
        
        return UserClarificationRequest(
            question=clarification_data.get("question", "Could you please clarify your request?"),
            options=clarification_data.get("options"),
            context=clarification_data.get("context", "Additional information needed"),
            request_type=clarification_data.get("request_type", "disambiguation")
        )
        
    except json.JSONDecodeError as e:
        logger.warning(f"LLM clarification returned invalid JSON: {result_text}")
        return UserClarificationRequest(
            question="Could you please provide more specific information about your request?",
            options=None,
            context="Unable to generate specific clarification question",
            request_type="additional_info"
        )
    except Exception as e:
        logger.error(f"LLM clarification failed: {e}")
        return UserClarificationRequest(
            question="Could you please clarify your request?",
            options=None,
            context=f"Error generating clarification: {str(e)}",
            request_type="additional_info"
        )


def llm_refine_query(original_query: str, missing_aspects: List[str]) -> str:
    """
    Refine query based on critique feedback
    
    Args:
        original_query: The original query
        missing_aspects: Aspects identified as missing from critique
        
    Returns:
        Refined query with focus on missing aspects
    """
    try:
        if not missing_aspects:
            return original_query
        
        missing_text = " ".join(missing_aspects)
        refined_query = f"{original_query} {missing_text}"
        
        # Basic deduplication and cleanup
        words = refined_query.split()
        seen = set()
        cleaned_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen:
                seen.add(word_lower)
                cleaned_words.append(word)
        
        return " ".join(cleaned_words)
        
    except Exception as e:
        logger.error(f"Query refinement failed: {e}")
        return original_query


def llm_detect_introspection(query: str) -> bool:
    """
    Detect if query is asking about agent capabilities or data inventory
    
    Args:
        query: User query to analyze
        
    Returns:
        True if this is an introspection query
    """
    introspection_keywords = [
        "what data", "what companies", "what years", "available data",
        "what can you", "how do you", "what do you", "help",
        "capabilities", "what information", "what documents"
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in introspection_keywords)


def generate_data_inventory_response() -> str:
    """
    Generate response for data inventory queries
    Note: This should be enhanced to query actual data sources
    """
    return """
I have access to SEC filing data for major US banks including:

**Companies**: BAC (Bank of America), JPM (JPMorgan Chase), GS (Goldman Sachs), 
WFC (Wells Fargo), MS (Morgan Stanley), and others.

**Time Period**: Primarily 2024-2025 data, with some historical information.

**Document Types**: 10-K annual reports, 10-Q quarterly reports, with detailed 
sections including MD&A, Risk Factors, Business Overview, and Financial Statements.

**Capabilities**: I can perform both specific fact extraction and comprehensive 
analysis, with iterative refinement to ensure thorough coverage of your questions.

To get specific data availability for a particular company or timeframe, 
please ask a more targeted question.
"""


def generate_capabilities_response() -> str:
    """
    Generate response for capabilities queries
    """
    return """
I am an advanced SEC filing analysis agent with the following capabilities:

**Intelligent Search**: I can perform both semantic (topic-based) and structured 
(entity-specific) searches across financial documents.

**Iterative Analysis**: For complex questions, I use a progressive approach - 
retrieving information in batches, synthesizing findings, critiquing my own work, 
and refining my search strategy based on gaps identified.

**Adaptive Planning**: I detect query types and adapt my approach accordingly, 
whether you need a quick fact, comprehensive analysis, or comparative study.

**Data Discovery**: Before retrieving content, I explore available data to ensure 
I'm accessing the most relevant information for your specific question.

**Quality Assurance**: I continuously evaluate my responses for completeness and 
accuracy, asking for clarification when I encounter ambiguous requests.

**Structured Output**: I provide well-organized responses with proper citations 
and data coverage summaries.

Feel free to ask me anything about SEC filings, financial data, or company analysis!
"""