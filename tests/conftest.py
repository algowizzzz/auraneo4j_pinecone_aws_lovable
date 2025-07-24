"""
Pytest configuration and fixtures for SEC Graph testing
"""

import pytest
import os
import sys
import json
import tempfile
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def sample_env_vars():
    """Sample environment variables for testing"""
    return {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USER': 'neo4j',
        'NEO4J_PASSWORD': 'testpassword',
        'PINECONE_API_KEY': 'test-pinecone-key',
        'PINECONE_INDEX_NAME': 'test-sec-index',
        'OPENAI_API_KEY': 'test-openai-key',
        'AWS_LAMBDA_FUNCTION_NAME': 'sec-ccr-langgraph-processor',
        'AWS_API_GATEWAY_URL': 'https://test-api.amazonaws.com'
    }

@pytest.fixture
def sample_sec_json():
    """Sample SEC filing JSON data for testing"""
    return {
        "domain": "external",
        "subdomain": "SEC",
        "Company": "ZION",
        "Document type": "10-K",
        "year": "2025",
        "quarter": "q1",
        "section": "ITEM 1. BUSINESS",
        "accession_number": "0000109380-25-000040",
        "cik": "0000109380",
        "filing_date": "2025-02-25",
        "text": "DESCRIPTION OF BUSINESS\n\nZions Bancorporation, National Association is a bank headquartered in Salt Lake City, Utah with annual net revenue of $3.1 billion in 2024..."
    }

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for testing"""
    mock_driver = Mock()
    mock_session = Mock()
    mock_transaction = Mock()
    
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_session.execute_write.return_value = None
    mock_session.run.return_value = []
    
    return mock_driver

@pytest.fixture
def mock_pinecone_client():
    """Mock Pinecone client for testing"""
    mock_client = Mock()
    mock_index = Mock()
    
    mock_client.Index.return_value = mock_index
    mock_index.query.return_value = {
        'matches': [
            {
                'id': 'test-id-1',
                'score': 0.95,
                'metadata': {
                    'text': 'Sample SEC text content',
                    'company': 'ZION',
                    'year': 2025,
                    'quarter': 'q1'
                }
            }
        ]
    }
    
    return mock_client

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = "Test LLM response"
    mock_client.invoke.return_value = mock_response
    
    return mock_client

@pytest.fixture
def sample_agent_state():
    """Sample AgentState for testing"""
    return {
        "query_raw": "What are Zions Bancorporation's capital ratios in 2025?",
        "metadata": {
            "company": "ZION",
            "year": "2025",
            "quarter": "q1",
            "doc_type": "10-K"
        },
        "route": "cypher",
        "fallback": ["hybrid", "rag"],
        "retrievals": [],
        "valid": False,
        "final_answer": "",
        "citations": []
    }

@pytest.fixture
def sample_retrieval_hits():
    """Sample retrieval hits for testing"""
    return [
        {
            "section_id": "test-section-1",
            "text": "Zions Bancorporation maintains strong capital ratios with CET1 of 10.9%",
            "score": 0.95,
            "source": "cypher",
            "metadata": {
                "company": "ZION",
                "year": 2025,
                "quarter": "q1",
                "section_name": "Capital Management"
            }
        },
        {
            "section_id": "test-section-2", 
            "text": "Our Tier 1 risk-based capital ratio is 11.0% and total risk-based capital ratio is 13.3%",
            "score": 0.92,
            "source": "cypher",
            "metadata": {
                "company": "ZION",
                "year": 2025,
                "quarter": "q1",
                "section_name": "Regulatory Capital"
            }
        }
    ]

@pytest.fixture
def temp_test_data_dir():
    """Create temporary directory with test SEC data"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample JSON file
        test_file = os.path.join(temp_dir, "external_SEC_ZION_10-K_2025_q1_Item1.Business.json")
        sample_data = {
            "domain": "external",
            "subdomain": "SEC", 
            "Company": "ZION",
            "Document type": "10-K",
            "year": "2025",
            "quarter": "q1",
            "section": "ITEM 1. BUSINESS",
            "text": "Test business description content..."
        }
        
        with open(test_file, 'w') as f:
            json.dump(sample_data, f)
            
        yield temp_dir

@pytest.fixture(autouse=True)
def setup_test_environment(sample_env_vars):
    """Automatically set up test environment variables"""
    original_env = {}
    
    # Store original values
    for key in sample_env_vars:
        original_env[key] = os.environ.get(key)
        
    # Set test values  
    for key, value in sample_env_vars.items():
        os.environ[key] = value
        
    yield
    
    # Restore original values
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

@pytest.fixture
def financial_entity_samples():
    """Sample financial entities for testing extraction"""
    return {
        "risks": ["market risk", "credit risk", "operational risk"],
        "products": ["loans", "deposits", "securities"],
        "metrics": ["capital ratio", "return on equity", "efficiency ratio"],
        "business_lines": ["retail banking", "commercial banking"],
        "regulations": ["Basel III", "Dodd Frank", "CCAR"]
    }

class TestDataHelper:
    """Helper class for creating test data"""
    
    @staticmethod
    def create_mock_graph_result(company: str, year: int, data: List[Dict[str, Any]]):
        """Create mock Neo4j result"""
        mock_records = []
        for item in data:
            mock_record = Mock()
            for key, value in item.items():
                setattr(mock_record, key, value)
            mock_records.append(mock_record)
        return mock_records
    
    @staticmethod
    def create_mock_pinecone_result(hits: List[Dict[str, Any]]):
        """Create mock Pinecone result"""
        return {
            'matches': [
                {
                    'id': hit.get('id', f'test-id-{i}'),
                    'score': hit.get('score', 0.8),
                    'metadata': hit.get('metadata', {})
                }
                for i, hit in enumerate(hits)
            ]
        }

@pytest.fixture
def test_data_helper():
    """Provide test data helper"""
    return TestDataHelper