#!/usr/bin/env python3
"""
Test Q1 (Goldman Sachs) and Q4 (Morgan Stanley) queries individually through each tool
to identify where placeholder values and company mapping issues occur
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The actual problematic queries from E2E results
Q1_GOLDMAN_SACHS = "From Goldman Sachs (GS) 2025 10-K filing, what are the total assets, total deposits, and shareholders' equity as of year-end? Provide the specific balance sheet figures and any notable changes mentioned."

Q4_MORGAN_STANLEY = "From Morgan Stanley (MS) 2025 10-K, what are the net revenues, net income, and return on equity for 2024? Also include any forward-looking guidance or outlook mentioned."

def test_rag_with_problematic_queries():
    """Test RAG node with Q1 and Q4"""
    print("🧪 Testing RAG Node with Q1 (Goldman Sachs) and Q4 (Morgan Stanley)")
    print("=" * 70)
    
    try:
        from agent.nodes.rag import rag
        
        # Test Q1 - Goldman Sachs
        print("\n📋 Q1 - Goldman Sachs Query:")
        print(f"Query: {Q1_GOLDMAN_SACHS}")
        
        state_q1 = {
            "query_raw": Q1_GOLDMAN_SACHS,
            "metadata": {"company": "GS", "year": "2025"},
            "route": "rag",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        start_time = time.time()
        result_q1 = rag(state_q1)
        execution_time = time.time() - start_time
        
        retrievals_q1 = result_q1.get("retrievals", [])
        print(f"✅ Q1 Results: {len(retrievals_q1)} retrievals in {execution_time:.2f}s")
        
        # Check company mapping
        gs_count = 0
        other_companies = set()
        for hit in retrievals_q1[:5]:
            metadata = hit.get("metadata", {})
            company = metadata.get("company", "Unknown")
            chunk_id = hit.get("id", "")
            
            if "gs_" in chunk_id.lower() or company == "GS":
                gs_count += 1
            else:
                other_companies.add(company)
            
            print(f"  - {chunk_id} | {company} | Score: {hit.get('score', 0):.3f}")
        
        print(f"📊 Q1 Company Analysis: GS={gs_count}, Others={other_companies}")
        
        # Test Q4 - Morgan Stanley
        print(f"\n📋 Q4 - Morgan Stanley Query:")
        print(f"Query: {Q4_MORGAN_STANLEY}")
        
        state_q4 = {
            "query_raw": Q4_MORGAN_STANLEY,
            "metadata": {"company": "MS", "year": "2025"},
            "route": "rag",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        start_time = time.time()
        result_q4 = rag(state_q4)
        execution_time = time.time() - start_time
        
        retrievals_q4 = result_q4.get("retrievals", [])
        print(f"✅ Q4 Results: {len(retrievals_q4)} retrievals in {execution_time:.2f}s")
        
        # Check company mapping
        ms_count = 0
        other_companies = set()
        for hit in retrievals_q4[:5]:
            metadata = hit.get("metadata", {})
            company = metadata.get("company", "Unknown")
            chunk_id = hit.get("id", "")
            
            if "ms_" in chunk_id.lower() or company == "MS":
                ms_count += 1
            else:
                other_companies.add(company)
            
            print(f"  - {chunk_id} | {company} | Score: {hit.get('score', 0):.3f}")
        
        print(f"📊 Q4 Company Analysis: MS={ms_count}, Others={other_companies}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        return False

def test_cypher_with_problematic_queries():
    """Test Cypher node with Q1 and Q4"""
    print("\n🧪 Testing Cypher Node with Q1 (Goldman Sachs) and Q4 (Morgan Stanley)")
    print("=" * 70)
    
    try:
        from agent.nodes.cypher import cypher
        
        # Test Q1 - Goldman Sachs
        print("\n📋 Q1 - Goldman Sachs Query:")
        
        state_q1 = {
            "query_raw": Q1_GOLDMAN_SACHS,
            "metadata": {"company": "GS", "year": "2025"},
            "route": "cypher",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        start_time = time.time()
        result_q1 = cypher(state_q1)
        execution_time = time.time() - start_time
        
        retrievals_q1 = result_q1.get("retrievals", [])
        print(f"✅ Q1 Results: {len(retrievals_q1)} retrievals in {execution_time:.2f}s")
        
        for i, hit in enumerate(retrievals_q1[:3]):
            text_preview = hit.get("text", "")[:100]
            print(f"  {i+1}. {text_preview}...")
        
        # Test Q4 - Morgan Stanley
        print(f"\n📋 Q4 - Morgan Stanley Query:")
        
        state_q4 = {
            "query_raw": Q4_MORGAN_STANLEY,
            "metadata": {"company": "MS", "year": "2025"},
            "route": "cypher",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        start_time = time.time()
        result_q4 = cypher(state_q4)
        execution_time = time.time() - start_time
        
        retrievals_q4 = result_q4.get("retrievals", [])
        print(f"✅ Q4 Results: {len(retrievals_q4)} retrievals in {execution_time:.2f}s")
        
        for i, hit in enumerate(retrievals_q4[:3]):
            text_preview = hit.get("text", "")[:100]
            print(f"  {i+1}. {text_preview}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Cypher test failed: {e}")
        return False

def test_hybrid_with_problematic_queries():
    """Test Hybrid node with Q1 and Q4"""
    print("\n🧪 Testing Hybrid Node with Q1 (Goldman Sachs) and Q4 (Morgan Stanley)")
    print("=" * 70)
    
    try:
        from agent.nodes.hybrid import hybrid
        
        # Test Q1 - Goldman Sachs
        print("\n📋 Q1 - Goldman Sachs Query:")
        
        state_q1 = {
            "query_raw": Q1_GOLDMAN_SACHS,
            "metadata": {"company": "GS", "year": "2025"},
            "route": "hybrid",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        start_time = time.time()
        result_q1 = hybrid(state_q1)
        execution_time = time.time() - start_time
        
        retrievals_q1 = result_q1.get("retrievals", [])
        print(f"✅ Q1 Results: {len(retrievals_q1)} retrievals in {execution_time:.2f}s")
        
        # Analyze sources
        pinecone_count = 0
        neo4j_count = 0
        gs_count = 0
        
        for hit in retrievals_q1[:5]:
            source = hit.get("source", "unknown")
            metadata = hit.get("metadata", {})
            company = metadata.get("company", "Unknown")
            chunk_id = hit.get("id", "")
            
            if "pinecone" in source.lower():
                pinecone_count += 1
            elif "neo4j" in source.lower() or "graph" in source.lower():
                neo4j_count += 1
                
            if "gs_" in chunk_id.lower() or company == "GS":
                gs_count += 1
            
            print(f"  - {chunk_id} | {company} | {source}")
        
        print(f"📊 Q1 Source Analysis: Pinecone={pinecone_count}, Neo4j={neo4j_count}, GS={gs_count}")
        
        # Test Q4 - Morgan Stanley
        print(f"\n📋 Q4 - Morgan Stanley Query:")
        
        state_q4 = {
            "query_raw": Q4_MORGAN_STANLEY,
            "metadata": {"company": "MS", "year": "2025"},
            "route": "hybrid",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        start_time = time.time()
        result_q4 = hybrid(state_q4)
        execution_time = time.time() - start_time
        
        retrievals_q4 = result_q4.get("retrievals", [])
        print(f"✅ Q4 Results: {len(retrievals_q4)} retrievals in {execution_time:.2f}s")
        
        # Analyze sources
        pinecone_count = 0
        neo4j_count = 0
        ms_count = 0
        
        for hit in retrievals_q4[:5]:
            source = hit.get("source", "unknown")
            metadata = hit.get("metadata", {})
            company = metadata.get("company", "Unknown")
            chunk_id = hit.get("id", "")
            
            if "pinecone" in source.lower():
                pinecone_count += 1
            elif "neo4j" in source.lower() or "graph" in source.lower():
                neo4j_count += 1
                
            if "ms_" in chunk_id.lower() or company == "MS":
                ms_count += 1
            
            print(f"  - {chunk_id} | {company} | {source}")
        
        print(f"📊 Q4 Source Analysis: Pinecone={pinecone_count}, Neo4j={neo4j_count}, MS={ms_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Hybrid test failed: {e}")
        return False

def main():
    """Run all individual tool tests with problematic queries"""
    print("🔍 INDIVIDUAL TOOL TESTING - Q1 & Q4 PROBLEMATIC QUERIES")
    print("=" * 80)
    
    # Test each tool
    results = {}
    
    results["rag"] = test_rag_with_problematic_queries()
    results["cypher"] = test_cypher_with_problematic_queries()
    results["hybrid"] = test_hybrid_with_problematic_queries()
    
    # Summary
    print(f"\n🎯 INDIVIDUAL TOOL TEST SUMMARY")
    print("=" * 50)
    
    for tool, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {tool.upper()}: {status}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    if passed == total:
        print(f"\n✅ All tools working with problematic queries ({passed}/{total})")
        print("📋 Next: Test Planner and Synthesizer nodes")
    else:
        print(f"\n⚠️  Issues found in {total-passed} tools")

if __name__ == "__main__":
    main()