"""
Text Fallback Utility - Load full text content from source JSON files
when Pinecone metadata has truncated or missing text content
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TextContentFallback:
    """Utility to load full text content from source JSON files"""
    
    def __init__(self, source_directory: str = "zion_10k_md&a_chunked"):
        self.source_directory = source_directory
        self._text_cache = {}  # Cache loaded text to avoid repeated file reads
        
    def get_full_text_content(self, retrieval_metadata: Dict[str, Any]) -> str:
        """
        Load full text content from source JSON file based on retrieval metadata.
        
        Args:
            retrieval_metadata: Metadata from Pinecone retrieval result
            
        Returns:
            Full text content from source file, or empty string if not found
        """
        try:
            # Try to identify source file from metadata
            source_file = self._identify_source_file(retrieval_metadata)
            if not source_file:
                return ""
                
            # Check cache first
            if source_file in self._text_cache:
                return self._text_cache[source_file]
                
            # Load from file
            source_path = os.path.join(self.source_directory, source_file)
            if os.path.exists(source_path):
                with open(source_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    full_text = data.get('text', '')
                    
                    # Cache the result
                    self._text_cache[source_file] = full_text
                    
                    logger.debug(f"Loaded {len(full_text)} chars from {source_file}")
                    return full_text
            else:
                logger.warning(f"Source file not found: {source_path}")
                return ""
                
        except Exception as e:
            logger.error(f"Error loading text from source file: {e}")
            return ""
    
    def _identify_source_file(self, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Identify the source JSON file based on metadata.
        
        Tries multiple approaches to find the correct file:
        1. Direct filename from metadata
        2. Constructed filename from company/year/section info
        3. Pattern matching in directory
        """
        # Approach 1: Direct filename
        direct_file = metadata.get('source_file') or metadata.get('section_filename')
        if direct_file:
            return direct_file
            
        # Approach 2: Construct filename from metadata
        company = metadata.get('company', '')
        year = metadata.get('year', '')
        section = metadata.get('section_type', '') or metadata.get('section', '')
        
        if company and year:
            # Try common filename patterns
            patterns = [
                f"external_SEC_{company}_10-K_{year}_q1_Item1.Business.json",
                f"external_SEC_{company}_10-K_{year}_q1_Item1.business.json",
                f"external_SEC_{company}_10-K_{year}_q1_{section}.json"
            ]
            
            for pattern in patterns:
                if os.path.exists(os.path.join(self.source_directory, pattern)):
                    return pattern
                    
        # Approach 3: Search directory for matching files
        if company and year:
            try:
                files = os.listdir(self.source_directory)
                for filename in files:
                    if (company in filename and 
                        str(year) in filename and 
                        filename.endswith('.json')):
                        return filename
            except Exception as e:
                logger.error(f"Error searching directory: {e}")
                
        return None
    
    def enhance_retrieval_with_full_text(self, retrieval_hit: Dict[str, Any], 
                                       min_text_length: int = 500) -> Dict[str, Any]:
        """
        Enhance a retrieval hit with full text content if current text is too short.
        
        Args:
            retrieval_hit: Dict with 'text', 'metadata', etc.
            min_text_length: Minimum text length to consider adequate
            
        Returns:
            Enhanced retrieval hit with full text content
        """
        current_text = retrieval_hit.get('text', '')
        
        # If text is adequate, return as-is
        if len(current_text) >= min_text_length:
            return retrieval_hit
            
        # Try to load full text
        metadata = retrieval_hit.get('metadata', {})
        full_text = self.get_full_text_content(metadata)
        
        if full_text and len(full_text) > len(current_text):
            # Create enhanced copy
            enhanced_hit = retrieval_hit.copy()
            enhanced_hit['text'] = full_text
            enhanced_hit['text_source'] = 'fallback_loaded'
            
            logger.info(f"Enhanced text from {len(current_text)} to {len(full_text)} chars")
            return enhanced_hit
        
        return retrieval_hit

# Global instance for easy import
text_fallback = TextContentFallback() 