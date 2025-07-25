"""
Neo4j Text Retrieval System
Replaces file-based text fallback with direct Neo4j queries for better performance and centralization
"""

import os
import logging
from typing import Dict, Any, Optional, List
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class Neo4jTextRetriever:
    """
    Retrieves full text content from Neo4j Section nodes instead of local files.
    Provides better performance, centralization, and eliminates file system dependencies.
    """
    
    def __init__(self, 
                 neo4j_uri: Optional[str] = None,
                 neo4j_user: Optional[str] = None, 
                 neo4j_password: Optional[str] = None):
        
        # Use provided parameters or fall back to environment variables
        self.uri = neo4j_uri or os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        self.user = neo4j_user or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = neo4j_password or os.getenv("NEO4J_PASSWORD", "newpassword")
        
        self.driver = None
        self._text_cache = {}  # Cache for performance
        
    def _get_driver(self):
        """Lazy initialization of Neo4j driver"""
        if self.driver is None:
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                logger.debug("Neo4j driver initialized for text retrieval")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j for text retrieval: {e}")
                raise
        return self.driver
    
    def get_text_by_filename(self, filename: str) -> Optional[str]:
        """
        Retrieve full text content by matching Section.filename
        
        Args:
            filename: Source filename (e.g., "external_SEC_PB_10-K_2022_q1_Item1.business.json")
            
        Returns:
            Full text content or None if not found
        """
        # Check cache first
        if filename in self._text_cache:
            logger.debug(f"Cache hit for {filename}")
            return self._text_cache[filename]
        
        try:
            driver = self._get_driver()
            with driver.session() as session:
                result = session.run("""
                    MATCH (s:Section)
                    WHERE s.filename = $filename
                    RETURN s.text as text, s.name as section_name, size(s.text) as text_length
                """, filename=filename)
                
                record = result.single()
                if record:
                    text = record['text']
                    section_name = record['section_name']
                    text_length = record['text_length']
                    
                    # Cache the result
                    self._text_cache[filename] = text
                    
                    logger.info(f"Retrieved {text_length:,} chars from Neo4j section '{section_name}' (file: {filename})")
                    return text
                else:
                    logger.warning(f"No section found with filename: {filename}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error retrieving text from Neo4j for {filename}: {e}")
            return None
    
    def get_text_by_metadata(self, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Retrieve text using various metadata fields to find the matching Section
        
        Args:
            metadata: Dict containing company, year, section info, source_file, etc.
            
        Returns:
            Full text content or None if not found
        """
        # Strategy 1: Direct filename match
        filename = metadata.get('source_file') or metadata.get('section_filename')
        if filename:
            text = self.get_text_by_filename(filename)
            if text:
                return text
        
        # Strategy 2: Construct filename from metadata
        company = metadata.get('company', '')
        year = metadata.get('year', '')
        section_type = metadata.get('section_type', '') or metadata.get('section', '')
        
        if company and year:
            # Try common patterns
            patterns = [
                f"external_SEC_{company}_10-K_{year}_q1_Item1.Business.json",
                f"external_SEC_{company}_10-K_{year}_q1_Item1.business.json",
                f"external_SEC_{company}_10-K_{year}_q1_{section_type}.json"
            ]
            
            for pattern in patterns:
                text = self.get_text_by_filename(pattern)
                if text:
                    return text
        
        # Strategy 3: Search by company and year (exact match)
        if company and year:
            try:
                driver = self._get_driver()
                with driver.session() as session:
                    result = session.run("""
                        MATCH (s:Section)
                        WHERE s.filename CONTAINS $company 
                        AND s.filename CONTAINS $year
                        AND s.text IS NOT NULL 
                        AND s.text <> ""
                        RETURN s.text as text, s.filename as filename, s.name as section_name
                        ORDER BY size(s.text) DESC
                        LIMIT 1
                    """, company=company, year=str(year))
                    
                    record = result.single()
                    if record:
                        text = record['text']
                        filename = record['filename']
                        
                        # Cache this result too
                        self._text_cache[filename] = text
                        
                        logger.info(f"Found text via exact search: {company} {year} -> {filename}")
                        return text
                        
            except Exception as e:
                logger.error(f"Error searching Neo4j for {company} {year}: {e}")
        
        # Strategy 4: Fallback to best available company match (any year)
        if company:
            try:
                driver = self._get_driver()
                with driver.session() as session:
                    result = session.run("""
                        MATCH (s:Section)
                        WHERE s.filename CONTAINS $company
                        AND s.text IS NOT NULL 
                        AND s.text <> ""
                        RETURN s.text as text, s.filename as filename, s.name as section_name,
                               size(s.text) as text_length
                        ORDER BY size(s.text) DESC
                        LIMIT 1
                    """, company=company)
                    
                    record = result.single()
                    if record:
                        text = record['text']
                        filename = record['filename']
                        text_length = record['text_length']
                        
                        # Cache this result too
                        self._text_cache[filename] = text
                        
                        logger.info(f"Found text via company fallback: {company} -> {filename} ({text_length:,} chars)")
                        return text
                        
            except Exception as e:
                logger.error(f"Error searching Neo4j for company {company}: {e}")
        
        logger.warning(f"Could not find text content for metadata: {metadata}")
        return None
    
    def enhance_retrieval_with_neo4j_text(self, retrieval_hit: Dict[str, Any], 
                                        min_text_length: int = 500) -> Dict[str, Any]:
        """
        Enhance a retrieval hit with full text content from Neo4j.
        Replaces the file-based text fallback system.
        
        Args:
            retrieval_hit: Dict with 'text', 'metadata', etc.
            min_text_length: Minimum text length to consider adequate
            
        Returns:
            Enhanced retrieval hit with full text content from Neo4j
        """
        current_text = retrieval_hit.get('text', '')
        
        # If text is adequate, return as-is
        if len(current_text) >= min_text_length:
            return retrieval_hit
            
        # Try to load full text from Neo4j
        metadata = retrieval_hit.get('metadata', {})
        full_text = self.get_text_by_metadata(metadata)
        
        if full_text and len(full_text) > len(current_text):
            # Create enhanced copy
            enhanced_hit = retrieval_hit.copy()
            enhanced_hit['text'] = full_text
            enhanced_hit['text_source'] = 'neo4j_retrieved'
            
            logger.info(f"Enhanced text from {len(current_text)} to {len(full_text)} chars via Neo4j")
            return enhanced_hit
        
        return retrieval_hit
    
    def get_section_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about text storage in Neo4j for monitoring
        
        Returns:
            Dict with section count, text coverage, size statistics
        """
        try:
            driver = self._get_driver()
            with driver.session() as session:
                result = session.run("""
                    MATCH (s:Section)
                    RETURN count(s) as total_sections,
                           count(CASE WHEN s.text IS NOT NULL AND s.text <> "" THEN 1 END) as sections_with_text,
                           avg(size(s.text)) as avg_text_length,
                           min(size(s.text)) as min_text_length,
                           max(size(s.text)) as max_text_length,
                           sum(size(s.text)) as total_text_size
                """)
                
                record = result.single()
                if record:
                    stats = {
                        'total_sections': record['total_sections'],
                        'sections_with_text': record['sections_with_text'],
                        'text_coverage_pct': (record['sections_with_text'] / record['total_sections'] * 100) if record['total_sections'] > 0 else 0,
                        'avg_text_length': int(record['avg_text_length']) if record['avg_text_length'] else 0,
                        'min_text_length': int(record['min_text_length']) if record['min_text_length'] else 0,
                        'max_text_length': int(record['max_text_length']) if record['max_text_length'] else 0,
                        'total_text_size_mb': (record['total_text_size'] / 1024 / 1024) if record['total_text_size'] else 0
                    }
                    return stats
                    
        except Exception as e:
            logger.error(f"Error getting section statistics: {e}")
            
        return {}
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            self.driver = None

# Global instance for easy import
neo4j_text_retriever = Neo4jTextRetriever() 