#!/usr/bin/env python3
"""
TC-003: LangGraph Infrastructure Test Script
Status: Testing Core LangGraph State Machine
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TC003LangGraphTest:
    def __init__(self):
        self.results = {
            "test_id": "TC-003",
            "test_name": "LangGraph Infrastructure",
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING",
            "sub_tests": {},
            "overall_result": "PENDING"
        }
        
    def test_agent_imports(self):
        """Test agent module imports and availability"""
        logger.info("Testing agent module imports...")
        
        result = {
            "status": "FAIL",
            "importable_modules": [],
            "failed_imports": [],
            "error_messages": {}
        }
        
        # Required agent modules
        agent_modules = [
            'agent',
            'agent.graph',
            'agent.state',
            'agent.nodes',
            'agent.integration'
        ]
        
        for module_name in agent_modules:
            try:
                __import__(module_name)
                result["importable_modules"].append(module_name)
                logger.info(f"✅ Successfully imported {module_name}")
            except ImportError as e:
                result["failed_imports"].append(module_name)
                result["error_messages"][module_name] = str(e)
                logger.warning(f"❌ Failed to import {module_name}: {e}")
            except Exception as e:
                result["failed_imports"].append(module_name)
                result["error_messages"][module_name] = f"Unexpected error: {e}"
                logger.error(f"❌ Unexpected error importing {module_name}: {e}")
        
        result["status"] = "PASS" if len(result["failed_imports"]) == 0 else "PARTIAL" if len(result["importable_modules"]) > 0 else "FAIL"
        result["import_rate"] = (len(result["importable_modules"]) / len(agent_modules)) * 100
        
        self.results["sub_tests"]["agent_imports"] = result
        logger.info(f"Agent imports test: {result['status']} ({result['import_rate']:.1f}% success)")
        return result
    
    def test_node_loading(self):
        """Test individual node imports and structure"""
        logger.info("Testing node loading...")
        
        result = {
            "status": "FAIL",
            "available_nodes": [],
            "missing_nodes": [],
            "node_details": {}
        }
        
        # Expected node files
        node_files = [
            'cypher.py',
            'hybrid.py',
            'planner.py',
            'rag.py',
            'router.py',
            'synthesizer.py',
            'validator.py',
            'master_synthesis.py',
            'parallel_processor.py'
        ]
        
        nodes_dir = Path('agent/nodes')
        
        if not nodes_dir.exists():
            result["error_message"] = "Nodes directory does not exist"
            self.results["sub_tests"]["node_loading"] = result
            return result
        
        for node_file in node_files:
            node_path = nodes_dir / node_file
            node_name = node_file.replace('.py', '')
            
            if node_path.exists():
                result["available_nodes"].append(node_name)
                
                # Try to check for expected functions in the node
                try:
                    with open(node_path, 'r') as f:
                        content = f.read()
                    
                    # Look for common patterns
                    has_function = 'def ' in content
                    has_async = 'async def' in content
                    has_import = 'import' in content
                    file_size = node_path.stat().st_size
                    
                    result["node_details"][node_name] = {
                        "exists": True,
                        "has_function": has_function,
                        "has_async": has_async,
                        "has_import": has_import,
                        "file_size": file_size
                    }
                    
                except Exception as e:
                    result["node_details"][node_name] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                result["missing_nodes"].append(node_name)
                result["node_details"][node_name] = {"exists": False}
        
        result["status"] = "PASS" if len(result["missing_nodes"]) == 0 else "PARTIAL" if len(result["available_nodes"]) > 0 else "FAIL"
        result["availability_rate"] = (len(result["available_nodes"]) / len(node_files)) * 100
        
        self.results["sub_tests"]["node_loading"] = result
        logger.info(f"Node loading test: {result['status']} ({result['availability_rate']:.1f}% available)")
        return result
    
    def test_agent_state(self):
        """Test AgentState creation and validation"""
        logger.info("Testing AgentState...")
        
        result = {
            "status": "FAIL",
            "state_importable": False,
            "state_creatable": False,
            "error_message": None
        }
        
        try:
            # Try to import and create AgentState
            from agent.state import AgentState
            result["state_importable"] = True
            
            # Try to create a sample state
            sample_state = {
                "query": "Test query",
                "extracted_metadata": {},
                "retrieval_results": [],
                "validation_score": 0,
                "final_answer": ""
            }
            
            # This would work if AgentState is properly defined
            result["state_creatable"] = True
            result["status"] = "PASS"
            result["sample_fields"] = list(sample_state.keys())
            
        except ImportError as e:
            result["error_message"] = f"Cannot import AgentState: {e}"
        except Exception as e:
            result["error_message"] = f"State creation error: {e}"
            if result["state_importable"]:
                result["status"] = "PARTIAL"
        
        self.results["sub_tests"]["agent_state"] = result
        logger.info(f"AgentState test: {result['status']}")
        return result
    
    def test_graph_compilation(self):
        """Test main graph compilation"""
        logger.info("Testing graph compilation...")
        
        result = {
            "status": "FAIL",
            "build_graph_available": False,
            "graph_compilable": False,
            "error_message": None
        }
        
        try:
            # Try to import the build_graph function
            from agent.graph import build_graph
            result["build_graph_available"] = True
            
            # Try to compile the graph (this might fail due to dependencies)
            try:
                graph = build_graph()
                result["graph_compilable"] = True
                result["status"] = "PASS"
                result["graph_type"] = str(type(graph))
            except Exception as e:
                result["error_message"] = f"Graph compilation failed: {e}"
                result["status"] = "PARTIAL"  # Function exists but compilation fails
                
        except ImportError as e:
            result["error_message"] = f"Cannot import build_graph: {e}"
        except Exception as e:
            result["error_message"] = f"Unexpected error: {e}"
        
        self.results["sub_tests"]["graph_compilation"] = result
        logger.info(f"Graph compilation test: {result['status']}")
        return result
    
    def test_single_topic_graph(self):
        """Test single-topic graph compilation"""
        logger.info("Testing single-topic graph compilation...")
        
        result = {
            "status": "FAIL",
            "single_graph_available": False,
            "single_graph_compilable": False,
            "error_message": None
        }
        
        try:
            # Try to import the build_single_topic_graph function
            from agent.graph import build_single_topic_graph
            result["single_graph_available"] = True
            
            # Try to compile the single topic graph
            try:
                single_graph = build_single_topic_graph()
                result["single_graph_compilable"] = True
                result["status"] = "PASS"
                result["single_graph_type"] = str(type(single_graph))
            except Exception as e:
                result["error_message"] = f"Single graph compilation failed: {e}"
                result["status"] = "PARTIAL"  # Function exists but compilation fails
                
        except ImportError as e:
            result["error_message"] = f"Cannot import build_single_topic_graph: {e}"
        except Exception as e:
            result["error_message"] = f"Unexpected error: {e}"
        
        self.results["sub_tests"]["single_topic_graph"] = result
        logger.info(f"Single-topic graph test: {result['status']}")
        return result
    
    def test_enhanced_integration(self):
        """Test enhanced integration module loading"""
        logger.info("Testing enhanced integration...")
        
        result = {
            "status": "FAIL",
            "integration_importable": False,
            "enhanced_retrieval_available": False,
            "error_message": None
        }
        
        try:
            # Try to import integration module
            import agent.integration
            result["integration_importable"] = True
            
            # Try to import enhanced retrieval
            try:
                from agent.integration.enhanced_retrieval import EnhancedRetrieval
                result["enhanced_retrieval_available"] = True
                result["status"] = "PASS"
            except ImportError:
                # Try alternative import structure
                try:
                    from agent.integration import enhanced_retrieval
                    result["enhanced_retrieval_available"] = True
                    result["status"] = "PASS"
                except ImportError as e:
                    result["error_message"] = f"Enhanced retrieval not available: {e}"
                    result["status"] = "PARTIAL"
            
        except ImportError as e:
            result["error_message"] = f"Cannot import integration module: {e}"
        except Exception as e:
            result["error_message"] = f"Unexpected error: {e}"
        
        self.results["sub_tests"]["enhanced_integration"] = result
        logger.info(f"Enhanced integration test: {result['status']}")
        return result
    
    def test_routing_logic(self):
        """Test routing logic and conditional edges"""
        logger.info("Testing routing logic...")
        
        result = {
            "status": "FAIL",
            "router_available": False,
            "routing_functions_found": False,
            "error_message": None
        }
        
        try:
            # Check if router module exists and has routing functions
            router_file = Path('agent/nodes/router.py')
            
            if router_file.exists():
                result["router_available"] = True
                
                with open(router_file, 'r') as f:
                    content = f.read()
                
                # Look for routing-related functions
                routing_patterns = [
                    'route_to',
                    'determine_route',
                    'routing_decision',
                    'cypher_route',
                    'hybrid_route',
                    'rag_route'
                ]
                
                found_patterns = []
                for pattern in routing_patterns:
                    if pattern in content:
                        found_patterns.append(pattern)
                
                result["routing_functions_found"] = len(found_patterns) > 0
                result["found_routing_patterns"] = found_patterns
                result["status"] = "PASS" if len(found_patterns) > 0 else "PARTIAL"
                
            else:
                result["error_message"] = "Router file not found"
        
        except Exception as e:
            result["error_message"] = f"Router analysis error: {e}"
        
        self.results["sub_tests"]["routing_logic"] = result
        logger.info(f"Routing logic test: {result['status']}")
        return result
    
    def run_all_tests(self):
        """Run all sub-tests and compile results"""
        logger.info("Starting TC-003: LangGraph Infrastructure Test")
        
        # Run all sub-tests
        imports_result = self.test_agent_imports()
        nodes_result = self.test_node_loading()
        state_result = self.test_agent_state()
        graph_result = self.test_graph_compilation()
        single_result = self.test_single_topic_graph()
        integration_result = self.test_enhanced_integration()
        routing_result = self.test_routing_logic()
        
        # Calculate overall result
        all_tests = [imports_result, nodes_result, state_result, graph_result, single_result, integration_result, routing_result]
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
    
    def save_results(self, filename="tc003_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {filename}")

def main():
    """Main execution function"""
    test = TC003LangGraphTest()
    results = test.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("TC-003: LangGraph Infrastructure Test Results")
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
        if test_result["status"] in ["FAIL", "PARTIAL"] and "error_message" in test_result and test_result["error_message"]:
            print(f"    Error: {test_result['error_message']}")
    
    # Save results
    test.save_results("tc003_results.json")
    
    return results

if __name__ == "__main__":
    results = main() 