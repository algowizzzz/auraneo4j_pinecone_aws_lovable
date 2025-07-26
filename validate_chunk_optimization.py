#!/usr/bin/env python3
"""
Task 3D.2 - Step 4: Validate ~20 Chunk Retrieval Optimization

Validates that all three agent nodes (RAG, Hybrid, Cypher) are properly 
configured to retrieve approximately 20 chunks consistently.

VALIDATION APPROACH:
1. Test each node with identical queries
2. Verify chunk counts are close to 20 target
3. Check performance consistency
4. Ensure optimization doesn't break functionality
"""

import os
import sys
import time
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def validate_chunk_optimization():
    """Validate ~20 chunk retrieval optimization across all nodes"""
    print("🧪 CHUNK RETRIEVAL OPTIMIZATION VALIDATION")
    print("=" * 60)
    
    try:
        # Import all three nodes
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agent.nodes.rag import rag
        from agent.nodes.hybrid import hybrid
        from agent.nodes.cypher import cypher
        
        # Test cases designed to generate ~20 chunks
        test_cases = [
            {
                "name": "Company-Specific Financial Query",
                "state": {
                    "query_raw": "risk management strategies and operational risk frameworks",
                    "metadata": {"company": "BAC"},
                    "route": "",
                    "retrievals": [],
                    "confidence": 0.0
                },
                "target_chunks": 20,
                "expectation": "Should return ~20 chunks about BAC's risk management"
            },
            {
                "name": "Cross-Company Business Analysis",
                "state": {
                    "query_raw": "business segments and revenue diversification strategies",
                    "metadata": {},
                    "route": "",
                    "retrievals": [],
                    "confidence": 0.0
                },
                "target_chunks": 20,
                "expectation": "Should return ~20 chunks from various companies about business segments"
            },
            {
                "name": "Temporal Query with Company Filter",
                "state": {
                    "query_raw": "strategic priorities and business transformation initiatives",
                    "metadata": {"company": "GS", "year": 2024},
                    "route": "",
                    "retrievals": [],
                    "confidence": 0.0
                },
                "target_chunks": 20,
                "expectation": "Should return ~20 chunks about GS 2024 strategic priorities"
            }
        ]
        
        nodes = [
            {"name": "RAG", "function": rag, "optimal_range": (15, 25)},
            {"name": "Hybrid", "function": hybrid, "optimal_range": (15, 25)},
            {"name": "Cypher", "function": cypher, "optimal_range": (15, 25)}
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🔍 TEST CASE: {test_case['name']}")
            print(f"Query: {test_case['state']['query_raw']}")
            print(f"Metadata: {test_case['state']['metadata']}")
            print(f"Target: ~{test_case['target_chunks']} chunks")
            print("-" * 50)
            
            test_results = []
            
            for node in nodes:
                node_name = node["name"]
                node_function = node["function"]
                optimal_min, optimal_max = node["optimal_range"]
                
                # Prepare state for this node
                test_state = test_case["state"].copy()
                test_state["route"] = node_name.lower()
                
                print(f"  📊 Testing {node_name} Node...")
                
                # Execute node
                start_time = time.time()
                result = node_function(test_state)
                execution_time = time.time() - start_time
                
                # Analyze results
                retrievals = result.get("retrievals", [])
                chunk_count = len(retrievals)
                confidence = result.get("confidence", 0.0)
                
                # Check if within optimal range
                is_optimal = optimal_min <= chunk_count <= optimal_max
                optimization_status = "✅ OPTIMAL" if is_optimal else f"⚠️  SUBOPTIMAL ({chunk_count})"
                
                print(f"    Results: {chunk_count} chunks, confidence: {confidence:.3f}, time: {execution_time:.2f}s")
                print(f"    Status: {optimization_status}")
                
                # Store detailed results
                test_results.append({
                    "node": node_name,
                    "chunks": chunk_count,
                    "confidence": confidence,
                    "time": execution_time,
                    "is_optimal": is_optimal,
                    "target": test_case["target_chunks"]
                })
                
                # Show sample chunk IDs to verify diversity
                if retrievals:
                    sample_chunks = [hit.get("id", hit.get("section_id", "unknown")) for hit in retrievals[:3]]
                    print(f"    Sample chunks: {sample_chunks}")
            
            results.append({
                "test_case": test_case["name"],
                "node_results": test_results
            })
        
        # Overall Analysis
        print(f"\n🎯 CHUNK OPTIMIZATION ANALYSIS")
        print("=" * 60)
        
        # Calculate statistics by node
        node_stats = {}
        for node in nodes:
            node_name = node["name"]
            node_chunks = []
            node_times = []
            node_optimal_count = 0
            
            for result in results:
                for node_result in result["node_results"]:
                    if node_result["node"] == node_name:
                        node_chunks.append(node_result["chunks"])
                        node_times.append(node_result["time"])
                        if node_result["is_optimal"]:
                            node_optimal_count += 1
            
            avg_chunks = sum(node_chunks) / len(node_chunks) if node_chunks else 0
            avg_time = sum(node_times) / len(node_times) if node_times else 0
            optimization_rate = (node_optimal_count / len(node_chunks)) * 100 if node_chunks else 0
            
            node_stats[node_name] = {
                "avg_chunks": avg_chunks,
                "avg_time": avg_time,
                "optimization_rate": optimization_rate,
                "chunk_range": (min(node_chunks), max(node_chunks)) if node_chunks else (0, 0)
            }
        
        # Display node statistics
        for node_name, stats in node_stats.items():
            print(f"\n📊 {node_name} Node Statistics:")
            print(f"  Average chunks retrieved: {stats['avg_chunks']:.1f}")
            print(f"  Chunk range: {stats['chunk_range'][0]}-{stats['chunk_range'][1]}")
            print(f"  Average response time: {stats['avg_time']:.2f}s")
            print(f"  Optimization rate: {stats['optimization_rate']:.1f}% (within 15-25 range)")
            
            # Performance assessment
            if stats['avg_chunks'] >= 15 and stats['avg_chunks'] <= 25:
                print(f"  Status: ✅ WELL OPTIMIZED")
            elif stats['avg_chunks'] >= 10:
                print(f"  Status: ✅ ACCEPTABLE")
            else:
                print(f"  Status: ❌ NEEDS OPTIMIZATION")
        
        # Overall system assessment
        overall_optimal_tests = sum(
            sum(1 for node_result in result["node_results"] if node_result["is_optimal"])
            for result in results
        )
        total_tests = sum(len(result["node_results"]) for result in results)
        overall_optimization_rate = (overall_optimal_tests / total_tests) * 100
        
        print(f"\n🎯 OVERALL OPTIMIZATION SUMMARY")
        print(f"  Total tests: {total_tests}")
        print(f"  Optimal results: {overall_optimal_tests}/{total_tests}")
        print(f"  System optimization rate: {overall_optimization_rate:.1f}%")
        
        if overall_optimization_rate >= 80:
            print(f"  ✅ EXCELLENT: System is well-optimized for ~20 chunk retrieval")
            success = True
        elif overall_optimization_rate >= 60:
            print(f"  ✅ GOOD: System mostly optimized, minor tweaks needed")
            success = True
        else:
            print(f"  ⚠️  NEEDS WORK: System requires optimization improvements")
            success = False
        
        # Recommendations
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        for node_name, stats in node_stats.items():
            if stats['avg_chunks'] < 15:
                print(f"  - {node_name}: Increase top_k or limit parameter")
            elif stats['avg_chunks'] > 25:
                print(f"  - {node_name}: Decrease top_k or limit parameter")
            else:
                print(f"  - {node_name}: Well optimized ✅")
        
        if success:
            print(f"\n🚀 READY FOR E2E TESTING: All nodes optimized for ~20 chunk retrieval!")
            return True
        else:
            print(f"\n🔧 OPTIMIZATION NEEDED: Address issues before E2E testing")
            return False
        
    except Exception as e:
        print(f"❌ Chunk optimization validation failed: {e}")
        return False

if __name__ == "__main__":
    success = validate_chunk_optimization()
    if success:
        print("🎉 Chunk optimization validation PASSED!")
    else:
        print("⚠️  Chunk optimization validation FAILED!")
    sys.exit(0 if success else 1)