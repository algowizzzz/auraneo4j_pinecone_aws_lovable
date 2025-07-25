"""
Hybrid Node - Neo4j Filtering + Pinecone Vector Search
Enhanced with Week 1 infrastructure for advanced financial entity relationships
"""

from agent.state import AgentState, RetrievalHit
from agent.nodes.cypher import Neo4jCypherRetriever
import sys
import os

# Add data_pipeline to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data_pipeline'))

try:
    from pinecone_integration import PineconeVectorStore
except ImportError:
    logger.warning("PineconeVectorStore not available - hybrid mode will fall back to Cypher only")
    PineconeVectorStore = None

# Import enhanced retrieval capabilities
try:
    from agent.integration.enhanced_retrieval import get_enhanced_retriever
    ENHANCED_RETRIEVAL_AVAILABLE = True
except ImportError:
    ENHANCED_RETRIEVAL_AVAILABLE = False

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class HybridRetriever:
    """Hybrid retrieval combining Neo4j metadata filtering with Pinecone semantic search"""
    
    def __init__(self):
        self.neo4j_retriever = Neo4jCypherRetriever()
        self.pinecone_store = None
        
        # Initialize Pinecone if available
        if PineconeVectorStore:
            try:
                pinecone_index = os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index') 
                self.pinecone_store = PineconeVectorStore(index_name=pinecone_index)
                logger.info("Hybrid retriever initialized with Pinecone")
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone for hybrid: {e}")
                self.pinecone_store = None
    
    def execute_hybrid_retrieval(self, query: str, metadata: Dict[str, Any], top_k: int = 15) -> List[RetrievalHit]:
        """
        Execute hybrid retrieval:
        1. Use metadata to filter relevant documents via Neo4j
        2. Perform semantic search within filtered set via Pinecone
        3. Merge and rank results
        """
        try:
            # Step 1: If we have Pinecone, use it with metadata filters
            if self.pinecone_store and metadata:
                logger.info("Executing Pinecone search with metadata filters")
                return self._pinecone_filtered_search(query, metadata, top_k)
            
            # Step 2: Fallback to Neo4j-only search with text matching
            else:
                logger.info("Falling back to Neo4j text matching")
                return self._neo4j_text_search(query, metadata, top_k)
                
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            return []
    
    def _pinecone_filtered_search(self, query: str, metadata: Dict[str, Any], top_k: int) -> List[RetrievalHit]:
        """Use Pinecone with metadata filtering"""
        try:
            # Build Pinecone filter dict (simple equality format)
            filter_dict = {}
            
            if metadata.get("company"):
                filter_dict["company"] = metadata["company"]
            
            if metadata.get("year"):
                filter_dict["year"] = int(metadata["year"])
                
            if metadata.get("quarter"):
                filter_dict["quarter"] = metadata["quarter"]
                
            if metadata.get("doc_type"):
                filter_dict["document_type"] = metadata["doc_type"]
            
            # Execute Pinecone search
            pinecone_results = self.pinecone_store.similarity_search(
                query=query,
                top_k=top_k,
                filter_dict=filter_dict
            )
            
            # Convert to RetrievalHit format
            hits = []
            for result in pinecone_results:
                hit = RetrievalHit(
                    section_id=result.get('id', 'unknown'),
                    text=result['metadata'].get('text', ''),
                    score=float(result['score']),
                    source="hybrid",
                    metadata=result['metadata']
                )
                hits.append(hit)
            
            logger.info(f"Pinecone hybrid search found {len(hits)} results")
            return hits
            
        except Exception as e:
            logger.error(f"Pinecone filtered search failed: {e}")
            return []
    
    def _neo4j_text_search(self, query: str, metadata: Dict[str, Any], top_k: int) -> List[RetrievalHit]:
        """Fallback to Neo4j fulltext search when Pinecone unavailable"""
        try:
            driver = self.neo4j_retriever._get_driver()
            
            # Build text search query
            base_query = """
            CALL db.index.fulltext.queryNodes('section_text_index', $search_text) 
            YIELD node, score
            MATCH (node)<-[:HAS_SECTION]-(d:Document)<-[:HAS_DOC]-(q:Quarter)<-[:HAS_QUARTER]-(y:Year)<-[:HAS_YEAR]-(c:Company)
            """
            
            # Add metadata filters
            conditions = []
            params = {"search_text": query}
            
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
            
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            return_clause = f"""
            {where_clause}
            RETURN c.name as company, y.value as year, q.label as quarter, 
                   d.document_type as doc_type, node.section as section_name,
                   node.filename as section_id, node.text as text, score
            ORDER BY score DESC
            LIMIT $top_k
            """
            
            full_query = f"{base_query} {return_clause}"
            params["top_k"] = top_k
            
            with driver.session() as session:
                result = session.run(full_query, params)
                
                hits = []
                for record in result:
                    hit = RetrievalHit(
                        section_id=record["section_id"],
                        text=record["text"] or "",
                        score=float(record["score"]),
                        source="hybrid",
                        metadata={
                            "section_name": record["section_name"],
                            "company": record["company"],
                            "year": record["year"],
                            "quarter": record["quarter"],
                            "doc_type": record["doc_type"]
                        }
                    )
                    hits.append(hit)
                
                logger.info(f"Neo4j text search found {len(hits)} results")
                return hits
                
        except Exception as e:
            logger.error(f"Neo4j text search failed: {e}")
            return []

# Global retriever instance
_hybrid_retriever = HybridRetriever()

def hybrid(state: AgentState) -> AgentState:
    """
    Hybrid retrieval node - enhanced metadata filtering with semantic search
    Enhanced with Week 1 infrastructure for financial entity relationships and advanced filtering
    
    Best for: Queries with some metadata but requiring explanation/summary
    """
    try:
        query = state.get("query_raw", "")
        metadata = state.get("metadata", {})
        
        logger.info(f"Hybrid node processing query: '{query[:50]}...' with metadata: {metadata}")
        
        # Try enhanced retrieval first if available
        hits = []
        if ENHANCED_RETRIEVAL_AVAILABLE:
            try:
                enhanced_retriever = get_enhanced_retriever()
                
                # Use enhanced Pinecone search which combines metadata filtering with entity extraction
                hits = enhanced_retriever.enhanced_pinecone_search(
                    query=query,
                    metadata=metadata,
                    top_k=15
                )
                logger.info(f"Enhanced hybrid search returned {len(hits)} hits")
                
                # If we have a company and year range, also try temporal analysis
                if metadata.get("company") and not hits:
                    temporal_hits = enhanced_retriever.temporal_competitive_search(
                        query=query,
                        company=metadata["company"],
                        timeframe_years=[2021, 2022, 2023, 2024, 2025],
                        include_competitors=False,  # Focus on company history
                        top_k=10
                    )
                    hits.extend(temporal_hits)
                    logger.info(f"Added {len(temporal_hits)} temporal analysis hits")
                    
            except Exception as e:
                logger.warning(f"Enhanced hybrid retrieval failed, falling back to standard: {e}")
        
        # Fallback to standard retrieval if enhanced failed or unavailable
        if not hits:
            hits = _hybrid_retriever.execute_hybrid_retrieval(query, metadata, top_k=15)
            logger.info(f"Standard hybrid search returned {len(hits)} hits")
        
        # Update state
        state["retrievals"] = hits
        
        # Track tool usage and confidence
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("hybrid")
        
        if "confidence_scores" not in state:
            state["confidence_scores"] = {}
        
        # Enhanced confidence calculation
        if hits:
            avg_score = sum(hit["score"] for hit in hits) / len(hits)
            base_confidence = min(1.0, avg_score * (len(hits) / 10))  # Normalize
            
            # Boost confidence for enhanced retrieval modes
            enhanced_sources = ["enhanced_pinecone", "temporal_analysis"]
            if any(hit.get("source", "") in enhanced_sources for hit in hits):
                enhanced_confidence = min(1.0, base_confidence * 1.15)  # Higher boost for hybrid
                confidence = enhanced_confidence
            else:
                confidence = base_confidence
        else:
            confidence = 0.0
            
        state["confidence_scores"]["hybrid"] = confidence
        
        logger.info(f"Hybrid node completed: {len(hits)} hits, confidence: {confidence:.2f}")
        
    except Exception as e:
        logger.error(f"Hybrid node error: {e}")
        state["retrievals"] = []
        if "error_messages" not in state:
            state["error_messages"] = []
        state["error_messages"].append(f"Hybrid error: {str(e)}")
    
    return state