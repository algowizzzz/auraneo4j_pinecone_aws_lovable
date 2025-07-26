"""
Enhanced Retrieval Integration - Deep Week 1 Infrastructure Integration
Connects LangGraph nodes with enhanced Neo4j schema, financial entities, and Pinecone capabilities
"""

import sys
import os
import logging
from typing import List, Dict, Any, Optional, Tuple

# Add data_pipeline to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data_pipeline'))

try:
    from enhanced_graph_schema import FinancialEntityExtractor
    from pinecone_integration import PineconeVectorStore
    from search_engine import HybridSearchEngine
except ImportError as e:
    logging.warning(f"Week 1 infrastructure not fully available: {e}")
    FinancialEntityExtractor = None
    PineconeVectorStore = None
    HybridSearchEngine = None

from agent.state import RetrievalHit
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class EnhancedFinancialRetriever:
    """
    Enhanced retriever that leverages all Week 1 infrastructure:
    - Financial entity extraction for improved routing
    - Enhanced Neo4j schema with entity relationships
    - Advanced Pinecone capabilities with financial concepts
    - Hybrid search with temporal and competitive analysis
    """
    
    def __init__(self, 
                 neo4j_uri: Optional[str] = None,
                 neo4j_user: Optional[str] = None, 
                 neo4j_password: Optional[str] = None,
                 pinecone_index: Optional[str] = None):
        
        self.entity_extractor = FinancialEntityExtractor() if FinancialEntityExtractor else None
        
        # Initialize enhanced components if available
        if neo4j_uri and neo4j_user and neo4j_password:
            self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        else:
            # Fallback to environment variables
            self.neo4j_driver = GraphDatabase.driver(
                os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
                auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'password'))
            )
        
        # Initialize Pinecone with enhanced capabilities
        if pinecone_index and PineconeVectorStore:
            try:
                self.pinecone_store = PineconeVectorStore(index_name=pinecone_index)
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone: {e}")
                self.pinecone_store = None
        else:
            self.pinecone_store = None
        
        # Initialize hybrid search engine
        if HybridSearchEngine and self.pinecone_store:
            try:
                self.hybrid_engine = HybridSearchEngine(
                    neo4j_uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
                    neo4j_user=os.getenv('NEO4J_USER', 'neo4j'),
                    neo4j_password=os.getenv('NEO4J_PASSWORD', 'password'),
                    pinecone_index=pinecone_index or os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index')
                )
            except Exception as e:
                logger.warning(f"Failed to initialize hybrid search engine: {e}")
                self.hybrid_engine = None
        else:
            self.hybrid_engine = None
        
        logger.info(f"Enhanced retriever initialized with entity extraction: {bool(self.entity_extractor)}, "
                   f"Pinecone: {bool(self.pinecone_store)}, Hybrid engine: {bool(self.hybrid_engine)}")
    
    def extract_financial_entities_from_query(self, query: str) -> Dict[str, List[str]]:
        """
        Extract financial entities from query to enhance routing decisions.
        Returns categorized entities for improved search targeting.
        """
        if not self.entity_extractor:
            return {}
        
        try:
            extracted = self.entity_extractor.extract_entities(query)
            
            # Flatten entity structure for easier consumption
            entity_summary = {}
            for category, entities in extracted.items():
                entity_names = [entity.get('name', entity.get('type', '')) for entity in entities]
                if entity_names:
                    entity_summary[category] = entity_names
            
            logger.info(f"Extracted financial entities: {entity_summary}")
            return entity_summary
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {}
    
    def enhanced_cypher_search(self, 
                              query: str, 
                              metadata: Dict[str, Any],
                              financial_entities: Dict[str, List[str]] = None,
                              state_entities: Dict[str, List[str]] = None) -> List[RetrievalHit]:
        """
        Enhanced Cypher search leveraging financial entity relationships.
        Uses the enhanced Neo4j schema to find entity-specific information.
        """
        try:
            # Use entities from state if available, otherwise extract them
            if state_entities:
                financial_entities = state_entities
            elif not financial_entities:
                financial_entities = self.extract_financial_entities_from_query(query)
            
            # Build enhanced Cypher query targeting financial entities
            cypher_query, params = self._build_enhanced_cypher_query(metadata, financial_entities)
            
            with self.neo4j_driver.session() as session:
                result = session.run(cypher_query, params)
                
                hits = []
                for record in result:
                    hit = RetrievalHit(
                        section_id=record.get("section_id", "unknown"),
                        text=record.get("text", ""),
                        score=float(record.get("score", 1.0)),
                        source="enhanced_cypher",
                        metadata={
                            "company": record.get("company"),
                            "year": record.get("year"),
                            "quarter": record.get("quarter"),
                            "section_name": record.get("section_name"),
                            "financial_entities": record.get("financial_entities", []),
                            "entity_relationships": record.get("entity_relationships", [])
                        }
                    )
                    hits.append(hit)
                
                logger.info(f"Enhanced Cypher search found {len(hits)} results with entity relationships")
                return hits
                
        except Exception as e:
            logger.error(f"Enhanced Cypher search failed: {e}")
            return []
    
    def enhanced_pinecone_search(self, 
                                query: str, 
                                metadata: Dict[str, Any],
                                financial_entities: Dict[str, List[str]] = None,
                                top_k: int = 15) -> List[RetrievalHit]:
        """
        Enhanced Pinecone search using financial concepts and advanced filtering.
        """
        if not self.pinecone_store:
            logger.warning("Pinecone not available for enhanced search")
            return []
        
        try:
            if not financial_entities:
                financial_entities = self.extract_financial_entities_from_query(query)
            
            # Use financial concepts for enhanced search
            if financial_entities:
                # Extract concepts for search
                concepts = []
                for category, entities in financial_entities.items():
                    concepts.extend(entities)
                
                if concepts:
                    results = self.pinecone_store.search_by_financial_concepts(
                        concepts=concepts,
                        companies=[metadata["company"]] if metadata.get("company") else None,
                        top_k=top_k
                    )
                else:
                    # Fallback to regular similarity search
                    filter_dict = self._build_pinecone_filter(metadata)
                    results = self.pinecone_store.similarity_search(
                        query=query,
                        top_k=top_k,
                        filter_dict=filter_dict
                    )
            else:
                # Standard search with metadata filtering
                filter_dict = self._build_pinecone_filter(metadata)
                results = self.pinecone_store.similarity_search(
                    query=query,
                    top_k=top_k,
                    filter_dict=filter_dict
                )
            
            # Convert to RetrievalHit format
            hits = []
            for result in results:
                hit = RetrievalHit(
                    section_id=result.get('id', 'unknown'),
                    text=result['metadata'].get('text', ''),
                    score=float(result['score']),
                    source="enhanced_pinecone",
                    metadata=result['metadata']
                )
                hits.append(hit)
            
            logger.info(f"Enhanced Pinecone search found {len(hits)} results")
            return hits
            
        except Exception as e:
            logger.error(f"Enhanced Pinecone search failed: {e}")
            return []
    
    def temporal_competitive_search(self, 
                                  query: str,
                                  company: str,
                                  timeframe_years: List[int] = None,
                                  include_competitors: bool = True,
                                  top_k: int = 20) -> List[RetrievalHit]:
        """
        Perform temporal and competitive analysis using enhanced infrastructure.
        """
        if not self.hybrid_engine:
            logger.warning("Hybrid engine not available for temporal/competitive search")
            return []
        
        try:
            hits = []
            
            # Search across timeframe for the target company
            if timeframe_years and len(timeframe_years) >= 2:
                company_results = self.hybrid_engine.search_company_timeline(
                    company=company,
                    start_year=min(timeframe_years),
                    end_year=max(timeframe_years)
                )
                
                # Convert to RetrievalHit format
                for result in company_results.get('results', []):
                    hit = RetrievalHit(
                        section_id=result.get('section_id', 'unknown'),
                        text=result.get('text', ''),
                        score=float(result.get('score', 0.8)),
                        source="temporal_analysis",
                        metadata=result.get('metadata', {})
                    )
                    hits.append(hit)
            
            # Add competitive analysis if requested
            if include_competitors and self.pinecone_store:
                competitor_results = self.pinecone_store.get_similar_sections_across_companies(
                    section_type="MD&A",  # Focus on Management Discussion & Analysis
                    reference_text=query,
                    exclude_company=company,
                    top_k=top_k // 2
                )
                
                for result in competitor_results:
                    hit = RetrievalHit(
                        section_id=result.get('id', 'unknown'),
                        text=result['metadata'].get('text', ''),
                        score=float(result['score']),
                        source="competitive_analysis",
                        metadata=result['metadata']
                    )
                    hits.append(hit)
            
            logger.info(f"Temporal/competitive search found {len(hits)} results")
            return hits
            
        except Exception as e:
            logger.error(f"Temporal/competitive search failed: {e}")
            return []
    
    def _build_enhanced_cypher_query(self, 
                                   metadata: Dict[str, Any], 
                                   financial_entities: Dict[str, List[str]]) -> Tuple[str, Dict[str, Any]]:
        """
        Build enhanced Cypher query that leverages financial entity relationships.
        """
        
        # Base query to find sections based on metadata
        base_query = """
        MATCH (c:Company)-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)
              -[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)
            """
        
        conditions = []
        params = {}
        
        # Standard metadata filters
        if metadata.get("company"):
            conditions.append("c.name = $company")
            params["company"] = metadata["company"]
        
        if metadata.get("year"):
            conditions.append("y.value = $year")
            params["year"] = int(metadata["year"])
        
        if metadata.get("quarter"):
            conditions.append("q.label = $quarter")
            params["quarter"] = metadata["quarter"]
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # If no financial entities, run a simpler query
        if not financial_entities:
            return_clause = """
            RETURN s.filename as section_id, s.text as text, s.section as section_name,
                   c.name as company, y.value as year, q.label as quarter,
                   1.0 as score, [] as financial_entities, [] as entity_relationships
            LIMIT 20
            """
            return f"{base_query} {where_clause} {return_clause}", params

        # Query with financial entities
        entity_conditions = []
        for category, entities in financial_entities.items():
            if entities:
                param_name = f"{category}_entities"
                entity_conditions.append(f"entity.name IN ${param_name}")
                params[param_name] = entities
        
        entity_where_clause = ""
        if entity_conditions:
            entity_where_clause = "WHERE " + " OR ".join(entity_conditions)

        full_query = f"""
        {base_query}
        {where_clause}
        WITH s, c, y, q
        OPTIONAL MATCH (s)-[rel:MENTIONS|HAS_RISK|DISCUSSES_PRODUCT]->(entity)
        {entity_where_clause}
        WITH s, c, y, q, collect(DISTINCT entity) as entities
        RETURN s.filename as section_id, s.text as text, s.section as section_name,
               c.name as company, y.value as year, q.label as quarter,
               1.0 as score,
               [entity in entities | entity.name] as financial_entities,
               [entity in entities | labels(entity)] as entity_relationships
        LIMIT 20
        """
        
        return full_query, params
    
    def _build_pinecone_filter(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build Pinecone filter dictionary from metadata."""
        filter_dict = {}
        
        if metadata.get("company"):
            filter_dict["company"] = {"$eq": metadata["company"]}
        
        if metadata.get("year"):
            filter_dict["year"] = {"$eq": int(metadata["year"])}
        
        if metadata.get("quarter"):
            filter_dict["quarter"] = {"$eq": metadata["quarter"]}
        
        if metadata.get("doc_type"):
            filter_dict["document_type"] = {"$eq": metadata["doc_type"]}
        
        return filter_dict
    
    def close(self):
        """Close database connections."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.hybrid_engine:
            self.hybrid_engine.close()

# Global enhanced retriever instance
_enhanced_retriever = None

def get_enhanced_retriever() -> EnhancedFinancialRetriever:
    """Get or create the global enhanced retriever instance."""
    global _enhanced_retriever
    
    if _enhanced_retriever is None:
        _enhanced_retriever = EnhancedFinancialRetriever()
    
    return _enhanced_retriever

def close_enhanced_retriever():
    """Close the global enhanced retriever."""
    global _enhanced_retriever
    
    if _enhanced_retriever:
        _enhanced_retriever.close()
        _enhanced_retriever = None