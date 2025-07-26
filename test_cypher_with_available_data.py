#!/usr/bin/env python3
"""
Test Cypher Node with Available Data
Tests the Cypher node using companies that are actually in the Neo4j database.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.nodes.cypher import cypher
from agent.state import AgentState

def test_cypher_with_available_companies():
    """Test Cypher node with companies that exist in the database."""
    
    print("🧪 Testing Cypher Node with Available Data")
    print("=" * 50)
    
    # Test cases using companies that are actually in the database
    test_cases = [
        {
            "query": "What are Goldman Sachs' capital ratios in 2025?",
            "company": "GS",
            "year": "2025"
        },
        {
            "query": "Tell me about Wells Fargo's business operations in 2024.",
            "company": "WFC", 
            "year": "2024"
        },
        {
            "query": "What are Bank of America's risk factors in 2025?",
            "company": "BAC",
            "year": "2025"
        }
    ]
    
    print(f"\n📋 Running {len(test_cases)} test cases with available data...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"  Test {i}: {test_case['company']} {test_case['year']} query")
        print(f"    Query: {test_case['query']}")
        
        # Create state with metadata
        state = AgentState(
            query=test_case['query'],
            plan={
                "metadata": {
                    "company": test_case['company'],
                    "year": test_case['year']
                }
            },
            subtasks=[],
            final_output=""
        )
        
        try:
            # Run cypher node
            result = cypher(state)
            
            # Handle different return types
            if isinstance(result, dict):
                # Check for results in different possible keys
                retrieval_hits = result.get('retrieval_hits', [])
                if not retrieval_hits:
                    retrieval_hits = result.get('retrievals', [])
            else:
                # If it returns an AgentState, get retrieval_hits from it
                retrieval_hits = getattr(result, 'retrieval_hits', [])
                if not retrieval_hits:
                    retrieval_hits = getattr(result, 'retrievals', [])
            
            if retrieval_hits:
                print(f"    ✅ Success: {len(retrieval_hits)} results")
                # Show first result preview
                first_hit = retrieval_hits[0]
                if hasattr(first_hit, 'text'):
                    preview = first_hit.text[:200] + "..." if len(first_hit.text) > 200 else first_hit.text
                elif isinstance(first_hit, dict) and 'text' in first_hit:
                    preview = first_hit['text'][:200] + "..." if len(first_hit['text']) > 200 else first_hit['text']
                else:
                    preview = str(first_hit)[:200] + "..."
                print(f"    📄 First result preview: {preview}")
            else:
                print(f"    ⚠️  No results found")
                print(f"    🔍 Return type: {type(result)}")
                print(f"    🔍 Return keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                # Debug: Show what's actually in retrievals
                if isinstance(result, dict) and 'retrievals' in result:
                    print(f"    🔍 Retrievals content: {result['retrievals']}")
                    print(f"    🔍 Retrievals type: {type(result['retrievals'])}")
                    print(f"    🔍 Retrievals length: {len(result['retrievals']) if hasattr(result['retrievals'], '__len__') else 'N/A'}")
                
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            import traceback
            print(f"    📋 Full error: {traceback.format_exc()}")
        
        print()
    
    print("✅ Cypher node testing completed!")

if __name__ == "__main__":
    test_cypher_with_available_companies() 