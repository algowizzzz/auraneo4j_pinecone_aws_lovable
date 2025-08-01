"""
RAG Node - Enhanced with Strong Company Filtering
Fixes cross-company data contamination issue
"""

from agent.state import AgentState
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import company normalization system
try:
    from agent.utils.company_mapping import normalize_company
    COMPANY_MAPPING_AVAILABLE = True
except ImportError:
    COMPANY_MAPPING_AVAILABLE = False

def rag(state: AgentState) -> AgentState:
    """
    Enhanced RAG Node with Strong Company Filtering
    Prevents cross-company data contamination
    """
    
    logger.info(f"RAG node processing query: '{state['query_raw'][:50]}...'")
    
    try:
        from pinecone import Pinecone
        from sentence_transformers import SentenceTransformer
        
        # Get query and metadata
        query = state.get("query_raw", "")
        metadata = state.get("metadata", {})
        
        if not query:
            logger.warning("Empty query provided to RAG node")
            state["retrievals"] = []
            state["confidence"] = 0.0
            return state
        
        # Initialize embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create query embedding
        query_embedding = model.encode([query])[0].tolist()
        
        # Connect to Pinecone
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        if not pinecone_api_key:
            logger.error("PINECONE_API_KEY not found in environment")
            state["retrievals"] = []
            state["confidence"] = 0.0
            return state
        
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index("sec-rag-index")
        
        # Get company filter from metadata
        company_filter = None
        if metadata.get("company"):
            company_filter = metadata["company"]
            # Normalize company name if mapping is available
            if COMPANY_MAPPING_AVAILABLE:
                normalized = normalize_company(company_filter)
                if normalized:
                    company_filter = normalized
            logger.info(f"Applying company filter: {company_filter}")
        
        # Perform semantic search
        results = index.query(
            vector=query_embedding,
            top_k=50,  # Get more results for filtering
            include_metadata=True,
        )
        
        # Apply strong company filtering
        retrievals = []
        for match in results.matches:
            # Extract company from multiple sources
            company = "Unknown"
            
            # 1. Try metadata first
            if match.metadata and match.metadata.get("company"):
                company = match.metadata["company"]
            
            # 2. Extract from filename as fallback
            elif "_" in match.id:
                company_part = match.id.split("_")[0].upper()
                company = company_part
            
            # Apply company filtering if specified
            if company_filter:
                # Strict company matching - only include exact matches
                if company.upper() != company_filter.upper():
                    continue
            
            # Get actual text content from properly populated databases
            text_content = "Content not available"
            if match.metadata and match.metadata.get("text"):
                text_content = match.metadata["text"]
            elif match.metadata and match.metadata.get("content"):
                text_content = match.metadata["content"]
            
            hit = {
                "id": match.id,
                "score": float(match.score),
                "text": text_content,
                "metadata": {
                    "source": match.id,
                    "company": company,
                    "chunk_id": match.id,
                    "filename": match.id,
                    **(dict(match.metadata) if match.metadata else {})
                },
                "source": match.id
            }
            retrievals.append(hit)
            
            # Stop when we have enough results
            if len(retrievals) >= 25:
                break
        
        # Log filtering results
        if company_filter:
            logger.info(f"Company filtering: {company_filter} -> {len(retrievals)} results (from {len(results.matches)} total)")
        
        # Calculate confidence
        confidence = 0.0
        if retrievals:
            confidence = sum(hit["score"] for hit in retrievals) / len(retrievals)
        
        # Log results
        logger.info(f"RAG node completed: {len(retrievals)} hits, confidence: {confidence:.2f}")
        
        # Update state
        state["retrievals"] = retrievals
        state["confidence"] = confidence
        state["route"] = "rag"
        
        return state
        
    except Exception as e:
        logger.error(f"RAG node error: {e}")
        state["retrievals"] = []
        state["confidence"] = 0.0
        return state