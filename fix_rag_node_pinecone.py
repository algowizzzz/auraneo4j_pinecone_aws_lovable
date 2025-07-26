#!/usr/bin/env python3
"""
Quick Fix: RAG Node Pinecone Integration

The RAG node is failing to access Pinecone despite our successful upload.
Let's create a simple test to validate the issue and fix it.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_direct_pinecone_access():
    """Test direct Pinecone access with our uploaded vectors"""
    print("🔍 Testing Direct Pinecone Access")
    print("=" * 50)
    
    try:
        from pinecone import Pinecone
        
        # Connect using same method as our successful upload
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index("sec-rag-index")
        
        # Test basic query
        print("📊 Testing vector similarity search...")
        
        # Create a test embedding (random for now, in production use sentence transformer)
        import numpy as np
        test_embedding = np.random.rand(384).tolist()
        
        results = index.query(
            vector=test_embedding,
            top_k=10,
            include_metadata=True
        )
        
        print(f"✅ Query successful: {len(results.matches)} results")
        for i, match in enumerate(results.matches[:3]):
            print(f"  {i+1}. {match.id} (Score: {match.score:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct Pinecone access failed: {e}")
        return False

def test_data_pipeline_import():
    """Test importing PineconeVectorStore from data_pipeline"""
    print("\n🔍 Testing Data Pipeline Import")
    print("=" * 50)
    
    try:
        # Add data_pipeline to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data_pipeline'))
        
        from pinecone_integration import PineconeVectorStore
        
        print("✅ PineconeVectorStore import successful")
        
        # Test initialization
        vector_store = PineconeVectorStore(index_name='sec-rag-index')
        print("✅ PineconeVectorStore initialization successful")
        
        # Test basic search
        results = vector_store.similarity_search("risk management", top_k=5)
        print(f"✅ Similarity search successful: {len(results)} results")
        
        return True, vector_store
        
    except Exception as e:
        print(f"❌ Data pipeline import failed: {e}")
        return False, None

def create_simple_rag_function():
    """Create a simple RAG function that works with our Pinecone data"""
    print("\n🔧 Creating Simple RAG Function")
    print("=" * 50)
    
    def simple_rag(state):
        """Simple RAG implementation using direct Pinecone access"""
        try:
            from pinecone import Pinecone
            from sentence_transformers import SentenceTransformer
            
            # Get query
            query = state.get("query_raw", "")
            if not query:
                return {"retrievals": [], "confidence": 0.0}
            
            # Initialize embedding model
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create query embedding
            query_embedding = model.encode([query])[0].tolist()
            
            # Connect to Pinecone
            pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
            index = pc.Index("sec-rag-index")
            
            # Perform search
            results = index.query(
                vector=query_embedding,
                top_k=20,
                include_metadata=True
            )
            
            # Format results
            retrievals = []
            for match in results.matches:
                hit = {
                    "id": match.id,
                    "score": float(match.score),
                    "metadata": dict(match.metadata) if match.metadata else {},
                    "text": f"Content from {match.id}"  # Placeholder
                }
                retrievals.append(hit)
            
            return {
                "retrievals": retrievals,
                "confidence": sum(hit["score"] for hit in retrievals) / len(retrievals) if retrievals else 0.0
            }
            
        except Exception as e:
            print(f"❌ Simple RAG function error: {e}")
            return {"retrievals": [], "confidence": 0.0}
    
    return simple_rag

def test_simple_rag():
    """Test our simple RAG function"""
    print("\n🧪 Testing Simple RAG Function")
    print("=" * 50)
    
    simple_rag = create_simple_rag_function()
    
    test_queries = [
        "What are the main risk factors for Wells Fargo?",
        "credit risk management strategies",
        "business strategy and revenue growth"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        
        state = {"query_raw": query}
        result = simple_rag(state)
        
        retrievals = result.get("retrievals", [])
        confidence = result.get("confidence", 0.0)
        
        print(f"  Results: {len(retrievals)} retrievals, confidence: {confidence:.3f}")
        
        if retrievals:
            for i, hit in enumerate(retrievals[:3]):
                print(f"    {i+1}. {hit['id']} (Score: {hit['score']:.3f})")

def main():
    print("🔧 RAG NODE PINECONE INTEGRATION FIX")
    print("=" * 60)
    
    # Test 1: Direct Pinecone access
    direct_success = test_direct_pinecone_access()
    
    # Test 2: Data pipeline import
    import_success, vector_store = test_data_pipeline_import()
    
    # Test 3: Simple RAG function
    if direct_success:
        test_simple_rag()
    
    # Summary
    print("\n📊 FIX ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"Direct Pinecone Access: {'✅ Working' if direct_success else '❌ Failed'}")
    print(f"Data Pipeline Import: {'✅ Working' if import_success else '❌ Failed'}")
    
    if direct_success:
        print("\n💡 SOLUTION:")
        print("Pinecone is working fine. The issue is in the RAG node import/initialization.")
        print("We can either:")
        print("1. Fix the existing RAG node import path")
        print("2. Use our simple RAG function as a replacement")
        print("3. Update the RAG node to use direct Pinecone access")
        
        return True
    else:
        print("\n❌ CRITICAL: Pinecone access is broken")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)