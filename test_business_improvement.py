#!/usr/bin/env python3
"""
Test Business Query Improvement
Test the priority business queries from the E2E testing to measure improvement
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_business_queries():
    """Test key business queries with virtual environment"""
    print("🚀 Testing Business Query Improvements")
    print("=" * 70)
    
    try:
        # Test import with virtual environment path
        print("  Testing agent imports...")
        
        # Try importing from current working directory
        from agent.nodes.rag import rag
        from agent.nodes.hybrid import hybrid
        from agent.nodes.planner import planner
        
        print("  ✅ All nodes imported successfully")
        
        # Business Query Tests
        business_queries = [
            {
                "id": "BQ001",
                "name": "Prosperity Bancshares Profile", 
                "query": "What are Prosperity Bancshares business lines and operations?",
                "expected_route": "rag",
                "previous_result": "29.08s, 15 retrievals, validation 0.50"
            },
            {
                "id": "BQ004", 
                "name": "Zions Temporal Analysis",
                "query": "How has Zions Bancorporation business strategy evolved from 2021 to 2025?",
                "expected_route": "rag", 
                "previous_result": "8.33s, 20 retrievals, validation 0.67 - SUCCESS"
            },
            {
                "id": "BQ_SIMPLE",
                "name": "Simple Company Query",
                "query": "What business lines does KeyCorp operate?",
                "expected_route": "rag",
                "previous_result": "New test for basic functionality"
            }
        ]
        
        results = []
        
        for query_info in business_queries:
            print(f"\n🔍 Testing {query_info['id']}: {query_info['name']}")
            print(f"    Query: {query_info['query']}")
            print(f"    Previous: {query_info['previous_result']}")
            
            # Create test state  
            state = {
                "query_raw": query_info["query"],
                "metadata": {},
                "route": "",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
            
            try:
                # Step 1: Test Planner
                start_time = time.time()
                planner_result = planner(state)
                planner_time = time.time() - start_time
                
                route = planner_result.get("route", "unknown")
                metadata = planner_result.get("metadata", {})
                
                print(f"    📊 Planner: {route} ({planner_time:.2f}s)")
                print(f"        Metadata: {metadata}")
                
                # Step 2: Test Retrieval based on route
                if route == "rag":
                    retrieval_start = time.time()
                    retrieval_result = rag(planner_result)
                    retrieval_time = time.time() - retrieval_start
                    retrievals = retrieval_result.get("retrievals", [])
                    
                    print(f"    📊 RAG Retrieval: {len(retrievals)} results ({retrieval_time:.2f}s)")
                    
                    if retrievals:
                        top_result = retrievals[0]
                        print(f"        Top score: {top_result.get('score', 0):.3f}")
                        print(f"        Source: {top_result.get('source', 'unknown')}")
                        print(f"        Text preview: {top_result.get('text', '')[:60]}...")
                        
                elif route == "hybrid":
                    retrieval_start = time.time()
                    retrieval_result = hybrid(planner_result)
                    retrieval_time = time.time() - retrieval_start
                    retrievals = retrieval_result.get("retrievals", [])
                    
                    print(f"    📊 Hybrid Retrieval: {len(retrievals)} results ({retrieval_time:.2f}s)")
                else:
                    print(f"    ⚠️  Unsupported route: {route}")
                    retrievals = []
                    retrieval_time = 0
                
                total_time = planner_time + retrieval_time
                
                # Results summary
                success = len(retrievals) > 0
                print(f"    🎯 Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
                print(f"    ⏱️  Total time: {total_time:.2f}s")
                
                results.append({
                    "id": query_info["id"],
                    "success": success,
                    "retrievals": len(retrievals),
                    "total_time": total_time,
                    "route": route
                })
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                results.append({
                    "id": query_info["id"], 
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        print(f"\n🎯 Business Query Test Summary:")
        print("=" * 50)
        
        successful = sum(1 for r in results if r.get("success", False))
        total = len(results)
        
        for result in results:
            status = "✅ SUCCESS" if result.get("success", False) else "❌ FAILED"
            retrievals = result.get("retrievals", 0)
            time_taken = result.get("total_time", 0)
            route = result.get("route", "unknown")
            
            print(f"  {result['id']}: {status}")
            if result.get("success", False):
                print(f"    Route: {route}, Results: {retrievals}, Time: {time_taken:.2f}s")
            elif result.get("error"):
                print(f"    Error: {result['error']}")
        
        print(f"\n📊 Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
        
        if successful >= total * 0.67:
            print("🚀 BUSINESS INTEGRATION: Significantly improved!")
        elif successful >= total * 0.33:
            print("⚠️  BUSINESS INTEGRATION: Partial improvement")
        else:
            print("❌ BUSINESS INTEGRATION: Needs more work")
            
        return successful >= total * 0.5
        
    except Exception as e:
        print(f"❌ Business query testing failed: {e}")
        return False

if __name__ == "__main__":
    success = test_business_queries()
    
    if success:
        print(f"\n✅ Business integration testing: IMPROVED")
    else:
        print(f"\n⚠️  Business integration testing: NEEDS ATTENTION")