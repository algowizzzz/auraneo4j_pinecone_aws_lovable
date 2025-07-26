import json
import glob
import re
import os
import numpy as np
from collections import defaultdict
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from pinecone_integration import PineconeVectorStore
from enhanced_graph_schema import EnhancedGraphSchemaManager, FinancialEntityExtractor
from data_validator import SECDataValidator
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OutputFolderGraphBuilder:
    """
    Enhanced graph builder for processing output folder with Markdown files:
    - Processes real SEC 10-K filings from output/ directory
    - Handles Markdown format instead of JSON
    - Implements hybrid chunking strategy
    - Creates comprehensive financial knowledge graph
    """
    
    def __init__(self, uri, user, password, embedding_model='all-MiniLM-L6-v2', use_pinecone=True):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.embedding_model = SentenceTransformer(embedding_model)
        self.use_pinecone = use_pinecone
        
        # Initialize components
        self.entity_extractor = FinancialEntityExtractor()
        self.schema_manager = EnhancedGraphSchemaManager(self.driver)
        
        # Initialize Pinecone if enabled
        if self.use_pinecone:
            try:
                pinecone_index = os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index')
                self.pinecone_store = PineconeVectorStore(index_name=pinecone_index)
                logger.info(f"Initialized Pinecone vector store: {pinecone_index}")
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone: {e}. Continuing without vector store.")
                self.pinecone_store = None
        else:
            self.pinecone_store = None
        
        logger.info("Initialized OutputFolderGraphBuilder with all enhancement modules")

    def parse_markdown_metadata(self, md_content):
        """Parse metadata from markdown file headers"""
        lines = md_content.split('\n')
        metadata = {}
        
        # Extract metadata from header
        for line in lines[:20]:  # Check first 20 lines for metadata
            if line.startswith('**Ticker:**'):
                metadata['company'] = line.split('**Ticker:**')[1].strip()
            elif line.startswith('**Form Type:**'):
                metadata['doc_type'] = line.split('**Form Type:**')[1].strip()
            elif line.startswith('**Filing Date:**'):
                metadata['filing_date'] = line.split('**Filing Date:**')[1].strip()
            elif line.startswith('**Accession Number:**'):
                metadata['accession_number'] = line.split('**Accession Number:**')[1].strip()
        
        # Extract text content (everything after metadata header)
        content_start = next((i for i, line in enumerate(lines) if line.startswith('### UNITED STATES')), 10)
        metadata['text'] = '\n'.join(lines[content_start:])
        
        # Set defaults for missing fields
        metadata.setdefault('domain', 'external')
        metadata.setdefault('subdomain', 'SEC')
        
        return metadata

    def discover_output_files(self, output_dir="output"):
        """Discover all markdown files in output directory structure"""
        md_files = []
        
        for company_dir in os.listdir(output_dir):
            company_path = os.path.join(output_dir, company_dir)
            if not os.path.isdir(company_path) or company_dir in ['chunking']:
                continue
                
            # Look for 10-K subdirectory
            tenk_path = os.path.join(company_path, '10-K')
            if not os.path.exists(tenk_path):
                continue
                
            # Find all year directories
            for year_dir in os.listdir(tenk_path):
                year_path = os.path.join(tenk_path, year_dir)
                if not os.path.isdir(year_path):
                    continue
                    
                # Find markdown files
                for filename in os.listdir(year_path):
                    if filename.endswith('.md'):
                        file_path = os.path.join(year_path, filename)
                        md_files.append({
                            'path': file_path,
                            'company': company_dir,
                            'year': year_dir,
                            'filename': filename
                        })
        
        return md_files

    def _clean_text(self, text):
        """Clean text artifacts and normalize formatting"""
        # Remove page numbers and artifacts
        text = re.sub(r'Page \d+', '', text)
        # Flatten simple tables (example: convert | Key | Value | to Key: Value)
        text = re.sub(r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', r'\1: \2\n', text)
        # Remove excessive whitespace
        text = ' '.join(text.split())
        return text

    def _chunk_text_by_size(self, text, max_words=1500, overlap_words=300):
        """Chunk text by size with overlap for better context"""
        words = text.split()
        if not words: 
            return []
        
        chunks = []
        for i in range(0, len(words), max_words - overlap_words):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)
        return chunks

    def generate_embeddings(self, text_list):
        """Generate embeddings for a list of texts"""
        try:
            embeddings = self.embedding_model.encode(text_list, convert_to_tensor=False)
            return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.0] * 384 for _ in text_list]  # Return zero embeddings as fallback

    def clear_database(self):
        """Clear the database before building"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("Database cleared")

    def create_full_schema(self):
        """Create comprehensive schema with all indexes and constraints"""
        with self.driver.session() as session:
            session.execute_write(self._create_base_constraints_and_indexes_tx)
        
        self.schema_manager.create_enhanced_constraints_and_indexes()
        logger.info("Comprehensive schema created")

    def _create_base_constraints_and_indexes_tx(self, tx):
        """Create base constraints and indexes for chunked schema"""
        # Unique constraints for new chunked schema
        constraints = [
            "CREATE CONSTRAINT unique_company IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT unique_year IF NOT EXISTS FOR (y:Year) REQUIRE (y.company, y.value) IS UNIQUE",
            "CREATE CONSTRAINT unique_quarter IF NOT EXISTS FOR (q:Quarter) REQUIRE (q.company, q.year, q.label) IS UNIQUE",
            "CREATE CONSTRAINT unique_document IF NOT EXISTS FOR (d:Document) REQUIRE d.filename IS UNIQUE",
            "CREATE CONSTRAINT unique_source_section IF NOT EXISTS FOR (s:SourceSection) REQUIRE s.filename IS UNIQUE",
            "CREATE CONSTRAINT unique_chunk IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE"
        ]
        
        # Text indexes for search
        indexes = [
            "CREATE INDEX chunk_text_index IF NOT EXISTS FOR (c:Chunk) ON (c.text)",
            "CREATE INDEX chunk_embedding_index IF NOT EXISTS FOR (c:Chunk) ON (c.embedding)"
        ]
        
        for constraint in constraints:
            try:
                tx.run(constraint)
            except Exception as e:
                logger.warning(f"Constraint might already exist: {e}")
        
        for index in indexes:
            try:
                tx.run(index)
            except Exception as e:
                logger.warning(f"Index might already exist: {e}")

    def build_graph_from_output(self, output_dir="output"):
        """Build graph from output folder structure"""
        
        # Discover all markdown files
        md_files = self.discover_output_files(output_dir)
        logger.info(f"Found {len(md_files)} markdown files to process")
        
        # Group files by document (company/year)
        grouped_files = defaultdict(list)
        for file_info in md_files:
            key = (file_info['company'], file_info['year'])
            grouped_files[key].append(file_info)
        
        logger.info(f"Processing {len(grouped_files)} document groups")
        
        # Process each group
        with self.driver.session() as session:
            for (company, year), file_infos in grouped_files.items():
                logger.info(f"Processing {company} {year} ({len(file_infos)} files)")
                
                # Process first file to get company info
                first_file = file_infos[0]
                with open(first_file['path'], 'r', encoding='utf-8') as f:
                    md_content = f.read()
                    record = self.parse_markdown_metadata(md_content)
                
                # Create document structure
                document_filename = f"SEC_{company}_{year}_Q1_10-K"  # Simplified for 10-K annual filings
                doc_params = {
                    "domain": record.get("domain", "external"),
                    "subdomain": record.get("subdomain", "SEC"),
                    "company": company,
                    "year": int(year),
                    "quarter_label": "Q1",  # Annual filing, using Q1 as default
                    "doc_type": "10-K",
                    "filename": document_filename,
                    "filing_date": record.get("filing_date"),
                    "cik": record.get("accession_number", "").split("-")[0] if record.get("accession_number") else "",
                    "accession_number": record.get("accession_number")
                }
                
                session.execute_write(self._create_document_tx, doc_params)
                
                # Process all files for this company/year
                all_chunks_data = []
                pinecone_documents = []
                
                for file_info in file_infos:
                    with open(file_info['path'], 'r', encoding='utf-8') as f:
                        md_content = f.read()
                        record = self.parse_markdown_metadata(md_content)
                        
                        basename = file_info['filename']
                        section_text = record.get("text", "")
                        cleaned_text = self._clean_text(section_text)
                        chunks = self._chunk_text_by_size(cleaned_text)
                        
                        if not chunks:
                            continue
                        
                        # Create SourceSection node
                        session.execute_write(self._create_source_section_tx, {
                            "doc_filename": document_filename,
                            "source_filename": basename,
                            "section_name": f"{company} 10-K {year}"
                        })
                        
                        # Process chunks
                        for i, chunk_text in enumerate(chunks):
                            chunk_id = f"{basename}_chunk_{i}"
                            extracted_entities = self.entity_extractor.extract_entities(chunk_text)
                            
                            chunk_data = {
                                "source_filename": basename,
                                "chunk_id": chunk_id,
                                "text": chunk_text,
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                                "financial_entities": extracted_entities
                            }
                            all_chunks_data.append(chunk_data)
                            
                            # Prepare for Pinecone
                            if self.pinecone_store:
                                pinecone_doc = {
                                    "id": chunk_id,
                                    "text": chunk_text,
                                    "company": company,
                                    "year": int(year),
                                    "quarter": "Q1",
                                    "document_type": "10-K",
                                    "source_filename": basename,
                                    "section_name": f"{company} 10-K {year}",
                                    "chunk_index": i,
                                    "total_chunks": len(chunks)
                                }
                                pinecone_documents.append(pinecone_doc)
                
                # Generate embeddings for all chunks
                if all_chunks_data:
                    texts = [chunk["text"] for chunk in all_chunks_data]
                    embeddings = self.generate_embeddings(texts)
                    
                    # Create chunk nodes
                    for chunk_data, embedding in zip(all_chunks_data, embeddings):
                        chunk_params = {
                            **chunk_data,
                            "embedding": embedding,
                            "embedding_dimension": len(embedding),
                            "financial_entities_json": json.dumps(chunk_data["financial_entities"]),
                            "word_count": len(chunk_data["text"].split())
                        }
                        session.execute_write(self._create_chunk_tx, chunk_params)
                    
                    # Store in Pinecone
                    if self.pinecone_store and pinecone_documents:
                        for doc, embedding in zip(pinecone_documents, embeddings):
                            doc["embedding"] = embedding
                        
                        self.pinecone_store.upsert_documents(pinecone_documents)
                        logger.info(f"Stored {len(pinecone_documents)} documents in Pinecone")
                
                # Create financial entity relationships
                for chunk_data in all_chunks_data:
                    if chunk_data["financial_entities"]:
                        self.schema_manager.create_financial_entities(chunk_data, chunk_data["financial_entities"])

    # Transaction methods (same as v5 but updated for chunked schema)
    def _create_document_tx(self, tx, params):
        """Create document and company hierarchy"""
        query = """
        MERGE (c:Company {name: $company})
        MERGE (c)-[:HAS_YEAR]->(y:Year {company: $company, value: $year})
        MERGE (y)-[:HAS_QUARTER]->(q:Quarter {company: $company, year: $year, label: $quarter_label})
        MERGE (q)-[:HAS_DOC]->(d:Document {filename: $filename})
        ON CREATE SET 
            d.domain = $domain, d.subdomain = $subdomain, d.document_type = $doc_type,
            d.filing_date = $filing_date, d.cik = $cik, d.accession_number = $accession_number,
            d.created = datetime()
        ON MATCH SET 
            d.domain = $domain, d.subdomain = $subdomain, d.document_type = $doc_type,
            d.filing_date = $filing_date, d.cik = $cik, d.accession_number = $accession_number,
            d.updated = datetime()
        """
        tx.run(query, params)

    def _create_source_section_tx(self, tx, params):
        """Create SourceSection node"""
        query = """
        MATCH (doc:Document {filename: $doc_filename})
        MERGE (doc)-[:HAS_SOURCE_SECTION]->(src:SourceSection {filename: $source_filename})
        ON CREATE SET src.name = $section_name
        """
        tx.run(query, params)

    def _create_chunk_tx(self, tx, params):
        """Create Chunk node and link to SourceSection"""
        query = """
        MATCH (src:SourceSection {filename: $source_filename})
        MERGE (c:Chunk {chunk_id: $chunk_id})
        ON CREATE SET
            c.text = $text, c.embedding = $embedding, c.embedding_dimension = $embedding_dimension,
            c.financial_entities = $financial_entities_json, c.word_count = $word_count,
            c.created = datetime()
        ON MATCH SET
            c.text = $text, c.embedding = $embedding, c.embedding_dimension = $embedding_dimension,
            c.financial_entities = $financial_entities_json, c.word_count = $word_count,
            c.updated = datetime()
        MERGE (src)-[:HAS_CHUNK {index: $chunk_index}]->(c)
        """
        tx.run(query, params)

    def get_statistics(self):
        """Get comprehensive statistics about the built graph"""
        stats = {}
        
        with self.driver.session() as session:
            # Node counts
            node_queries = {
                "Company": "MATCH (c:Company) RETURN count(c) as count",
                "Document": "MATCH (d:Document) RETURN count(d) as count", 
                "SourceSection": "MATCH (s:SourceSection) RETURN count(s) as count",
                "Chunk": "MATCH (c:Chunk) RETURN count(c) as count",
                "Product": "MATCH (p:Product) RETURN count(p) as count",
                "Risk": "MATCH (r:Risk) RETURN count(r) as count"
            }
            
            stats['node_counts'] = {}
            for node_type, query in node_queries.items():
                result = session.run(query).single()
                stats['node_counts'][node_type] = result['count'] if result else 0
        
        return stats

    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()

# Main execution
if __name__ == "__main__":
    # Database connection
    URI = os.getenv('NEO4J_URI', 'neo4j+s://ea31579d.databases.neo4j.io')
    USER = os.getenv('NEO4J_USERNAME', 'neo4j') 
    PASSWORD = os.getenv('NEO4J_PASSWORD', 'qKcfMP9ZHvkmpZzNJ5OmqwFSqmCj8sscfzxZroEbpfM')
    
    builder = OutputFolderGraphBuilder(URI, USER, PASSWORD)

    try:
        logger.info("=== Starting Output Folder Graph Build ===")
        
        logger.info("Clearing the database...")
        builder.clear_database()
        
        logger.info("Creating comprehensive schema...")
        builder.create_full_schema()

        logger.info("Building graph from output folder...")
        builder.build_graph_from_output("../output")

        logger.info("=== Build Complete! ===")
        
        # Print statistics
        stats = builder.get_statistics()
        
        print(f"\n=== Final Statistics ===")
        print(f"Graph Statistics:")
        for node_type, count in stats['node_counts'].items():
            print(f"  {node_type}: {count}")
            
    except Exception as e:
        logger.error(f"Error during output folder graph creation: {e}")
        raise
    finally:
        builder.close()
