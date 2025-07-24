#!/usr/bin/env python3
"""
TC-001: Environment & Dependencies Setup Test Script
Status: Testing Infrastructure Requirements
"""

import os
import sys
import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path
import importlib.util

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TC001EnvironmentTest:
    def __init__(self):
        self.results = {
            "test_id": "TC-001",
            "test_name": "Environment & Dependencies Setup",
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING",
            "sub_tests": {},
            "overall_result": "PENDING"
        }
        
    def test_env_variables(self):
        """Test required environment variables"""
        logger.info("Testing environment variables...")
        
        required_vars = [
            'OPENAI_API_KEY',
            'NEO4J_URI', 
            'NEO4J_USERNAME',
            'NEO4J_PASSWORD',
            'PINECONE_API_KEY',
            'PINECONE_ENVIRONMENT'
        ]
        
        missing_vars = []
        present_vars = []
        
        # Check .env file existence
        env_file_exists = os.path.exists('.env')
        
        for var in required_vars:
            if os.getenv(var):
                present_vars.append(var)
            else:
                missing_vars.append(var)
        
        result = {
            "status": "PASS" if len(missing_vars) == 0 else "FAIL",
            "env_file_exists": env_file_exists,
            "present_variables": present_vars,
            "missing_variables": missing_vars,
            "total_required": len(required_vars),
            "total_present": len(present_vars)
        }
        
        self.results["sub_tests"]["environment_variables"] = result
        logger.info(f"Environment variables test: {result['status']}")
        return result
    
    def test_dependencies(self):
        """Test Python dependencies installation"""
        logger.info("Testing dependencies installation...")
        
        required_packages = [
            'langchain',
            'langgraph', 
            'neo4j',
            'pinecone-client',
            'openai',
            'pandas',
            'numpy',
            'faiss-cpu',
            'sentence-transformers'
        ]
        
        installed_packages = []
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                installed_packages.append(package)
            except ImportError:
                missing_packages.append(package)
        
        # Check requirements.txt exists
        req_file_exists = os.path.exists('requirements.txt')
        
        result = {
            "status": "PASS" if len(missing_packages) == 0 else "FAIL",
            "requirements_file_exists": req_file_exists,
            "installed_packages": installed_packages,
            "missing_packages": missing_packages,
            "total_required": len(required_packages),
            "total_installed": len(installed_packages)
        }
        
        self.results["sub_tests"]["dependencies"] = result
        logger.info(f"Dependencies test: {result['status']}")
        return result
    
    def test_neo4j_connectivity(self):
        """Test Neo4j database connectivity"""
        logger.info("Testing Neo4j connectivity...")
        
        result = {
            "status": "FAIL",
            "connection_successful": False,
            "error_message": None,
            "database_accessible": False
        }
        
        try:
            from neo4j import GraphDatabase
            
            uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            username = os.getenv('NEO4J_USERNAME', 'neo4j')
            password = os.getenv('NEO4J_PASSWORD', '')
            
            if not password:
                result["error_message"] = "Neo4j password not provided"
            else:
                driver = GraphDatabase.driver(uri, auth=(username, password))
                
                with driver.session() as session:
                    # Test basic connectivity
                    session.run("RETURN 1 as test")
                    result["connection_successful"] = True
                    result["database_accessible"] = True
                    result["status"] = "PASS"
                
                driver.close()
                
        except ImportError:
            result["error_message"] = "neo4j package not installed"
        except Exception as e:
            result["error_message"] = str(e)
        
        self.results["sub_tests"]["neo4j_connectivity"] = result
        logger.info(f"Neo4j connectivity test: {result['status']}")
        return result
    
    def test_pinecone_connectivity(self):
        """Test Pinecone API connectivity"""
        logger.info("Testing Pinecone connectivity...")
        
        result = {
            "status": "FAIL",
            "api_key_valid": False,
            "connection_successful": False,
            "error_message": None
        }
        
        try:
            import pinecone
            
            api_key = os.getenv('PINECONE_API_KEY')
            environment = os.getenv('PINECONE_ENVIRONMENT')
            
            if not api_key:
                result["error_message"] = "Pinecone API key not provided"
            elif not environment:
                result["error_message"] = "Pinecone environment not provided"
            else:
                # Test API key validity
                pinecone.init(api_key=api_key, environment=environment)
                
                # List indexes to test connectivity
                indexes = pinecone.list_indexes()
                result["api_key_valid"] = True
                result["connection_successful"] = True
                result["status"] = "PASS"
                result["available_indexes"] = indexes
                
        except ImportError:
            result["error_message"] = "pinecone-client package not installed"
        except Exception as e:
            result["error_message"] = str(e)
        
        self.results["sub_tests"]["pinecone_connectivity"] = result
        logger.info(f"Pinecone connectivity test: {result['status']}")
        return result
    
    def test_openai_connectivity(self):
        """Test OpenAI API connectivity"""
        logger.info("Testing OpenAI connectivity...")
        
        result = {
            "status": "FAIL",
            "api_key_valid": False,
            "connection_successful": False,
            "error_message": None
        }
        
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                result["error_message"] = "OpenAI API key not provided"
            else:
                openai.api_key = api_key
                
                # Test API connectivity with a simple request
                response = openai.Model.list()
                result["api_key_valid"] = True
                result["connection_successful"] = True
                result["status"] = "PASS"
                result["models_available"] = len(response.data) > 0
                
        except ImportError:
            result["error_message"] = "openai package not installed"
        except Exception as e:
            result["error_message"] = str(e)
        
        self.results["sub_tests"]["openai_connectivity"] = result
        logger.info(f"OpenAI connectivity test: {result['status']}")
        return result
    
    def test_directory_structure(self):
        """Test directory structure and permissions"""
        logger.info("Testing directory structure and permissions...")
        
        required_dirs = [
            'agent',
            'agent/nodes',
            'agent/integration',
            'data_pipeline',
            'tests',
            'zion_10k_md&a_chunked'
        ]
        
        required_files = [
            'main.py',
            'requirements.txt',
            'agent/__init__.py',
            'agent/graph.py',
            'agent/state.py',
            'data_pipeline/__init__.py'
        ]
        
        existing_dirs = []
        missing_dirs = []
        existing_files = []
        missing_files = []
        
        # Check directories
        for dir_path in required_dirs:
            if os.path.isdir(dir_path):
                existing_dirs.append(dir_path)
            else:
                missing_dirs.append(dir_path)
        
        # Check files
        for file_path in required_files:
            if os.path.isfile(file_path):
                existing_files.append(file_path)
            else:
                missing_files.append(file_path)
        
        # Check data files count
        data_dir = Path('zion_10k_md&a_chunked')
        json_files_count = len(list(data_dir.glob('*.json'))) if data_dir.exists() else 0
        
        result = {
            "status": "PASS" if len(missing_dirs) == 0 and len(missing_files) == 0 else "FAIL",
            "existing_directories": existing_dirs,
            "missing_directories": missing_dirs,
            "existing_files": existing_files,
            "missing_files": missing_files,
            "json_data_files_count": json_files_count,
            "expected_data_files": "125+",
            "directory_structure_complete": len(missing_dirs) == 0,
            "required_files_present": len(missing_files) == 0
        }
        
        self.results["sub_tests"]["directory_structure"] = result
        logger.info(f"Directory structure test: {result['status']}")
        return result
    
    def run_all_tests(self):
        """Run all sub-tests and compile results"""
        logger.info("Starting TC-001: Environment & Dependencies Setup Test")
        
        # Run all sub-tests
        env_result = self.test_env_variables()
        deps_result = self.test_dependencies()
        neo4j_result = self.test_neo4j_connectivity()
        pinecone_result = self.test_pinecone_connectivity()
        openai_result = self.test_openai_connectivity()
        dir_result = self.test_directory_structure()
        
        # Calculate overall result
        all_tests = [env_result, deps_result, neo4j_result, pinecone_result, openai_result, dir_result]
        passed_tests = [test for test in all_tests if test["status"] == "PASS"]
        
        self.results["overall_result"] = "PASS" if len(passed_tests) == len(all_tests) else "PARTIAL" if len(passed_tests) > 0 else "FAIL"
        self.results["status"] = "COMPLETED"
        self.results["summary"] = {
            "total_sub_tests": len(all_tests),
            "passed_sub_tests": len(passed_tests),
            "failed_sub_tests": len(all_tests) - len(passed_tests),
            "success_rate": (len(passed_tests) / len(all_tests)) * 100
        }
        
        return self.results
    
    def save_results(self, filename="tc001_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {filename}")

def main():
    """Main execution function"""
    test = TC001EnvironmentTest()
    results = test.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("TC-001: Environment & Dependencies Setup Test Results")
    print("="*60)
    print(f"Overall Result: {results['overall_result']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"Passed: {results['summary']['passed_sub_tests']}/{results['summary']['total_sub_tests']}")
    
    print("\nSub-test Results:")
    for test_name, test_result in results["sub_tests"].items():
        status_icon = "✅" if test_result["status"] == "PASS" else "❌"
        print(f"  {status_icon} {test_name}: {test_result['status']}")
        if test_result["status"] == "FAIL" and "error_message" in test_result:
            print(f"    Error: {test_result['error_message']}")
    
    # Save results
    test.save_results("tc001_results.json")
    
    return results

if __name__ == "__main__":
    results = main() 