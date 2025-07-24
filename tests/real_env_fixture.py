"""
Real Environment Fixture for Phase 2 Component Testing
Provides consistent real API credentials across all test classes
"""

import pytest
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Store real credentials before pytest fixtures can override them
REAL_CREDENTIALS = {
    'NEO4J_URI': os.getenv('NEO4J_URI'),
    'NEO4J_USERNAME': os.getenv('NEO4J_USERNAME'),
    'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD'),
    'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
    'PINECONE_INDEX_NAME': os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index'),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
}

def get_real_env(key: str) -> str:
    """Get real environment variable, bypassing pytest fixtures"""
    return REAL_CREDENTIALS.get(key)

@pytest.fixture
def real_environment():
    """
    Fixture that temporarily sets real environment variables,
    bypassing conftest.py mock fixtures for component testing
    """
    original_env = {}
    
    # Store original values
    for key in REAL_CREDENTIALS:
        original_env[key] = os.environ.get(key)
        
    # Set real values
    for key, value in REAL_CREDENTIALS.items():
        if value:
            os.environ[key] = value
    
    try:
        yield REAL_CREDENTIALS
    finally:
        # Restore original values
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

@pytest.fixture
def planner_with_real_env(real_environment):
    """Get planner function with real environment loaded"""
    # Import after environment is set
    from agent.nodes.planner import planner
    return planner

@pytest.fixture
def cypher_node_with_real_env(real_environment):
    """Get cypher node with real environment loaded"""
    from agent.nodes.cypher import cypher
    return cypher

@pytest.fixture
def hybrid_node_with_real_env(real_environment):
    """Get hybrid node with real environment loaded"""
    from agent.nodes.hybrid import hybrid
    return hybrid

@pytest.fixture
def rag_node_with_real_env(real_environment):
    """Get RAG node with real environment loaded"""
    from agent.nodes.rag import rag
    return rag

@pytest.fixture
def validator_with_real_env(real_environment):
    """Get validator node with real environment loaded"""
    from agent.nodes.validator import validator
    return validator

@pytest.fixture
def synthesizer_with_real_env(real_environment):
    """Get synthesizer node with real environment loaded"""
    from agent.nodes.synthesizer import synthesizer
    return synthesizer