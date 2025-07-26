"""
Enhanced Planner Node - Holistic Query Routing Intelligence
Addresses systemic routing issues identified in analysis:
1. Overly aggressive Cypher routing
2. Poor section-specific query handling
3. No tabular data recognition
4. Generic fallback strategies
5. Missing multi-step workflow support
"""

from langchain_openai import ChatOpenAI
from agent.state import AgentState
import re
import json
import logging
import os
from typing import Dict, Any, List, Tuple
from enum import Enum

# Import enhanced capabilities
try:
    from agent.integration.enhanced_retrieval import get_enhanced_retriever
    ENHANCED_ENTITY_EXTRACTION_AVAILABLE = True
except ImportError:
    ENHANCED_ENTITY_EXTRACTION_AVAILABLE = False

try:
    from agent.utils.company_mapping import normalize_company
    COMPANY_MAPPING_AVAILABLE = True
except ImportError:
    COMPANY_MAPPING_AVAILABLE = False

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Enhanced query classification"""
    SINGLE_FACT = "single_fact"          # "What is BAC's CET1 ratio?"
    TABULAR_DATA = "tabular_data"        # "Show balance sheet table"
    SECTION_CONTENT = "section_content"   # "From MD&A section, what..."
    EXPLANATION = "explanation"           # "Explain risk management strategy"
    COMPARISON = "comparison"             # "Compare GS and MS"
    OPEN_ENDED = "open_ended"            # "What are banking trends?"
    MULTI_STEP = "multi_step"            # "From balance sheet, show assets"

class QueryClassifier:
    """Intelligent query classification for better routing decisions"""
    
    # Patterns for different query types
    TABULAR_PATTERNS = [
        r'\b(?:balance\s+sheet|income\s+statement|cash\s+flow\s+statement)\b',
        r'\b(?:table|chart|schedule|exhibit)\b',
        r'\b(?:financial\s+highlights|key\s+metrics|summary\s+data)\b',
        r'\b(?:consolidated\s+statements?)\b',
        r'\bshow\s+(?:me\s+)?(?:the\s+)?(?:numbers|figures|data|metrics)\b'
    ]
    
    SECTION_PATTERNS = [
        r'\bfrom\s+(?:the\s+)?(?:MD&A|md&a|management.+discussion)\b',
        r'\bin\s+(?:the\s+)?(?:risk\s+factors?|business\s+section)\b',
        r'\b(?:Item\s+[1-9A-Z]+|section\s+[1-9A-Z]+)\b',
        r'\bfrom\s+(?:the\s+)?(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s+section\b'
    ]
    
    EXPLANATION_PATTERNS = [
        r'\b(?:explain|describe|discuss|analyze|detail)\b',
        r'\b(?:what\s+is|how\s+does|why\s+did|how\s+has)\b',
        r'\b(?:strategy|approach|methodology|framework)\b',
        r'\b(?:factors?|reasons?|causes?|impacts?)\b'
    ]
    
    COMPARISON_PATTERNS = [
        r'\b(?:compare|contrast|versus|vs\.?|against)\b',
        r'\b(?:differences?|similarities|compared\s+to)\b',
        r'\band\s+[A-Z]{2,5}\b.*\b(?:revenue|performance|risk)\b',  # "GS and MS revenue"
        r'\bbetween\s+\w+\s+and\s+\w+\b'
    ]
    
    SINGLE_FACT_PATTERNS = [
        r'\bwhat\s+(?:is|was|were)\s+(?:the\s+)?(?:specific|exact)?\s*[A-Z]+.+\b(?:ratio|rate|amount|value|number)\b',
        r'\b(?:CET1|tier\s+1|leverage|ROE|ROA|ROI)\s+ratio\b',
        r'\btotal\s+(?:assets|revenue|income|deposits)\b',
        r'\bnet\s+(?:income|revenue|interest\s+income)\b'
    ]
    
    MULTI_STEP_PATTERNS = [
        r'\bfrom\s+(?:.+?),\s*(?:show|find|get|extract|what)\b',
        r'\bin\s+(?:.+?)\s+section,\s*(?:show|find|what|how)\b',
        r'\baccording\s+to\s+(?:.+?),\s*(?:what|show|find)\b'
    ]
    
    @classmethod
    def classify_query(cls, query: str) -> Tuple[QueryType, float]:
        """
        Classify query type with confidence score
        Returns: (QueryType, confidence_score)
        """
        query_lower = query.lower()
        
        # Multi-step detection (highest priority)
        multi_step_score = cls._pattern_match_score(query_lower, cls.MULTI_STEP_PATTERNS)
        if multi_step_score > 0.7:
            return QueryType.MULTI_STEP, multi_step_score
        
        # Tabular data detection
        tabular_score = cls._pattern_match_score(query_lower, cls.TABULAR_PATTERNS)
        if tabular_score > 0.5:
            return QueryType.TABULAR_DATA, tabular_score
            
        # Section content detection
        section_score = cls._pattern_match_score(query_lower, cls.SECTION_PATTERNS)
        if section_score > 0.5:
            return QueryType.SECTION_CONTENT, section_score
        
        # Comparison detection
        comparison_score = cls._pattern_match_score(query_lower, cls.COMPARISON_PATTERNS)
        if comparison_score > 0.5:
            return QueryType.COMPARISON, comparison_score
        
        # Explanation detection  
        explanation_score = cls._pattern_match_score(query_lower, cls.EXPLANATION_PATTERNS)
        if explanation_score > 0.4:
            return QueryType.EXPLANATION, explanation_score
        
        # Single fact detection
        fact_score = cls._pattern_match_score(query_lower, cls.SINGLE_FACT_PATTERNS)
        if fact_score > 0.6:
            return QueryType.SINGLE_FACT, fact_score
        
        # Default to open-ended
        return QueryType.OPEN_ENDED, 0.3
    
    @staticmethod
    def _pattern_match_score(text: str, patterns: List[str]) -> float:
        """Calculate match score for a list of patterns"""
        matches = 0
        total_patterns = len(patterns)
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        
        return matches / total_patterns if total_patterns > 0 else 0.0

class EnhancedQueryRouter:
    """Enhanced routing logic based on query classification"""
    
    # Routing rules based on query type
    ROUTING_RULES = {
        QueryType.SINGLE_FACT: {
            "primary": "cypher",
            "fallback": ["hybrid", "rag"],
            "reason": "Single facts work well with structured Neo4j queries"
        },
        QueryType.TABULAR_DATA: {
            "primary": "hybrid", 
            "fallback": ["rag", "cypher"],
            "reason": "Tables need semantic search to find table sections first"
        },
        QueryType.SECTION_CONTENT: {
            "primary": "hybrid",
            "fallback": ["rag", "cypher"], 
            "reason": "Sections need semantic search to locate content"
        },
        QueryType.EXPLANATION: {
            "primary": "hybrid",
            "fallback": ["rag", "multi"],
            "reason": "Explanations need cross-section reasoning"
        },
        QueryType.COMPARISON: {
            "primary": "multi",
            "fallback": ["hybrid", "rag"],
            "reason": "Comparisons often involve multiple entities/timeframes"
        },
        QueryType.OPEN_ENDED: {
            "primary": "rag",
            "fallback": ["hybrid", "multi"],
            "reason": "Open questions need broad semantic search"
        },
        QueryType.MULTI_STEP: {
            "primary": "hybrid",
            "fallback": ["rag", "multi"],
            "reason": "Multi-step queries need flexible retrieval strategies"
        }
    }
    
    @classmethod
    def route(cls, query_type: QueryType, metadata_completeness: float) -> Dict[str, Any]:
        """
        Route query based on type and metadata completeness
        
        Args:
            query_type: Classified query type
            metadata_completeness: Score 0-1 for how complete metadata is
            
        Returns:
            Dict with route, fallback, and reasoning
        """
        base_routing = cls.ROUTING_RULES[query_type]
        
        # Adjust routing based on metadata completeness
        route = base_routing["primary"]
        fallback = base_routing["fallback"].copy()
        
        # If metadata is very incomplete, prefer RAG over Cypher
        if metadata_completeness < 0.3 and route == "cypher":
            route = "rag"
            fallback = ["hybrid", "cypher"]
        
        # If it's a comparison but only one company detected, use hybrid
        if query_type == QueryType.COMPARISON and metadata_completeness < 0.5:
            route = "hybrid"
            fallback = ["rag", "multi"]
        
        return {
            "route": route,
            "fallback": fallback,
            "reason": base_routing["reason"],
            "query_type": query_type.value,
            "metadata_completeness": metadata_completeness
        }

# Initialize LLM for enhanced planning
_llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Enhanced system prompt with better routing logic
ENHANCED_PLANNER_SYS = """\
You are an expert SEC filing query routing system. Your job is to produce a JSON object with:
  route          : "cypher", "hybrid", "rag", or "multi"
  fallback       : ordered list of backup routes
  metadata       : {company, year, quarter, doc_type}
  sub_tasks      : optional sub-task breakdown
  reasoning      : brief explanation of routing decision

**ENHANCED ROUTING INTELLIGENCE**

1. **TABULAR DATA QUERIES** (balance sheet, income statement, financial tables):
   → Route: "hybrid" or "rag" (need semantic search to find table sections)
   → Examples: "balance sheet table", "show financial highlights", "income statement data"

2. **SECTION-SPECIFIC QUERIES** (MD&A, Risk Factors, specific sections):
   → Route: "hybrid" or "rag" (need semantic search to locate sections)
   → Examples: "from MD&A section", "risk factors discussion", "business overview"

3. **SINGLE FACT EXTRACTION** (specific ratios, single numbers):
   → Route: "cypher" (structured queries work well for single facts)
   → Examples: "CET1 ratio", "total assets", "net income"

4. **EXPLANATORY QUERIES** (strategies, explanations, analysis):
   → Route: "hybrid" (need cross-section reasoning)
   → Examples: "explain strategy", "discuss approach", "analyze factors"

5. **COMPARISON QUERIES** (multiple entities, comparisons):
   → Route: "multi" or "hybrid" (need multiple data sources)
   → Examples: "compare GS and MS", "JPM versus BAC"

6. **OPEN-ENDED QUERIES** (industry trends, general questions):
   → Route: "rag" (need broad semantic search)
   → Examples: "banking trends", "regulatory changes"

**CRITICAL**: Extract complete metadata and provide clear reasoning for your routing decision.

Return ONLY valid JSON. Do NOT wrap in markdown.
"""

def _extract_enhanced_metadata(query: str) -> Dict[str, Any]:
    """Enhanced metadata extraction with better company detection"""
    metadata = {}
    
    # Company patterns - more comprehensive
    company_patterns = [
        # Full names
        r'\b(Bank of America|Wells Fargo|JPMorgan Chase|Goldman Sachs|Morgan Stanley|Citigroup)\b',
        # Tickers
        r'\b(BAC|WFC|JPM|GS|MS|C|TFC|FITB|RF|KEY|ZION)\b',
        # Partial names that should map
        r'\b(Goldman|Morgan|Wells|Citi|Truist|Fifth Third)\b'
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            metadata["company"] = match.group(1)
            break
    
    # Year extraction
    year_match = re.search(r'\b(20[2-3]\d)\b', query)
    if year_match:
        metadata["year"] = year_match.group(1)
    
    # Quarter extraction
    quarter_match = re.search(r'\b(Q[1-4]|[Qq]uarter\s+[1-4])\b', query, re.IGNORECASE)
    if quarter_match:
        q_text = quarter_match.group(1).upper()
        if q_text.startswith('Q'):
            metadata["quarter"] = q_text
        else:
            q_num = re.search(r'(\d)', q_text).group(1)
            metadata["quarter"] = f"Q{q_num}"
    
    # Document type extraction - enhanced
    doc_patterns = [
        (r'\b(10-K)\b', '10-K'),
        (r'\b(10-Q)\b', '10-Q'),
        (r'\b(8-K)\b', '8-K'),
        (r'\bMD&A\b', 'MD&A'),
        (r'\brisk\s+factors?\b', 'Risk Factors'),
        (r'\bbusiness\s+(?:section|overview)\b', 'Business')
    ]
    
    for pattern, doc_type in doc_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            metadata["doc_type"] = doc_type
            break
    
    return metadata

def _calculate_metadata_completeness(metadata: Dict[str, Any]) -> float:
    """Calculate how complete the metadata is (0-1 score)"""
    weights = {
        "company": 0.4,    # Most important
        "year": 0.3,       # Very important  
        "doc_type": 0.2,   # Somewhat important
        "quarter": 0.1     # Least important
    }
    
    score = 0.0
    for field, weight in weights.items():
        if metadata.get(field):
            score += weight
    
    return min(score, 1.0)

def planner(state: AgentState) -> AgentState:
    """
    Enhanced planner with holistic query routing intelligence
    
    Addresses identified systemic issues:
    1. Better query type classification
    2. Tabular data specific handling
    3. Section-aware routing
    4. Context-aware fallback strategies
    5. Multi-step query support
    """
    try:
        query = state["query_raw"]
        logger.info(f"Enhanced planning for query: {query[:100]}...")
        
        # Step 1: Enhanced metadata extraction
        metadata = _extract_enhanced_metadata(query)
        metadata_completeness = _calculate_metadata_completeness(metadata)
        logger.debug(f"Metadata: {metadata}, completeness: {metadata_completeness:.2f}")
        
        # Step 2: Intelligent query classification
        query_type, classification_confidence = QueryClassifier.classify_query(query)
        logger.info(f"Query classified as: {query_type.value} (confidence: {classification_confidence:.2f})")
        
        # Step 3: Enhanced routing decision
        routing_decision = EnhancedQueryRouter.route(query_type, metadata_completeness)
        logger.info(f"Routing decision: {routing_decision['route']} (reason: {routing_decision['reason']})")
        
        # Step 4: LLM validation and metadata completion
        llm_prompt = (
            ENHANCED_PLANNER_SYS
            + f"\n\nQuery: {query}"
            + f"\n\nPre-classified as: {query_type.value}"
            + f"\n\nSuggested route: {routing_decision['route']}"
            + f"\n\nPartial metadata: {json.dumps(metadata, indent=2)}"
            + f"\n\nComplete the metadata extraction and validate/adjust the routing decision."
        )
        
        response = _llm.invoke(llm_prompt)
        result_text = response.content.strip()
        
        # Clean markdown if present
        if result_text.startswith("```"):
            result_text = result_text.split('\n', 1)[1]
        if result_text.endswith("```"):
            result_text = result_text.rsplit('\n', 1)[0]
        
        try:
            llm_plan = json.loads(result_text)
        except json.JSONDecodeError as e:
            logger.warning(f"LLM returned invalid JSON, using rule-based routing: {result_text}")
            llm_plan = {
                "route": routing_decision["route"],
                "fallback": routing_decision["fallback"],
                "metadata": metadata,
                "reasoning": routing_decision["reason"]
            }
        
        # Step 5: Finalize plan with enhancements
        final_plan = {
            "route": llm_plan.get("route", routing_decision["route"]),
            "fallback": llm_plan.get("fallback", routing_decision["fallback"]),
            "metadata": llm_plan.get("metadata", metadata),
            "sub_tasks": llm_plan.get("sub_tasks", []),
            "reasoning": llm_plan.get("reasoning", routing_decision["reason"]),
            "query_type": query_type.value,
            "classification_confidence": classification_confidence,
            "metadata_completeness": metadata_completeness
        }
        
        # Step 6: Company name normalization
        if COMPANY_MAPPING_AVAILABLE and final_plan["metadata"].get("company"):
            raw_company = final_plan["metadata"]["company"]
            normalized_ticker = normalize_company(raw_company)
            
            if normalized_ticker:
                final_plan["metadata"]["company"] = normalized_ticker
                logger.info(f"Normalized '{raw_company}' → '{normalized_ticker}'")
            else:
                logger.warning(f"Could not normalize company: '{raw_company}'")
        
        # Step 7: Update state
        state.update(final_plan)
        
        # Step 8: Track tool usage
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("enhanced_planner")
        
        logger.info(f"Final routing: {final_plan['route']} → {final_plan['fallback']}")
        logger.info(f"Query type: {query_type.value}, Reasoning: {final_plan.get('reasoning', 'N/A')}")
        
        return state
        
    except Exception as e:
        logger.error(f"Enhanced planner failed: {e}")
        # Intelligent fallback based on query patterns
        safe_route = "rag"  # Most versatile default
        if "table" in query.lower() or "balance sheet" in query.lower():
            safe_route = "hybrid"  # Better for tabular data
        
        state.update({
            "route": safe_route,
            "fallback": ["hybrid", "rag"],
            "metadata": {},
            "sub_tasks": [],
            "reasoning": f"Fallback due to planner error: {str(e)}",
            "error_messages": [f"Enhanced planner error: {str(e)}"]
        })
        return state

# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_queries = [
        "From BAC 2025 10-K filing, balance sheet table",
        "Show me JPM's income statement numbers from 2024", 
        "What is Wells Fargo's CET1 ratio in 2024?",
        "Explain BAC's risk management strategy",
        "Compare GS and MS revenue trends",
        "What are the main banking industry trends?",
        "From MS 2025 MD&A section, what are key highlights?"
    ]
    
    print("🧪 TESTING ENHANCED PLANNER")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        state = {"query_raw": query}
        result = planner(state)
        
        print(f"   Route: {result['route']}")
        print(f"   Type: {result.get('query_type', 'unknown')}")
        print(f"   Company: {result['metadata'].get('company', 'none')}")
        print(f"   Reasoning: {result.get('reasoning', 'none')[:60]}...")
        print(f"   Fallback: {result['fallback']}")