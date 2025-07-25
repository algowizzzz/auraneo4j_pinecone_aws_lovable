#!/usr/bin/env python3
"""
Debug Hybrid Node - Zion Query Issue
Investigate why BQ004 (Zion temporal analysis) returns 0 results
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_zion_hybrid_issue():
    """Debug why Zion hybrid query fails"""
    print("🔍 Debugging Hybrid Node - Zion Query Issue")
    print("=" * 60)
    
    # Test data availability first
    print("\n1. 🗄️ Testing Data Availability")
    try:
        # Check Neo4j for ZION data
        from neo4j import GraphDatabase
        
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            # Check ZION company data
            result = session.run("""
                MATCH (c:Company {name: "ZION"})-[:HAS_YEAR]->(y:Year)
                RETURN c.name as company, collect(y.value) as years
            """)
            
            zion_data = list(result)
            if zion_data:
                company = zion_data[0]["company"]
                years = sorted(zion_data[0]["years"])
                print(f"    ✅ Found {company} data for years: {years}")
            else:
                print("    ❌ No ZION data found in Neo4j")
                
                # Check what companies do exist
                result = session.run("MATCH (c:Company) RETURN c.name ORDER BY c.name")
                companies = [record["c.name"] for record in result]
                print(f"    Available companies: {companies[:10]}...")
        
        driver.close()
        
    except Exception as e:
        print(f"    ❌ Neo4j check failed: {e}")
    
    # Test Pinecone availability
    print("\n2. 🔗 Testing Pinecone Availability")
    try:
        from data_pipeline.pinecone_integration import PineconeVectorStore
        
        vector_store = PineconeVectorStore()
        print("    ✅ Pinecone initialized successfully")
        
        # Test search with ZION filter
        filter_dict = {"company": "ZION"}
        results = vector_store.similarity_search(
            query="business strategy evolution",
            top_k=5,
            filter_dict=filter_dict
        )
        
        print(f"    📊 ZION Pinecone search: {len(results)} results")
        
        if results:
            for i, result in enumerate(results[:2], 1):
                metadata = result.get('metadata', {})
                company = metadata.get('company', 'Unknown')
                year = metadata.get('year', 'Unknown')
                score = result.get('score', 0)
                print(f"        {i}. {company} {year}: score {score:.3f}")
        
    except Exception as e:
        print(f"    ❌ Pinecone test failed: {e}")
    
    # Test planner metadata extraction
    print("\n3. 🧠 Testing Planner Metadata Extraction")
    try:
        from agent.nodes.planner import planner
        
        test_query = "How has Zions Bancorporation business strategy evolved from 2021 to 2025?"
        
        state = {
            "query_raw": test_query,
            "metadata": {},
            "route": "",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        result = planner(state)
        route = result.get("route", "unknown")
        metadata = result.get("metadata", {})
        
        print(f"    📊 Planner result:")
        print(f"        Route: {route}")
        print(f"        Metadata: {metadata}")
        
        # Check if metadata company matches Neo4j company name
        planned_company = metadata.get("company", "")
        print(f"    🔍 Company mapping: '{planned_company}' -> Need to check if this exists in data")
        
    except Exception as e:
        print(f"    ❌ Planner test failed: {e}")
    
    # Test hybrid node directly
    print("\n4. 🔗 Testing Hybrid Node Directly")
    try:
        from agent.nodes.hybrid import hybrid
        
        # Use exact state from failed test
        test_state = {
            "query_raw": "How has Zions Bancorporation business strategy evolved from 2021 to 2025?",
            "metadata": {'company': 'ZION', 'year': '2021', 'quarter': None, 'doc_type': None},
            "route": "hybrid",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        print(f"    🧪 Testing with state: {test_state['metadata']}")
        
        result = hybrid(test_state)
        retrievals = result.get("retrievals", [])
        errors = result.get("error_messages", [])
        
        print(f"    📊 Hybrid result: {len(retrievals)} retrievals")
        
        if errors:
            print(f"    ❌ Errors: {errors}")
        
        if retrievals:
            for i, hit in enumerate(retrievals[:2], 1):
                score = hit.get("score", 0)
                source = hit.get("source", "unknown")
                metadata = hit.get("metadata", {})
                print(f"        {i}. Score: {score:.3f}, Source: {source}")
                print(f"           Metadata: {metadata}")
        else:
            print("    ⚠️ No results - investigating why...")
            
            # Check if enhanced retrieval import is failing
            try:
                from agent.integration.enhanced_retrieval import get_enhanced_retriever
                print("    ✅ Enhanced retrieval available")
            except ImportError:
                print("    ⚠️ Enhanced retrieval not available - using fallback")
        
    except Exception as e:
        print(f"    ❌ Hybrid node test failed: {e}")
    
    print("\n🎯 Diagnosis Summary:")
    print("=" * 60)
    print("Key areas to investigate:")
    print("1. Company name mapping (ZION vs. Zions Bancorporation)")
    print("2. Pinecone filter format compatibility")
    print("3. Enhanced retrieval import issues")
    print("4. Neo4j company name standardization")

if __name__ == "__main__":
    debug_zion_hybrid_issue()