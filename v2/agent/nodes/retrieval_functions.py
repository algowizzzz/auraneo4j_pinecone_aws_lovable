"""
Simplified Stateless Retrieval Functions for Enhanced Iterative Planner
These functions are called by the planner with specific parameters and return results
"""

import os
import logging
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "newpassword")

# Pinecone setup
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "sec-rag-index")


def simplified_cypher(
    query: str, 
    filters: Dict[str, Any], 
    limit: int = 50, 
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Simplified Cypher retrieval function
    
    Args:
        query: Search query (currently not used for pure structural queries)
        filters: Standardized metadata filters
        limit: Maximum number of chunks to return
        skip: Number of chunks to skip (for pagination)
        
    Returns:
        List of chunk dictionaries with metadata
    """
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
        # Build Cypher query from filters
        cypher_query, params = _build_cypher_query(filters, limit, skip)
        
        with driver.session() as session:
            result = session.run(cypher_query, params)
            
            chunks = []
            for record in result:
                chunk = {
                    "id": record.get("section_id", ""),
                    "text": record.get("text", ""),
                    "score": 1.0,  # Cypher doesn't provide semantic scoring
                    "metadata": {
                        "source": "cypher",
                        "section_name": record.get("section_name", ""),
                        "source_filename": record.get("source_filename", ""),
                        "company": record.get("company", ""),
                        "year": record.get("year", ""),
                        "quarter": record.get("quarter", ""),
                        "doc_type": record.get("doc_type", ""),
                        "entities": record.get("entities", []),
                        "word_count": record.get("word_count", 0)
                    }
                }
                chunks.append(chunk)
        
        driver.close()
        logger.info(f"Cypher retrieved {len(chunks)} chunks")
        return chunks
        
    except Exception as e:
        logger.error(f"Cypher retrieval failed: {e}")
        return []


def simplified_rag(
    query: str, 
    filters: Dict[str, Any], 
    limit: int = 50, 
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Simplified RAG retrieval function using Pinecone - matches working v1 approach
    
    Args:
        query: Semantic search query
        filters: Standardized metadata filters
        limit: Maximum number of chunks to return
        skip: Number of chunks to skip (for pagination)
        
    Returns:
        List of chunk dictionaries with metadata and similarity scores
    """
    try:
        from pinecone import Pinecone
        from sentence_transformers import SentenceTransformer
        
        if not PINECONE_API_KEY:
            logger.error("Pinecone API key not found")
            return []
        
        # Initialize Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Initialize embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = model.encode([query])[0].tolist()
        
        # Get company filter from filters (supporting multi-company queries)
        company_filters = []
        if filters.get("companies"):
            if isinstance(filters["companies"], list):
                company_filters = filters["companies"]
            else:
                company_filters = [filters["companies"]]
        elif filters.get("company"):
            company_filters = [filters["company"]]
        
        # Perform semantic search (using v1 approach)
        results = index.query(
            vector=query_embedding,
            top_k=limit + skip + 10,  # Get extra for filtering and skip
            include_metadata=True,
        )
        
        # Apply strong company filtering (v1 approach)
        chunks = []
        processed = 0
        
        for match in results.matches:
            # Extract company from multiple sources (v1 logic)
            company = "Unknown"
            
            # 1. Try metadata first
            if match.metadata and match.metadata.get("company"):
                company = match.metadata["company"]
            
            # 2. Extract from filename as fallback
            elif "_" in match.id:
                company_part = match.id.split("_")[0].upper()
                if len(company_part) <= 5:  # Likely a ticker
                    company = company_part
            
            # Apply company filter if specified (support multiple companies)
            if company_filters:
                company_match = any(company.upper() == cf.upper() for cf in company_filters)
                if not company_match:
                    continue
            
            # Apply skip
            if processed < skip:
                processed += 1
                continue
            
            # Stop if we have enough chunks
            if len(chunks) >= limit:
                break
            
            # Convert to v2 format but using v1 data structure
            chunk = {
                "id": match.id,
                "text": match.metadata.get("text", ""),
                "score": float(match.score),
                "metadata": {
                    "source": "rag",
                    "company": company,
                    "year": match.metadata.get("year", ""),
                    "quarter": match.metadata.get("quarter", ""),
                    "doc_type": match.metadata.get("form_type", ""),
                    "section_name": match.metadata.get("filename", ""),
                    "source_filename": match.metadata.get("filename", ""),
                    "item": match.metadata.get("item", ""),
                    "part": match.metadata.get("part", ""),
                    "regulatory_level": match.metadata.get("regulatory_level", ""),
                    "section_type": match.metadata.get("section_type", "")
                }
            }
            chunks.append(chunk)
            processed += 1
        
        logger.info(f"RAG retrieved {len(chunks)} chunks (filtered by companies: {company_filters})")
        return chunks
        
    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return []


def simplified_hybrid(
    query: str, 
    filters: Dict[str, Any], 
    limit: int = 50, 
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Simplified hybrid retrieval combining Cypher and RAG
    
    Args:
        query: Search query
        filters: Standardized metadata filters
        limit: Maximum number of chunks to return
        skip: Number of chunks to skip (for pagination)
        
    Returns:
        Combined and deduplicated results from both sources
    """
    try:
        # Split limit between sources
        cypher_limit = limit // 2
        rag_limit = limit - cypher_limit
        
        # Get results from both sources
        cypher_results = simplified_cypher(query, filters, cypher_limit, skip // 2)
        rag_results = simplified_rag(query, filters, rag_limit, skip // 2)
        
        # Simple deduplication by text similarity (basic approach)
        combined_results = []
        seen_texts = set()
        
        # Add RAG results first (they have semantic scores)
        for chunk in rag_results:
            text_snippet = chunk["text"][:100].lower()  # First 100 chars for dedup
            if text_snippet not in seen_texts:
                seen_texts.add(text_snippet)
                chunk["metadata"]["source"] = "hybrid_rag"
                combined_results.append(chunk)
        
        # Add Cypher results if not duplicates
        for chunk in cypher_results:
            text_snippet = chunk["text"][:100].lower()
            if text_snippet not in seen_texts:
                seen_texts.add(text_snippet)
                chunk["metadata"]["source"] = "hybrid_cypher"
                combined_results.append(chunk)
        
        # Sort by score (RAG chunks have real scores, Cypher chunks get 1.0)
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"Hybrid retrieved {len(combined_results)} chunks")
        return combined_results[:limit]
        
    except Exception as e:
        logger.error(f"Hybrid retrieval failed: {e}")
        return []


def cypher_discover_metadata(
    company: Optional[str] = None,
    year: Optional[int] = None,
    discovery_type: str = "years"
) -> List[Any]:
    """
    Use Cypher to discover available metadata (years, quarters, sections, etc.)
    
    Args:
        company: Company ticker to filter by
        year: Year to filter by
        discovery_type: "years", "quarters", "sections", "companies", "doc_types"
        
    Returns:
        List of discovered values
    """
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
        query, params = _build_discovery_query(company, year, discovery_type)
        
        with driver.session() as session:
            result = session.run(query, params)
            values = [record["value"] for record in result]
        
        driver.close()
        logger.info(f"Discovered {len(values)} {discovery_type}: {values}")
        return values
        
    except Exception as e:
        logger.error(f"Metadata discovery failed: {e}")
        return []


def _build_cypher_query(filters: Dict[str, Any], limit: int, skip: int) -> tuple[str, Dict[str, Any]]:
    """Build Cypher query from standardized filters - matches working v1 pattern"""
    
    conditions = []
    params = {}
    
    # Base query structure - exact match with working v1 pattern
    base_query = """
    MATCH (c:Company)-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)
          -[:HAS_DOC]->(d:Document)-[:HAS_SOURCE_SECTION]->(s:SourceSection)
          -[:HAS_CHUNK]->(chunk:Chunk)
    """
    
    # Add conditions based on filters - handle single values or lists
    if filters.get("companies"):
        companies = filters["companies"] if isinstance(filters["companies"], list) else [filters["companies"]]
        if len(companies) == 1:
            conditions.append("c.name = $company")
            params["company"] = companies[0]
        else:
            conditions.append("c.name IN $companies")
            params["companies"] = companies
    
    if filters.get("years"):
        years = filters["years"] if isinstance(filters["years"], list) else [filters["years"]]
        # Convert to integers
        years = [int(y) if isinstance(y, str) else y for y in years]
        if len(years) == 1:
            conditions.append("y.value = $year")
            params["year"] = years[0]
        else:
            conditions.append("y.value IN $years")
            params["years"] = years
    
    if filters.get("quarters"):
        quarters = filters["quarters"] if isinstance(filters["quarters"], list) else [filters["quarters"]]
        if len(quarters) == 1:
            conditions.append("q.label = $quarter")
            params["quarter"] = quarters[0]
        else:
            conditions.append("q.label IN $quarters")
            params["quarters"] = quarters
    
    if filters.get("doc_types"):
        doc_types = filters["doc_types"] if isinstance(filters["doc_types"], list) else [filters["doc_types"]]
        if len(doc_types) == 1:
            conditions.append("d.document_type = $doc_type")
            params["doc_type"] = doc_types[0]
        else:
            conditions.append("d.document_type IN $doc_types")
            params["doc_types"] = doc_types
    
    if filters.get("regulatory_sections"):
        section_conditions = []
        for i, section in enumerate(filters["regulatory_sections"]):
            param_name = f"section_{i}"
            section_conditions.append(f"s.name CONTAINS ${param_name}")
            params[param_name] = section
        if section_conditions:
            conditions.append(f"({' OR '.join(section_conditions)})")
    
    # Build WHERE clause
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    
    # Return clause - exact match with working v1 pattern but with SKIP/LIMIT
    return_clause = f"""
    RETURN chunk.chunk_id as section_id,
           chunk.text as text,
           s.name as section_name,
           s.filename as source_filename,
           c.name as company,
           y.value as year,
           q.label as quarter,
           d.document_type as doc_type,
           chunk.financial_entities as entities,
           chunk.word_count as word_count
    ORDER BY y.value DESC, q.label, s.name, chunk.chunk_id
    SKIP {skip} LIMIT {limit}
    """
    
    full_query = f"{base_query} {where_clause} {return_clause}"
    return full_query, params


def _build_pinecone_filter(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Build Pinecone filter from standardized filters"""
    
    pinecone_filter = {}
    
    if filters.get("companies"):
        if len(filters["companies"]) == 1:
            pinecone_filter["company"] = {"$eq": filters["companies"][0]}
        else:
            pinecone_filter["company"] = {"$in": filters["companies"]}
    
    if filters.get("years"):
        if len(filters["years"]) == 1:
            pinecone_filter["year"] = {"$eq": str(filters["years"][0])}
        else:
            pinecone_filter["year"] = {"$in": [str(y) for y in filters["years"]]}
    
    if filters.get("quarters"):
        if len(filters["quarters"]) == 1:
            pinecone_filter["quarter"] = {"$eq": filters["quarters"][0]}
        else:
            pinecone_filter["quarter"] = {"$in": filters["quarters"]}
    
    if filters.get("doc_types"):
        if len(filters["doc_types"]) == 1:
            pinecone_filter["doc_type"] = {"$eq": filters["doc_types"][0]}
        else:
            pinecone_filter["doc_type"] = {"$in": filters["doc_types"]}
    
    return pinecone_filter


def _build_discovery_query(company: Optional[str], year: Optional[int], discovery_type: str) -> tuple[str, Dict[str, Any]]:
    """Build discovery query for metadata exploration"""
    
    params = {}
    
    if discovery_type == "years":
        base_query = "MATCH (c:Company)-[:HAS_YEAR]->(y:Year)"
        if company:
            base_query += " WHERE c.name = $company"
            params["company"] = company
        return_clause = " RETURN DISTINCT y.value as value ORDER BY y.value DESC"
        
    elif discovery_type == "quarters":
        base_query = "MATCH (c:Company)-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)"
        conditions = []
        if company:
            conditions.append("c.name = $company")
            params["company"] = company
        if year:
            conditions.append("y.value = $year")
            params["year"] = year
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        return_clause = " RETURN DISTINCT q.label as value ORDER BY q.label"
        base_query += where_clause
        
    elif discovery_type == "companies":
        base_query = "MATCH (c:Company)"
        return_clause = " RETURN DISTINCT c.name as value ORDER BY c.name"
        
    elif discovery_type == "doc_types":
        base_query = "MATCH (c:Company)-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)-[:HAS_DOC]->(d:Document)"
        conditions = []
        if company:
            conditions.append("c.name = $company")
            params["company"] = company
        if year:
            conditions.append("y.value = $year")
            params["year"] = year
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        return_clause = " RETURN DISTINCT d.document_type as value ORDER BY d.document_type"
        base_query += where_clause
        
    elif discovery_type == "sections":
        base_query = "MATCH (c:Company)-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)-[:HAS_DOC]->(d:Document)-[:HAS_SOURCE_SECTION]->(s:SourceSection)"
        conditions = []
        if company:
            conditions.append("c.name = $company")
            params["company"] = company
        if year:
            conditions.append("y.value = $year")
            params["year"] = year
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        return_clause = " RETURN DISTINCT s.name as value ORDER BY s.name"
        base_query += where_clause
        
    else:
        raise ValueError(f"Unknown discovery type: {discovery_type}")
    
    full_query = base_query + return_clause
    return full_query, params