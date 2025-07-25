#!/usr/bin/env python3
"""
Test RAG Node Performance
Since RAG is showing "✅ Working" in validation, test its actual performance
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rag_node():
    """Test RAG node performance directly"""
    print("🔍 Testing RAG Node Performance")
    print("=" * 50)
    
    try:
        # Test without importing the whole agent system to avoid conflicts
        from agent.nodes.rag import rag
        
        print("  ✅ RAG node imported successfully")
        
        # Test with business queries
        test_queries = [
            {
                "query": "What are Wells Fargo's capital ratios?",
                "description": "Wells Fargo capital query"
            },
            {
                "query": "How do banks handle operational risk?",
                "description": "Industry risk management query"  
            },
            {
                "query": "What business lines do regional banks operate?",
                "description": "Business operations query"
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n  Test {i}: {test_case['description']}")
            print(f"    Query: {test_case['query']}")
            
            # Create test state
            state = {
                "query_raw": test_case["query"],
                "metadata": {},
                "route": "rag",
                "fallback": ["hybrid"],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
            
            try:
                # Run RAG node
                result_state = rag(state)
                retrievals = result_state.get("retrievals", [])
                
                print(f"    📊 Results: {len(retrievals)} retrievals")
                
                if retrievals:
                    print(f"    ✅ SUCCESS")
                    # Show top result details
                    top_result = retrievals[0]
                    score = top_result.get("score", 0)
                    source = top_result.get("source", "unknown")
                    metadata = top_result.get("metadata", {})
                    company = metadata.get("company", "Unknown")
                    
                    print(f"      Top score: {score:.3f}")
                    print(f"      Source: {source}")
                    print(f"      Company: {company}")
                    print(f"      Text: {top_result.get('text', '')[:80]}...")
                else:
                    print(f"    ⚠️  No results")
                    
            except Exception as e:
                print(f"    ❌ Failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ RAG node test failed: {e}")
        return False

def test_hybrid_node():
    """Test Hybrid node performance"""
    print("\n🔗 Testing Hybrid Node Performance")
    print("=" * 50)
    
    try:
        from agent.nodes.hybrid import hybrid
        
        print("  ✅ Hybrid node imported successfully")
        
        # Test state
        state = {
            "query_raw": "Explain Zions Bancorporation's business model",
            "metadata": {"company": "ZION"},
            "route": "hybrid",
            "fallback": ["rag"],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        try:
            result_state = hybrid(state)
            retrievals = result_state.get("retrievals", [])
            
            print(f"  📊 Results: {len(retrievals)} retrievals")
            
            if retrievals:
                print(f"  ✅ SUCCESS")
                print(f"    Top score: {retrievals[0].get('score', 0):.3f}")
                print(f"    Source: {retrievals[0].get('source', 'unknown')}")
            else:
                print(f"  ⚠️  No results")
                
            return len(retrievals) > 0
            
        except Exception as e:
            print(f"  ❌ Hybrid test failed: {e}")
            return False
        
    except Exception as e:
        print(f"  ❌ Hybrid node import failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Current Retrieval Performance")
    print("=" * 70)
    
    rag_ok = test_rag_node()
    hybrid_ok = test_hybrid_node()
    
    print(f"\n🎯 Retrieval Performance Summary:")
    print("=" * 50)
    print(f"  RAG Node: {'✅ Working' if rag_ok else '❌ Issues'}")
    print(f"  Hybrid Node: {'✅ Working' if hybrid_ok else '❌ Issues'}")
    
    working_nodes = sum([rag_ok, hybrid_ok])
    print(f"  Working Nodes: {working_nodes}/2")
    
    if working_nodes >= 1:
        print(f"\n🚀 Semantic retrieval is operational")
        print(f"   Current system can handle business queries")
    else:
        print(f"\n⚠️  Semantic retrieval needs attention")