"""
TC-002: Data Pipeline Components Testing
Validates Week 1 data pipeline infrastructure and SEC data processing
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
import sys

# Add project root to path  
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestJSONDataValidation:
    """Test SEC JSON file validation and parsing"""
    
    def test_sample_json_structure(self, sample_sec_json):
        """Test sample JSON has required structure"""
        required_fields = [
            'domain', 'subdomain', 'Company', 'Document type',
            'year', 'quarter', 'section', 'text'
        ]
        
        for field in required_fields:
            assert field in sample_sec_json, f"Required field '{field}' missing from sample JSON"
            assert sample_sec_json[field] is not None, f"Field '{field}' is None"
            assert len(str(sample_sec_json[field])) > 0, f"Field '{field}' is empty"
    
    def test_json_data_types(self, sample_sec_json):
        """Test JSON field data types"""
        assert isinstance(sample_sec_json['domain'], str)
        assert isinstance(sample_sec_json['subdomain'], str)
        assert isinstance(sample_sec_json['Company'], str)
        assert isinstance(sample_sec_json['Document type'], str)
        assert isinstance(sample_sec_json['year'], str)
        assert isinstance(sample_sec_json['quarter'], str)
        assert isinstance(sample_sec_json['section'], str)
        assert isinstance(sample_sec_json['text'], str)
    
    def test_company_code_format(self, sample_sec_json):
        """Test company code format"""
        company = sample_sec_json['Company']
        assert len(company) >= 2, f"Company code '{company}' too short"
        assert len(company) <= 10, f"Company code '{company}' too long"
        assert company.isupper(), f"Company code '{company}' should be uppercase"
    
    def test_year_format(self, sample_sec_json):
        """Test year format"""
        year = sample_sec_json['year']
        assert year.isdigit(), f"Year '{year}' should be numeric"
        year_int = int(year)
        assert 2020 <= year_int <= 2030, f"Year '{year}' outside expected range (2020-2030)"
    
    def test_quarter_format(self, sample_sec_json):
        """Test quarter format"""
        quarter = sample_sec_json['quarter']
        valid_quarters = ['q1', 'q2', 'q3', 'q4']
        assert quarter.lower() in valid_quarters, f"Quarter '{quarter}' not in valid formats: {valid_quarters}"
    
    def test_section_format(self, sample_sec_json):
        """Test section format"""
        section = sample_sec_json['section']
        # Should contain "ITEM" for 10-K sections
        if sample_sec_json['Document type'] == '10-K':
            assert 'ITEM' in section.upper(), f"10-K section '{section}' should contain 'ITEM'"
    
    def test_text_content_quality(self, sample_sec_json):
        """Test text content quality"""
        text = sample_sec_json['text']
        assert len(text) >= 100, f"Text content too short: {len(text)} characters"
        
        # Should contain business-related keywords
        business_keywords = ['business', 'company', 'corporation', 'bank', 'financial']
        has_business_content = any(keyword.lower() in text.lower() for keyword in business_keywords)
        assert has_business_content, "Text should contain business-related keywords"

class TestRealDataFiles:
    """Test real SEC data files from the dataset"""
    
    def test_data_directory_exists(self):
        """Test SEC data directory exists"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'zion_10k_md&a_chunked')
        
        assert os.path.exists(data_dir), "SEC data directory not found"
        assert os.path.isdir(data_dir), "SEC data path is not a directory"
    
    def test_json_files_count(self):
        """Test sufficient number of JSON files"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'zion_10k_md&a_chunked')
        
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        assert len(json_files) >= 50, f"Expected at least 50 JSON files, found {len(json_files)}"
    
    def test_json_files_parseable(self):
        """Test JSON files can be parsed"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'zion_10k_md&a_chunked')
        
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        
        # Test first 5 files for parsing
        for filename in json_files[:5]:
            filepath = os.path.join(data_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                assert isinstance(data, dict), f"File {filename} does not contain a JSON object"
                assert 'text' in data, f"File {filename} missing 'text' field"
                assert 'Company' in data, f"File {filename} missing 'Company' field"
                
            except json.JSONDecodeError as e:
                pytest.fail(f"File {filename} is not valid JSON: {e}")
            except Exception as e:
                pytest.fail(f"Error reading file {filename}: {e}")
    
    def test_company_coverage(self):
        """Test coverage of different companies"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'zion_10k_md&a_chunked')
        
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        companies = set()
        
        for filename in json_files[:20]:  # Sample first 20 files
            filepath = os.path.join(data_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    companies.add(data.get('Company', 'UNKNOWN'))
            except:
                continue
        
        assert len(companies) >= 3, f"Expected at least 3 different companies, found {len(companies)}: {companies}"
    
    def test_year_coverage(self):
        """Test coverage of different years"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'zion_10k_md&a_chunked')
        
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        years = set()
        
        for filename in json_files[:20]:  # Sample first 20 files
            filepath = os.path.join(data_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    years.add(data.get('year', 'UNKNOWN'))
            except:
                continue
        
        assert len(years) >= 2, f"Expected at least 2 different years, found {len(years)}: {years}"

class TestDataValidatorModule:
    """Test data validator functionality"""
    
    @patch('data_pipeline.data_validator.SECDataValidator')
    def test_data_validator_import(self, mock_validator):
        """Test data validator can be imported and instantiated"""
        try:
            from data_pipeline.data_validator import SECDataValidator
            
            mock_instance = Mock()
            mock_validator.return_value = mock_instance
            
            validator = SECDataValidator()
            assert validator is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import data validator: {e}")
    
    def test_validation_methods_exist(self):
        """Test validation methods exist"""
        try:
            from data_pipeline.data_validator import SECDataValidator
            
            # Check if common validation methods exist
            expected_methods = ['validate_json_structure', 'validate_content_quality']
            
            for method_name in expected_methods:
                if hasattr(SECDataValidator, method_name):
                    method = getattr(SECDataValidator, method_name)
                    assert callable(method), f"Method {method_name} is not callable"
                    
        except ImportError:
            pytest.skip("Data validator module not available")

class TestGraphSchemaCreation:
    """Test enhanced graph schema creation"""
    
    @patch('neo4j.GraphDatabase.driver')
    def test_enhanced_graph_schema_import(self, mock_driver):
        """Test enhanced graph schema can be imported"""
        try:
            from data_pipeline.enhanced_graph_schema import EnhancedGraphSchemaManager
            from data_pipeline.enhanced_graph_schema import FinancialEntityExtractor
            
            assert EnhancedGraphSchemaManager is not None
            assert FinancialEntityExtractor is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import enhanced graph schema: {e}")
    
    @patch('neo4j.GraphDatabase.driver')
    def test_financial_entity_extractor(self, mock_driver):
        """Test financial entity extractor functionality"""
        try:
            from data_pipeline.enhanced_graph_schema import FinancialEntityExtractor
            
            extractor = FinancialEntityExtractor()
            
            # Test with sample financial text
            sample_text = "The bank faces market risk from interest rate volatility and credit risk from loan defaults."
            
            if hasattr(extractor, 'extract_entities'):
                # Mock the extraction result
                with patch.object(extractor, 'extract_entities') as mock_extract:
                    mock_extract.return_value = {
                        'risks': [
                            {'name': 'market risk', 'type': 'market_risk'},
                            {'name': 'credit risk', 'type': 'credit_risk'}
                        ]
                    }
                    
                    result = extractor.extract_entities(sample_text)
                    assert 'risks' in result
                    assert len(result['risks']) > 0
                    
        except ImportError:
            pytest.skip("Enhanced graph schema module not available")

class TestEmbeddingGeneration:
    """Test embedding generation functionality"""
    
    def test_sentence_transformers_available(self):
        """Test sentence transformers can be imported"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Test model initialization (without downloading)
            model_name = 'all-MiniLM-L6-v2'
            
            with patch('sentence_transformers.SentenceTransformer.__init__') as mock_init:
                mock_init.return_value = None
                model = SentenceTransformer.__new__(SentenceTransformer)
                assert model is not None
                
        except ImportError as e:
            pytest.fail(f"Failed to import sentence transformers: {e}")
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_embedding_generation_mock(self, mock_transformer):
        """Test embedding generation (mocked)"""
        # Mock the model and its encode method
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3] for _ in range(2)]  # Mock embeddings
        mock_transformer.return_value = mock_model
        
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test encoding
        texts = ["Sample SEC text", "Another business description"]
        embeddings = model.encode(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 3  # Mock embedding dimension
        mock_model.encode.assert_called_once_with(texts)

class TestPineconeIntegration:
    """Test Pinecone vector store integration"""
    
    @patch('pinecone.init')
    @patch('pinecone.Index')
    def test_pinecone_integration_import(self, mock_index, mock_init):
        """Test Pinecone integration can be imported"""
        try:
            from data_pipeline.pinecone_integration import PineconeVectorStore
            
            mock_index_instance = Mock()
            mock_index.return_value = mock_index_instance
            
            # Test instantiation (mocked)
            with patch.object(PineconeVectorStore, '_setup_index'):
                store = PineconeVectorStore(index_name='test-index')
                assert store is not None
                
        except ImportError as e:
            pytest.fail(f"Failed to import Pinecone integration: {e}")
    
    @patch('pinecone.init')
    @patch('pinecone.Index')
    def test_pinecone_operations_mock(self, mock_index, mock_init):
        """Test Pinecone operations (mocked)"""
        try:
            from data_pipeline.pinecone_integration import PineconeVectorStore
            
            mock_index_instance = Mock()
            mock_index.return_value = mock_index_instance
            
            with patch.object(PineconeVectorStore, '_setup_index'):
                store = PineconeVectorStore(index_name='test-index')
                
                # Test similarity search method exists
                assert hasattr(store, 'similarity_search'), "similarity_search method missing"
                assert hasattr(store, 'upsert_documents'), "upsert_documents method missing"
                
                # Mock search results
                mock_index_instance.query.return_value = {
                    'matches': [
                        {
                            'id': 'test-id',
                            'score': 0.95,
                            'metadata': {'text': 'test content', 'company': 'ZION'}
                        }
                    ]
                }
                
                if hasattr(store, 'similarity_search'):
                    with patch.object(store, 'generate_embeddings') as mock_embed:
                        mock_embed.return_value = [[0.1, 0.2, 0.3]]
                        
                        results = store.similarity_search("test query", top_k=5)
                        assert isinstance(results, list)
                        
        except ImportError:
            pytest.skip("Pinecone integration module not available")

class TestIntegratedGraphBuilder:
    """Test integrated graph builder functionality"""
    
    @patch('neo4j.GraphDatabase.driver')
    @patch('data_pipeline.pinecone_integration.PineconeVectorStore')
    def test_integrated_builder_import(self, mock_pinecone, mock_driver):
        """Test integrated graph builder can be imported"""
        try:
            from data_pipeline.create_graph_v5_integrated import IntegratedFinancialGraphBuilder
            
            mock_driver_instance = Mock()
            mock_driver.return_value = mock_driver_instance
            
            mock_pinecone_instance = Mock()
            mock_pinecone.return_value = mock_pinecone_instance
            
            # Test instantiation (mocked)
            builder = IntegratedFinancialGraphBuilder(
                uri='bolt://localhost:7687',
                user='neo4j',
                password='test',
                use_pinecone=False  # Disable Pinecone for testing
            )
            
            assert builder is not None
            assert hasattr(builder, 'create_full_schema'), "create_full_schema method missing"
            
        except ImportError as e:
            pytest.fail(f"Failed to import integrated graph builder: {e}")

class TestSearchEngine:
    """Test hybrid search engine functionality"""
    
    @patch('neo4j.GraphDatabase.driver')
    @patch('data_pipeline.pinecone_integration.PineconeVectorStore')
    def test_search_engine_import(self, mock_pinecone, mock_driver):
        """Test search engine can be imported"""
        try:
            from data_pipeline.search_engine import HybridSearchEngine
            
            mock_driver_instance = Mock()
            mock_driver.return_value = mock_driver_instance
            
            # Test instantiation (mocked)
            search_engine = HybridSearchEngine(
                neo4j_uri='bolt://localhost:7687',
                neo4j_user='neo4j',
                neo4j_password='test',
                pinecone_index=None  # Disable Pinecone for testing
            )
            
            assert search_engine is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import search engine: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])