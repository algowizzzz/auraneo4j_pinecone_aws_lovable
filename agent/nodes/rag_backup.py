"""
RAG Node - Pure Pinecone Vector Search
Enhanced with Week 1 infrastructure for financial concept search and competitive analysis
"""

from agent.state import AgentState, RetrievalHit
import sys
import os

# Add data_pipeline to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data_pipeline'))

# Import Neo4j text retrieval system (replaces file-based fallback)
from agent.utils.neo4j_text_retrieval import neo4j_text_retriever

try:
    from pinecone_integration import PineconeVectorStore
except ImportError:
    logger.warning("PineconeVectorStore not available - RAG mode will not function")
    PineconeVectorStore = None

# Import enhanced retrieval capabilities
try:
    from agent.integration.enhanced_retrieval import get_enhanced_retriever
    ENHANCED_RETRIEVAL_AVAILABLE = True
except ImportError:
    ENHANCED_RETRIEVAL_AVAILABLE = False

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RAGRetriever:
    """Pure semantic retrieval using Pinecone vector search"""
    
    def __init__(self):
        self.pinecone_store = None
        
        # Initialize Pinecone if available
        if PineconeVectorStore:
            try:
                pinecone_index = os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index')
                self.pinecone_store = PineconeVectorStore(index_name=pinecone_index)
                logger.info("RAG retriever initialized with Pinecone")
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone for RAG: {e}")
                self.pinecone_store = None
    
    def execute_rag_retrieval(self, query: str, companies: Optional[List[str]] = None, top_k: int = 20) -> List[RetrievalHit]:
        """
        Execute pure semantic search across all documents.
        
        Args:
            query: User query for semantic search
            companies: Optional list of companies to filter by
            top_k: Number of results to return
        """
        try:
            if not self.pinecone_store:
                logger.error("Pinecone not available for RAG retrieval")
                return []
            
            # Build optional filter for companies (Pinecone simple format)
            filter_dict = {}
            if companies:
                if len(companies) == 1:
                    filter_dict["company"] = companies[0]  # Simple equality for single company
                else:
                    # For multiple companies, we'll do separate searches and merge
                    # Pinecone doesn't support $in operator easily
                    filter_dict["company"] = companies[0]  # Use first company for now
            
            # Execute semantic search
            logger.info(f"Executing RAG search for: '{query[:50]}...'")
            if filter_dict:
                logger.info(f"With company filter: {companies}")
            
            pinecone_results = self.pinecone_store.similarity_search(
                query=query,
                top_k=top_k,
                filter_dict=filter_dict if filter_dict else None
            )
            
            # Convert to RetrievalHit format with text enhancement
            hits = []
            for result in pinecone_results:
                # Handle both old and new metadata formats
                result_metadata = result['metadata']
                
                # Create initial hit with standardized metadata
                hit_dict = {
                    'section_id': result.get('id', 'unknown'),
                    'text': result_metadata.get('text', ''),
                    'score': float(result['score']),
                    'source': "rag",
                    'metadata': {
                        "section_name": result_metadata.get('section_name', 'Unknown'),
                        "source_filename": result_metadata.get('source_filename', result_metadata.get('filename', 'Unknown')),
                        "company": result_metadata.get('company', 'Unknown'),
                        "year": result_metadata.get('year', 0),
                        "quarter": result_metadata.get('quarter', 'Unknown'),
                        "doc_type": result_metadata.get('document_type', 'Unknown'),
                        "chunk_index": result_metadata.get('chunk_index', 0),
                        "total_chunks": result_metadata.get('total_chunks', 1)
                    }
                }
                
                # Enhance with full text from Neo4j (replaces file-based fallback)
                enhanced_hit = neo4j_text_retriever.enhance_retrieval_with_neo4j_text(hit_dict, min_text_length=500)
                
                # Convert to RetrievalHit
                hit = RetrievalHit(
                    section_id=enhanced_hit['section_id'],
                    text=enhanced_hit['text'],
                    score=enhanced_hit['score'],
                    source=enhanced_hit['source'],
                    metadata=enhanced_hit['metadata']
                )
                hits.append(hit)
            
            enhanced_count = sum(1 for hit in hits if len(hit.get('text', '')) > 500)
            logger.info(f"RAG search found {len(hits)} results, {enhanced_count} enhanced with full text")
            return hits
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return []
    
    def execute_financial_concept_search(self, concepts: List[str], companies: Optional[List[str]] = None, top_k: int = 15) -> List[RetrievalHit]:
        """
        Search for specific financial concepts across documents.
        Uses the financial concept search from our Pinecone integration.
        """
        try:
            if not self.pinecone_store:
                logger.error("Pinecone not available for concept search")
                return []
            
            logger.info(f"Executing financial concept search for: {concepts}")
            
            pinecone_results = self.pinecone_store.search_by_financial_concepts(
                concepts=concepts,
                companies=companies,
                top_k=top_k
            )
            
            # Convert to RetrievalHit format with text enhancement
            hits = []
            for result in pinecone_results:
                # Handle both old and new metadata formats
                result_metadata = result['metadata']
                
                # Create initial hit with standardized metadata
                hit_dict = {
                    'section_id': result.get('id', 'unknown'),
                    'text': result_metadata.get('text', ''),
                    'score': float(result['score']),
                    'source': "rag",
                    'metadata': {
                        "section_name": result_metadata.get('section_name', 'Unknown'),
                        "source_filename": result_metadata.get('source_filename', result_metadata.get('filename', 'Unknown')),
                        "company": result_metadata.get('company', 'Unknown'),
                        "year": result_metadata.get('year', 0),
                        "quarter": result_metadata.get('quarter', 'Unknown'),
                        "doc_type": result_metadata.get('document_type', 'Unknown'),
                        "chunk_index": result_metadata.get('chunk_index', 0),
                        "total_chunks": result_metadata.get('total_chunks', 1)
                    }
                }
                
                # Enhance with full text from Neo4j (replaces file-based fallback)
                enhanced_hit = neo4j_text_retriever.enhance_retrieval_with_neo4j_text(hit_dict, min_text_length=500)
                
                # Convert to RetrievalHit
                hit = RetrievalHit(
                    section_id=enhanced_hit['section_id'],
                    text=enhanced_hit['text'],
                    score=enhanced_hit['score'],
                    source=enhanced_hit['source'],
                    metadata=enhanced_hit['metadata']
                )
                hits.append(hit)
            
            enhanced_count = sum(1 for hit in hits if len(hit.get('text', '')) > 500)
            logger.info(f"Financial concept search found {len(hits)} results, {enhanced_count} enhanced with full text")
            return hits
            
        except Exception as e:
            logger.error(f"Financial concept search failed: {e}")
            return []
    
    def execute_cross_company_search(self, query: str, exclude_company: Optional[str] = None, top_k: int = 15) -> List[RetrievalHit]:
        """
        Search across multiple companies, optionally excluding one.
        Useful for competitive analysis.
        """
        try:
            if not self.pinecone_store:
                logger.error("Pinecone not available for cross-company search")
                return []
            
            filter_dict = {}
            if exclude_company:
                filter_dict["company"] = {"$ne": exclude_company}
            
            logger.info(f"Executing cross-company search for: '{query[:50]}...'")
            if exclude_company:
                logger.info(f"Excluding company: {exclude_company}")
            
            pinecone_results = self.pinecone_store.similarity_search(
                query=query,
                top_k=top_k,
                filter_dict=filter_dict if filter_dict else None
            )
            
            # Convert to RetrievalHit format with text enhancement
            hits = []
            for result in pinecone_results:
                # Handle both old and new metadata formats
                result_metadata = result['metadata']
                
                # Create initial hit with standardized metadata
                hit_dict = {
                    'section_id': result.get('id', 'unknown'),
                    'text': result_metadata.get('text', ''),
                    'score': float(result['score']),
                    'source': "rag",
                    'metadata': {
                        "section_name": result_metadata.get('section_name', 'Unknown'),
                        "source_filename": result_metadata.get('source_filename', result_metadata.get('filename', 'Unknown')),
                        "company": result_metadata.get('company', 'Unknown'),
                        "year": result_metadata.get('year', 0),
                        "quarter": result_metadata.get('quarter', 'Unknown'),
                        "doc_type": result_metadata.get('document_type', 'Unknown'),
                        "chunk_index": result_metadata.get('chunk_index', 0),
                        "total_chunks": result_metadata.get('total_chunks', 1)
                    }
                }
                
                # Enhance with full text from Neo4j (replaces file-based fallback)
                enhanced_hit = neo4j_text_retriever.enhance_retrieval_with_neo4j_text(hit_dict, min_text_length=500)
                
                # Convert to RetrievalHit
                hit = RetrievalHit(
                    section_id=enhanced_hit['section_id'],
                    text=enhanced_hit['text'],
                    score=enhanced_hit['score'],
                    source=enhanced_hit['source'],
                    metadata=enhanced_hit['metadata']
                )
                hits.append(hit)
            
            enhanced_count = sum(1 for hit in hits if len(hit.get('text', '')) > 500)
            logger.info(f"Cross-company search found {len(hits)} results, {enhanced_count} enhanced with full text")
            return hits
            
        except Exception as e:
            logger.error(f"Cross-company search failed: {e}")
            return []

# Global retriever instance
_rag_retriever = RAGRetriever()

def rag(state: AgentState) -> AgentState:
    """
    RAG retrieval node - enhanced semantic search for open-ended queries
    Enhanced with Week 1 infrastructure for financial concept search and competitive analysis
    
    Best for: Incomplete metadata, broad conceptual questions, comparative analysis
    """
    try:
        query = state.get("query_raw", "")
        metadata = state.get("metadata", {})
        
        logger.info(f"RAG node processing query: '{query[:50]}...'")
        
        # Try enhanced retrieval first if available
        hits = []
        if ENHANCED_RETRIEVAL_AVAILABLE:
            try:
                enhanced_retriever = get_enhanced_retriever()
                
                # Check if this is a temporal/competitive analysis query
                comparison_indicators = ["compare", "versus", "vs", "difference", "similar", "peer", "competitor"]
                temporal_indicators = ["trend", "over time", "historical", "since", "through"]
                
                is_comparison = any(indicator in query.lower() for indicator in comparison_indicators)
                is_temporal = any(indicator in query.lower() for indicator in temporal_indicators)
                
                if (is_comparison or is_temporal) and metadata.get("company"):
                    # Use enhanced temporal/competitive search
                    hits = enhanced_retriever.temporal_competitive_search(
                        query=query,
                        company=metadata["company"],
                        timeframe_years=[2021, 2022, 2023, 2024, 2025],  # Default timeframe
                        include_competitors=is_comparison,
                        top_k=20
                    )
                    logger.info(f"Enhanced temporal/competitive search returned {len(hits)} hits")
                else:
                    # Use enhanced Pinecone search with financial entity extraction
                    hits = enhanced_retriever.enhanced_pinecone_search(
                        query=query,
                        metadata=metadata,
                        top_k=20
                    )
                    logger.info(f"Enhanced Pinecone search returned {len(hits)} hits")
                    
            except Exception as e:
                logger.warning(f"Enhanced RAG retrieval failed, falling back to standard: {e}")
        
        # Fallback to standard retrieval if enhanced failed or unavailable
        if not hits:
            # Check if this is a comparative/cross-company query
            comparison_indicators = ["compare", "versus", "vs", "difference", "similar", "peer"]
            is_comparison = any(indicator in query.lower() for indicator in comparison_indicators)
            
            # Check for financial concept keywords
            financial_concepts = ["risk", "capital", "liquidity", "credit", "market", "operational", "regulatory"]
            detected_concepts = [concept for concept in financial_concepts if concept in query.lower()]
            
            if is_comparison and metadata.get("company"):
                # Cross-company search excluding the specified company
                hits = _rag_retriever.execute_cross_company_search(
                    query=query, 
                    exclude_company=metadata["company"],
                    top_k=15
                )
            elif detected_concepts:
                # Financial concept-specific search
                companies = [metadata["company"]] if metadata.get("company") else None
                hits = _rag_retriever.execute_financial_concept_search(
                    concepts=detected_concepts,
                    companies=companies,
                    top_k=15
                )
            else:
                # General semantic search
                companies = [metadata["company"]] if metadata.get("company") else None
                hits = _rag_retriever.execute_rag_retrieval(
                    query=query,
                    companies=companies,
                    top_k=20
                )
            logger.info(f"Standard RAG search returned {len(hits)} hits")
        
        # Update state
        state["retrievals"] = hits
        
        # Track tool usage and confidence
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("rag")
        
        if "confidence_scores" not in state:
            state["confidence_scores"] = {}
        
        # Enhanced confidence calculation
        if hits:
            # For RAG, confidence is based on the average similarity score
            avg_score = sum(hit["score"] for hit in hits) / len(hits)
            base_confidence = min(1.0, avg_score)  # Similarity scores are typically 0-1
            
            # Boost confidence for enhanced retrieval modes
            enhanced_sources = ["enhanced_pinecone", "temporal_analysis", "competitive_analysis"]
            if any(hit.get("source", "") in enhanced_sources for hit in hits):
                enhanced_confidence = min(1.0, base_confidence * 1.1)
                confidence = enhanced_confidence
            else:
                confidence = base_confidence
        else:
            confidence = 0.0
            
        state["confidence_scores"]["rag"] = confidence
        
        logger.info(f"RAG node completed: {len(hits)} hits, confidence: {confidence:.2f}")
        
    except Exception as e:
        logger.error(f"RAG node error: {e}")
        state["retrievals"] = []
        if "error_messages" not in state:
            state["error_messages"] = []
        state["error_messages"].append(f"RAG error: {str(e)}")
    
    return state