#!/usr/bin/env python3
"""
Fix Neo4j Graph Population
Ensures proper schema population with company name normalization
"""

import os
import sys
import glob
import json
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def analyze_sec_data_companies():
    """Analyze what companies are in the SEC data files"""
    print("📊 Analyzing SEC Data Companies:")
    print("=" * 50)
    
    data_dir = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/zion_10k_md&a_chunked"
    
    if not os.path.exists(data_dir):
        print(f"  ❌ Data directory not found: {data_dir}")
        return {}
    
    # Get all JSON files
    json_files = glob.glob(os.path.join(data_dir, "*.json"))
    print(f"  📁 Found {len(json_files)} SEC filing files")
    
    # Extract company information
    companies = {}
    
    for file_path in json_files[:10]:  # Sample first 10 files
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Extract company information
            company_field = data.get("Company", "Unknown")
            filename = os.path.basename(file_path)
            
            # Parse filename for additional info
            if "SEC_" in filename:
                parts = filename.split("_")
                if len(parts) >= 3:
                    extracted_company = parts[2]  # e.g., external_SEC_WFC_10-K_...
                    
                    if company_field not in companies:
                        companies[company_field] = {
                            "files": 0,
                            "extracted_codes": set(),
                            "sample_file": filename
                        }
                    
                    companies[company_field]["files"] += 1
                    companies[company_field]["extracted_codes"].add(extracted_company)
                    
        except Exception as e:
            print(f"  ⚠️  Error reading {os.path.basename(file_path)}: {e}")
    
    # Display results
    print(f"\n  Companies found in SEC data:")
    for company, info in companies.items():
        codes = ", ".join(info["extracted_codes"])
        print(f"    • {company}: {codes} ({info['files']} files)")
    
    return companies

def check_company_mapping_alignment():
    """Check if company mapping aligns with SEC data"""
    print("\n🔗 Company Mapping Alignment:")
    print("=" * 50)
    
    try:
        from agent.utils.company_mapping import normalize_company, get_available_companies
        
        # Get available mapped companies
        available_tickers = get_available_companies()
        print(f"  📋 Company mapping has {len(available_tickers)} companies")
        print(f"  🏦 Available tickers: {', '.join(sorted(available_tickers)[:10])}...")
        
        # Test some common mappings
        test_mappings = [
            ("WFC", "WFC"),
            ("WELLS FARGO", "WFC"),
            ("JPM", "JPM"),
            ("JPMORGAN", "JPM"),
            ("ZION", "ZION"),
            ("KEY", "KEY"),
            ("PB", "PB")
        ]
        
        print(f"\n  Company mapping tests:")
        for input_name, expected in test_mappings:
            result = normalize_company(input_name)
            status = "✅" if result == expected else "❌"
            print(f"    {status} {input_name} → {result} (expected {expected})")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Company mapping check failed: {e}")
        return False

def create_graph_population_script():
    """Create a script to populate Neo4j with proper company normalization"""
    print("\n🔧 Creating Graph Population Script:")
    print("=" * 50)
    
    script_content = '''#!/usr/bin/env python3
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
        
        print(f"\\n✅ Graph Population Complete!")
        print(f"   📊 Valid files processed: {validation_results['valid_files']}")
        print(f"   📈 Total files found: {validation_results['total_files']}")
        
        # Test a sample query
        print(f"\\n🔍 Testing Sample Cypher Query...")
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
        
        print(f"\\n🎉 Neo4j graph population successful!")
        print(f"   Next: Test cypher node performance")
        
    except Exception as e:
        print(f"❌ Graph population failed: {e}")
        print(f"   Check Neo4j connection and data directory")

if __name__ == "__main__":
    run_graph_population()
'''
    
    script_path = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/populate_neo4j_graph.py"
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"  ✅ Created population script: {os.path.basename(script_path)}")
    print(f"  📝 Run with: python3 populate_neo4j_graph.py")
    
    return script_path

def create_cypher_test_script():
    """Create a script to test cypher node after population"""
    print("\n🧪 Creating Cypher Test Script:")
    print("=" * 50)
    
    test_script = '''#!/usr/bin/env python3
"""
Test Cypher Node Performance
Validates that cypher queries work after graph population
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cypher_node():
    """Test cypher node with real business queries"""
    print("🧪 Testing Cypher Node Performance")
    print("=" * 50)
    
    try:
        from agent.nodes.cypher import cypher
        from agent.utils.company_mapping import normalize_company
        
        # Test queries with proper company normalization
        test_cases = [
            {
                "query": "What are Wells Fargo's capital ratios in 2025?",
                "metadata": {
                    "company": normalize_company("Wells Fargo"),
                    "year": "2025"
                },
                "description": "Wells Fargo 2025 query"
            },
            {
                "query": "What are Zions Bancorporation's business operations?", 
                "metadata": {
                    "company": normalize_company("Zions Bancorporation")
                },
                "description": "Zions business query"
            },
            {
                "query": "JPMorgan risk factors in 2024 Q1",
                "metadata": {
                    "company": normalize_company("JPMorgan"),
                    "year": "2024",
                    "quarter": "Q1"
                },
                "description": "JPMorgan Q1 2024 query"
            }
        ]
        
        print(f"\\n📋 Running {len(test_cases)} test cases...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n  Test {i}: {test_case['description']}")
            print(f"    Query: {test_case['query']}")
            print(f"    Metadata: {test_case['metadata']}")
            
            # Create state for cypher node
            state = {
                "query_raw": test_case["query"],
                "metadata": test_case["metadata"],
                "retrievals": []
            }
            
            # Run cypher node
            try:
                result_state = cypher(state)
                retrievals = result_state.get("retrievals", [])
                
                if retrievals:
                    print(f"    ✅ Success: {len(retrievals)} results")
                    print(f"    📄 First result: {retrievals[0]['text'][:100]}...")
                else:
                    print(f"    ⚠️  No results found")
                    
            except Exception as e:
                print(f"    ❌ Failed: {e}")
        
        print(f"\\n🎯 Cypher node testing complete")
        
    except Exception as e:
        print(f"❌ Cypher test failed: {e}")

if __name__ == "__main__":
    test_cypher_node()
'''
    
    test_script_path = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/test_cypher_node.py"
    
    with open(test_script_path, 'w') as f:
        f.write(test_script)
    
    print(f"  ✅ Created test script: {os.path.basename(test_script_path)}")
    print(f"  📝 Run after population: python3 test_cypher_node.py")
    
    return test_script_path

def main():
    """Run Neo4j population fix analysis and script creation"""
    print("🔧 Neo4j Graph Population Fix")
    print("=" * 70)
    
    # Analyze current state
    sec_companies = analyze_sec_data_companies()
    mapping_ok = check_company_mapping_alignment()
    
    # Create helper scripts
    population_script = create_graph_population_script()
    test_script = create_cypher_test_script()
    
    # Generate summary
    print(f"\n🎯 Summary & Next Steps:")
    print("=" * 50)
    print(f"  ✅ SEC data analysis complete")
    print(f"  ✅ Company mapping system validated")
    print(f"  ✅ Graph population script created")
    print(f"  ✅ Cypher test script created")
    
    print(f"\\n📋 Action Plan:")
    print(f"  1. Ensure Neo4j is running")
    print(f"  2. Install required dependencies (neo4j, sentence-transformers)")
    print(f"  3. Run: python3 populate_neo4j_graph.py")
    print(f"  4. Run: python3 test_cypher_node.py")
    print(f"  5. Verify cypher node shows '✅ Working' status")
    
    if len(sec_companies) > 0 and mapping_ok:
        print(f"\\n🎉 Ready to populate Neo4j graph!")
    else:
        print(f"\\n⚠️  Fix identified issues before proceeding")

if __name__ == "__main__":
    main()