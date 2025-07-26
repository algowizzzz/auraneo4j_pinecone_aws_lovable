"""
Company Name Normalization System
Maps various company name formats to standardized stock tickers for metadata filtering
"""

import re
from typing import Dict, List, Optional

class CompanyMapper:
    """Maps various company name formats to standardized stock tickers"""
    
    def __init__(self):
        # Comprehensive mapping from company names/variations to stock tickers
        self.company_mappings = {
            # Major Banks (Tier 1)
            "WELLS FARGO": "WFC",
            "WELLS FARGO & COMPANY": "WFC", 
            "WELLS FARGO BANK": "WFC",
            "WFC": "WFC",
            
            "JPMORGAN": "JPM",
            "JP MORGAN": "JPM", 
            "JPMORGAN CHASE": "JPM",
            "JP MORGAN CHASE": "JPM",
            "JPMORGAN CHASE & CO": "JPM",
            "CHASE": "JPM",
            "JPM": "JPM",
            
            "BANK OF AMERICA": "BAC",
            "BANK OF AMERICA CORPORATION": "BAC",
            "BOFA": "BAC",
            "BOA": "BAC", 
            "BAC": "BAC",
            
            "GOLDMAN SACHS": "GS",
            "GOLDMAN SACHS GROUP": "GS",
            "GOLDMAN SACHS & CO": "GS",
            "GOLDMAN": "GS",
            "GS": "GS",
            
            "MORGAN STANLEY": "MS",
            "MORGAN STANLEY & CO": "MS",
            "MS": "MS",
            
            # Regional Banks (Tier 2)
            "ZIONS BANCORPORATION": "ZION",
            "ZIONS BANK": "ZION",
            "ZION": "ZION",
            
            "KEYCORP": "KEY",
            "KEY BANK": "KEY", 
            "KEYBANK": "KEY",
            "KEY": "KEY",
            
            "TRUIST": "TFC",
            "TRUIST FINANCIAL": "TFC",
            "TRUIST FINANCIAL CORPORATION": "TFC", 
            "TFC": "TFC",
            
            "FIFTH THIRD": "FITB",
            "FIFTH THIRD BANK": "FITB",
            "FIFTH THIRD BANCORP": "FITB",
            "FITB": "FITB",
            
            "REGIONS": "RF",
            "REGIONS BANK": "RF",
            "REGIONS FINANCIAL": "RF",
            "REGIONS FINANCIAL CORPORATION": "RF",
            "RF": "RF",
            
            "BANK OF NEW YORK MELLON": "BK",
            "BNY MELLON": "BK",
            "THE BANK OF NEW YORK MELLON": "BK",
            "MELLON": "BK",
            "BK": "BK",
            
            "M&T BANK": "MTB",
            "MT BANK": "MTB", 
            "M&T BANK CORPORATION": "MTB",
            "MTB": "MTB",
            
            # Community Banks (Tier 3)
            "COMMERCE BANCSHARES": "CBSH",
            "COMMERCE BANK": "CBSH",
            "CBSH": "CBSH",
            
            "POPULAR": "BPOP",
            "POPULAR BANK": "BPOP",
            "POPULAR INC": "BPOP",
            "BPOP": "BPOP",
            
            "CULLEN/FROST": "CFR",
            "FROST BANK": "CFR",
            "CFR": "CFR",
            
            "CITIZENS FINANCIAL": "CFG",
            "CITIZENS BANK": "CFG",
            "CFG": "CFG",
            
            "COMERICA": "CMA", 
            "COMERICA BANK": "CMA",
            "CMA": "CMA",
            
            "EAST WEST": "EWBC",
            "EAST WEST BANK": "EWBC",
            "EWBC": "EWBC",
            
            "FIRST CITIZENS": "FCNCA",
            "FIRST CITIZENS BANCSHARES": "FCNCA",
            "FCNCA": "FCNCA",
            
            "FIRST HORIZON": "FHN",
            "FIRST HORIZON BANK": "FHN",
            "FHN": "FHN",
            
            "OLD NATIONAL": "ONB",
            "OLD NATIONAL BANK": "ONB",
            "ONB": "ONB",
            
            "PROSPERITY": "PB", 
            "PROSPERITY BANK": "PB",
            "PB": "PB",
            
            "PINNACLE": "PNFP",
            "PINNACLE FINANCIAL": "PNFP",
            "PNFP": "PNFP",
            
            "SYNOVUS": "SNV",
            "SYNOVUS BANK": "SNV",
            "SNV": "SNV",
            
            "SOUTHERN": "SSB",
            "SOUTHERN BANK": "SSB", 
            "SSB": "SSB",
            
            "UMB": "UMBF",
            "UMB BANK": "UMBF",
            "UMB FINANCIAL": "UMBF",
            "UMBF": "UMBF",
            
            "US BANK": "USB",
            "U.S. BANK": "USB",
            "US BANCORP": "USB",
            "USB": "USB",
            
            "WESTERN ALLIANCE": "WAL",
            "WAL": "WAL",
            
            "WEBSTER": "WBS",
            "WEBSTER BANK": "WBS",
            "WBS": "WBS",
            
            "WINTRUST": "WTFC",
            "WINTRUST FINANCIAL": "WTFC", 
            "WTFC": "WTFC",
            
            "BOK FINANCIAL": "BOKF",
            "BOKF": "BOKF"
        }
        
        # Create reverse mapping for ticker validation
        self.ticker_to_names = {}
        for name, ticker in self.company_mappings.items():
            if ticker not in self.ticker_to_names:
                self.ticker_to_names[ticker] = []
            self.ticker_to_names[ticker].append(name)
    
    def normalize_company_name(self, company_input: str) -> Optional[str]:
        """
        Normalize company name to standard ticker
        
        Args:
            company_input: Raw company name from user query or extraction
            
        Returns:
            Standardized ticker or None if not found
        """
        if not company_input:
            return None
            
        # Clean and normalize input
        normalized_input = self._clean_company_name(company_input)
        
        # Direct lookup
        if normalized_input in self.company_mappings:
            return self.company_mappings[normalized_input]
        
        # Fuzzy matching for partial names
        return self._fuzzy_match(normalized_input)
    
    def _clean_company_name(self, name: str) -> str:
        """Clean and standardize company name format"""
        if not name:
            return ""
            
        # Convert to uppercase
        cleaned = name.upper().strip()
        
        # Remove common corporate suffixes
        suffixes = [
            "CORPORATION", "CORP", "CORP.", "INC", "INC.", "INCORPORATED",
            "LLC", "L.L.C.", "COMPANY", "CO", "CO.", "BANCORP", "BANCORPORATION",
            "FINANCIAL", "BANK", "BANKING", "GROUP", "HOLDINGS", "NA", "N.A."
        ]
        
        for suffix in suffixes:
            # Remove suffix if it's at the end (with word boundary)
            pattern = rf'\b{re.escape(suffix)}\b$'
            cleaned = re.sub(pattern, '', cleaned).strip()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _fuzzy_match(self, name: str) -> Optional[str]:
        """Attempt fuzzy matching for partial company names"""
        
        # Check if the name is contained in any of our mappings
        for company_name, ticker in self.company_mappings.items():
            if name in company_name or company_name in name:
                return ticker
        
        # Check for common abbreviations
        abbreviations = {
            "BofA": "BAC",
            "B of A": "BAC", 
            "WF": "WFC",
            "JPM": "JPM",
            "Chase": "JPM"
        }
        
        if name in abbreviations:
            return abbreviations[name]
            
        return None
    
    def get_company_variations(self, ticker: str) -> List[str]:
        """Get all known variations for a given ticker"""
        return self.ticker_to_names.get(ticker, [])
    
    def is_valid_ticker(self, ticker: str) -> bool:
        """Check if ticker exists in our dataset"""
        return ticker in self.ticker_to_names
    
    def get_all_tickers(self) -> List[str]:
        """Get all available company tickers"""
        return list(self.ticker_to_names.keys())


# Global instance for easy import
company_mapper = CompanyMapper()


def normalize_company(company_name: str) -> Optional[str]:
    """
    Convenience function for normalizing company names
    
    Args:
        company_name: Raw company name
        
    Returns:
        Standardized ticker or None
    """
    return company_mapper.normalize_company_name(company_name)


def get_available_companies() -> List[str]:
    """Get list of all available company tickers"""
    return company_mapper.get_all_tickers()


if __name__ == "__main__":
    # Test the mapping system
    test_cases = [
        "Wells Fargo",
        "WELLS FARGO & COMPANY", 
        "JPMorgan Chase",
        "Bank of America Corporation",
        "Zions Bancorporation",
        "WFC",
        "JPM",
        "BAC"
    ]
    
    print("🏦 Company Name Normalization Test:")
    print("=" * 50)
    for test_name in test_cases:
        result = normalize_company(test_name)
        print(f"{test_name:30} → {result}")
    
    print(f"\n📊 Total Companies Available: {len(get_available_companies())}")
    print(f"Companies: {', '.join(sorted(get_available_companies()))}") 