#!/usr/bin/env python3
"""
Neo4j Schema Diagnostic Tool
Analyzes current Neo4j database structure and identifies schema mismatches
"""

import os
import sys
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_neo4j_connection():
    """Test Neo4j database connection"""
    print("🔗 Testing Neo4j Connection:")
    print("=" * 50)
    
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "newpassword")
        
        print(f"  URI: {uri}")
        print(f"  Username: {username}")
        print(f"  Password: {'*' * len(password) if password else 'Not set'}")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful' as message")
            message = result.single()["message"]
            print(f"  ✅ {message}")
            
        driver.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False

def analyze_database_content(driver):
    """Analyze current database content and structure"""
    print("\n📊 Database Content Analysis:")
    print("=" * 50)
    
    try:
        with driver.session() as session:
            # Get node counts by label
            print("  Node Counts:")
            node_query = """
            CALL db.labels() YIELD label
            CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) YIELD value
            RETURN label, value.count as count
            ORDER BY value.count DESC
            """
            
            try:
                result = session.run(node_query)
                for record in result:
                    label = record["label"]
                    count = record["count"]
                    print(f"    • {label}: {count:,} nodes")
            except Exception as e:
                # Fallback without APOC
                print("    Using basic counting (APOC not available):")
                basic_labels = session.run("CALL db.labels() YIELD label RETURN label")
                for record in basic_labels:
                    label = record["label"]
                    count_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    count = count_result.single()["count"]
                    print(f"    • {label}: {count:,} nodes")
            
            # Get relationship counts
            print("\n  Relationship Counts:")
            rel_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
            relationships = session.run(rel_query)
            
            for record in relationships:
                rel_type = record["relationshipType"]
                count_result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                count = count_result.single()["count"]
                print(f"    • {rel_type}: {count:,} relationships")
                
    except Exception as e:
        print(f"  ❌ Content analysis failed: {e}")

def check_expected_schema(driver):
    """Check if expected schema from cypher.py exists"""
    print("\n🔍 Expected Schema Validation:")
    print("=" * 50)
    
    expected_patterns = [
        ("Company nodes", "MATCH (c:Company) RETURN count(c) as count"),
        ("Year nodes", "MATCH (y:Year) RETURN count(y) as count"), 
        ("Quarter nodes", "MATCH (q:Quarter) RETURN count(q) as count"),
        ("Company→Year relationships", "MATCH (c:Company)-[:HAS_YEAR]->(y:Year) RETURN count(*) as count"),
        ("Year→Quarter relationships", "MATCH (y:Year)-[:HAS_QUARTER]->(q:Quarter) RETURN count(*) as count"),
        ("Filing content", "MATCH (n) WHERE n.text IS NOT NULL RETURN count(n) as count"),
        ("Company metadata", "MATCH (c:Company) WHERE c.ticker IS NOT NULL RETURN count(c) as count")
    ]
    
    try:
        with driver.session() as session:
            for description, query in expected_patterns:
                try:
                    result = session.run(query)
                    count = result.single()["count"]
                    status = "✅" if count > 0 else "❌"
                    print(f"  {status} {description}: {count:,}")
                except Exception as e:
                    print(f"  ❌ {description}: Query failed - {e}")
                    
    except Exception as e:
        print(f"  ❌ Schema validation failed: {e}")

def analyze_sec_data_integration(driver):
    """Check how SEC filing data is integrated"""
    print("\n📄 SEC Filing Data Analysis:")
    print("=" * 50)
    
    sec_queries = [
        ("Nodes with SEC content", "MATCH (n) WHERE n.text CONTAINS 'SEC' OR n.text CONTAINS 'Securities' RETURN count(n) as count"),
        ("Company ticker presence", "MATCH (n) WHERE n.company IS NOT NULL OR n.ticker IS NOT NULL RETURN count(n) as count"),
        ("Year/Quarter metadata", "MATCH (n) WHERE n.year IS NOT NULL OR n.quarter IS NOT NULL RETURN count(n) as count"),
        ("Financial content", "MATCH (n) WHERE n.text CONTAINS 'capital' OR n.text CONTAINS 'risk' OR n.text CONTAINS 'business' RETURN count(n) as count"),
        ("Sample company data", "MATCH (n) WHERE n.company IN ['WFC', 'JPM', 'BAC', 'ZION'] RETURN n.company as company, count(n) as count ORDER BY count DESC LIMIT 5")
    ]
    
    try:
        with driver.session() as session:
            for description, query in sec_queries:
                try:
                    result = session.run(query)
                    if "LIMIT" in query:
                        # Handle grouped results
                        print(f"  {description}:")
                        for record in result:
                            company = record.get("company", "Unknown")
                            count = record.get("count", 0)
                            print(f"    • {company}: {count:,} nodes")
                    else:
                        count = result.single()["count"]
                        status = "✅" if count > 0 else "❌"
                        print(f"  {status} {description}: {count:,}")
                except Exception as e:
                    print(f"  ❌ {description}: Query failed - {e}")
                    
    except Exception as e:
        print(f"  ❌ SEC data analysis failed: {e}")

def identify_schema_mismatches():
    """Identify specific schema mismatches based on cypher.py expectations"""
    print("\n⚠️  Schema Mismatch Analysis:")
    print("=" * 50)
    
    # Read the cypher.py file to understand expected schema
    try:
        with open('/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/agent/nodes/cypher.py', 'r') as f:
            cypher_code = f.read()
            
        # Extract expected patterns
        expected_elements = []
        if "Company)-[:HAS_YEAR]->(y:Year)" in cypher_code:
            expected_elements.append("Company→Year→Quarter hierarchy")
        if "MATCH (c:Company)" in cypher_code:
            expected_elements.append("Company nodes")
        if "metadata.get(\"company\")" in cypher_code:
            expected_elements.append("Company metadata filtering")
            
        print("  Expected by cypher.py:")
        for element in expected_elements:
            print(f"    • {element}")
            
        print("\n  Common mismatch patterns:")
        print("    • Data stored as flat nodes instead of hierarchical structure")
        print("    • Company names vs. ticker inconsistencies") 
        print("    • Missing temporal relationships (Year/Quarter)")
        print("    • SEC content not properly structured for graph queries")
        
    except Exception as e:
        print(f"  ❌ Could not analyze cypher.py: {e}")

def generate_recommendations():
    """Generate specific recommendations for fixing schema issues"""
    print("\n🔧 Recommendations:")
    print("=" * 50)
    
    recommendations = [
        "1. Run create_graph_v5_integrated.py to populate Neo4j with proper schema",
        "2. Ensure SEC JSON files are processed into Company→Year→Quarter hierarchy", 
        "3. Integrate company_mapping.py for consistent ticker normalization",
        "4. Add indexes on frequently queried properties (company, year, quarter)",
        "5. Test cypher queries against populated database",
        "6. Validate financial entity extraction and graph relationships"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")

def main():
    """Run complete Neo4j schema diagnostic"""
    print("🔍 Neo4j Schema Diagnostic Report")
    print("=" * 70)
    
    # Test connection first
    if not test_neo4j_connection():
        print("\n❌ Cannot proceed without Neo4j connection")
        print("   Check credentials and ensure Neo4j is running")
        return
    
    # Connect and analyze
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "newpassword")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Run all analyses
        analyze_database_content(driver)
        check_expected_schema(driver)
        analyze_sec_data_integration(driver)
        identify_schema_mismatches()
        generate_recommendations()
        
        driver.close()
        
        print(f"\n🎯 Next Steps:")
        print("  1. Review findings above")
        print("  2. Run graph population pipeline if needed")
        print("  3. Test cypher node performance after fixes")
        
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")

if __name__ == "__main__":
    main()