#!/usr/bin/env python3
"""
Simple debug script to test retrieval node structure
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_retrieval_structure():
    """Test retrieval node structure without heavy operations"""
    
    print("🔍 Testing Retrieval Node Structure")
    print("=" * 50)
    
    # Test imports
    print("\n📦 Testing Imports...")
    try:
        from agent.nodes.cypher import cypher, Neo4jCypherRetriever
        print("✅ Cypher node imported")
        
        from agent.nodes.hybrid import hybrid, HybridRetriever  
        print("✅ Hybrid node imported")
        
        from agent.nodes.rag import rag, RAGRetriever
        print("✅ RAG node imported")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return
    
    # Test class instantiation (without heavy initialization)
    print("\n🏗️ Testing Class Structure...")
    try:
        # These might fail due to missing connections, but we can check structure
        try:
            cypher_retriever = Neo4jCypherRetriever()
            print("✅ Neo4jCypherRetriever instantiated")
        except Exception as e:
            print(f"⚠️ Neo4jCypherRetriever failed (expected): {str(e)[:50]}...")
        
        try:
            hybrid_retriever = HybridRetriever()
            print("✅ HybridRetriever instantiated")
        except Exception as e:
            print(f"⚠️ HybridRetriever failed (expected): {str(e)[:50]}...")
            
        try:
            rag_retriever = RAGRetriever()
            print("✅ RAGRetriever instantiated")
        except Exception as e:
            print(f"⚠️ RAGRetriever failed (expected): {str(e)[:50]}...")
            
    except Exception as e:
        print(f"❌ Class instantiation failed: {e}")
    
    # Test function signatures
    print("\n🔧 Testing Function Signatures...")
    
    test_state = {
        "query_raw": "test",
        "metadata": {},
        "route": "test",
        "fallback": [],
        "retrievals": [],
        "valid": False,
        "final_answer": "",
        "citations": []
    }
    
    functions = [
        ("cypher", cypher),
        ("hybrid", hybrid),
        ("rag", rag)
    ]
    
    for name, func in functions:
        try:
            # Don't actually run, just check if callable
            assert callable(func), f"{name} should be callable"
            print(f"✅ {name} function is callable")
        except Exception as e:
            print(f"❌ {name} function test failed: {e}")

if __name__ == "__main__":
    test_retrieval_structure()