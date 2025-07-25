#!/usr/bin/env python3
"""
Simple Cypher Node Test
Direct test of cypher node functionality with current database
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cypher_simple():
    """Simple test of cypher node"""
    print("🧪 Simple Cypher Node Test")
    print("=" * 50)
    
    try:
        # Import cypher node
        from agent.nodes.cypher import Neo4jCypherRetriever
        
        print("✅ Cypher node imported successfully")
        
        # Create retriever
        retriever = Neo4jCypherRetriever()
        print("✅ Cypher retriever created")
        
        # Test with simple metadata
        test_metadata = {
            "company": "ZION",  # We know this exists from diagnostic
        }
        
        print(f"\n🔍 Testing with metadata: {test_metadata}")
        
        # Execute retrieval
        results = retriever.execute_cypher_retrieval(test_metadata)
        
        print(f"📊 Results: {len(results)} hits")
        
        if results:
            print(f"✅ SUCCESS: Cypher node returned {len(results)} results")
            print(f"📄 First result preview:")
            print(f"   Section: {results[0].metadata.get('section_name', 'Unknown')}")
            print(f"   Company: {results[0].metadata.get('company', 'Unknown')}")
            print(f"   Text: {results[0].text[:100]}...")
        else:
            print("⚠️  No results returned")
            
        # Close connection
        retriever.close()
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cypher_queries():
    """Test different query patterns"""
    print("\n🔍 Testing Different Query Patterns")
    print("=" * 50)
    
    test_cases = [
        {"company": "ZION"},
        {"year": "2025"},
        {"company": "ZION", "year": "2025"},
        {}  # Empty metadata
    ]
    
    try:
        from agent.nodes.cypher import Neo4jCypherRetriever
        retriever = Neo4jCypherRetriever()
        
        for i, metadata in enumerate(test_cases, 1):
            print(f"\n  Test {i}: {metadata}")
            try:
                results = retriever.execute_cypher_retrieval(metadata)
                print(f"    Results: {len(results)} hits")
                if results:
                    print(f"    ✅ Success")
                else:
                    print(f"    ⚠️  No results")
            except Exception as e:
                print(f"    ❌ Failed: {e}")
        
        retriever.close()
        
    except Exception as e:
        print(f"❌ Query testing failed: {e}")

if __name__ == "__main__":
    success = test_cypher_simple()
    test_cypher_queries()
    
    if success:
        print(f"\n🎉 Cypher node is working!")
    else:
        print(f"\n⚠️  Cypher node needs fixes")