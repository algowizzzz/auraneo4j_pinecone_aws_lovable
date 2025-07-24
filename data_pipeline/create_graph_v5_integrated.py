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

class IntegratedFinancialGraphBuilder:
    """
    Integrated graph builder combining all enhancements:
    - Semantic embeddings with Pinecone
    - Enhanced financial entity extraction
    - Advanced relationship modeling
    - Data validation and quality assurance
    """
    
    def __init__(self, uri, user, password, embedding_model='all-MiniLM-L6-v2', use_pinecone=True):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.embedding_model = SentenceTransformer(embedding_model)
        self.use_pinecone = use_pinecone
        
        # Initialize components
        self.validator = SECDataValidator()
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
            
        logger.info(f"Initialized integrated graph builder with embedding model: {embedding_model}")

    def close(self):
        self.driver.close()

    def clear_database(self):
        with self.driver.session() as session:
            session.execute_write(self._clear_db)

    @staticmethod
    def _clear_db(tx):
        tx.run("MATCH (n) DETACH DELETE n")

    def create_full_schema(self):
        """Create complete schema with all enhancements"""
        with self.driver.session() as session:
            # Create base constraints and indexes
            session.execute_write(self._create_base_constraints_and_indexes_tx)
            
        # Create enhanced schema
        self.schema_manager.create_enhanced_constraints_and_indexes()

    @staticmethod
    def _create_base_constraints_and_indexes_tx(tx):
        # Base uniqueness constraints for entities
        tx.run("CREATE CONSTRAINT unique_domain IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE")
        tx.run("CREATE CONSTRAINT unique_subdomain IF NOT EXISTS FOR (s:Subdomain) REQUIRE s.name IS UNIQUE")
        tx.run("CREATE CONSTRAINT unique_company IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE")
        
        # Composite uniqueness constraints for contextual entities
        tx.run("CREATE CONSTRAINT unique_year IF NOT EXISTS FOR (y:Year) REQUIRE (y.company, y.value) IS UNIQUE")
        tx.run("CREATE CONSTRAINT unique_quarter IF NOT EXISTS FOR (q:Quarter) REQUIRE (q.company, q.year, q.label) IS UNIQUE")
        
        # Uniqueness for documents and sections
        tx.run("CREATE CONSTRAINT unique_document IF NOT EXISTS FOR (d:Document) REQUIRE d.filename IS UNIQUE")
        tx.run("CREATE CONSTRAINT unique_section IF NOT EXISTS FOR (s:Section) REQUIRE s.filename IS UNIQUE")
        
        # Enhanced indexes for search capabilities
        tx.run("""
        CREATE INDEX doc_lookup IF NOT EXISTS FOR (d:Document) 
        ON (d.company, d.year, d.quarter, d.document_type)
        """)
        tx.run("CREATE FULLTEXT INDEX section_text_index IF NOT EXISTS FOR (s:Section) ON EACH [s.text, s.name]")
        tx.run("CREATE INDEX section_embedding_index IF NOT EXISTS FOR (s:Section) ON (s.embedding_dimension)")

    def generate_embeddings(self, text_list):
        """Generate embeddings for a list of texts"""
        try:
            embeddings = self.embedding_model.encode(text_list, convert_to_tensor=False)
            return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.0] * 384 for _ in text_list]  # Return zero embeddings as fallback

    def validate_and_build_graph(self, data_dir, file_pattern, validation_report_path=None):
        """Validate data and build graph with comprehensive error handling"""
        
        # Step 1: Validate all files
        logger.info("Step 1: Validating data files...")
        validation_results = self.validator.validate_directory(data_dir, file_pattern)
        
        if validation_report_path:
            self.validator.generate_validation_report(validation_results, validation_report_path)
        
        # Check if we have valid files to process
        if validation_results['valid_files'] == 0:
            raise ValueError("No valid files found to process!")
        
        logger.info(f"Validation complete: {validation_results['valid_files']}/{validation_results['total_files']} files are valid")
        
        # Step 2: Process only valid files
        valid_files = [result.file_path for result in validation_results['validation_results'] if result.is_valid]
        
        # Group files by document
        grouped_files = self._group_files_by_document(valid_files)
        logger.info(f"Processing {len(grouped_files)} document groups")
        
        # Step 3: Build graph with enhanced processing
        self._build_enhanced_graph(grouped_files)
        
        # Step 4: Create advanced relationships
        logger.info("Creating advanced relationships...")
        self._create_advanced_relationships()
        
        return validation_results

    def _group_files_by_document(self, file_paths):
        """Group files by document using the validator's pattern"""
        grouped_files = defaultdict(list)
        
        for f_path in file_paths:
            basename = os.path.basename(f_path)
            match = self.validator.filename_pattern.search(basename)
            if match:
                company, doc_type, year, quarter, _, _ = match.groups()
                key = (company.upper(), doc_type.upper(), year, quarter.upper())
                grouped_files[key].append(f_path)
        
        return grouped_files

    def _build_enhanced_graph(self, grouped_files):
        """Build graph with all enhancements"""
        with self.driver.session() as session:
            for (company, doc_type, year, quarter), filenames in grouped_files.items():
                logger.info(f"Processing {company} {year} {quarter} {doc_type}")
                
                # Define the parent Document's unique filename
                document_filename = f"SEC_{company}_{year}_{quarter}_{doc_type}"
                
                # Use metadata from the first file in the group to create the parent doc
                with open(filenames[0], 'r') as f:
                    record = json.load(f)
                    
                    # Extract company classification from first document
                    company_text = record.get("text", "")
                    
                    # Prepare document parameters
                    doc_params = {
                        "domain": record.get("domain"),
                        "subdomain": record.get("subdomain"),
                        "company": company,
                        "year": int(year),
                        "quarter_label": quarter,
                        "doc_type": doc_type,
                        "filename": document_filename,
                        "filing_date": record.get("filing_date"),
                        "cik": record.get("cik"),
                        "accession_number": record.get("accession_number")
                    }
                
                # Create the hierarchy up to the Document node
                session.execute_write(self._create_document_tx, doc_params)
                
                # Enhance company classification
                self.schema_manager.enhance_company_classification(company, company_text)

                # Collect all section data for batch processing
                section_data_list = []
                pinecone_documents = []
                
                for f_path in filenames:
                    with open(f_path, 'r') as f:
                        record = json.load(f)
                        basename = os.path.basename(f_path)
                        
                        section_text = record.get("text", "")
                        section_name = record.get("section", "Unnamed Section")
                        
                        # Extract financial entities
                        extracted_entities = self.entity_extractor.extract_entities(section_text)
                        
                        section_info = {
                            "doc_filename": document_filename,
                            "section_filename": basename,
                            "section_name": section_name,
                            "text": section_text,
                            "financial_entities": extracted_entities,
                            "record": record
                        }
                        section_data_list.append(section_info)
                        
                        # Prepare data for Pinecone
                        if self.pinecone_store:
                            pinecone_doc = {
                                **section_info,
                                "company": company,
                                "year": int(year),
                                "quarter": quarter,
                                "document_type": doc_type,
                                "filing_date": record.get("filing_date"),
                                "cik": record.get("cik"),
                                "accession_number": record.get("accession_number")
                            }
                            pinecone_documents.append(pinecone_doc)

                # Generate embeddings for all sections in batch
                if section_data_list:
                    texts = [data["text"] for data in section_data_list]
                    embeddings = self.generate_embeddings(texts)
                    
                    # Process each section with its embedding and entities
                    for i, section_data in enumerate(section_data_list):
                        section_data["embedding"] = embeddings[i]
                        section_data["embedding_dimension"] = len(embeddings[i])
                        
                        # Create section with embedding
                        session.execute_write(self._create_section_with_embedding_tx, section_data)
                        
                        # Create financial entities and relationships
                        self.schema_manager.create_financial_entities(section_data, section_data["financial_entities"])
                
                # Upload to Pinecone if available
                if self.pinecone_store and pinecone_documents:
                    try:
                        success = self.pinecone_store.upsert_documents(pinecone_documents)
                        if success:
                            logger.info(f"Successfully uploaded {len(pinecone_documents)} documents to Pinecone")
                        else:
                            logger.warning("Failed to upload documents to Pinecone")
                    except Exception as e:
                        logger.error(f"Error uploading to Pinecone: {e}")

    @staticmethod
    def _create_document_tx(tx, params):
        query = """
        MERGE (domain:Domain {name: $domain})
        MERGE (domain)-[:HAS_SUBDOMAIN]->(subdomain:Subdomain {name: $subdomain})
        MERGE (subdomain)-[:HAS_COMPANY]->(company:Company {name: $company})
        ON CREATE SET
            company.industry = 'Banking',
            company.sector = 'Financial Services'
        MERGE (company)-[:HAS_YEAR]->(year:Year {company: $company, value: $year, name: toString($year)})
        MERGE (year)-[:HAS_QUARTER]->(quarter:Quarter {company: $company, year: $year, label: $quarter_label, name: $quarter_label})
        
        MERGE (quarter)-[:HAS_DOC]->(doc:Document {filename: $filename})
        ON CREATE SET
            doc.name = $doc_type,
            doc.document_type = $doc_type,
            doc.company = $company,
            doc.year = $year,
            doc.quarter = $quarter_label,
            doc.filing_date = $filing_date,
            doc.cik = $cik,
            doc.accession_number = $accession_number
        """
        tx.run(query, **params)

    @staticmethod
    def _create_section_with_embedding_tx(tx, params):
        # Clean the text by replacing newlines with spaces
        clean_text = params.get("text", "").replace('\n', ' ')
        
        # Convert embedding to proper format for Neo4j
        embedding = params.get("embedding", [])
        
        query = """
        MATCH (doc:Document {filename: $doc_filename})
        MERGE (section:Section {filename: $section_filename})
        ON CREATE SET
            section.name = $section_name,
            section.section = $section_name,
            section.text = $clean_text,
            section.embedding = $embedding,
            section.embedding_dimension = $embedding_dimension,
            section.financial_entities = $financial_entities_json,
            section.word_count = $word_count,
            section.created = datetime()
        ON MATCH SET
            section.text = $clean_text,
            section.embedding = $embedding,
            section.embedding_dimension = $embedding_dimension,
            section.financial_entities = $financial_entities_json,
            section.word_count = $word_count,
            section.updated = datetime()
        MERGE (doc)-[:HAS_SECTION]->(section)
        """
        
        # Prepare parameters
        section_params = {
            "doc_filename": params["doc_filename"],
            "section_filename": params["section_filename"],
            "section_name": params["section_name"],
            "clean_text": clean_text,
            "embedding": embedding,
            "embedding_dimension": params["embedding_dimension"],
            "financial_entities_json": json.dumps(params["financial_entities"]),
            "word_count": len(clean_text.split())
        }
        
        tx.run(query, **section_params)

    def _create_advanced_relationships(self):
        """Create all advanced relationships"""
        logger.info("Creating temporal relationships...")
        self.create_horizontal_links()
        
        logger.info("Creating semantic similarity links...")
        self.create_semantic_similarity_links()
        
        logger.info("Creating competitive relationships...")
        self.schema_manager.create_competitive_relationships()
        
        logger.info("Creating trend analysis...")
        self.schema_manager.create_temporal_trend_analysis()
        
        logger.info("Creating risk correlation network...")
        self.schema_manager.create_risk_correlation_network()

    def create_horizontal_links(self):
        with self.driver.session() as session:
            session.execute_write(self._create_horizontal_links_tx)
    
    @staticmethod
    def _create_horizontal_links_tx(tx):
        # Link Years chronologically for each company
        tx.run("""
        MATCH (c:Company)-[:HAS_YEAR]->(y:Year)
        WITH c, y ORDER BY y.value
        WITH c, collect(y) AS years
        UNWIND range(0, size(years) - 2) AS i
        WITH years[i] AS y1, years[i+1] AS y2
        MERGE (y1)-[:NEXT_YEAR]->(y2)
        """)

        # Link Quarters chronologically for each Year
        tx.run("""
        MATCH (y:Year)-[:HAS_QUARTER]->(q:Quarter)
        WITH y, q ORDER BY q.label
        WITH y, collect(q) AS quarters
        UNWIND range(0, size(quarters) - 2) AS i
        WITH quarters[i] AS q1, quarters[i+1] AS q2
        MERGE (q1)-[:NEXT_QUARTER]->(q2)
        """)

        # Link similar Documents across companies (same period and type)
        tx.run("""
        MATCH (d:Document)
        WITH d.year AS year, d.quarter AS quarter, d.document_type as doc_type, collect(d) AS documents
        WHERE size(documents) > 1
        UNWIND range(0, size(documents) - 2) AS i
        WITH documents[i] AS d1, documents[i+1] AS d2
        MERGE (d1)-[:SIMILAR_DOC]->(d2)
        """)

    def create_semantic_similarity_links(self, similarity_threshold=0.7):
        """Create similarity links between sections based on embeddings"""
        with self.driver.session() as session:
            session.execute_write(self._create_semantic_links_tx, similarity_threshold)

    @staticmethod
    def _create_semantic_links_tx(tx, threshold):
        # Create semantic similarity links for same section types across companies
        query = """
        MATCH (s1:Section), (s2:Section)
        WHERE s1 <> s2 
        AND s1.embedding IS NOT NULL 
        AND s2.embedding IS NOT NULL
        AND s1.section = s2.section  // Same section type across different companies
        WITH s1, s2, 
             reduce(dot = 0.0, i IN range(0, size(s1.embedding)-1) | 
                dot + s1.embedding[i] * s2.embedding[i]) AS dot_product,
             sqrt(reduce(norm1 = 0.0, i IN range(0, size(s1.embedding)-1) | 
                norm1 + s1.embedding[i] * s1.embedding[i])) AS norm1,
             sqrt(reduce(norm2 = 0.0, i IN range(0, size(s2.embedding)-1) | 
                norm2 + s2.embedding[i] * s2.embedding[i])) AS norm2
        WITH s1, s2, dot_product / (norm1 * norm2) AS cosine_similarity
        WHERE cosine_similarity > $threshold
        MERGE (s1)-[:SEMANTICALLY_SIMILAR {similarity: cosine_similarity, created: datetime()}]->(s2)
        """
        tx.run(query, threshold=threshold)

    def get_comprehensive_stats(self):
        """Get comprehensive statistics about the created graph"""
        with self.driver.session() as session:
            # Base entity counts
            base_stats = session.run("""
            MATCH (n)
            RETURN labels(n)[0] AS node_type, count(n) AS count
            ORDER BY count DESC
            """)
            
            stats = {'node_counts': {record["node_type"]: record["count"] for record in base_stats}}
            
            # Relationship counts
            rel_stats = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS relationship_type, count(r) AS count
            ORDER BY count DESC
            """)
            
            stats['relationship_counts'] = {record["relationship_type"]: record["count"] for record in rel_stats}
            
            # Enhanced schema stats
            enhanced_stats = self.schema_manager.get_enhanced_schema_stats()
            stats.update(enhanced_stats)
            
            # Pinecone stats
            if self.pinecone_store:
                try:
                    pinecone_stats = self.pinecone_store.get_index_stats()
                    stats['pinecone_stats'] = pinecone_stats
                except Exception as e:
                    logger.warning(f"Could not get Pinecone stats: {e}")
            
            return stats


if __name__ == "__main__":
    # --- Connection details ---
    URI = "neo4j://localhost:7687"
    USER = "neo4j"
    PASSWORD = "newpassword"

    # --- Data location ---
    DATA_DIRECTORY = "zion_10k_md&a_chunked"
    FILE_PATTERN = "*.json"
    VALIDATION_REPORT = "comprehensive_validation_report.json"

    builder = IntegratedFinancialGraphBuilder(URI, USER, PASSWORD)

    try:
        logger.info("=== Starting Integrated Financial Graph Build ===")
        
        logger.info("Clearing the database...")
        builder.clear_database()
        
        logger.info("Creating comprehensive schema...")
        builder.create_full_schema()

        logger.info("Validating data and building enhanced graph...")
        validation_results = builder.validate_and_build_graph(
            DATA_DIRECTORY, 
            FILE_PATTERN, 
            VALIDATION_REPORT
        )

        logger.info("=== Build Complete! ===")
        
        # Print comprehensive statistics
        stats = builder.get_comprehensive_stats()
        
        print(f"\n=== Final Statistics ===")
        print(f"Validation Results:")
        print(f"  Total files processed: {validation_results['total_files']}")
        print(f"  Valid files: {validation_results['valid_files']}")
        print(f"  Success rate: {validation_results['valid_files']/validation_results['total_files']*100:.1f}%")
        
        print(f"\nGraph Statistics:")
        for node_type, count in stats['node_counts'].items():
            print(f"  {node_type}: {count}")
        
        print(f"\nRelationship Statistics:")
        for rel_type, count in list(stats['relationship_counts'].items())[:10]:  # Top 10
            print(f"  {rel_type}: {count}")
        
        if 'pinecone_stats' in stats:
            print(f"\nPinecone Statistics:")
            print(f"  Total vectors: {stats['pinecone_stats'].get('total_vector_count', 'N/A')}")
            
    except Exception as e:
        logger.error(f"Error during integrated graph creation: {e}")
        raise
    finally:
        builder.close()