#!/usr/bin/env python3
"""
Populate Neo4j Graph with Company Name Normalization
Integrates company_mapping.py with graph creation pipeline
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_graph_population():
    """Run graph population with company normalization"""
    print("🚀 Starting Neo4j Graph Population")
    print("=" * 60)
    
    try:
        # Import required modules
        from data_pipeline.create_graph_v5_integrated import IntegratedFinancialGraphBuilder
        from agent.utils.company_mapping import normalize_company
        
        # Neo4j connection parameters
        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "newpassword")
        
        print(f"📡 Connecting to Neo4j: {uri}")
        
        # Initialize graph builder
        builder = IntegratedFinancialGraphBuilder(
            uri=uri,
            user=username, 
            password=password,
            use_pinecone=True
        )
        
        # Data directory
        data_dir = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/zion_10k_md&a_chunked"
        file_pattern = "external_SEC_*.json"
        
        print(f"📁 Processing files from: {data_dir}")
        print(f"🔍 Pattern: {file_pattern}")
        
        # Run validation and graph building
        validation_results = builder.validate_and_build_graph(
            data_dir=data_dir,
            file_pattern=file_pattern,
            validation_report_path="graph_population_validation.json"
        )
        
        print(f"\n✅ Graph Population Complete!")
        print(f"   📊 Valid files processed: {validation_results['valid_files']}")
        print(f"   📈 Total files found: {validation_results['total_files']}")
        
        # Test a sample query
        print(f"\n🔍 Testing Sample Cypher Query...")
        with builder.driver.session() as session:
            result = session.run("""
                MATCH (c:Company)-[:HAS_YEAR]->(y:Year)
                RETURN c.name as company, count(y) as years
                ORDER BY years DESC
                LIMIT 5
            """)
            
            print("   Top companies by year coverage:")
            for record in result:
                company = record["company"]
                years = record["years"]
                print(f"     • {company}: {years} years")
                
        builder.driver.close()
        
        print(f"\n🎉 Neo4j graph population successful!")
        print(f"   Next: Test cypher node performance")
        
    except Exception as e:
        print(f"❌ Graph population failed: {e}")
        print(f"   Check Neo4j connection and data directory")

if __name__ == "__main__":
    run_graph_population()
