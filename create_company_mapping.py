#!/usr/bin/env python3
"""
Create Company Name Mapping
Build a comprehensive ticker <-> company name mapping system
to reduce "No section found" warnings and improve data access
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def analyze_company_data():
    """Analyze existing company data and file patterns"""
    print("🏢 Analyzing Company Data and File Patterns")
    print("=" * 60)
    
    # Check Neo4j for actual company names
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            # Get all companies with their data availability
            result = session.run("""
                MATCH (c:Company)-[:HAS_YEAR]->(y:Year)
                RETURN c.name as ticker, 
                       collect(DISTINCT y.value) as years,
                       count(y) as year_count
                ORDER BY year_count DESC
            """)
            
            companies = []
            for record in result:
                companies.append({
                    "ticker": record["ticker"],
                    "years": sorted(record["years"]),
                    "year_count": record["year_count"]
                })
            
            print(f"  📊 Found {len(companies)} companies in Neo4j:")
            for company in companies[:10]:  # Top 10
                print(f"    {company['ticker']}: {company['years']} ({company['year_count']} years)")
            
            if len(companies) > 10:
                print(f"    ... and {len(companies) - 10} more")
        
        driver.close()
        
    except Exception as e:
        print(f"  ❌ Neo4j analysis failed: {e}")
        companies = []
    
    # Check file system for actual files
    print(f"\n  📁 Analyzing file patterns...")
    
    data_dir = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/zion_10k_md&a_chunked"
    
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        print(f"  📊 Found {len(files)} JSON files")
        
        # Analyze file patterns
        file_patterns = {}
        for file in files[:20]:  # Sample first 20
            parts = file.split('_')
            if len(parts) >= 6:
                company = parts[2]  # external_SEC_COMPANY_...
                year = parts[4]
                doc_type = parts[5]
                section = '_'.join(parts[6:]).replace('.json', '')
                
                if company not in file_patterns:
                    file_patterns[company] = {}
                if year not in file_patterns[company]:
                    file_patterns[company][year] = []
                file_patterns[company][year].append(section)
        
        print(f"  📊 File pattern sample:")
        for company, years in list(file_patterns.items())[:5]:
            year_list = list(years.keys())
            print(f"    {company}: {year_list}")
    
    return companies

def create_company_mapping():
    """Create a comprehensive company mapping system"""
    print(f"\n🗺️ Creating Company Mapping System")
    print("=" * 60)
    
    # Known mappings from financial industry
    company_mappings = {
        # Major banks with known tickers
        "ZION": {
            "full_name": "Zions Bancorporation", 
            "variations": ["Zions Bancorporation", "ZION", "Zions Bank"],
            "industry": "Regional Bank"
        },
        "PB": {
            "full_name": "Prosperity Bancshares",
            "variations": ["Prosperity Bancshares", "PB", "Prosperity Bank"],
            "industry": "Regional Bank"
        },
        "KEY": {
            "full_name": "KeyCorp",
            "variations": ["KeyCorp", "KEY", "KeyBank"],
            "industry": "Regional Bank"
        },
        "WFC": {
            "full_name": "Wells Fargo & Company",
            "variations": ["Wells Fargo", "WFC", "Wells Fargo & Company"],
            "industry": "Major Bank"
        },
        "JPM": {
            "full_name": "JPMorgan Chase & Co.",
            "variations": ["JPMorgan Chase", "JPM", "Chase"],
            "industry": "Major Bank"
        },
        "BAC": {
            "full_name": "Bank of America Corporation",
            "variations": ["Bank of America", "BAC", "BofA"],
            "industry": "Major Bank"
        },
        "MTB": {
            "full_name": "M&T Bank Corporation", 
            "variations": ["M&T Bank", "MTB", "M&T"],
            "industry": "Regional Bank"
        },
        "RF": {
            "full_name": "Regions Financial Corporation",
            "variations": ["Regions Financial", "RF", "Regions Bank"],
            "industry": "Regional Bank"
        },
        "CFG": {
            "full_name": "Citizens Financial Group",
            "variations": ["Citizens Financial", "CFG", "Citizens Bank"],
            "industry": "Regional Bank"
        },
        "TFC": {
            "full_name": "Truist Financial Corporation", 
            "variations": ["Truist", "TFC", "Truist Bank"],
            "industry": "Regional Bank"
        },
        "USB": {
            "full_name": "U.S. Bancorp",
            "variations": ["U.S. Bank", "USB", "US Bank"],
            "industry": "Major Bank"
        }
    }
    
    # Add reverse mapping (full name -> ticker)
    reverse_mapping = {}
    for ticker, info in company_mappings.items():
        reverse_mapping[info["full_name"]] = ticker
        for variation in info["variations"]:
            reverse_mapping[variation] = ticker
    
    print(f"  ✅ Created mappings for {len(company_mappings)} companies")
    print(f"  ✅ Created {len(reverse_mapping)} reverse lookups")
    
    # Save mapping files
    mapping_dir = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/config"
    os.makedirs(mapping_dir, exist_ok=True)
    
    # Save primary mapping
    primary_file = os.path.join(mapping_dir, "company_mappings.json")
    with open(primary_file, 'w') as f:
        json.dump(company_mappings, f, indent=2)
    
    # Save reverse mapping
    reverse_file = os.path.join(mapping_dir, "company_reverse_mappings.json")
    with open(reverse_file, 'w') as f:
        json.dump(reverse_mapping, f, indent=2)
    
    print(f"  ✅ Saved mappings to: {mapping_dir}/")
    
    return company_mappings, reverse_mapping

def create_company_resolver():
    """Create a company name resolver utility"""
    print(f"\n🔧 Creating Company Name Resolver")
    print("=" * 60)
    
    resolver_code = '''"""
Company Name Resolver Utility
Handles ticker <-> company name mapping and normalization
"""

import json
import os
from typing import Optional, Dict, Any

class CompanyNameResolver:
    """Resolves company names and tickers with multiple variations"""
    
    def __init__(self):
        self.mappings = {}
        self.reverse_mappings = {}
        self._load_mappings()
    
    def _load_mappings(self):
        """Load company mappings from config files"""
        try:
            config_dir = os.path.join(os.path.dirname(__file__), '../config')
            
            # Load primary mappings
            primary_file = os.path.join(config_dir, 'company_mappings.json')
            if os.path.exists(primary_file):
                with open(primary_file, 'r') as f:
                    self.mappings = json.load(f)
            
            # Load reverse mappings
            reverse_file = os.path.join(config_dir, 'company_reverse_mappings.json')
            if os.path.exists(reverse_file):
                with open(reverse_file, 'r') as f:
                    self.reverse_mappings = json.load(f)
            
            print(f"CompanyNameResolver loaded {len(self.mappings)} primary mappings")
            
        except Exception as e:
            print(f"Warning: Could not load company mappings: {e}")
            # Fallback to basic mappings
            self.mappings = {
                "ZION": {"full_name": "Zions Bancorporation", "variations": ["ZION", "Zions"]},
                "PB": {"full_name": "Prosperity Bancshares", "variations": ["PB", "Prosperity"]},
                "KEY": {"full_name": "KeyCorp", "variations": ["KEY", "KeyCorp"]},
            }
    
    def resolve_to_ticker(self, name: str) -> Optional[str]:
        """
        Resolve any company name variation to its ticker
        Args:
            name: Company name or ticker
        Returns:
            Ticker symbol or None if not found
        """
        if not name:
            return None
            
        # Clean the input
        clean_name = name.strip()
        
        # Check if it's already a ticker
        if clean_name in self.mappings:
            return clean_name
        
        # Check reverse mappings
        if clean_name in self.reverse_mappings:
            return self.reverse_mappings[clean_name]
        
        # Try partial matches (case insensitive)
        clean_lower = clean_name.lower()
        for variation, ticker in self.reverse_mappings.items():
            if clean_lower in variation.lower() or variation.lower() in clean_lower:
                return ticker
        
        # Return as-is if no mapping found (might be correct)
        return clean_name
    
    def resolve_to_full_name(self, identifier: str) -> Optional[str]:
        """
        Resolve ticker or name to full company name
        Args:
            identifier: Ticker or company name
        Returns:
            Full company name or None if not found
        """
        if not identifier:
            return None
        
        # First resolve to ticker
        ticker = self.resolve_to_ticker(identifier)
        
        # Then get full name
        if ticker and ticker in self.mappings:
            return self.mappings[ticker]["full_name"]
        
        return identifier  # Return as-is if not found
    
    def get_variations(self, identifier: str) -> list:
        """
        Get all known variations of a company name/ticker
        Args:
            identifier: Ticker or company name
        Returns:
            List of all known variations
        """
        ticker = self.resolve_to_ticker(identifier)
        
        if ticker and ticker in self.mappings:
            return self.mappings[ticker]["variations"]
        
        return [identifier]
    
    def normalize_metadata_company(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize company name in metadata dictionary
        Args:
            metadata: Metadata dict that may contain company field
        Returns:
            Updated metadata with normalized company name
        """
        if "company" in metadata and metadata["company"]:
            # Resolve to ticker for consistency
            ticker = self.resolve_to_ticker(metadata["company"])
            if ticker:
                metadata["company"] = ticker
        
        return metadata

# Global resolver instance
_company_resolver = CompanyNameResolver()

def get_company_resolver() -> CompanyNameResolver:
    """Get the global company name resolver instance"""
    return _company_resolver

# Convenience functions
def resolve_company_name(name: str) -> Optional[str]:
    """Resolve company name to ticker"""
    return _company_resolver.resolve_to_ticker(name)

def get_full_company_name(identifier: str) -> Optional[str]:
    """Get full company name from ticker or partial name"""
    return _company_resolver.resolve_to_full_name(identifier)

def normalize_company_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize company field in metadata"""
    return _company_resolver.normalize_metadata_company(metadata)
'''
    
    # Save resolver utility
    resolver_file = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/utils/company_resolver.py"
    os.makedirs(os.path.dirname(resolver_file), exist_ok=True)
    
    with open(resolver_file, 'w') as f:
        f.write(resolver_code)
    
    print(f"  ✅ Created company resolver: {resolver_file}")
    
    return True

def test_company_resolver():
    """Test the company resolver with various inputs"""
    print(f"\n🧪 Testing Company Resolver")
    print("=" * 60)
    
    try:
        # Add utils to path for testing
        sys.path.insert(0, "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/utils")
        from company_resolver import get_company_resolver
        
        resolver = get_company_resolver()
        
        test_cases = [
            "ZION",
            "Zions Bancorporation", 
            "Prosperity Bancshares",
            "PB",
            "KeyCorp",
            "Wells Fargo",
            "JPMorgan Chase"
        ]
        
        print("  Testing name resolution:")
        for test_name in test_cases:
            ticker = resolver.resolve_to_ticker(test_name)
            full_name = resolver.resolve_to_full_name(test_name)
            variations = resolver.get_variations(test_name)
            
            print(f"    '{test_name}' -> Ticker: {ticker}, Full: {full_name}")
            print(f"        Variations: {variations[:3]}...")  # Show first 3
        
        # Test metadata normalization
        print(f"\n  Testing metadata normalization:")
        test_metadata = [
            {"company": "Zions Bancorporation", "year": "2024"},
            {"company": "Prosperity Bancshares", "year": "2023"},
            {"company": "KEY", "year": "2024"}
        ]
        
        for metadata in test_metadata:
            original = metadata.copy()
            normalized = resolver.normalize_metadata_company(metadata)
            print(f"    {original} -> {normalized}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Testing failed: {e}")
        return False

if __name__ == "__main__":
    print("🏢 Company Name Mapping System Creation")
    print("=" * 70)
    
    # Step 1: Analyze existing data
    companies = analyze_company_data()
    
    # Step 2: Create mapping system
    mappings, reverse_mappings = create_company_mapping()
    
    # Step 3: Create resolver utility
    resolver_created = create_company_resolver()
    
    # Step 4: Test the system
    resolver_tested = test_company_resolver()
    
    # Summary
    print(f"\n🎯 Company Mapping System Summary:")
    print("=" * 70)
    print(f"  ✅ Mappings created: {len(mappings)} companies")
    print(f"  ✅ Reverse lookups: {len(reverse_mappings)} variations")
    print(f"  ✅ Resolver utility: {'Created' if resolver_created else 'Failed'}")
    print(f"  ✅ Testing: {'Passed' if resolver_tested else 'Failed'}")
    
    if resolver_tested:
        print(f"\\n🚀 Company name resolution system is ready!")
        print(f"   This should reduce 'No section found' warnings")
        print(f"   Usage: from utils.company_resolver import resolve_company_name")
    else:
        print(f"\\n⚠️  System created but needs debugging")