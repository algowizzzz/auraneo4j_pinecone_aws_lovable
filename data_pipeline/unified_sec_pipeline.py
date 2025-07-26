#!/usr/bin/env python3
"""
Unified SEC Data Pipeline - Complete Rebuild
Addresses all identified issues:
1. Text content truncation in Pinecone
2. Schema misalignment between Neo4j and RAG node
3. Missing text content validation
4. Incomplete pipeline execution
5. Dependency issues

This pipeline ensures both databases contain full, retrievable text content.
"""

import os
import sys
import json
import re
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Third-party imports
import numpy as np
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of processing a single file"""
    file_path: str
    company: str
    year: str
    chunks_created: int
    neo4j_success: bool
    pinecone_success: bool
    errors: List[str]
    text_length: int

class UnifiedSECPipeline:
    """
    Unified pipeline for processing SEC filings into both Neo4j and Pinecone
    with full text content preservation and comprehensive validation
    """
    
    def __init__(self, 
                 neo4j_uri: str = None,
                 neo4j_user: str = None,
                 neo4j_password: str = None,
                 pinecone_api_key: str = None,
                 embedding_model: str = 'all-MiniLM-L6-v2',
                 pinecone_index: str = 'sec-rag-index'):
        
        # Environment setup
        self.neo4j_uri = neo4j_uri or os.getenv('NEO4J_URI')
        self.neo4j_user = neo4j_user or os.getenv('NEO4J_USERNAME', 'neo4j')
        self.neo4j_password = neo4j_password or os.getenv('NEO4J_PASSWORD')
        self.pinecone_api_key = pinecone_api_key or os.getenv('PINECONE_API_KEY')
        self.pinecone_index_name = pinecone_index
        
        # Validate environment
        self._validate_environment()
        
        # Initialize components
        self.embedding_model = SentenceTransformer(embedding_model)
        self.neo4j_driver = None
        self.pinecone_index = None
        
        # Processing statistics
        self.stats = {
            'files_processed': 0,
            'chunks_created': 0,
            'neo4j_nodes_created': 0,
            'pinecone_vectors_created': 0,
            'errors': []
        }
        
        logger.info("UnifiedSECPipeline initialized successfully")
    
    def _validate_environment(self):
        """Validate all required environment variables"""
        required_vars = {
            'NEO4J_URI': self.neo4j_uri,
            'NEO4J_PASSWORD': self.neo4j_password,
            'PINECONE_API_KEY': self.pinecone_api_key
        }
        
        missing = [var for var, value in required_vars.items() if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        
        logger.info("✅ Environment validation passed")
    
    def initialize_connections(self):
        """Initialize connections to Neo4j and Pinecone"""
        logger.info("🔌 Initializing database connections...")
        
        # Initialize Neo4j
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            # Test connection
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            logger.info("✅ Neo4j connection established")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Neo4j: {e}")
        
        # Initialize Pinecone
        try:
            pc = Pinecone(api_key=self.pinecone_api_key)
            
            # Create index if it doesn't exist
            existing_indexes = [idx.name for idx in pc.list_indexes()]
            if self.pinecone_index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.pinecone_index_name}")
                pc.create_index(
                    name=self.pinecone_index_name,
                    dimension=384,  # all-MiniLM-L6-v2 dimension
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
                time.sleep(10)  # Wait for index to be ready
            
            self.pinecone_index = pc.Index(self.pinecone_index_name)
            logger.info("✅ Pinecone connection established")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Pinecone: {e}")
    
    def clear_databases(self, confirm: bool = False):
        """Clear both databases for clean start"""
        if not confirm:
            response = input("⚠️  This will DELETE ALL DATA in both databases. Type 'YES' to confirm: ")
            if response != 'YES':
                logger.info("Database clear cancelled")
                return
        
        logger.info("🗑️  Clearing databases...")
        
        # Clear Neo4j
        with self.neo4j_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("✅ Neo4j cleared")
        
        # Clear Pinecone
        self.pinecone_index.delete(delete_all=True)
        logger.info("✅ Pinecone cleared")
    
    def create_neo4j_schema(self):
        """Create optimized Neo4j schema aligned with RAG node expectations"""
        logger.info("📊 Creating Neo4j schema...")
        
        with self.neo4j_driver.session() as session:
            # Constraints
            constraints = [
                "CREATE CONSTRAINT unique_company IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
                "CREATE CONSTRAINT unique_section IF NOT EXISTS FOR (s:Section) REQUIRE s.filename IS UNIQUE",
                "CREATE CONSTRAINT unique_chunk IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE"
            ]
            
            # Indexes for search performance
            indexes = [
                "CREATE INDEX section_text_index IF NOT EXISTS FOR (s:Section) ON (s.text)",
                "CREATE INDEX chunk_text_index IF NOT EXISTS FOR (c:Chunk) ON (c.text)",
                "CREATE INDEX company_name_index IF NOT EXISTS FOR (c:Company) ON (c.name)"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.warning(f"Constraint might already exist: {e}")
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    logger.warning(f"Index might already exist: {e}")
        
        logger.info("✅ Neo4j schema created")
    
    def discover_markdown_files(self, output_dir: str = "output") -> List[Dict[str, str]]:
        """Discover all markdown files in output directory"""
        md_files = []
        output_path = Path(output_dir)
        
        if not output_path.exists():
            raise FileNotFoundError(f"Output directory not found: {output_dir}")
        
        # Walk through company/form-type/year structure
        for company_dir in output_path.iterdir():
            if not company_dir.is_dir() or company_dir.name.startswith('.'):
                continue
            
            # Look for 10-K directory
            tenk_dir = company_dir / "10-K"
            if not tenk_dir.exists():
                continue
            
            # Find year directories
            for year_dir in tenk_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                
                # Find markdown files
                for md_file in year_dir.glob("*.md"):
                    md_files.append({
                        'path': str(md_file),
                        'company': company_dir.name,
                        'year': year_dir.name,
                        'filename': md_file.name
                    })
        
        logger.info(f"📁 Found {len(md_files)} markdown files")
        return md_files
    
    def parse_markdown_file(self, file_path: str) -> Dict[str, Any]:
        """Parse SEC markdown file and extract metadata + content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')
            metadata = {}
            
            # Extract metadata from header
            for i, line in enumerate(lines[:20]):
                if line.startswith('**Ticker:**'):
                    metadata['ticker'] = line.split('**Ticker:**')[1].strip()
                elif line.startswith('**Form Type:**'):
                    metadata['form_type'] = line.split('**Form Type:**')[1].strip()
                elif line.startswith('**Filing Date:**'):
                    metadata['filing_date'] = line.split('**Filing Date:**')[1].strip()
                elif line.startswith('**Accession Number:**'):
                    metadata['accession_number'] = line.split('**Accession Number:**')[1].strip()
            
            # Extract main content (skip metadata header)
            content_start = 0
            for i, line in enumerate(lines):
                if line.startswith('### UNITED STATES') or line.startswith('# UNITED STATES'):
                    content_start = i
                    break
            
            full_text = '\n'.join(lines[content_start:])
            
            # Clean and process text
            cleaned_text = self._clean_text(full_text)
            
            return {
                'metadata': metadata,
                'raw_text': full_text,
                'cleaned_text': cleaned_text,
                'text_length': len(cleaned_text)
            }
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Clean up table formatting
        text = re.sub(r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', r'\1: \2', text)
        
        # Remove page numbers and artifacts
        text = re.sub(r'Page \d+', '', text)
        text = re.sub(r'Table of Contents', '', text)
        
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()
    
    def create_chunks(self, text: str, max_words: int = 1500, overlap_words: int = 300) -> List[str]:
        """Create overlapping text chunks"""
        words = text.split()
        if len(words) <= max_words:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = min(start + max_words, len(words))
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            
            if end >= len(words):
                break
                
            start += (max_words - overlap_words)
        
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.0] * 384 for _ in texts]
    
    def store_in_neo4j(self, company: str, year: str, filename: str, 
                      chunks: List[str], embeddings: List[List[float]]) -> bool:
        """Store document data in Neo4j with FULL text content"""
        try:
            with self.neo4j_driver.session() as session:
                # Create company
                session.run("""
                    MERGE (c:Company {name: $company})
                    ON CREATE SET c.created = datetime()
                """, company=company)
                
                # Create section with FULL TEXT - this is what RAG node expects
                section_result = session.run("""
                    MATCH (c:Company {name: $company})
                    MERGE (c)-[:HAS_SECTION]->(s:Section {filename: $filename})
                    ON CREATE SET 
                        s.name = $section_name,
                        s.text = $full_text,
                        s.company = $company,
                        s.year = $year,
                        s.form_type = '10-K',
                        s.created = datetime()
                    ON MATCH SET
                        s.text = $full_text,
                        s.updated = datetime()
                    RETURN s
                """, {
                    'company': company,
                    'filename': filename,
                    'section_name': f"{company} 10-K {year}",
                    'full_text': ' '.join(chunks),  # Store combined text
                    'year': int(year)
                })
                
                # Create individual chunks
                for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk_id = f"{filename}_chunk_{i}"
                    
                    session.run("""
                        MATCH (s:Section {filename: $filename})
                        MERGE (c:Chunk {chunk_id: $chunk_id})
                        ON CREATE SET
                            c.text = $text,
                            c.embedding = $embedding,
                            c.chunk_index = $index,
                            c.word_count = $word_count,
                            c.created = datetime()
                        ON MATCH SET
                            c.text = $text,
                            c.embedding = $embedding,
                            c.updated = datetime()
                        MERGE (s)-[:HAS_CHUNK {index: $index}]->(c)
                    """, {
                        'filename': filename,
                        'chunk_id': chunk_id,
                        'text': chunk_text,
                        'embedding': embedding,
                        'index': i,
                        'word_count': len(chunk_text.split())
                    })
                
                self.stats['neo4j_nodes_created'] += len(chunks) + 2  # chunks + section + company
                return True
                
        except Exception as e:
            logger.error(f"Error storing in Neo4j: {e}")
            return False
    
    def store_in_pinecone(self, company: str, year: str, filename: str,
                         chunks: List[str], embeddings: List[List[float]]) -> bool:
        """Store document data in Pinecone with FULL text content"""
        try:
            vectors = []
            
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{filename}_chunk_{i}"
                
                # CRITICAL FIX: Store FULL text content (no truncation)
                metadata = {
                    'company': company,
                    'year': int(year),
                    'form_type': '10-K',
                    'filename': filename,
                    'chunk_index': i,
                    'text': chunk_text,  # FULL TEXT - no [:1500] truncation!
                    'word_count': len(chunk_text.split()),
                    'created': datetime.now().isoformat()
                }
                
                # Ensure metadata stays under Pinecone's 40KB limit
                metadata_size = len(json.dumps(metadata).encode('utf-8'))
                if metadata_size > 35000:  # Keep buffer for other fields
                    # Only truncate if absolutely necessary
                    metadata['text'] = chunk_text[:30000]
                    logger.warning(f"Text truncated for {vector_id} due to size limits")
                
                vectors.append({
                    'id': vector_id,
                    'values': embedding,
                    'metadata': metadata
                })
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.pinecone_index.upsert(vectors=batch)
            
            self.stats['pinecone_vectors_created'] += len(vectors)
            return True
            
        except Exception as e:
            logger.error(f"Error storing in Pinecone: {e}")
            return False
    
    def process_file(self, file_info: Dict[str, str]) -> ProcessingResult:
        """Process a single markdown file"""
        file_path = file_info['path']
        company = file_info['company']
        year = file_info['year']
        filename = file_info['filename']
        
        logger.info(f"📄 Processing {company} {year} - {filename}")
        
        result = ProcessingResult(
            file_path=file_path,
            company=company,
            year=year,
            chunks_created=0,
            neo4j_success=False,
            pinecone_success=False,
            errors=[],
            text_length=0
        )
        
        try:
            # Parse file
            parsed_data = self.parse_markdown_file(file_path)
            if not parsed_data:
                result.errors.append("Failed to parse file")
                return result
            
            result.text_length = parsed_data['text_length']
            
            # Create chunks
            chunks = self.create_chunks(parsed_data['cleaned_text'])
            result.chunks_created = len(chunks)
            
            if not chunks:
                result.errors.append("No chunks created")
                return result
            
            # Generate embeddings
            embeddings = self.generate_embeddings(chunks)
            
            # Store in both databases
            result.neo4j_success = self.store_in_neo4j(
                company, year, filename, chunks, embeddings
            )
            
            result.pinecone_success = self.store_in_pinecone(
                company, year, filename, chunks, embeddings
            )
            
            if result.neo4j_success and result.pinecone_success:
                logger.info(f"✅ Successfully processed {filename} ({len(chunks)} chunks)")
            else:
                logger.warning(f"⚠️  Partial success for {filename}")
            
            self.stats['chunks_created'] += len(chunks)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            result.errors.append(str(e))
        
        return result
    
    def validate_storage(self) -> Dict[str, Any]:
        """Validate that both databases contain retrievable text content"""
        logger.info("🔍 Validating text content storage...")
        
        validation_results = {
            'neo4j_sections_with_text': 0,
            'neo4j_chunks_with_text': 0,
            'pinecone_vectors_with_text': 0,
            'sample_text_lengths': [],
            'validation_passed': False
        }
        
        try:
            # Check Neo4j sections (what RAG node queries)
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (s:Section)
                    WHERE s.text IS NOT NULL AND s.text <> ''
                    RETURN count(s) as section_count,
                           avg(size(s.text)) as avg_text_length,
                           collect(size(s.text))[0..5] as sample_lengths
                """)
                
                record = result.single()
                if record:
                    validation_results['neo4j_sections_with_text'] = record['section_count']
                    validation_results['neo4j_avg_text_length'] = record['avg_text_length']
                
                # Check chunks too
                result = session.run("""
                    MATCH (c:Chunk)
                    WHERE c.text IS NOT NULL AND c.text <> ''
                    RETURN count(c) as chunk_count
                """)
                record = result.single()
                if record:
                    validation_results['neo4j_chunks_with_text'] = record['chunk_count']
            
            # Check Pinecone vectors
            sample_query = self.pinecone_index.query(
                vector=[0.1] * 384,
                top_k=10,
                include_metadata=True
            )
            
            text_count = 0
            text_lengths = []
            
            for match in sample_query.matches:
                if match.metadata and match.metadata.get('text'):
                    text = match.metadata['text']
                    if len(text.strip()) > 10:
                        text_count += 1
                        text_lengths.append(len(text))
            
            validation_results['pinecone_vectors_with_text'] = text_count
            validation_results['sample_text_lengths'] = text_lengths
            
            # Validation criteria
            neo4j_valid = validation_results['neo4j_sections_with_text'] > 0
            pinecone_valid = validation_results['pinecone_vectors_with_text'] > 0
            
            validation_results['validation_passed'] = neo4j_valid and pinecone_valid
            
            if validation_results['validation_passed']:
                logger.info("✅ Validation PASSED - Both databases contain text content")
            else:
                logger.error("❌ Validation FAILED - Missing text content in databases")
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            validation_results['validation_error'] = str(e)
        
        return validation_results
    
    def run_pipeline(self, output_dir: str = "output", max_files: int = None) -> Dict[str, Any]:
        """Run the complete pipeline"""
        logger.info("🚀 Starting Unified SEC Pipeline")
        start_time = time.time()
        
        try:
            # Initialize connections
            self.initialize_connections()
            
            # Create schema
            self.create_neo4j_schema()
            
            # Discover files
            md_files = self.discover_markdown_files(output_dir)
            
            if max_files:
                md_files = md_files[:max_files]
                logger.info(f"📋 Limited to {max_files} files for testing")
            
            # Process files
            results = []
            self.stats['files_processed'] = 0
            
            for file_info in md_files:
                result = self.process_file(file_info)
                results.append(result)
                self.stats['files_processed'] += 1
                
                # Log progress
                if self.stats['files_processed'] % 5 == 0:
                    logger.info(f"📊 Progress: {self.stats['files_processed']}/{len(md_files)} files")
            
            # Validate storage
            validation_results = self.validate_storage()
            
            # Final statistics
            execution_time = time.time() - start_time
            
            final_stats = {
                'execution_time': execution_time,
                'processing_stats': self.stats,
                'validation_results': validation_results,
                'file_results': results,
                'success': validation_results.get('validation_passed', False)
            }
            
            if final_stats['success']:
                logger.info(f"🎉 Pipeline completed successfully in {execution_time:.2f}s")
                logger.info(f"📊 Created {self.stats['chunks_created']} chunks across {self.stats['files_processed']} files")
            else:
                logger.error("❌ Pipeline completed with validation failures")
            
            return final_stats
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        
        finally:
            self.close_connections()
    
    def close_connections(self):
        """Close database connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        logger.info("🔌 Connections closed")

def main():
    """Main execution function"""
    pipeline = UnifiedSECPipeline()
    
    try:
        # Test with limited dataset first
        logger.info("🧪 Testing with limited dataset (max 6 files)")
        
        # Clear databases (will prompt for confirmation)
        pipeline.clear_databases()
        
        # Run pipeline
        results = pipeline.run_pipeline(max_files=6)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 PIPELINE EXECUTION SUMMARY")
        print("="*60)
        print(f"Success: {'✅ YES' if results['success'] else '❌ NO'}")
        print(f"Execution Time: {results['execution_time']:.2f}s")
        print(f"Files Processed: {results['processing_stats']['files_processed']}")
        print(f"Chunks Created: {results['processing_stats']['chunks_created']}")
        print(f"Neo4j Sections with Text: {results['validation_results']['neo4j_sections_with_text']}")
        print(f"Pinecone Vectors with Text: {results['validation_results']['pinecone_vectors_with_text']}")
        
        if results['success']:
            print("\n🎉 Ready to test with full dataset! Remove emergency fix from RAG node.")
        else:
            print("\n❌ Fix validation issues before proceeding.")
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()