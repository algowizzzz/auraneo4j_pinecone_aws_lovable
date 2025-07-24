"""
Planner Node - Intelligent Query Routing for SEC Agent
Enhanced with Week 1 infrastructure for financial entity-aware routing decisions
"""

from langchain_openai import ChatOpenAI
from agent.state import AgentState
import re
import json
import logging
import os
from typing import Dict, Any

# Import enhanced retrieval capabilities for entity extraction
try:
    from agent.integration.enhanced_retrieval import get_enhanced_retriever
    ENHANCED_ENTITY_EXTRACTION_AVAILABLE = True
except ImportError:
    ENHANCED_ENTITY_EXTRACTION_AVAILABLE = False

logger = logging.getLogger(__name__)

# Initialize LLM for planner decisions
_llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Planner system prompt from readme specifications
PLANNER_SYS = """\
You are PlanLLM, an expert routing assistant for an SEC-filing Q&A agent.
Your job is ONLY to produce a valid JSON object with keys:
  route          : "cypher", "hybrid", "rag", or "multi"
  fallback       : ordered list of backup routes
  metadata       : {company, year, quarter, doc_type}
  sub_tasks      : optional [{topic, metadata, suggested_route}]

**Rules**
1. Prefer "cypher" when ALL critical metadata (company, year, quarter OR doc_type)
   is present AND the user asks for a specific fact, figure, or extract.
2. Use "hybrid" when metadata filters exist BUT the user requests explanation,
   summary, comparison, or multi-section reasoning.
3. Use "rag" when metadata is incomplete or the query is open-ended.
4. Use "multi" when ≥2 distinct risk categories, time periods, or companies appear.
5. Provide at most TWO fallback routes.
6. Confidence is implicit in your routing order; do not add extra keys.

Return ONLY valid JSON. Do NOT wrap in markdown.
"""

def _extract_metadata(query: str) -> Dict[str, Any]:
    """
    Extract metadata from query using regex patterns.
    Looks for company names, years, quarters, and document types.
    """
    metadata = {}
    
    # Company patterns - expanded from readme example
    company_patterns = [
        r"\b(?:Bank\s+of\s+Montreal|BMO)\b",
        r"\b(?:Bank\s+of\s+America|BAC)\b", 
        r"\b(?:JPMorgan|JPM)\b",
        r"\b(?:Wells\s+Fargo|WFC)\b",
        r"\b(?:Zions?\s+Banc?corporation|ZION)\b",
        r"\b(?:KeyCorp|KEY)\b",
        r"\b(?:Truist|TFC)\b",
        r"\b(?:Bank\s+of\s+New\s+York\s+Mellon|BK)\b",
        # Add all companies from our dataset
        r"\b(?:BOKF|BPOP|CBSH|CFG|CFR|CMA|EWBC|FCNCA|FHN|FITB|MTB|ONB|PB|PNFP|RF|SNV|SSB|UMBF|USB|WAL|WBS|WTFC)\b"
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            metadata["company"] = match.group(0).upper()
            break
    
    # Year pattern
    year_match = re.search(r"\b(20[2-3]\d)\b", query)
    if year_match:
        metadata["year"] = year_match.group(1)
    
    # Quarter pattern
    quarter_match = re.search(r"\b(Q[1-4]|[Qq]uarter\s+[1-4])\b", query, re.IGNORECASE)
    if quarter_match:
        q_text = quarter_match.group(1).upper()
        if q_text.startswith('Q'):
            metadata["quarter"] = q_text
        else:
            # Convert "Quarter 1" to "Q1"
            q_num = re.search(r'(\d)', q_text).group(1)
            metadata["quarter"] = f"Q{q_num}"
    
    # Document type pattern
    doc_patterns = [
        r"\b(10-K)\b",
        r"\b(10-Q)\b", 
        r"\b(8-K)\b",
        r"\bItem\s+1A\b",  # Risk factors section
        r"\bItem\s+1\b",   # Business section
        r"\bItem\s+7\b"    # MD&A section
    ]
    
    for pattern in doc_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            metadata["doc_type"] = match.group(1).upper()
            break
    
    return metadata

def planner(state: AgentState) -> AgentState:
    """
    Enhanced planner function implementing intelligent routing logic.
    
    Uses LLM and financial entity extraction to make routing decisions based on:
    - Extracted metadata completeness
    - Financial entity analysis from Week 1 infrastructure
    - Query type classification  
    - Multi-topic detection
    - Confidence-based fallback planning
    """
    try:
        query = state["query_raw"]
        logger.info(f"Planning route for query: {query[:100]}...")
        
        # Extract metadata using regex
        meta_raw = _extract_metadata(query)
        logger.debug(f"Extracted metadata: {meta_raw}")
        
        # Extract financial entities if enhanced infrastructure is available
        financial_entities = {}
        if ENHANCED_ENTITY_EXTRACTION_AVAILABLE:
            try:
                enhanced_retriever = get_enhanced_retriever()
                financial_entities = enhanced_retriever.extract_financial_entities_from_query(query)
                logger.info(f"Extracted financial entities: {financial_entities}")
            except Exception as e:
                logger.warning(f"Financial entity extraction failed: {e}")
        
        # Enhanced prompt including financial entity analysis
        enhanced_prompt_addition = ""
        if financial_entities:
            enhanced_prompt_addition = f"\n\nDetected financial entities:\n{json.dumps(financial_entities, indent=2)}\n\nConsider these entities when making routing decisions:\n- Cypher: Better for specific entities with complete metadata\n- Hybrid: Good for entity relationships and explanations\n- RAG: Best for concept exploration across entities"
        
        # Ask LLM to make routing decision
        prompt = (
            PLANNER_SYS
            + "\n\nUser query:\n"
            + query
            + "\n\nExtracted metadata (may be partial):\n"
            + json.dumps(meta_raw, indent=2)
            + enhanced_prompt_addition
        )
        
        response = _llm.invoke(prompt)
        result_text = response.content.strip()
        
        # Clean up response if it's wrapped in markdown
        if result_text.startswith("```"):
            result_text = result_text.split('\n', 1)[1]
        if result_text.endswith("```"):
            result_text = result_text.rsplit('\n', 1)[0]
        
        try:
            plan = json.loads(result_text)
        except json.JSONDecodeError as e:
            logger.warning(f"LLM returned invalid JSON: {result_text}")
            # Fallback to safe defaults
            plan = {
                "route": "rag",
                "fallback": ["hybrid"],
                "metadata": meta_raw,
                "sub_tasks": []
            }
        
        # Ensure required fields exist
        plan.setdefault("route", "rag")
        plan.setdefault("fallback", ["hybrid"])
        plan.setdefault("metadata", meta_raw)
        plan.setdefault("sub_tasks", [])
        
        # Update state with planning results
        state.update(plan)
        
        # Store financial entities for use by retrieval nodes
        if financial_entities:
            state["financial_entities"] = financial_entities
        
        # Track tool usage for debugging
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("planner")
        
        logger.info(f"Planned route: {plan['route']}, fallbacks: {plan['fallback']}")
        if plan['sub_tasks']:
            logger.info(f"Sub-tasks detected: {len(plan['sub_tasks'])}")
        
        return state
        
    except Exception as e:
        logger.error(f"Planner failed: {e}")
        # Safe fallback
        state.update({
            "route": "rag",
            "fallback": ["hybrid"],
            "metadata": {},
            "sub_tasks": [],
            "error_messages": [f"Planner error: {str(e)}"]
        })
        return state

# Test the planner with sample queries
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_queries = [
        "What are BMO's top risks in 2025 Q1?",
        "Compare JPMorgan and Bank of America's operational risk strategies", 
        "Explain Zions Bancorporation's business model evolution",
        "What regulatory changes affected banks in 2024?"
    ]
    
    for query in test_queries:
        print(f"\n=== Testing: {query} ===")
        state = {"query_raw": query}
        result = planner(state)
        print(f"Route: {result['route']}")
        print(f"Metadata: {result['metadata']}")
        print(f"Fallbacks: {result['fallback']}")
        if result.get('sub_tasks'):
            print(f"Sub-tasks: {[t['topic'] for t in result['sub_tasks']]}")