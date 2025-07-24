#!/usr/bin/env python3
"""
Debug script to understand planner behavior
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_planner_behavior():
    """Test and debug planner behavior"""
    
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
    
    try:
        from agent.nodes.planner import planner
        
        test_queries = [
            "What are Zions Bancorporation's capital ratios in 2025 Q1?",
            "Explain Bank of America's risk management strategy",
            "Compare regional banks' competitive positioning",
            "Analyze market risk, credit risk, and operational risk for JPMorgan"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing Query: {query}")
            print("=" * 60)
            
            initial_state = {
                "query_raw": query,
                "metadata": {},
                "route": "",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
            
            try:
                result_state = planner(initial_state)
                
                print(f"Route: {result_state.get('route', 'NOT SET')}")
                print(f"Fallback: {result_state.get('fallback', [])}")
                print(f"Metadata: {result_state.get('metadata', {})}")
                
                if "subtasks" in result_state:
                    print(f"Subtasks: {result_state.get('subtasks', [])}")
                    
                # Print all keys in the result state for debugging
                print(f"All result keys: {list(result_state.keys())}")
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                
    except Exception as e:
        print(f"Failed to import planner: {e}")

if __name__ == "__main__":
    test_planner_behavior()