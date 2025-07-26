#!/usr/bin/env python3
"""
Check Neo4j Data Availability
Examines what companies, years, and documents are currently in the Neo4j database.
"""

import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_neo4j_driver():
    """Establishes connection to Neo4j and returns the driver."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        logger.error("NEO4J_URI and NEO4J_PASSWORD must be set in .env file.")
        sys.exit(1)
    return GraphDatabase.driver(uri, auth=(user, password))

def check_database_content():
    """Check what data is currently in the Neo4j database."""
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        print("🔍 Checking Neo4j Database Content")
        print("=" * 50)
        
        # Check total node counts
        print("\n📊 Node Statistics:")
        result = session.run("MATCH (n) RETURN labels(n) as label, count(n) as count ORDER BY count DESC")
        for record in result:
            print(f"  {record['label']}: {record['count']}")
        
        # Check companies
        print("\n🏢 Available Companies:")
        result = session.run("MATCH (c:Company) RETURN c.name as company ORDER BY c.name")
        companies = [record['company'] for record in result]
        for company in companies:
            print(f"  - {company}")
        
        # Check years
        print("\n📅 Available Years:")
        result = session.run("MATCH (y:Year) RETURN y.value as year ORDER BY y.value")
        years = [record['year'] for record in result]
        for year in years:
            print(f"  - {year}")
        
        # Check company-year combinations
        print("\n🔗 Company-Year Combinations:")
        result = session.run("""
            MATCH (c:Company)-[:HAS_YEAR]->(y:Year)
            RETURN c.name as company, y.value as year
            ORDER BY c.name, y.value
        """)
        
        company_years = {}
        for record in result:
            company = record['company']
            year = record['year']
            if company not in company_years:
                company_years[company] = []
            company_years[company].append(year)
        
        for company, years in company_years.items():
            print(f"  {company}: {', '.join(map(str, sorted(years)))}")
        
        # Check document types
        print("\n📄 Document Types:")
        result = session.run("MATCH (d:Document) RETURN d.form_type as form_type, count(*) as count ORDER BY count DESC")
        for record in result:
            print(f"  {record['form_type']}: {record['count']} documents")
        
        # Check sections
        print("\n📋 Section Types:")
        result = session.run("MATCH (s:Section) RETURN s.section as section_type, count(*) as count ORDER BY count DESC LIMIT 10")
        for record in result:
            print(f"  {record['section_type']}: {record['count']} sections")
        
        # Check chunks
        print("\n🧩 Chunk Statistics:")
        result = session.run("MATCH (ch:Chunk) RETURN count(ch) as total_chunks")
        for record in result:
            print(f"  Total chunks: {record['total_chunks']}")
        
        # Sample some specific data for JPM 2025
        print("\n🔍 Sample Query - JPM 2025:")
        result = session.run("""
            MATCH (c:Company {name: 'JPM'})-[:HAS_YEAR]->(y:Year {value: 2025})
                  -[:HAS_QUARTER]->(q:Quarter)-[:HAS_DOC]->(d:Document)
                  -[:HAS_SECTION]->(s:Section)
            RETURN d.form_type as form_type, s.section as section, count(*) as count
            ORDER BY count DESC
            LIMIT 5
        """)
        sections_found = list(result)
        if sections_found:
            for record in sections_found:
                print(f"  {record['form_type']} - {record['section']}: {record['count']} sections")
        else:
            print("  ❌ No JPM 2025 data found")
    
    driver.close()

if __name__ == "__main__":
    check_database_content() 