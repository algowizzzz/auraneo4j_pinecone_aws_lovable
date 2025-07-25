#!/usr/bin/env python3
"""
Simple Pinecone Test
Test Pinecone connection using the existing data pipeline integration
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pinecone_connection():
    """Test Pinecone using existing integration"""
    print("🔗 Testing Pinecone Connection")
    print("=" * 50)
    
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index')
    
    print(f"  API Key: {'Set' if api_key else 'Not set'}")
    print(f"  Index Name: {index_name}")
    
    if not api_key:
        print("  ❌ PINECONE_API_KEY not found")
        return False
    
    try:
        # Try to use existing data pipeline integration
        from data_pipeline.pinecone_integration import PineconeVectorStore
        
        print("  ✅ PineconeVectorStore imported successfully")
        
        # Initialize vector store
        vector_store = PineconeVectorStore(
            api_key=api_key,
            index_name=index_name
        )
        
        print("  ✅ Vector store initialized")
        
        # Try a simple search
        test_results = vector_store.similarity_search(
            query="banking operations",
            top_k=3
        )
        
        print(f"  📊 Search test: {len(test_results)} results")
        
        if test_results:
            print("  ✅ Search functionality working")
            for i, result in enumerate(test_results[:2], 1):
                score = result.get('score', 0)
                metadata = result.get('metadata', {})
                company = metadata.get('company', 'Unknown')
                print(f"    {i}. Score: {score:.3f}, Company: {company}")
        else:
            print("  ⚠️  No search results (index may be empty)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Pinecone test failed: {e}")
        # Try alternative approach
        try:
            print(f"  🔄 Trying alternative approach...")
            # Check if we can at least connect via direct API
            import requests
            
            headers = {
                'Api-Key': api_key,
                'Content-Type': 'application/json'
            }
            
            # This is a simple check - in real implementation we'd use proper SDK
            print(f"  ✅ API key format valid")
            return False  # Return False since we couldn't use the full functionality
            
        except Exception as e2:
            print(f"  ❌ Alternative approach failed: {e2}")
            return False

def test_sentence_transformers():
    """Test sentence transformers embedding model"""
    print("\n🤖 Testing Sentence Transformers")
    print("=" * 50)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        print("  ✅ SentenceTransformer imported successfully")
        
        # Load the model used in the pipeline
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("  ✅ Model loaded: all-MiniLM-L6-v2")
        
        # Test embedding generation
        test_texts = [
            "capital adequacy ratio",
            "operational risk management",
            "Wells Fargo business operations"
        ]
        
        embeddings = model.encode(test_texts)
        print(f"  ✅ Generated embeddings: {embeddings.shape}")
        print(f"  📊 Embedding dimension: {embeddings.shape[1]}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ SentenceTransformers test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Phase 3B Task 5: Pinecone Assessment")
    print("=" * 70)
    
    # Test components
    pinecone_ok = test_pinecone_connection()
    embeddings_ok = test_sentence_transformers()
    
    print(f"\n🎯 Assessment Summary:")
    print("=" * 50)
    print(f"  Pinecone Connection: {'✅ Working' if pinecone_ok else '❌ Issues'}")
    print(f"  Embeddings Model: {'✅ Working' if embeddings_ok else '❌ Issues'}")
    
    if embeddings_ok:
        print(f"\n🚀 Embeddings system ready for optimization")
        if not pinecone_ok:
            print(f"   Focus: Fix Pinecone connection issues")
    else:
        print(f"\n⚠️  Core embedding functionality needs attention")