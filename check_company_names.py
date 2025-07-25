#!/usr/bin/env python3
"""
Check Company Names in Neo4j
Direct Neo4j query to see actual company names vs. expected tickers
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def check_company_names():
    """Check actual company names in database"""
    print("🏦 Checking Company Names in Neo4j")
    print("=" * 50)
    
    try:
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            # Get all company names
            result = session.run("""
                MATCH (c:Company)
                RETURN c.name as company_name, 
                       count{(c)-[:HAS_YEAR]->()} as years
                ORDER BY years DESC
            """)
            
            print("  Companies in database:")
            for record in result:
                name = record["company_name"]
                years = record["years"]
                print(f"    • {name}: {years} years")
            
            # Check what years exist for ZION specifically
            print(f"\n  ZION year breakdown:")
            result = session.run("""
                MATCH (c:Company {name: "ZION"})-[:HAS_YEAR]->(y:Year)
                RETURN y.value as year, count{(y)-[:HAS_QUARTER]->()} as quarters
                ORDER BY year
            """)
            
            for record in result:
                year = record["year"]
                quarters = record["quarters"]
                print(f"    • {year}: {quarters} quarters")
                
            # Check 2025 data across all companies
            print(f"\n  2025 data across companies:")
            result = session.run("""
                MATCH (c:Company)-[:HAS_YEAR]->(y:Year {value: 2025})
                RETURN c.name as company, count{(y)-[:HAS_QUARTER]->()} as quarters
                ORDER BY quarters DESC
            """)
            
            for record in result:
                company = record["company"]
                quarters = record["quarters"]
                print(f"    • {company}: {quarters} quarters")
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Failed to check company names: {e}")

if __name__ == "__main__":
    check_company_names()