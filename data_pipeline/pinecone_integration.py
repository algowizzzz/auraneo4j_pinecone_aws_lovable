import os
import json
import time
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class PineconeVectorStore:
    def __init__(self, 
                 api_key: Optional[str] = None,
                 index_name: str = "sec-rag-index",
                 embedding_model: str = 'all-MiniLM-L6-v2',
                 dimension: int = 384):
        
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        self.index_name = index_name
        self.embedding_model = SentenceTransformer(embedding_model)
        self.dimension = dimension
        
        if not self.api_key:
            raise ValueError("Pinecone API key not found. Please set PINECONE_API_KEY environment variable.")
        
        # Initialize Pinecone with new API
        self.pc = Pinecone(api_key=self.api_key)
        
        # Create or connect to index
        self._setup_index()
        
    def _setup_index(self):
        """Create or connect to Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                # Wait for index to be ready
                time.sleep(10)
            
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Error setting up Pinecone index: {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.0] * self.dimension for _ in texts]

    def upsert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Upsert documents to Pinecone index"""
        try:
            # Prepare vectors for upsert
            vectors = []
            texts = [doc['text'] for doc in documents]
            embeddings = self.generate_embeddings(texts)
            
            for i, doc in enumerate(documents):
                vector_id = f"{doc.get('company', 'unknown')}_{doc.get('year', 'unknown')}_{doc.get('quarter', 'unknown')}_{doc.get('section_filename', i)}"
                
                metadata = {
                    'company': doc.get('company', ''),
                    'year': doc.get('year', 0),
                    'quarter': doc.get('quarter', ''),
                    'section_type': doc.get('section_name', ''),
                    'document_type': doc.get('document_type', ''),
                    'section_filename': doc.get('section_filename', ''),
                    'source_file': doc.get('section_filename', ''),  # For text fallback
                    'doc_filename': doc.get('doc_filename', ''),
                    'text': doc.get('text', '')[:1500],  # Truncate to stay under 40KB
                    'filing_date': doc.get('filing_date', ''),
                    'cik': doc.get('cik', ''),
                    'financial_entities': json.dumps(doc.get('financial_entities', {}))[:2000]  # Truncate JSON
                }
                
                vectors.append({
                    'id': vector_id,
                    'values': embeddings[i],
                    'metadata': metadata
                })
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i//batch_size + 1} with {len(batch)} vectors")
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting documents to Pinecone: {e}")
            return False

    def similarity_search(self, 
                         query: str, 
                         top_k: int = 10,
                         filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Perform search
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            results = []
            for match in search_results['matches']:
                result = {
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match['metadata']
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []

    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}

    def delete_index(self):
        """Delete the Pinecone index"""
        try:
            pinecone.delete_index(self.index_name)
            logger.info(f"Deleted Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"Error deleting index: {e}")

    def search_by_company_and_timeframe(self, 
                                      company: str,
                                      start_year: int,
                                      end_year: int,
                                      section_type: Optional[str] = None,
                                      top_k: int = 20) -> List[Dict[str, Any]]:
        """Search documents by company and timeframe"""
        filter_dict = {
            "company": {"$eq": company},
            "year": {"$gte": start_year, "$lte": end_year}
        }
        
        if section_type:
            filter_dict["section_type"] = {"$eq": section_type}
        
        # Use a generic business query for searching
        query = f"{company} business operations financial performance"
        
        return self.similarity_search(query, top_k=top_k, filter_dict=filter_dict)

    def search_by_financial_concepts(self, 
                                   concepts: List[str],
                                   companies: Optional[List[str]] = None,
                                   top_k: int = 15) -> List[Dict[str, Any]]:
        """Search for documents containing specific financial concepts"""
        query = " ".join(concepts)
        
        filter_dict = {}
        if companies:
            filter_dict["company"] = {"$in": companies}
        
        return self.similarity_search(query, top_k=top_k, filter_dict=filter_dict)

    def get_similar_sections_across_companies(self, 
                                            section_type: str,
                                            reference_text: str,
                                            exclude_company: Optional[str] = None,
                                            top_k: int = 10) -> List[Dict[str, Any]]:
        """Find similar sections across different companies"""
        filter_dict = {"section_type": {"$eq": section_type}}
        
        if exclude_company:
            filter_dict["company"] = {"$ne": exclude_company}
        
        return self.similarity_search(reference_text, top_k=top_k, filter_dict=filter_dict)


if __name__ == "__main__":
    # Test the Pinecone integration
    logging.basicConfig(level=logging.INFO)
    
    try:
        vector_store = PineconeVectorStore()
        stats = vector_store.get_index_stats()
        logger.info(f"Pinecone index stats: {stats}")
        
        # Test search
        results = vector_store.similarity_search("banking operations", top_k=5)
        logger.info(f"Search results: {len(results)} documents found")
        
    except Exception as e:
        logger.error(f"Error testing Pinecone integration: {e}")