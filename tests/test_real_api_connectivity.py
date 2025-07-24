"""
Real API Connectivity Tests
Tests actual connections to Neo4j Aura, Pinecone, and OpenAI APIs
"""

import pytest
import os
import sys
from typing import Dict, Any
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file BEFORE pytest fixtures override them
from dotenv import load_dotenv
load_dotenv()

# Store real credentials before pytest fixtures can override them
REAL_CREDENTIALS = {
    'NEO4J_URI': os.getenv('NEO4J_URI'),
    'NEO4J_USERNAME': os.getenv('NEO4J_USERNAME'),
    'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD'),
    'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
    'PINECONE_INDEX_NAME': os.getenv('PINECONE_INDEX_NAME', 'sec-graph-index'),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_real_env(key: str) -> str:
    """Get real environment variable, bypassing pytest fixtures"""
    return REAL_CREDENTIALS.get(key)

class TestNeo4jConnectivity:
    """Test real Neo4j Aura connectivity"""
    
    def test_neo4j_connection_real(self):
        """Test actual Neo4j Aura connection"""
        try:
            import neo4j
            from neo4j import GraphDatabase
            
            # Get credentials from real environment (bypassing pytest fixtures)
            uri = get_real_env('NEO4J_URI')
            username = get_real_env('NEO4J_USERNAME')  
            password = get_real_env('NEO4J_PASSWORD')
            
            assert uri is not None, "NEO4J_URI not set"
            assert username is not None, "NEO4J_USERNAME not set"
            assert password is not None, "NEO4J_PASSWORD not set"
            
            # Test connection
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            # Verify connection with simple query
            with driver.session() as session:
                result = session.run("RETURN 'Connection successful' as message")
                record = result.single()
                assert record["message"] == "Connection successful"
                
            driver.close()
            logger.info("✅ Neo4j Aura connection successful")
            
        except Exception as e:
            pytest.fail(f"Neo4j connection failed: {e}")
    
    def test_neo4j_database_access(self):
        """Test database access and basic operations"""
        try:
            from neo4j import GraphDatabase
            
            uri = get_real_env('NEO4J_URI')
            username = get_real_env('NEO4J_USERNAME')
            password = get_real_env('NEO4J_PASSWORD')
            
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            with driver.session() as session:
                # Test creating a temporary node
                result = session.run(
                    "CREATE (test:TestNode {name: 'connectivity_test', timestamp: $timestamp}) "
                    "RETURN test.name as name",
                    timestamp=str(os.getenv('USER', 'test_user'))
                )
                record = result.single()
                assert record["name"] == "connectivity_test"
                
                # Clean up test node
                session.run("MATCH (test:TestNode {name: 'connectivity_test'}) DELETE test")
                
            driver.close()
            logger.info("✅ Neo4j database operations successful")
            
        except Exception as e:
            pytest.fail(f"Neo4j database operations failed: {e}")

class TestPineconeConnectivity:
    """Test real Pinecone connectivity"""
    
    def test_pinecone_connection_real(self):
        """Test actual Pinecone connection"""
        try:
            from pinecone import Pinecone
            
            # Get credentials from environment
            api_key = get_real_env('PINECONE_API_KEY')
            index_name = get_real_env('PINECONE_INDEX_NAME')
            
            assert api_key is not None, "PINECONE_API_KEY not set"
            assert api_key != 'test_pinecone_key', "PINECONE_API_KEY still contains test value"
            
            # Initialize Pinecone
            pc = Pinecone(api_key=api_key)
            
            # List indexes to verify connection
            indexes = pc.list_indexes()
            logger.info(f"Available Pinecone indexes: {[idx.name for idx in indexes]}")
            
            logger.info("✅ Pinecone connection successful")
            
        except Exception as e:
            pytest.fail(f"Pinecone connection failed: {e}")
    
    def test_pinecone_index_access(self):
        """Test Pinecone index access and operations"""
        try:
            from pinecone import Pinecone
            import numpy as np
            
            api_key = get_real_env('PINECONE_API_KEY')
            index_name = get_real_env('PINECONE_INDEX_NAME')
            
            pc = Pinecone(api_key=api_key)
            
            # Check if our index exists
            indexes = pc.list_indexes()
            index_names = [idx.name for idx in indexes]
            
            if index_name not in index_names:
                logger.warning(f"Index '{index_name}' not found. Available: {index_names}")
                # Try to create index for testing
                from pinecone import ServerlessSpec
                pc.create_index(
                    name=index_name,
                    dimension=384,  # sentence-transformers dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                logger.info(f"Created test index: {index_name}")
            
            # Connect to index
            index = pc.Index(index_name)
            
            # Test basic index operations
            stats = index.describe_index_stats()
            logger.info(f"Index stats: {stats}")
            
            # Test vector operations with small test vector
            test_vector = np.random.random(384).tolist()
            test_id = "connectivity_test_vector"
            
            # Upsert test vector
            index.upsert(vectors=[(test_id, test_vector, {"test": "connectivity"})])
            
            # Query test vector
            results = index.query(vector=test_vector, top_k=1, include_metadata=True)
            assert len(results.matches) > 0, "No query results returned"
            
            # Clean up test vector
            index.delete(ids=[test_id])
            
            logger.info("✅ Pinecone index operations successful")
            
        except Exception as e:
            pytest.fail(f"Pinecone index operations failed: {e}")

class TestOpenAIConnectivity:
    """Test real OpenAI API connectivity"""
    
    def test_openai_connection_real(self):
        """Test actual OpenAI API connection"""
        try:
            from openai import OpenAI
            
            # Get API key from environment
            api_key = get_real_env('OPENAI_API_KEY')
            
            assert api_key is not None, "OPENAI_API_KEY not set"
            assert api_key != 'test_openai_key', "OPENAI_API_KEY still contains test value"
            assert api_key.startswith('sk-'), "OPENAI_API_KEY should start with 'sk-'"
            
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Test with simple completion
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "Say 'Connection test successful' and nothing else."}
                ],
                max_tokens=10,
                temperature=0
            )
            
            content = response.choices[0].message.content.strip()
            assert "Connection test successful" in content, f"Unexpected response: {content}"
            
            logger.info("✅ OpenAI API connection successful")
            
        except Exception as e:
            pytest.fail(f"OpenAI API connection failed: {e}")
    
    def test_openai_models_access(self):
        """Test OpenAI model access and capabilities"""
        try:
            from openai import OpenAI
            
            api_key = get_real_env('OPENAI_API_KEY')
            client = OpenAI(api_key=api_key)
            
            # Test model listing
            models = client.models.list()
            model_ids = [model.id for model in models.data]
            
            # Check for required models
            required_models = ['gpt-4o-mini', 'gpt-4o']
            available_required = [model for model in required_models if model in model_ids]
            
            assert len(available_required) > 0, f"No required models available. Found: {available_required}"
            
            # Test embeddings model if available
            if 'text-embedding-3-small' in model_ids:
                embeddings_response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input="Test embedding for connectivity check"
                )
                embedding = embeddings_response.data[0].embedding
                assert len(embedding) > 0, "Empty embedding returned"
                logger.info(f"✅ Embedding model working (dimension: {len(embedding)})")
            
            logger.info(f"✅ OpenAI models accessible: {available_required}")
            
        except Exception as e:
            pytest.fail(f"OpenAI models access failed: {e}")

class TestIntegratedConnectivity:
    """Test integrated connectivity across all services"""
    
    def test_full_stack_connectivity(self):
        """Test end-to-end connectivity across Neo4j, Pinecone, and OpenAI"""
        try:
            # Test sequence: OpenAI -> embedding -> Pinecone -> Neo4j
            from openai import OpenAI
            from pinecone import Pinecone
            from neo4j import GraphDatabase
            import numpy as np
            
            # 1. Initialize clients
            openai_client = OpenAI(api_key=get_real_env('OPENAI_API_KEY'))
            pc = Pinecone(api_key=get_real_env('PINECONE_API_KEY'))
            index_name = get_real_env('PINECONE_INDEX_NAME')
            
            test_text = "Zions Bancorporation reported strong capital ratios in Q1 2025"
            
            # 2. Get embedding using correct model for existing index
            temp_index = pc.Index(index_name)
            index_stats = temp_index.describe_index_stats()
            expected_dim = index_stats.dimension
            
            if expected_dim == 384:
                # Use sentence transformers to match existing index
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')
                embedding = model.encode(test_text).tolist()
            else:
                # Use OpenAI embedding
                embedding_response = openai_client.embeddings.create(
                    model="text-embedding-3-small", 
                    input=test_text
                )
                embedding = embedding_response.data[0].embedding
            
            # 3. Pinecone: Store and query embedding
            
            try:
                index = pc.Index(index_name)
            except:
                # Create index if it doesn't exist
                from pinecone import ServerlessSpec
                pc.create_index(
                    name=index_name,
                    dimension=len(embedding),
                    metric='cosine',
                    spec=ServerlessSpec(cloud='aws', region='us-east-1')
                )
                index = pc.Index(index_name)
            
            # Store test vector
            test_id = "full_stack_test"
            index.upsert(vectors=[(test_id, embedding, {"company": "ZION", "test": "full_stack"})])
            
            # Query similar vectors
            query_results = index.query(vector=embedding, top_k=1, include_metadata=True)
            assert len(query_results.matches) > 0, "No Pinecone query results"
            
            # 4. Neo4j: Store metadata and relationships
            driver = GraphDatabase.driver(
                get_real_env('NEO4J_URI'),
                auth=(get_real_env('NEO4J_USERNAME'), get_real_env('NEO4J_PASSWORD'))
            )
            
            with driver.session() as session:
                # Create test node
                session.run(
                    "MERGE (c:Company {symbol: 'ZION'}) "
                    "SET c.test_connectivity = true "
                    "RETURN c.symbol as symbol"
                )
                
                # Verify node creation
                result = session.run("MATCH (c:Company {symbol: 'ZION'}) RETURN c.symbol as symbol")
                record = result.single()
                assert record["symbol"] == "ZION"
            
            # 5. OpenAI: Generate response based on retrieved data
            completion_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": f"Summarize this financial text in one sentence: {test_text}"}
                ],
                max_tokens=50,
                temperature=0
            )
            
            summary = completion_response.choices[0].message.content
            assert len(summary) > 10, "Generated summary too short"
            
            # Cleanup
            index.delete(ids=[test_id])
            with driver.session() as session:
                session.run("MATCH (c:Company {symbol: 'ZION'}) REMOVE c.test_connectivity")
            driver.close()
            
            logger.info("✅ Full stack connectivity successful!")
            logger.info(f"Pipeline: Text -> Embedding({len(embedding)}) -> Pinecone -> Neo4j -> Summary({len(summary)} chars)")
            
        except Exception as e:
            pytest.fail(f"Full stack connectivity failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])