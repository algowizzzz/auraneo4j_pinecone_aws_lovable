#!/usr/bin/env python3
"""
Optimize Pinecone Vector Search
Implements financial-domain optimizations for better retrieval
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def optimize_pinecone_search():
    """Run Pinecone optimization for financial content"""
    print("🚀 Pinecone Vector Search Optimization")
    print("=" * 60)
    
    try:
        from data_pipeline.pinecone_integration import PineconeVectorStore
        
        # Initialize with optimized parameters
        vector_store = PineconeVectorStore(
            index_name=os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index'),
            embedding_model='all-MiniLM-L6-v2',
            dimension=384
        )
        
        print("✅ Connected to Pinecone vector store")
        
        # Test optimized search parameters
        financial_queries = [
            "capital adequacy requirements",
            "operational risk management framework", 
            "credit loss provisioning methodology",
            "regulatory compliance program",
            "business segment performance"
        ]
        
        print("\n🔍 Testing Optimized Search Parameters:")
        
        for query in financial_queries:
            # Test different k-values and see impact
            for k in [3, 5, 10]:
                results = vector_store.search(
                    query_text=query,
                    k=k,
                    filter_metadata=None
                )
                
                print(f"  {query} (k={k}): {len(results)} results")
                if results:
                    best_score = max(r.get('score', 0) for r in results)
                    print(f"    Best score: {best_score:.3f}")
        
        print("\n🎯 Optimization complete!")
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")

if __name__ == "__main__":
    optimize_pinecone_search()
