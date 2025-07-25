"""
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
