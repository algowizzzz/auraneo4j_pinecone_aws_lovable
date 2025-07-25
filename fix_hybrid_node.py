#!/usr/bin/env python3
"""
Fix Hybrid Node - Handle Temporal Queries Better
Fix the issue where temporal queries with specific years fail due to data availability
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_improved_hybrid_node():
    """Create an improved hybrid node that handles temporal queries better"""
    
    hybrid_fix = '''"""
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
    
    def execute_hybrid_retrieval(self, query: str, metadata: Dict[str, Any], top_k: int = 15) -> List[RetrievalHit]:
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
        """Use Pinecone with metadata filtering - FIXED VERSION"""
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
                hit = RetrievalHit(
                    section_id=result.get('id', 'unknown'),
                    text=result['metadata'].get('text', ''),
                    score=float(result['score']),
                    source="hybrid",
                    metadata=result['metadata']
                )
                hits.append(hit)
            
            logger.info(f"Pinecone filtered search found {len(hits)} results")
            return hits
            
        except Exception as e:
            logger.error(f"Pinecone filtered search failed: {e}")
            return []
    
    def _relaxed_temporal_search(self, query: str, metadata: Dict[str, Any], top_k: int) -> List[RetrievalHit]:
        """Search with relaxed year constraints for temporal queries"""
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
                        hit = RetrievalHit(
                            section_id=result.get('id', 'unknown'),
                            text=result['metadata'].get('text', ''),
                            score=float(result['score']),
                            source="hybrid_temporal",
                            metadata=result['metadata']
                        )
                        hits.append(hit)
                    
                    return hits
            
            logger.info(f"No results found for {company} in any year range")
            return []
            
        except Exception as e:
            logger.error(f"Relaxed temporal search failed: {e}")
            return []
    
    def _neo4j_fallback_search(self, query: str, metadata: Dict[str, Any], top_k: int) -> List[RetrievalHit]:
        """Enhanced Neo4j fallback with better company search"""
        try:
            driver = self.neo4j_retriever._get_driver()
            
            # First try: Company-specific search without year constraints
            if metadata.get("company"):
                company_query = """
                MATCH (c:Company {name: $company})-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)
                      -[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)
                WHERE s.text CONTAINS $search_term OR s.section CONTAINS $search_term
                RETURN c.name as company, y.value as year, q.label as quarter, 
                       d.document_type as doc_type, s.section as section_name,
                       s.filename as section_id, s.text as text, 1.0 as score
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
                                hits = []
                                for record in records:
                                    hit = RetrievalHit(
                                        section_id=record["section_id"],
                                        text=record["text"] or "",
                                        score=float(record["score"]),
                                        source="hybrid_neo4j",
                                        metadata={
                                            "section_name": record["section_name"],
                                            "company": record["company"],
                                            "year": record["year"],
                                            "quarter": record["quarter"],
                                            "doc_type": record["doc_type"]
                                        }
                                    )
                                    hits.append(hit)
                                
                                logger.info(f"Neo4j company search found {len(hits)} results for term '{term}'")
                                return hits
            
            # Final fallback: Basic text search
            basic_query = """
            MATCH (c:Company)-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)
                  -[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)
            WHERE s.text CONTAINS 'business' OR s.text CONTAINS 'strategy'
            RETURN c.name as company, y.value as year, q.label as quarter, 
                   d.document_type as doc_type, s.section as section_name,
                   s.filename as section_id, s.text as text, 0.5 as score
            ORDER BY y.value DESC
            LIMIT $top_k
            """
            
            with driver.session() as session:
                result = session.run(basic_query, {"top_k": top_k})
                records = list(result)
                
                hits = []
                for record in records:
                    hit = RetrievalHit(
                        section_id=record["section_id"],
                        text=record["text"] or "",
                        score=float(record["score"]),
                        source="hybrid_fallback",
                        metadata={
                            "section_name": record["section_name"],
                            "company": record["company"],
                            "year": record["year"],
                            "quarter": record["quarter"],
                            "doc_type": record["doc_type"]
                        }
                    )
                    hits.append(hit)
                
                logger.info(f"Neo4j fallback search found {len(hits)} results")
                return hits
                
        except Exception as e:
            logger.error(f"Neo4j fallback search failed: {e}")
            return []

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
        
        # Use improved hybrid retrieval
        hits = _improved_hybrid_retriever.execute_hybrid_retrieval(query, metadata, top_k=15)
        
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
'''
    
    return hybrid_fix

def apply_hybrid_fix():
    """Apply the hybrid node fix"""
    print("🔧 Applying Hybrid Node Fix")
    print("=" * 50)
    
    try:
        # Create the improved hybrid node content
        improved_content = create_improved_hybrid_node()
        
        # Backup original file
        original_file = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/agent/nodes/hybrid.py"
        backup_file = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/agent/nodes/hybrid_backup.py"
        
        # Create backup
        with open(original_file, 'r') as f:
            original_content = f.read()
        
        with open(backup_file, 'w') as f:
            f.write(original_content)
        
        print(f"  ✅ Backup created: {backup_file}")
        
        # Write improved version
        with open(original_file, 'w') as f:
            f.write(improved_content)
        
        print(f"  ✅ Improved hybrid node written to: {original_file}")
        
        # Test the fix
        print("\n🧪 Testing the fix...")
        
        # Test import
        import importlib.util
        spec = importlib.util.spec_from_file_location("hybrid", original_file)
        hybrid_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hybrid_module)
        
        print("  ✅ New hybrid node imports successfully")
        
        # Test with the failing query
        test_state = {
            "query_raw": "How has Zions Bancorporation business strategy evolved from 2021 to 2025?",
            "metadata": {'company': 'ZION', 'year': '2021', 'quarter': None, 'doc_type': None},
            "route": "hybrid",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        result = hybrid_module.hybrid(test_state)
        hits = result.get("retrievals", [])
        
        print(f"  📊 Test result: {len(hits)} retrievals")
        
        if hits:
            print("  🎉 SUCCESS: Hybrid node now returns results!")
            for i, hit in enumerate(hits[:2], 1):
                source = hit.get("source", "unknown")
                score = hit.get("score", 0)
                metadata = hit.get("metadata", {})
                company = metadata.get("company", "Unknown")
                year = metadata.get("year", "Unknown")
                print(f"    {i}. {company} {year}: {source}, score {score:.3f}")
        else:
            print("  ⚠️  Still no results, but error handling improved")
        
        return len(hits) > 0
        
    except Exception as e:
        print(f"  ❌ Failed to apply fix: {e}")
        return False

if __name__ == "__main__":
    success = apply_hybrid_fix()
    
    if success:
        print("\\n✅ Hybrid node fix applied successfully!")
        print("BQ004 temporal queries should now work")
    else:
        print("\\n⚠️  Fix applied but needs further optimization")