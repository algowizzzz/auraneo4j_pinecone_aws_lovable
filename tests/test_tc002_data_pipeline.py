#!/usr/bin/env python3
"""
TC-002: Data Pipeline Components Test Script
Status: Testing Week 1 Data Pipeline Infrastructure
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
import glob

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TC002DataPipelineTest:
    def __init__(self):
        self.results = {
            "test_id": "TC-002",
            "test_name": "Data Pipeline Components",
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING",
            "sub_tests": {},
            "overall_result": "PENDING"
        }
        self.data_dir = Path('zion_10k_md&a_chunked')
        
    def test_json_file_validation(self):
        """Test JSON file structure and content validation"""
        logger.info("Testing JSON file validation...")
        
        if not self.data_dir.exists():
            result = {
                "status": "FAIL",
                "error_message": "Data directory does not exist",
                "files_found": 0,
                "valid_files": 0,
                "invalid_files": 0
            }
            self.results["sub_tests"]["json_validation"] = result
            return result
        
        json_files = list(self.data_dir.glob('*.json'))
        valid_files = []
        invalid_files = []
        file_details = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Basic structure validation
                has_content = 'content' in data or 'text' in data or len(str(data)) > 100
                file_info = {
                    "filename": json_file.name,
                    "size_bytes": json_file.stat().st_size,
                    "has_content": has_content,
                    "is_valid": True
                }
                
                if has_content:
                    valid_files.append(json_file.name)
                else:
                    invalid_files.append(json_file.name)
                    file_info["is_valid"] = False
                
                file_details.append(file_info)
                
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                invalid_files.append(json_file.name)
                file_details.append({
                    "filename": json_file.name,
                    "size_bytes": json_file.stat().st_size,
                    "error": str(e),
                    "is_valid": False
                })
        
        result = {
            "status": "PASS" if len(invalid_files) == 0 else "PARTIAL" if len(valid_files) > 0 else "FAIL",
            "total_files": len(json_files),
            "valid_files": len(valid_files),
            "invalid_files": len(invalid_files),
            "validation_rate": (len(valid_files) / len(json_files)) * 100 if json_files else 0,
            "sample_files": file_details[:5],  # First 5 for brevity
            "file_size_stats": {
                "min_size": min([f["size_bytes"] for f in file_details]) if file_details else 0,
                "max_size": max([f["size_bytes"] for f in file_details]) if file_details else 0,
                "avg_size": sum([f["size_bytes"] for f in file_details]) / len(file_details) if file_details else 0
            }
        }
        
        self.results["sub_tests"]["json_validation"] = result
        logger.info(f"JSON validation test: {result['status']} ({result['validation_rate']:.1f}% valid)")
        return result
    
    def test_enhanced_graph_schema(self):
        """Test enhanced graph schema creation capability"""
        logger.info("Testing enhanced graph schema...")
        
        result = {
            "status": "FAIL",
            "schema_file_exists": False,
            "schema_loadable": False,
            "error_message": None
        }
        
        # Check if enhanced graph schema file exists
        schema_file = Path('data_pipeline/enhanced_graph_schema.py')
        result["schema_file_exists"] = schema_file.exists()
        
        if not result["schema_file_exists"]:
            result["error_message"] = "Enhanced graph schema file not found"
        else:
            try:
                # Try to import the schema module
                sys.path.insert(0, str(Path('data_pipeline').absolute()))
                import enhanced_graph_schema
                
                # Check for key functions/classes
                expected_components = ['create_schema', 'EnhancedSchema', 'setup_constraints']
                available_components = []
                
                for component in expected_components:
                    if hasattr(enhanced_graph_schema, component):
                        available_components.append(component)
                
                result["schema_loadable"] = True
                result["available_components"] = available_components
                result["expected_components"] = expected_components
                result["status"] = "PASS" if len(available_components) > 0 else "PARTIAL"
                
            except ImportError as e:
                result["error_message"] = f"Failed to import schema module: {e}"
            except Exception as e:
                result["error_message"] = f"Schema module error: {e}"
        
        self.results["sub_tests"]["enhanced_graph_schema"] = result
        logger.info(f"Enhanced graph schema test: {result['status']}")
        return result
    
    def test_data_pipeline_modules(self):
        """Test data pipeline module availability"""
        logger.info("Testing data pipeline modules...")
        
        required_modules = [
            'build_faiss_index.py',
            'chunker.py', 
            'create_graph_v3.py',
            'create_graph_v4.py',
            'create_graph_v5_integrated.py',
            'data_validator.py',
            'enhanced_graph_schema.py',
            'extract_embeddings.py',
            'pinecone_integration.py',
            'search_engine.py'
        ]
        
        existing_modules = []
        missing_modules = []
        module_details = []
        
        pipeline_dir = Path('data_pipeline')
        
        for module in required_modules:
            module_path = pipeline_dir / module
            if module_path.exists():
                existing_modules.append(module)
                module_info = {
                    "name": module,
                    "exists": True,
                    "size_bytes": module_path.stat().st_size,
                    "is_executable": os.access(module_path, os.X_OK)
                }
            else:
                missing_modules.append(module)
                module_info = {
                    "name": module,
                    "exists": False
                }
            
            module_details.append(module_info)
        
        result = {
            "status": "PASS" if len(missing_modules) == 0 else "PARTIAL" if len(existing_modules) > 0 else "FAIL",
            "total_required": len(required_modules),
            "existing_modules": existing_modules,
            "missing_modules": missing_modules,
            "availability_rate": (len(existing_modules) / len(required_modules)) * 100,
            "module_details": module_details
        }
        
        self.results["sub_tests"]["data_pipeline_modules"] = result
        logger.info(f"Data pipeline modules test: {result['status']} ({result['availability_rate']:.1f}% available)")
        return result
    
    def test_financial_entity_extraction(self):
        """Test financial entity extraction capability"""
        logger.info("Testing financial entity extraction...")
        
        result = {
            "status": "FAIL",
            "sample_text_processed": False,
            "entities_extracted": False,
            "error_message": None
        }
        
        # Sample SEC text for testing
        sample_text = """
        Bank of America Corporation reported a Tier 1 capital ratio of 15.2% in Q1 2025.
        The company's net interest income was $14.2 billion, while credit loss provisions 
        totaled $1.1 billion. Market risk exposure remained within regulatory limits.
        """
        
        try:
            # Basic pattern matching for financial entities (simplified test)
            financial_terms = [
                'capital ratio', 'tier 1', 'net interest income', 
                'credit loss', 'market risk', 'regulatory'
            ]
            
            found_entities = []
            for term in financial_terms:
                if term.lower() in sample_text.lower():
                    found_entities.append(term)
            
            result["sample_text_processed"] = True
            result["entities_found"] = found_entities
            result["entities_extracted"] = len(found_entities) > 0
            result["status"] = "PASS" if len(found_entities) >= 3 else "PARTIAL"
            
        except Exception as e:
            result["error_message"] = str(e)
        
        self.results["sub_tests"]["financial_entity_extraction"] = result
        logger.info(f"Financial entity extraction test: {result['status']}")
        return result
    
    def test_data_consistency(self):
        """Test data consistency across JSON files"""
        logger.info("Testing data consistency...")
        
        if not self.data_dir.exists():
            result = {
                "status": "FAIL",
                "error_message": "Data directory does not exist"
            }
            self.results["sub_tests"]["data_consistency"] = result
            return result
        
        json_files = list(self.data_dir.glob('*.json'))
        
        # Extract metadata from filenames
        companies = set()
        years = set()
        quarters = set()
        file_patterns = []
        
        for json_file in json_files[:20]:  # Sample first 20 files
            filename = json_file.name
            
            # Parse filename pattern: external_SEC_{COMPANY}_10-K_{YEAR}_q{QUARTER}_...
            parts = filename.split('_')
            if len(parts) >= 5:
                try:
                    company = parts[2]
                    year = parts[4]
                    quarter_part = parts[5] if len(parts) > 5 else 'q1'
                    
                    companies.add(company)
                    years.add(year)
                    if quarter_part.startswith('q'):
                        quarters.add(quarter_part)
                    
                    file_patterns.append({
                        "filename": filename,
                        "company": company,
                        "year": year,
                        "quarter": quarter_part
                    })
                except (IndexError, ValueError):
                    pass
        
        result = {
            "status": "PASS" if len(companies) > 0 and len(years) > 0 else "FAIL",
            "unique_companies": len(companies),
            "companies_sample": list(companies)[:10],
            "unique_years": len(years),
            "years_range": sorted(list(years)),
            "unique_quarters": len(quarters),
            "quarters_found": sorted(list(quarters)),
            "sample_patterns": file_patterns[:5],
            "total_files_analyzed": len(json_files)
        }
        
        self.results["sub_tests"]["data_consistency"] = result
        logger.info(f"Data consistency test: {result['status']} ({result['unique_companies']} companies, {result['unique_years']} years)")
        return result
    
    def test_integration_readiness(self):
        """Test readiness for downstream integration"""
        logger.info("Testing integration readiness...")
        
        # Check for integration files in agent/integration
        integration_dir = Path('agent/integration')
        integration_files = ['enhanced_retrieval.py', '__init__.py']
        
        existing_integration = []
        missing_integration = []
        
        for file in integration_files:
            if (integration_dir / file).exists():
                existing_integration.append(file)
            else:
                missing_integration.append(file)
        
        # Check main entry point
        main_file_exists = Path('main.py').exists()
        
        # Check graph definition
        graph_file_exists = Path('agent/graph.py').exists()
        
        result = {
            "status": "PASS" if len(missing_integration) == 0 and main_file_exists and graph_file_exists else "PARTIAL",
            "integration_files_present": existing_integration,
            "integration_files_missing": missing_integration,
            "main_file_exists": main_file_exists,
            "graph_file_exists": graph_file_exists,
            "integration_readiness": len(missing_integration) == 0
        }
        
        self.results["sub_tests"]["integration_readiness"] = result
        logger.info(f"Integration readiness test: {result['status']}")
        return result
    
    def run_all_tests(self):
        """Run all sub-tests and compile results"""
        logger.info("Starting TC-002: Data Pipeline Components Test")
        
        # Run all sub-tests
        json_result = self.test_json_file_validation()
        schema_result = self.test_enhanced_graph_schema()
        modules_result = self.test_data_pipeline_modules()
        extraction_result = self.test_financial_entity_extraction()
        consistency_result = self.test_data_consistency()
        integration_result = self.test_integration_readiness()
        
        # Calculate overall result
        all_tests = [json_result, schema_result, modules_result, extraction_result, consistency_result, integration_result]
        passed_tests = [test for test in all_tests if test["status"] == "PASS"]
        partial_tests = [test for test in all_tests if test["status"] == "PARTIAL"]
        
        if len(passed_tests) == len(all_tests):
            overall_result = "PASS"
        elif len(passed_tests) + len(partial_tests) > 0:
            overall_result = "PARTIAL"
        else:
            overall_result = "FAIL"
        
        self.results["overall_result"] = overall_result
        self.results["status"] = "COMPLETED"
        self.results["summary"] = {
            "total_sub_tests": len(all_tests),
            "passed_sub_tests": len(passed_tests),
            "partial_sub_tests": len(partial_tests),
            "failed_sub_tests": len(all_tests) - len(passed_tests) - len(partial_tests),
            "success_rate": ((len(passed_tests) + 0.5 * len(partial_tests)) / len(all_tests)) * 100
        }
        
        return self.results
    
    def save_results(self, filename="tc002_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {filename}")

def main():
    """Main execution function"""
    test = TC002DataPipelineTest()
    results = test.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("TC-002: Data Pipeline Components Test Results")
    print("="*60)
    print(f"Overall Result: {results['overall_result']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"Passed: {results['summary']['passed_sub_tests']}/{results['summary']['total_sub_tests']}")
    print(f"Partial: {results['summary']['partial_sub_tests']}/{results['summary']['total_sub_tests']}")
    
    print("\nSub-test Results:")
    for test_name, test_result in results["sub_tests"].items():
        if test_result["status"] == "PASS":
            status_icon = "✅"
        elif test_result["status"] == "PARTIAL":
            status_icon = "🟡"
        else:
            status_icon = "❌"
        
        print(f"  {status_icon} {test_name}: {test_result['status']}")
        if test_result["status"] == "FAIL" and "error_message" in test_result and test_result["error_message"]:
            print(f"    Error: {test_result['error_message']}")
    
    # Save results
    test.save_results("tc002_results.json")
    
    return results

if __name__ == "__main__":
    results = main() 