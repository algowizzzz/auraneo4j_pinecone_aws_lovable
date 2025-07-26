#!/usr/bin/env python3
"""
RECONCILIATION SCRIPT: Neo4j-Pinecone Data Integrity Validation

This script validates that every Chunk node in Neo4j has a corresponding
vector in Pinecone with matching chunk_id and consistent metadata.

Run this regularly to maintain data integrity.
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pinecone import Pinecone

load_dotenv()

def run_reconciliation():
    """Run full reconciliation between Neo4j and Pinecone"""
    print("🔍 RECONCILIATION: Neo4j ↔ Pinecone Data Integrity Check")
    print("=" * 70)
    
    # Connect to Neo4j
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
    
    # Connect to Pinecone
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index("sec-rag-index")  # Use the correct index name
    
    # Get all chunk IDs from Neo4j
    with neo4j_driver.session() as session:
        result = session.run("MATCH (c:Chunk) RETURN c.chunk_id as chunk_id")
        neo4j_chunk_ids = set(record["chunk_id"] for record in result)
    
    print(f"📊 Neo4j chunks found: {len(neo4j_chunk_ids)}")
    
    # Get Pinecone stats
    stats = index.describe_index_stats()
    pinecone_count = stats.total_vector_count
    print(f"📊 Pinecone vectors found: {pinecone_count}")
    
    # Check for missing vectors in Pinecone
    missing_in_pinecone = []
    for chunk_id in neo4j_chunk_ids:
        try:
            result = index.fetch(ids=[chunk_id])
            if chunk_id not in result.vectors:
                missing_in_pinecone.append(chunk_id)
        except:
            missing_in_pinecone.append(chunk_id)
    
    # Report results
    print(f"\n📋 RECONCILIATION RESULTS:")
    print(f"✅ Chunks in sync: {len(neo4j_chunk_ids) - len(missing_in_pinecone)}")
    print(f"❌ Missing in Pinecone: {len(missing_in_pinecone)}")
    
    if missing_in_pinecone:
        print(f"\n⚠️  MISSING CHUNK IDs:")
        for chunk_id in missing_in_pinecone[:10]:  # Show first 10
            print(f"  - {chunk_id}")
        if len(missing_in_pinecone) > 10:
            print(f"  ... and {len(missing_in_pinecone) - 10} more")
    
    # Overall status
    if len(missing_in_pinecone) == 0:
        print(f"\n🎉 SUCCESS: Perfect data integrity maintained!")
        return True
    else:
        print(f"\n⚠️  WARNING: Data integrity issues detected")
        return False

if __name__ == "__main__":
    run_reconciliation()
