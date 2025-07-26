#!/usr/bin/env python3
"""
Fix Neo4j Graph Population
Directly repairs missing metadata in the Neo4j database.
"""

import os
import sys
import re
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_neo4j_driver():
    """Establishes connection to Neo4j and returns the driver."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        logger.error("NEO4J_URI and NEO4J_PASSWORD must be set in .env file.")
        sys.exit(1)
    return GraphDatabase.driver(uri, auth=(user, password))

def fix_source_section_metadata(driver):
    """
    Fixes missing ticker and form_type metadata in SourceSection nodes.
    """
    logger.info("Starting metadata repair for SourceSection nodes...")
    with driver.session() as session:
        result = session.run("MATCH (s:SourceSection) WHERE s.ticker IS NULL OR s.form_type IS NULL RETURN id(s) as id, s.filename as filename")
        nodes_to_update = [dict(record) for record in result]
        
        logger.info(f"Found {len(nodes_to_update)} SourceSection nodes needing repair.")
        
        for node in nodes_to_update:
            node_id = node['id']
            filename = node['filename']
            if not filename:
                logger.warning(f"Skipping node {node_id} due to missing filename.")
                continue

            # Extract ticker and form_type from filename (e.g., "jpm_10k_20250214_0000019617.md")
            parts = filename.split('_')
            if len(parts) >= 2:
                ticker = parts[0].upper()
                form_type = parts[1].upper().replace('-', '') # "10-K" -> "10K"
                
                session.run("""
                    MATCH (s) WHERE id(s) = $id
                    SET s.ticker = $ticker, s.form_type = $form_type
                """, id=node_id, ticker=ticker, form_type=form_type)
                logger.info(f"Updated node {node_id} with ticker='{ticker}' and form_type='{form_type}'.")
            else:
                logger.warning(f"Could not parse ticker and form_type from filename: {filename}")

def fix_chunk_metadata(driver):
    """
    Ensures all Chunk nodes have a chunk_index.
    """
    logger.info("Starting metadata repair for Chunk nodes...")
    with driver.session() as session:
        result = session.run("""
            MATCH (s:SourceSection)-[:HAS_CHUNK]->(c:Chunk)
            WHERE c.chunk_index IS NULL
            RETURN id(s) as source_id
        """)
        source_ids = [record["source_id"] for record in result]
        
        logger.info(f"Found {len(set(source_ids))} SourceSection nodes with chunks needing chunk_index repair.")

        for source_id in set(source_ids):
            chunks_result = session.run("""
                MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
                WHERE id(s) = $source_id
                RETURN id(c) as chunk_id
                ORDER BY c.chunk_id // Assuming chunk_id provides a sort order
            """, source_id=source_id)
            
            chunk_ids = [record["chunk_id"] for record in chunks_result]
            
            for i, chunk_id in enumerate(chunk_ids):
                session.run("""
                    MATCH (c) WHERE id(c) = $chunk_id
                    SET c.chunk_index = $chunk_index
                """, chunk_id=chunk_id, chunk_index=i)
            logger.info(f"Repaired chunk_index for {len(chunk_ids)} chunks under SourceSection {source_id}.")


def main():
    """Main function to run the metadata repair."""
    driver = get_neo4j_driver()
    try:
        fix_source_section_metadata(driver)
        fix_chunk_metadata(driver)
        logger.info("Neo4j metadata repair process completed.")
    finally:
        driver.close()

if __name__ == "__main__":
    main()