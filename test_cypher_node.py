#!/usr/bin/env python3
"""
Test Cypher Node Performance
Validates that cypher queries work after graph population
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cypher_node():
    """Test cypher node with real business queries"""
    print("🧪 Testing Cypher Node Performance")
    print("=" * 50)
    
    try:
        from agent.nodes.cypher import cypher
        from agent.utils.company_mapping import normalize_company
        
        # Test queries with proper company normalization
        test_cases = [
            {
                "query": "What are Wells Fargo's capital ratios in 2025?",
                "metadata": {
                    "company": normalize_company("Wells Fargo"),
                    "year": "2025"
                },
                "description": "Wells Fargo 2025 query"
            },
            {
                "query": "What are Zions Bancorporation's business operations?", 
                "metadata": {
                    "company": normalize_company("Zions Bancorporation")
                },
                "description": "Zions business query"
            },
            {
                "query": "JPMorgan risk factors in 2024 Q1",
                "metadata": {
                    "company": normalize_company("JPMorgan"),
                    "year": "2024",
                    "quarter": "Q1"
                },
                "description": "JPMorgan Q1 2024 query"
            }
        ]
        
        print(f"\n📋 Running {len(test_cases)} test cases...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n  Test {i}: {test_case['description']}")
            print(f"    Query: {test_case['query']}")
            print(f"    Metadata: {test_case['metadata']}")
            
            # Create state for cypher node
            state = {
                "query_raw": test_case["query"],
                "metadata": test_case["metadata"],
                "retrievals": []
            }
            
            # Run cypher node
            try:
                result_state = cypher(state)
                retrievals = result_state.get("retrievals", [])
                
                if retrievals:
                    print(f"    ✅ Success: {len(retrievals)} results")
                    print(f"    📄 First result: {retrievals[0]['text'][:100]}...")
                else:
                    print(f"    ⚠️  No results found")
                    
            except Exception as e:
                print(f"    ❌ Failed: {e}")
        
        print(f"\n🎯 Cypher node testing complete")
        
    except Exception as e:
        print(f"❌ Cypher test failed: {e}")

if __name__ == "__main__":
    test_cypher_node()
