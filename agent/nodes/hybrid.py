"""
Hybrid Node - Neo4j Filtering + Pinecone Vector Search (FIXED VERSION)
Enhanced with better temporal query handling and fallback mechanisms
"""

from agent.state import AgentState, RetrievalHit
from agent.nodes.cypher import Neo4jCypherRetriever
import sys
import os
import logging
from typing import List, Dict, Any

# Add data_pipeline to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data_pipeline'))

try:
    from pinecone_integration import PineconeVectorStore
    PINECONE_AVAILABLE = True
except ImportError:
    logger.warning("PineconeVectorStore not available - hybrid mode will fall back to Cypher only")
    PineconeVectorStore = None
    PINECONE_AVAILABLE = False

logger = logging.getLogger(__name__)

class ImprovedHybridRetriever:
    """Improved hybrid retrieval with better temporal query handling"""
    
    def __init__(self):
        self.neo4j_retriever = Neo4jCypherRetriever()
        self.pinecone_store = None
        
        # Initialize Pinecone if available
        if PINECONE_AVAILABLE:
            try:
                pinecone_index = os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index') 
                self.pinecone_store = PineconeVectorStore(index_name=pinecone_index)
                logger.info("Improved hybrid retriever initialized with Pinecone")
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone for hybrid: {e}")
                self.pinecone_store = None
    
    def execute_hybrid_retrieval(self, query: str, metadata: Dict[str, Any], top_k: int = 20) -> List[RetrievalHit]:
        """
        Execute improved hybrid retrieval with better temporal handling:
        1. Check data availability for requested filters
        2. Relax filters if no data found
        3. Fall back gracefully to broader searches
        """
        try:
            # Step 1: Try exact metadata match
            if self.pinecone_store and metadata:
                logger.info("Trying exact metadata match with Pinecone")
                hits = self._pinecone_filtered_search(query, metadata, top_k)
                
                if hits:
                    logger.info(f"Exact match found {len(hits)} results")
                    return hits
                
                # Step 2: If no results, try relaxed temporal search
                if metadata.get("company") and metadata.get("year"):
                    logger.info("Exact match failed, trying relaxed temporal search")
                    hits = self._relaxed_temporal_search(query, metadata, top_k)
                    
                    if hits:
                        logger.info(f"Relaxed temporal search found {len(hits)} results")
                        return hits
                
                # Step 3: Try company-only search
                if metadata.get("company"):
                    logger.info("Temporal search failed, trying company-only search")
                    company_metadata = {"company": metadata["company"]}
                    hits = self._pinecone_filtered_search(query, company_metadata, top_k)
                    
                    if hits:
                        logger.info(f"Company-only search found {len(hits)} results")
                        return hits
            
            # Step 4: Final fallback to Neo4j text search
            logger.info("All Pinecone searches failed, falling back to Neo4j")
            return self._neo4j_fallback_search(query, metadata, top_k)
                
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            return []
    
    def _pinecone_filtered_search(self, query: str, metadata: Dict[str, Any], top_k: int) -> List[RetrievalHit]:
        """Use Pinecone with metadata filtering - UPDATED for chunked data"""
        try:
            # Build Pinecone filter dict (use proper format for new API)
            filter_dict = {}
            
            if metadata.get("company"):
                filter_dict["company"] = {"$eq": metadata["company"]}
            
            if metadata.get("year"):
                filter_dict["year"] = {"$eq": int(metadata["year"])}
                
            if metadata.get("quarter"):
                filter_dict["quarter"] = {"$eq": metadata["quarter"]}
                
            if metadata.get("doc_type"):
                filter_dict["document_type"] = {"$eq": metadata["doc_type"]}
            
            # Execute Pinecone search
            pinecone_results = self.pinecone_store.similarity_search(
                query=query,
                top_k=top_k,
                filter_dict=filter_dict if filter_dict else None
            )
            
            # Convert to RetrievalHit format
            hits = []
            for result in pinecone_results:
                # Handle both old and new metadata formats
                result_metadata = result['metadata']
                hit = RetrievalHit(
                    section_id=result.get('id', 'unknown'),
                    text=result_metadata.get('text', ''),
                    score=float(result['score']),
                    source="hybrid",
                    metadata={
                        "section_name": result_metadata.get('section_name', 'Unknown'),
                        "source_filename": result_metadata.get('source_filename', result_metadata.get('filename', 'Unknown')),
                        "company": result_metadata.get('company', 'Unknown'),
                        "year": result_metadata.get('year', 0),
                        "quarter": result_metadata.get('quarter', 'Unknown'),
                        "doc_type": result_metadata.get('document_type', 'Unknown'),
                        "chunk_index": result_metadata.get('chunk_index', 0),
                        "total_chunks": result_metadata.get('total_chunks', 1)
                    }
                )
                hits.append(hit)
            
            logger.info(f"Pinecone filtered search found {len(hits)} chunk results")
            return hits
            
        except Exception as e:
            logger.error(f"Pinecone filtered search failed: {e}")
            return []
    
    def _relaxed_temporal_search(self, query: str, metadata: Dict[str, Any], top_k: int) -> List[RetrievalHit]:
        """Search with relaxed year constraints for temporal queries - UPDATED for chunked data"""
        try:
            company = metadata.get("company")
            target_year = int(metadata.get("year", 2024))
            
            # Try a range of years around the target
            year_ranges = [
                [target_year],  # Exact year
                [target_year - 1, target_year, target_year + 1],  # ±1 year
                [target_year - 2, target_year - 1, target_year, target_year + 1, target_year + 2],  # ±2 years
            ]
            
            for year_range in year_ranges:
                filter_dict = {
                    "company": {"$eq": company},
                    "year": {"$in": year_range}
                }
                
                results = self.pinecone_store.similarity_search(
                    query=query,
                    top_k=top_k,
                    filter_dict=filter_dict
                )
                
                if results:
                    logger.info(f"Found {len(results)} results for {company} in years {year_range}")
                    
                    # Convert to RetrievalHit format
                    hits = []
                    for result in results:
                        result_metadata = result['metadata']
                        hit = RetrievalHit(
                            section_id=result.get('id', 'unknown'),
                            text=result_metadata.get('text', ''),
                            score=float(result['score']),
                            source="hybrid_temporal",
                            metadata={
                                "section_name": result_metadata.get('section_name', 'Unknown'),
                                "source_filename": result_metadata.get('source_filename', result_metadata.get('filename', 'Unknown')),
                                "company": result_metadata.get('company', 'Unknown'),
                                "year": result_metadata.get('year', 0),
                                "quarter": result_metadata.get('quarter', 'Unknown'),
                                "doc_type": result_metadata.get('document_type', 'Unknown'),
                                "chunk_index": result_metadata.get('chunk_index', 0),
                                "total_chunks": result_metadata.get('total_chunks', 1)
                            }
                        )
                        hits.append(hit)
                    
                    return hits
            
            logger.info(f"No chunk results found for {company} in any year range")
            return []
            
        except Exception as e:
            logger.error(f"Relaxed temporal search failed: {e}")
            return []
    
    def _neo4j_fallback_search(self, query: str, metadata: Dict[str, Any], top_k: int) -> List[RetrievalHit]:
        """Enhanced Neo4j fallback with better company search and context expansion"""
        try:
            driver = self.neo4j_retriever._get_driver()
            
            # First try: Company-specific search with new chunked schema
            if metadata.get("company"):
                company_query = """
                MATCH (c:Company {name: $company})-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)
                      -[:HAS_DOC]->(d:Document)-[:HAS_SOURCE_SECTION]->(s:SourceSection)
                      -[:HAS_CHUNK]->(chunk:Chunk)
                WHERE chunk.text CONTAINS $search_term OR s.name CONTAINS $search_term
                RETURN c.name as company, y.value as year, q.label as quarter, 
                       d.document_type as doc_type, s.name as section_name,
                       s.filename as source_filename,
                       chunk.chunk_id as section_id, chunk.text as text, 1.0 as score
                ORDER BY y.value DESC
                LIMIT $top_k
                """
                
                # Extract key terms from query for search
                search_terms = ["business", "strategy", "operations", "evolution", "risk", "management"]
                for term in search_terms:
                    if term.lower() in query.lower():
                        params = {
                            "company": metadata["company"],
                            "search_term": term,
                            "top_k": top_k
                        }
                        
                        with driver.session() as session:
                            result = session.run(company_query, params)
                            records = list(result)
                            
                            if records:
                                # Get initial hits
                                initial_hits = []
                                for record in records:
                                    hit = RetrievalHit(
                                        section_id=record["section_id"],
                                        text=record["text"] or "",
                                        score=float(record["score"]),
                                        source="hybrid_neo4j",
                                        metadata={
                                            "section_name": record["section_name"],
                                            "source_filename": record["source_filename"],
                                            "company": record["company"],
                                            "year": record["year"],
                                            "quarter": record["quarter"],
                                            "doc_type": record["doc_type"]
                                        }
                                    )
                                    initial_hits.append(hit)
                                
                                # Apply context expansion
                                expanded_hits = self._expand_context(initial_hits, driver)
                                
                                logger.info(f"Neo4j company search found {len(initial_hits)} initial results, expanded to {len(expanded_hits)} with context")
                                return expanded_hits
            
            # Final fallback: Basic text search with chunked schema
            basic_query = """
            MATCH (c:Company)-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)
                  -[:HAS_DOC]->(d:Document)-[:HAS_SOURCE_SECTION]->(s:SourceSection)
                  -[:HAS_CHUNK]->(chunk:Chunk)
            WHERE chunk.text CONTAINS 'business' OR chunk.text CONTAINS 'strategy'
            RETURN c.name as company, y.value as year, q.label as quarter, 
                   d.document_type as doc_type, s.name as section_name,
                   s.filename as source_filename,
                   chunk.chunk_id as section_id, chunk.text as text, 0.5 as score
            ORDER BY y.value DESC
            LIMIT $top_k
            """
            
            with driver.session() as session:
                result = session.run(basic_query, {"top_k": top_k})
                records = list(result)
                
                initial_hits = []
                for record in records:
                    hit = RetrievalHit(
                        section_id=record["section_id"],
                        text=record["text"] or "",
                        score=float(record["score"]),
                        source="hybrid_fallback",
                        metadata={
                            "section_name": record["section_name"],
                            "source_filename": record["source_filename"],
                            "company": record["company"],
                            "year": record["year"],
                            "quarter": record["quarter"],
                            "doc_type": record["doc_type"]
                        }
                    )
                    initial_hits.append(hit)
                
                # Apply context expansion
                expanded_hits = self._expand_context(initial_hits, driver)
                
                logger.info(f"Neo4j fallback search found {len(initial_hits)} initial results, expanded to {len(expanded_hits)} with context")
                return expanded_hits
                
        except Exception as e:
            logger.error(f"Neo4j fallback search failed: {e}")
            return []

    def _expand_context(self, hits: List[RetrievalHit], driver) -> List[RetrievalHit]:
        """
        Expand context by fetching neighboring chunks for each hit.
        For each retrieved chunk, get the previous and next chunks from the same source section.
        """
        try:
            expanded_hits = []
            processed_chunks = set()
            
            for hit in hits:
                # Handle both dict and RetrievalHit objects
                if isinstance(hit, dict):
                    chunk_id = hit.get("section_id")
                    hit_score = hit.get("score", 0.0)
                    hit_source = hit.get("source", "hybrid")
                    hit_metadata = hit.get("metadata", {})
                else:
                    chunk_id = hit.section_id
                    hit_score = hit.score
                    hit_source = hit.source
                    hit_metadata = hit.metadata

                if not chunk_id:
                    continue
                
                # Skip if we've already processed this chunk
                if chunk_id in processed_chunks:
                    continue
                
                # Parse chunk index from chunk_id (format: filename_chunk_N)
                if "_chunk_" in chunk_id:
                    base_name = chunk_id.rsplit("_chunk_", 1)[0]
                    try:
                        chunk_index = int(chunk_id.rsplit("_chunk_", 1)[1])
                    except ValueError:
                        # If we can't parse the index, just add the original hit
                        expanded_hits.append(hit)
                        processed_chunks.add(chunk_id)
                        continue
                    
                    # Get neighboring chunks (previous and next)
                    context_query = """
                    MATCH (s:SourceSection)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.chunk_id STARTS WITH $base_name + '_chunk_'
                    AND (chunk.chunk_id = $prev_chunk OR chunk.chunk_id = $current_chunk OR chunk.chunk_id = $next_chunk)
                    RETURN chunk.chunk_id as chunk_id, chunk.text as text,
                           s.name as section_name, s.filename as source_filename
                    ORDER BY chunk.chunk_id
                    """
                    
                    prev_chunk = f"{base_name}_chunk_{max(0, chunk_index - 1)}"
                    current_chunk = chunk_id
                    next_chunk = f"{base_name}_chunk_{chunk_index + 1}"
                    
                    with driver.session() as session:
                        result = session.run(context_query, {
                            "base_name": base_name,
                            "prev_chunk": prev_chunk,
                            "current_chunk": current_chunk,
                            "next_chunk": next_chunk
                        })
                        
                        context_chunks = list(result)
                        
                        if context_chunks:
                            # Combine text from neighboring chunks
                            combined_text = " ".join([chunk["text"] for chunk in context_chunks])
                            
                            # Create an expanded hit with combined context
                            expanded_hit = RetrievalHit(
                                section_id=chunk_id,  # Keep original chunk_id for citation
                                text=combined_text,
                                score=hit_score,
                                source=f"{hit_source}_expanded",
                                metadata={
                                    **hit_metadata,
                                    "context_chunks": len(context_chunks),
                                    "original_chunk_id": chunk_id
                                }
                            )
                            expanded_hits.append(expanded_hit)
                            
                            # Mark all processed chunks
                            for chunk in context_chunks:
                                processed_chunks.add(chunk["chunk_id"])
                        else:
                            # If no neighbors found, just add the original hit
                            expanded_hits.append(hit)
                            processed_chunks.add(chunk_id)
                else:
                    # If chunk_id doesn't follow expected format, just add the original hit
                    expanded_hits.append(hit)
                    processed_chunks.add(chunk_id)
            
            return expanded_hits
            
        except Exception as e:
            logger.error(f"Context expansion failed: {e}")
            # If expansion fails, return original hits
            return hits

# Global retriever instance
_improved_hybrid_retriever = ImprovedHybridRetriever()

def hybrid(state: AgentState) -> AgentState:
    """
    IMPROVED Hybrid retrieval node - better temporal query handling
    """
    try:
        query = state.get("query_raw", "")
        metadata = state.get("metadata", {})
        
        logger.info(f"IMPROVED Hybrid node processing: '{query[:50]}...' with metadata: {metadata}")
        
        # Use improved hybrid retrieval with ~20 chunk optimization
        hits = _improved_hybrid_retriever.execute_hybrid_retrieval(query, metadata, top_k=20)
        
        # Update state
        state["retrievals"] = hits
        
        # Track tool usage and confidence
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("hybrid_improved")
        
        if "confidence_scores" not in state:
            state["confidence_scores"] = {}
        
        # Calculate confidence based on results
        if hits:
            avg_score = sum(hit["score"] for hit in hits) / len(hits)
            base_confidence = min(1.0, avg_score * (len(hits) / 10))
            
            # Boost confidence for successful temporal searches
            temporal_sources = ["hybrid_temporal", "hybrid_neo4j"]
            if any(hit.get("source", "") in temporal_sources for hit in hits):
                confidence = min(1.0, base_confidence * 1.2)
            else:
                confidence = base_confidence
        else:
            confidence = 0.0
            
        state["confidence_scores"]["hybrid"] = confidence
        
        logger.info(f"IMPROVED Hybrid node completed: {len(hits)} hits, confidence: {confidence:.2f}")
        
    except Exception as e:
        logger.error(f"IMPROVED Hybrid node error: {e}")
        state["retrievals"] = []
        if "error_messages" not in state:
            state["error_messages"] = []
        state["error_messages"].append(f"Hybrid error: {str(e)}")
    
    return state
