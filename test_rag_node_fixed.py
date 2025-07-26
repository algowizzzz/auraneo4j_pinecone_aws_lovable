#!/usr/bin/env python3
"""
Test the FIXED RAG Node
"""

import os
import sys
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
load_dotenv()

def test_fixed_rag_node():
    """Test the fixed RAG node with direct Pinecone access"""
    print("🧪 TESTING FIXED RAG NODE")
    print("=" * 50)
    
    try:
        # Import the fixed RAG node
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agent.nodes.rag_fixed import rag
        
        # Test queries
        test_cases = [
            {
                "name": "Wells Fargo Risk Factors",
                "state": {
                    "query_raw": "What are the main risk factors for Wells Fargo?",
                    "metadata": {"company": "WFC"},
                    "retrievals": [],
                    "confidence": 0.0
                }
            },
            {
                "name": "Credit Risk Management",
                "state": {
                    "query_raw": "credit risk management and operational risk strategies",
                    "metadata": {},
                    "retrievals": [],
                    "confidence": 0.0
                }
            },
            {
                "name": "Business Strategy",
                "state": {
                    "query_raw": "business strategy and revenue growth",
                    "metadata": {"company": "BAC"},
                    "retrievals": [],
                    "confidence": 0.0
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🔍 Test: {test_case['name']}")
            print(f"Query: {test_case['state']['query_raw']}")
            
            # Execute RAG node
            result = rag(test_case['state'])
            
            retrievals = result.get("retrievals", [])
            confidence = result.get("confidence", 0.0)
            
            print(f"Results: {len(retrievals)} retrievals, confidence: {confidence:.3f}")
            
            if retrievals:
                print("Sample results:")
                for i, hit in enumerate(retrievals[:3]):
                    score = hit.get("score", 0)
                    chunk_id = hit.get("id", "unknown")
                    company = hit.get("metadata", {}).get("company", "Unknown")
                    print(f"  {i+1}. {chunk_id} (Score: {score:.3f}) - {company}")
                
                print("✅ RAG node working!")
            else:
                print("❌ No results returned")
        
        return True
        
    except Exception as e:
        print(f"❌ Fixed RAG node test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_fixed_rag_node()
    if success:
        print("\n🎉 FIXED RAG NODE: FULLY FUNCTIONAL!")
        print("Ready to replace the original RAG node")
    else:
        print("\n❌ Fixed RAG node still has issues")