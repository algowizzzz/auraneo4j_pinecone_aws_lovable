#!/usr/bin/env python3
"""
Debug script to test retrieval nodes functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_retrieval_nodes():
    """Test and debug retrieval node behavior"""
    
    # Set real environment variables
    real_credentials = {
        'NEO4J_URI': os.getenv('NEO4J_URI'),
        'NEO4J_USERNAME': os.getenv('NEO4J_USERNAME'),
        'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD'),
        'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
        'PINECONE_INDEX_NAME': os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }
    
    for key, value in real_credentials.items():
        if value:
            os.environ[key] = value
    
    print("🔍 Testing Retrieval Nodes")
    print("=" * 60)
    
    # Test cypher node
    print("\n📊 Testing Cypher Node...")
    try:
        from agent.nodes.cypher import cypher
        
        cypher_state = {
            "query_raw": "What are Zions Bancorporation's capital ratios?",
            "metadata": {"company": "ZIONS BANCORPORATION", "year": "2025"},
            "route": "cypher",
            "fallback": ["hybrid", "rag"],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        result = cypher(cypher_state)
        retrievals = result.get("retrievals", [])
        print(f"✅ Cypher: {len(retrievals)} results")
        if retrievals:
            print(f"   First result: {retrievals[0].get('text', '')[:100]}...")
            
    except Exception as e:
        print(f"❌ Cypher failed: {e}")
    
    # Test RAG node  
    print("\n🔍 Testing RAG Node...")
    try:
        from agent.nodes.rag import rag
        
        rag_state = {
            "query_raw": "How do banks handle market risk?",
            "metadata": {},
            "route": "rag", 
            "fallback": ["hybrid", "cypher"],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        result = rag(rag_state)
        retrievals = result.get("retrievals", [])
        print(f"✅ RAG: {len(retrievals)} results")
        if retrievals:
            print(f"   First result: {retrievals[0].get('text', '')[:100]}...")
            print(f"   Score: {retrievals[0].get('score', 'N/A')}")
            
    except Exception as e:
        print(f"❌ RAG failed: {e}")
    
    # Test hybrid node
    print("\n🔗 Testing Hybrid Node...")
    try:
        from agent.nodes.hybrid import hybrid
        
        hybrid_state = {
            "query_raw": "Explain Bank of America's business strategy",
            "metadata": {"company": "BANK OF AMERICA"},
            "route": "hybrid",
            "fallback": ["rag", "cypher"],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        result = hybrid(hybrid_state)
        retrievals = result.get("retrievals", [])
        print(f"✅ Hybrid: {len(retrievals)} results")
        if retrievals:
            print(f"   First result: {retrievals[0].get('text', '')[:100]}...")
            print(f"   Score: {retrievals[0].get('score', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Hybrid failed: {e}")

if __name__ == "__main__":
    test_retrieval_nodes()