#!/usr/bin/env python3
"""
Task 3D.2 - Step 3: Cypher Node Focused Testing

Quick validation of Cypher node with diverse prompts to test:
- Graph relationship traversal with chunked schema
- Company-specific queries
- Cross-company comparisons
- Temporal queries
- Performance with ~20 chunk retrieval
"""

import os
import sys
import time
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def test_cypher_node_diverse_prompts():
    """Test Cypher node with diverse set of prompts"""
    print("🧪 CYPHER NODE FOCUSED TESTING - DIVERSE PROMPTS")
    print("=" * 60)
    
    try:
        # Import Cypher node
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agent.nodes.cypher import cypher
        
        # Diverse test cases
        test_cases = [
            {
                "name": "Company-Specific Query",
                "state": {
                    "query_raw": "What are Wells Fargo's main business segments?",
                    "metadata": {"company": "WFC"},
                    "route": "cypher",
                    "retrievals": [],
                    "confidence": 0.0
                },
                "expectation": "Should find WFC-specific chunks about business segments"
            },
            {
                "name": "Cross-Company Comparison",
                "state": {
                    "query_raw": "Compare risk management approaches between Bank of America and Morgan Stanley",
                    "metadata": {"companies": ["BAC", "MS"]},
                    "route": "cypher",
                    "retrievals": [],
                    "confidence": 0.0
                },
                "expectation": "Should retrieve chunks from both BAC and MS about risk management"
            },
            {
                "name": "Temporal/Year-Specific Query",
                "state": {
                    "query_raw": "What were Goldman Sachs' strategic priorities in 2024?",
                    "metadata": {"company": "GS", "year": 2024},
                    "route": "cypher",
                    "retrievals": [],
                    "confidence": 0.0
                },
                "expectation": "Should find GS 2024 content about strategic priorities"
            },
            {
                "name": "Financial Concept Query",
                "state": {
                    "query_raw": "Show me information about credit risk and operational risk management",
                    "metadata": {"concepts": ["credit risk", "operational risk"]},
                    "route": "cypher",
                    "retrievals": [],
                    "confidence": 0.0
                },
                "expectation": "Should find chunks containing risk management concepts"
            },
            {
                "name": "Document Type Query",
                "state": {
                    "query_raw": "Find 10-K filing information about regulatory compliance",
                    "metadata": {"doc_type": "10-K", "topic": "regulatory compliance"},
                    "route": "cypher",
                    "retrievals": [],
                    "confidence": 0.0
                },
                "expectation": "Should retrieve 10-K document chunks about regulatory compliance"
            },
            {
                "name": "Open-Ended Query",
                "state": {
                    "query_raw": "What are the key business challenges facing major banks?",
                    "metadata": {},
                    "route": "cypher",
                    "retrievals": [],
                    "confidence": 0.0
                },
                "expectation": "Should return diverse chunks about business challenges across companies"
            }
        ]
        
        results = []
        total_time = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 TEST {i}/6: {test_case['name']}")
            print(f"Query: {test_case['state']['query_raw']}")
            print(f"Metadata: {test_case['state']['metadata']}")
            print(f"Expected: {test_case['expectation']}")
            
            # Execute Cypher node
            start_time = time.time()
            result = cypher(test_case['state'])
            execution_time = time.time() - start_time
            total_time += execution_time
            
            # Analyze results
            retrievals = result.get("retrievals", [])
            confidence = result.get("confidence", 0.0)
            retrieval_count = len(retrievals)
            
            print(f"📊 Results: {retrieval_count} retrievals, confidence: {confidence:.3f}, time: {execution_time:.2f}s")
            
            # Show sample results
            if retrievals:
                print(f"📄 Sample chunks:")
                companies_found = set()
                
                for j, hit in enumerate(retrievals[:5]):
                    chunk_id = hit.get("id", "unknown")
                    score = hit.get("score", 0)
                    metadata = hit.get("metadata", {})
                    company = metadata.get("company", "Unknown")
                    
                    # Extract company from chunk_id if not in metadata
                    if company == "Unknown" and "_" in chunk_id:
                        company = chunk_id.split("_")[0].upper()
                    
                    companies_found.add(company)
                    print(f"  {j+1}. {chunk_id} (Score: {score:.3f}) - {company}")
                
                print(f"🏢 Companies found: {sorted(list(companies_found))}")
                
                # Check if we're getting close to 20 chunks
                if retrieval_count >= 15:
                    print("✅ Good chunk retrieval count (~20 target)")
                elif retrieval_count >= 10:
                    print("✅ Reasonable chunk retrieval count")
                else:
                    print(f"⚠️  Lower retrieval count: {retrieval_count}")
                
                success = True
            else:
                print("❌ No results returned")
                success = False
            
            results.append({
                "name": test_case['name'],
                "success": success,
                "retrievals": retrieval_count,
                "confidence": confidence,
                "time": execution_time
            })
        
        # Summary
        successful_tests = sum(1 for r in results if r["success"])
        avg_time = total_time / len(test_cases)
        avg_retrievals = sum(r["retrievals"] for r in results) / len(results)
        avg_confidence = sum(r["confidence"] for r in results) / len(results)
        
        print(f"\n🎯 CYPHER NODE FOCUSED TEST SUMMARY")
        print("=" * 50)
        print(f"✅ Tests passed: {successful_tests}/{len(test_cases)}")
        print(f"⏱️  Average time: {avg_time:.2f}s")
        print(f"📊 Average retrievals: {avg_retrievals:.1f}")
        print(f"📊 Average confidence: {avg_confidence:.3f}")
        
        # Performance assessment
        if avg_time < 2.0:
            print("✅ Excellent Cypher performance (< 2s average)")
        elif avg_time < 5.0:
            print("✅ Good Cypher performance (< 5s average)")
        else:
            print(f"⚠️  Slower Cypher performance ({avg_time:.2f}s average)")
        
        # Individual test results
        print(f"\n📋 Individual Test Results:")
        for result in results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"  {result['name']}: {status} ({result['retrievals']} chunks, {result['time']:.2f}s)")
        
        if successful_tests == len(test_cases):
            print(f"\n🎉 CYPHER NODE: FULLY FUNCTIONAL WITH DIVERSE PROMPTS ✅")
            return True
        else:
            print(f"\n⚠️  CYPHER NODE: Some issues detected ({successful_tests}/{len(test_cases)} passed)")
            return False
        
    except Exception as e:
        print(f"❌ Cypher node test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_cypher_node_diverse_prompts()
    if success:
        print("🚀 Ready to proceed to retrieval optimization and E2E testing!")
    else:
        print("🔧 Address Cypher node issues before proceeding")
    sys.exit(0 if success else 1)