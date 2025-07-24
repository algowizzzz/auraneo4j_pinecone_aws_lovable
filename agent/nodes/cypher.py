"""
Cypher Node - Structured Neo4j Graph Queries
Integrates with enhanced Neo4j schema from Week 1
"""

from agent.state import AgentState, RetrievalHit
from neo4j import GraphDatabase
import os
import logging
from typing import List, Dict, Any

# Import enhanced retrieval capabilities
try:
    from agent.integration.enhanced_retrieval import get_enhanced_retriever
    ENHANCED_RETRIEVAL_AVAILABLE = True
except ImportError:
    ENHANCED_RETRIEVAL_AVAILABLE = False

logger = logging.getLogger(__name__)

class Neo4jCypherRetriever:
    """Neo4j retrieval using structured Cypher queries"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        self.user = os.getenv("NEO4J_USERNAME", "neo4j") 
        self.password = os.getenv("NEO4J_PASSWORD", "newpassword")
        self.driver = None
        
    def _get_driver(self):
        """Lazy initialization of Neo4j driver"""
        if self.driver is None:
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise
        return self.driver
    
    def build_cypher_query(self, metadata: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Build dynamic Cypher query based on available metadata.
        Returns (query, parameters)
        """
        conditions = []
        params = {}
        
        # Base query structure matching our enhanced schema
        base_query = """
        MATCH (c:Company)-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)
              -[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)
        """
        
        # Add conditions based on available metadata
        if metadata.get("company"):
            conditions.append("c.name = $company")
            params["company"] = metadata["company"]
        
        if metadata.get("year"):
            conditions.append("y.value = $year")
            params["year"] = int(metadata["year"])
        
        if metadata.get("quarter"):
            conditions.append("q.label = $quarter")
            params["quarter"] = metadata["quarter"]
            
        if metadata.get("doc_type"):
            conditions.append("d.document_type = $doc_type")
            params["doc_type"] = metadata["doc_type"]
        
        # Build WHERE clause
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # Return statement with section data
        return_clause = """
        RETURN s.filename as section_id, 
               s.text as text,
               s.section as section_name,
               c.name as company,
               y.value as year,
               q.label as quarter,
               d.document_type as doc_type,
               s.financial_entities as entities
        ORDER BY y.value DESC, q.label, s.section
        LIMIT 20
        """
        
        full_query = f"{base_query} {where_clause} {return_clause}"
        
        return full_query, params
    
    def execute_cypher_retrieval(self, metadata: Dict[str, Any]) -> List[RetrievalHit]:
        """Execute Cypher query and return structured results"""
        try:
            query, params = self.build_cypher_query(metadata)
            logger.info(f"Executing Cypher query with params: {params}")
            
            driver = self._get_driver()
            
            with driver.session() as session:
                result = session.run(query, params)
                
                hits = []
                for record in result:
                    hit = RetrievalHit(
                        section_id=record["section_id"],
                        text=record["text"] or "",
                        score=1.0,  # Cypher results are exact matches
                        source="cypher",
                        metadata={
                            "section_name": record["section_name"],
                            "company": record["company"],
                            "year": record["year"],
                            "quarter": record["quarter"],
                            "doc_type": record["doc_type"],
                            "financial_entities": record["entities"]
                        }
                    )
                    hits.append(hit)
                
                logger.info(f"Cypher retrieval found {len(hits)} sections")
                return hits
                
        except Exception as e:
            logger.error(f"Cypher retrieval failed: {e}")
            return []
    
    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()

# Global retriever instance
_retriever = Neo4jCypherRetriever()

def cypher(state: AgentState) -> AgentState:
    """
    Cypher retrieval node - retrieves structured data from Neo4j graph
    Enhanced with Week 1 infrastructure for financial entity relationships
    
    Best for: Specific company/year/quarter queries with precise metadata
    """
    try:
        query = state.get("query_raw", "")
        metadata = state.get("metadata", {})
        logger.info(f"Cypher node processing metadata: {metadata}")
        
        # Try enhanced retrieval first if available
        hits = []
        if ENHANCED_RETRIEVAL_AVAILABLE:
            try:
                enhanced_retriever = get_enhanced_retriever()
                # Use enhanced Cypher search with financial entities from planner
                financial_entities = state.get("financial_entities", {})
                hits = enhanced_retriever.enhanced_cypher_search(
                    query, metadata, state_entities=financial_entities
                )
                logger.info(f"Enhanced Cypher search returned {len(hits)} hits")
            except Exception as e:
                logger.warning(f"Enhanced retrieval failed, falling back to standard: {e}")
        
        # Fallback to standard retrieval if enhanced failed or unavailable
        if not hits:
            hits = _retriever.execute_cypher_retrieval(metadata)
            logger.info(f"Standard Cypher search returned {len(hits)} hits")
        
        # Update state
        state["retrievals"] = hits
        
        # Track tool usage and confidence
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("cypher")
        
        if "confidence_scores" not in state:
            state["confidence_scores"] = {}
        
        # Enhanced confidence calculation
        if hits:
            # Higher confidence for enhanced retrieval with financial entities
            base_confidence = 1.0
            if any("enhanced_cypher" in hit.get("source", "") for hit in hits):
                # Boost confidence for enhanced retrieval
                enhanced_confidence = min(1.0, base_confidence * 1.1)
                state["confidence_scores"]["cypher"] = enhanced_confidence
            else:
                state["confidence_scores"]["cypher"] = base_confidence
        else:
            state["confidence_scores"]["cypher"] = 0.0
        
        logger.info(f"Cypher node completed: {len(hits)} hits, confidence: {state['confidence_scores']['cypher']:.2f}")
        
    except Exception as e:
        logger.error(f"Cypher node error: {e}")
        state["retrievals"] = []
        if "error_messages" not in state:
            state["error_messages"] = []
        state["error_messages"].append(f"Cypher error: {str(e)}")
    
    return state

# Cleanup function for proper resource management
def cleanup_cypher():
    """Clean up Neo4j connections"""
    global _retriever
    if _retriever:
        _retriever.close()