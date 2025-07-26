"""
RAG Node - FIXED Version with Direct Pinecone Access
Fixes the import issue by using direct Pinecone integration
"""

from agent.state import AgentState
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def rag(state: AgentState) -> AgentState:
    """
    FIXED RAG Node - Pure Pinecone Vector Search
    Uses direct Pinecone access instead of problematic imports
    """
    
    logger.info(f"RAG node processing query: '{state['query_raw'][:50]}...'")
    
    try:
        from pinecone import Pinecone
        from sentence_transformers import SentenceTransformer
        
        # Get query
        query = state.get("query_raw", "")
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
        
        # Prepare search filters if company specified
        filter_dict = None
        metadata = state.get("metadata", {})
        if metadata.get("company"):
            # Use exact company matching - Pinecone doesn't support regex
            company = metadata["company"]
            # Skip filtering for now - we'll filter post-search
            # filter_dict = {"company": {"$eq": company}}
        
        # Perform search
        results = index.query(
            vector=query_embedding,
            top_k=20,  # Target ~20 chunks as requested
            include_metadata=True,
            filter=filter_dict
        )
        
        # Format results for agent state
        retrievals = []
        company_filter = metadata.get("company", "").upper() if metadata.get("company") else None
        
        for match in results.matches:
            # Extract company from filename if not in metadata
            filename = match.id
            company = "Unknown"
            if "_" in filename:
                company_part = filename.split("_")[0].upper()
                company = company_part
            
            # Apply post-search company filtering if specified
            if company_filter and company_filter != company:
                continue
            
            hit = {
                "id": match.id,
                "score": float(match.score),
                "text": f"Content from {match.id}",  # Placeholder - in production would fetch actual text
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