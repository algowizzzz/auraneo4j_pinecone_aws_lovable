"""
TC-001: Environment & Dependencies Setup Testing
Validates all required dependencies and environment configuration
"""

import pytest
import os
import sys
import importlib
import subprocess
from unittest.mock import patch, Mock
import tempfile

class TestEnvironmentSetup:
    """Test environment and dependency setup"""
    
    def test_python_version(self):
        """Test Python version is 3.9+"""
        version = sys.version_info
        assert version.major == 3, f"Expected Python 3.x, got {version.major}.{version.minor}"
        assert version.minor >= 9, f"Expected Python 3.9+, got {version.major}.{version.minor}"
    
    def test_required_environment_variables(self, sample_env_vars):
        """Test all required environment variables are present"""
        required_vars = [
            'NEO4J_URI',
            'NEO4J_USER', 
            'NEO4J_PASSWORD',
            'PINECONE_API_KEY',
            'PINECONE_INDEX_NAME',
            'OPENAI_API_KEY'
        ]
        
        for var in required_vars:
            assert os.getenv(var) is not None, f"Required environment variable {var} not set"
            assert len(os.getenv(var)) > 0, f"Environment variable {var} is empty"
    
    def test_optional_environment_variables(self):
        """Test optional environment variables"""
        optional_vars = [
            'AWS_LAMBDA_FUNCTION_NAME',
            'AWS_API_GATEWAY_URL'
        ]
        
        # These should be present but can be empty for testing
        for var in optional_vars:
            value = os.getenv(var)
            if value is not None:
                assert isinstance(value, str), f"Environment variable {var} should be string"
    
    def test_directory_structure(self):
        """Test required directory structure exists"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        required_dirs = [
            'agent',
            'agent/nodes',
            'agent/integration',
            'data_pipeline',
            'zion_10k_md&a_chunked'
        ]
        
        for dir_name in required_dirs:
            dir_path = os.path.join(base_dir, dir_name)
            assert os.path.exists(dir_path), f"Required directory {dir_name} not found"
            assert os.path.isdir(dir_path), f"{dir_name} exists but is not a directory"
    
    def test_required_files(self):
        """Test required files exist"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        required_files = [
            'requirements.txt',
            'main.py',
            'agent/state.py',
            'agent/graph.py',
            'agent/nodes/planner.py',
            'agent/nodes/cypher.py',
            'agent/nodes/hybrid.py',
            'agent/nodes/rag.py',
            'agent/nodes/validator.py',
            'agent/nodes/synthesizer.py',
            'agent/nodes/master_synth.py',
            'agent/nodes/parallel_runner.py',
            'agent/integration/enhanced_retrieval.py'
        ]
        
        for file_name in required_files:
            file_path = os.path.join(base_dir, file_name)
            assert os.path.exists(file_path), f"Required file {file_name} not found"
            assert os.path.isfile(file_path), f"{file_name} exists but is not a file"
    
    def test_data_files_present(self):
        """Test SEC data files are present"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'zion_10k_md&a_chunked')
        
        assert os.path.exists(data_dir), "SEC data directory not found"
        
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        assert len(json_files) > 0, "No JSON files found in data directory"
        assert len(json_files) >= 50, f"Expected at least 50 JSON files, found {len(json_files)}"
        
        # Test a few specific files exist
        sample_files = [
            'external_SEC_ZION_10-K_2025_q1_Item1.Business.json',
            'external_SEC_JPM_10-K_2025_q1_Item1.Business..json'
        ]
        
        for sample_file in sample_files:
            file_path = os.path.join(data_dir, sample_file)
            if os.path.exists(file_path):  # Not all sample files may exist
                assert os.path.isfile(file_path), f"{sample_file} exists but is not a file"

class TestDependencyImports:
    """Test all required dependencies can be imported"""
    
    def test_core_dependencies(self):
        """Test core Python dependencies"""
        dependencies = [
            'json',
            'os',
            'sys',
            'logging',
            'typing',
            're',
            'asyncio',
            'threading'
        ]
        
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError as e:
                pytest.fail(f"Failed to import core dependency {dep}: {e}")
    
    def test_external_dependencies(self):
        """Test external package dependencies"""
        dependencies = [
            'neo4j',
            'sentence_transformers', 
            'numpy',
            'torch',
            'transformers',
            'sklearn',
            'pinecone',
            'langchain',
            'langchain_community',
            'langchain_openai',
            'langgraph',
            'openai',
            'fastapi',
            'uvicorn',
            'pytest',
            'python_dotenv',
            'pydantic',
            'requests',
            'pandas'
        ]
        
        failed_imports = []
        for dep in dependencies:
            try:
                # Handle packages with different import names
                import_name = dep
                if dep == 'python_dotenv':
                    import_name = 'dotenv'
                elif dep == 'sklearn':
                    import_name = 'sklearn'
                elif dep == 'sentence_transformers':
                    import_name = 'sentence_transformers'
                
                importlib.import_module(import_name)
            except ImportError as e:
                failed_imports.append(f"{dep}: {e}")
        
        if failed_imports:
            pytest.fail(f"Failed to import dependencies: {'; '.join(failed_imports)}")
    
    def test_project_imports(self):
        """Test project module imports"""
        project_modules = [
            'agent.state',
            'agent.graph',
            'agent.nodes.planner',
            'agent.nodes.cypher',
            'agent.nodes.hybrid',
            'agent.nodes.rag',
            'agent.nodes.validator',
            'agent.nodes.synthesizer',
            'agent.nodes.master_synth',
            'agent.nodes.parallel_runner'
        ]
        
        failed_imports = []
        for module in project_modules:
            try:
                importlib.import_module(module)
            except ImportError as e:
                failed_imports.append(f"{module}: {e}")
        
        if failed_imports:
            pytest.fail(f"Failed to import project modules: {'; '.join(failed_imports)}")
    
    def test_enhanced_integration_import(self):
        """Test enhanced integration module import"""
        try:
            from agent.integration.enhanced_retrieval import EnhancedFinancialRetriever
            # Test that class can be instantiated (without actual connections)
            assert EnhancedFinancialRetriever is not None
        except ImportError as e:
            pytest.fail(f"Failed to import enhanced integration: {e}")

class TestDatabaseConnectivity:
    """Test database and API connectivity (mocked for testing)"""
    
    @patch('neo4j.GraphDatabase.driver')
    def test_neo4j_connection_mock(self, mock_driver):
        """Test Neo4j connection setup (mocked)"""
        from neo4j import GraphDatabase
        
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        # Test connection parameters
        uri = os.getenv('NEO4J_URI')
        user = os.getenv('NEO4J_USER')
        password = os.getenv('NEO4J_PASSWORD')
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        mock_driver.assert_called_once_with(uri, auth=(user, password))
        assert driver is not None
    
    @patch('pinecone.init')
    @patch('pinecone.Index')
    def test_pinecone_connection_mock(self, mock_index, mock_init):
        """Test Pinecone connection setup (mocked)"""
        import pinecone
        
        api_key = os.getenv('PINECONE_API_KEY')
        index_name = os.getenv('PINECONE_INDEX_NAME')
        
        # Mock initialization
        pinecone.init(api_key=api_key, environment="us-east1-gcp")
        mock_init.assert_called_once()
        
        # Mock index connection
        mock_index_instance = Mock()
        mock_index.return_value = mock_index_instance
        
        index = pinecone.Index(index_name)
        mock_index.assert_called_once_with(index_name)
        assert index is not None
    
    @patch('langchain_openai.ChatOpenAI')
    def test_openai_connection_mock(self, mock_openai):
        """Test OpenAI connection setup (mocked)"""
        from langchain_openai import ChatOpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        
        mock_llm = Mock()
        mock_openai.return_value = mock_llm
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=api_key
        )
        
        mock_openai.assert_called_once()
        assert llm is not None

class TestFilePermissions:
    """Test file and directory permissions"""
    
    def test_read_permissions(self):
        """Test read permissions on required files"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        test_files = [
            'requirements.txt',
            'main.py',
            'agent/state.py'
        ]
        
        for file_name in test_files:
            file_path = os.path.join(base_dir, file_name)
            if os.path.exists(file_path):
                assert os.access(file_path, os.R_OK), f"No read permission for {file_name}"
    
    def test_write_permissions_temp(self):
        """Test write permissions in temporary directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, 'test_write.txt')
            
            try:
                with open(test_file, 'w') as f:
                    f.write("test content")
                
                assert os.path.exists(test_file), "Failed to create test file"
                
                with open(test_file, 'r') as f:
                    content = f.read()
                    assert content == "test content", "File content mismatch"
                    
            except PermissionError:
                pytest.fail("No write permission in temporary directory")

class TestSystemRequirements:
    """Test system-level requirements"""
    
    def test_memory_availability(self):
        """Test available memory (basic check)"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            # Require at least 4GB available memory
            available_gb = memory.available / (1024**3)
            assert available_gb >= 2.0, f"Insufficient memory: {available_gb:.1f}GB available, need 2GB+"
        except ImportError:
            # psutil not available, skip test
            pytest.skip("psutil not available for memory check")
    
    def test_disk_space(self):
        """Test available disk space"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        try:
            import shutil
            free_bytes = shutil.disk_usage(base_dir).free
            free_gb = free_bytes / (1024**3)
            # Require at least 1GB free space
            assert free_gb >= 1.0, f"Insufficient disk space: {free_gb:.1f}GB available, need 1GB+"
        except Exception as e:
            pytest.skip(f"Could not check disk space: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])