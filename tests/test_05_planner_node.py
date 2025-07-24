"""
TC-005: Planner Node Testing
Tests the core routing intelligence and metadata extraction of the planner node
"""

import pytest
import os
import sys
from typing import Dict, Any, List
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import standardized real environment fixtures
from tests.real_env_fixture import real_environment, planner_with_real_env, get_real_env

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPlannerNodeBasics:
    """Test basic planner node functionality"""
    
    def test_planner_import(self):
        """Test that planner node can be imported successfully"""
        try:
            from agent.nodes.planner import planner
            assert callable(planner), "Planner should be a callable function"
            logger.info("✅ Planner node import successful")
        except ImportError as e:
            pytest.fail(f"Failed to import planner node: {e}")
    
    def test_agent_state_import(self):
        """Test that AgentState can be imported and used"""
        try:
            from agent.state import AgentState
            
            # Test basic state creation
            test_state = {
                "query_raw": "Test query",
                "metadata": {},
                "route": "",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
            
            # Verify state structure is valid
            assert isinstance(test_state, dict), "AgentState should be dict-like"
            logger.info("✅ AgentState import and creation successful")
            
        except ImportError as e:
            pytest.fail(f"Failed to import AgentState: {e}")

class TestPlannerQueryClassification:
    """Test planner's query classification and routing logic"""
    
    @pytest.fixture
    def test_queries(self):
        """Test queries with expected routing decisions"""
        return [
            {
                "query": "What are Zions Bancorporation's capital ratios in 2025 Q1?",
                "expected_route": "cypher",
                "expected_metadata": {
                    "company": "ZIONS BANCORPORATION",
                    "year": "2025", 
                    "quarter": "Q1"
                },
                "description": "Specific metric query should route to cypher"
            },
            {
                "query": "Explain Bank of America's risk management strategy",
                "expected_route": "rag",
                "expected_metadata": {
                    "company": "BANK OF AMERICA"
                },
                "description": "Strategy explanation without year/quarter should route to RAG"
            },
            {
                "query": "Compare regional banks' competitive positioning",
                "expected_route": "rag", 
                "expected_metadata": {},
                "description": "Comparative analysis should route to RAG"
            },
            {
                "query": "Analyze market risk, credit risk, and operational risk for JPMorgan",
                "expected_route": "multi",
                "expected_metadata": {
                    "company": "JPMORGAN"
                },
                "description": "Multi-topic analysis should route to parallel processing"
            }
        ]
    
    def test_query_routing_basic(self, planner_with_real_env, test_queries):
        """Test basic query routing decisions"""
        
        for test_case in test_queries:
            try:
                # Create initial state
                initial_state = {
                    "query_raw": test_case["query"],
                    "metadata": {},
                    "route": "",
                    "fallback": [],
                    "retrievals": [],
                    "valid": False,
                    "final_answer": "",
                    "citations": []
                }
                
                # Run planner
                result_state = planner_with_real_env(initial_state)
                
                # Validate routing decision
                actual_route = result_state.get("route", "")
                expected_route = test_case["expected_route"]
                
                assert actual_route == expected_route, (
                    f"Query: '{test_case['query']}'\n"
                    f"Expected route: {expected_route}\n"
                    f"Actual route: {actual_route}\n"
                    f"Description: {test_case['description']}"
                )
                
                logger.info(f"✅ Routing test passed: {test_case['description']}")
                
            except Exception as e:
                pytest.fail(f"Planner routing failed for query '{test_case['query']}': {e}")
    
    def test_metadata_extraction(self, planner_with_real_env, test_queries):
        """Test metadata extraction accuracy"""
        
        for test_case in test_queries:
            try:
                initial_state = {
                    "query_raw": test_case["query"],
                    "metadata": {},
                    "route": "",
                    "fallback": [],
                    "retrievals": [],
                    "valid": False,
                    "final_answer": "",
                    "citations": []
                }
                
                result_state = planner_with_real_env(initial_state)
                extracted_metadata = result_state.get("metadata", {})
                expected_metadata = test_case["expected_metadata"]
                
                # Check each expected metadata field
                for key, expected_value in expected_metadata.items():
                    if key == "topics":
                        # Special handling for topic lists
                        extracted_topics = extracted_metadata.get(key, [])
                        assert len(extracted_topics) == len(expected_value), (
                            f"Expected {len(expected_value)} topics, got {len(extracted_topics)}"
                        )
                    else:
                        extracted_value = extracted_metadata.get(key)
                        assert extracted_value == expected_value, (
                            f"Metadata mismatch for key '{key}'\n"
                            f"Expected: {expected_value}\n"
                            f"Actual: {extracted_value}\n"
                            f"Query: {test_case['query']}"
                        )
                
                logger.info(f"✅ Metadata extraction passed for: {test_case['description']}")
                
            except Exception as e:
                pytest.fail(f"Metadata extraction failed for query '{test_case['query']}': {e}")

class TestPlannerFinancialEntityExtraction:
    """Test planner's financial entity recognition"""
    
    @pytest.fixture
    def planner_function(self):
        from agent.nodes.planner import planner
        return planner
    
    @pytest.fixture
    def entity_test_cases(self):
        """Test cases for financial entity extraction"""
        return [
            {
                "query": "What are Wells Fargo's credit risk exposures in 2024?",
                "expected_entities": {
                    "risks": ["credit risk"],
                    "company": "WFC",
                    "year": "2024"
                }
            },
            {
                "query": "How do Basel III requirements affect regional bank capital ratios?",
                "expected_entities": {
                    "regulations": ["Basel III"],
                    "metrics": ["capital ratios"],
                    "scope": "regional banks"
                }
            },
            {
                "query": "Compare loan portfolios and deposit strategies across major banks",
                "expected_entities": {
                    "products": ["loan portfolios", "deposit strategies"],
                    "scope": "major banks"
                }
            },
            {
                "query": "What operational risks does JPMorgan's investment banking division face?",
                "expected_entities": {
                    "risks": ["operational risks"],
                    "business_lines": ["investment banking"],
                    "company": "JPM"
                }
            }
        ]
    
    def test_financial_entity_recognition(self, planner_function, entity_test_cases):
        """Test extraction of financial entities from queries"""
        
        for test_case in entity_test_cases:
            try:
                initial_state = {
                    "query_raw": test_case["query"],
                    "metadata": {},
                    "route": "",
                    "fallback": [],
                    "retrievals": [],
                    "valid": False,
                    "final_answer": "",
                    "citations": []
                }
                
                result_state = planner_function(initial_state)
                extracted_metadata = result_state.get("metadata", {})
                
                # Check for extracted financial entities
                expected_entities = test_case["expected_entities"]
                
                for entity_type, expected_values in expected_entities.items():
                    if entity_type in ["risks", "products", "business_lines", "regulations", "metrics"]:
                        # These should be lists of extracted entities
                        extracted_list = extracted_metadata.get(entity_type, [])
                        
                        for expected_entity in expected_values:
                            # Check if entity or similar concept is extracted
                            found = any(expected_entity.lower() in str(item).lower() 
                                      for item in extracted_list)
                            assert found, (
                                f"Expected entity '{expected_entity}' not found in {entity_type}\n"
                                f"Extracted: {extracted_list}\n"
                                f"Query: {test_case['query']}"
                            )
                    else:
                        # Direct value comparison for company, year, etc.
                        extracted_value = extracted_metadata.get(entity_type)
                        expected_value = expected_values
                        assert extracted_value == expected_value, (
                            f"Entity mismatch for {entity_type}\n"
                            f"Expected: {expected_value}\n"
                            f"Actual: {extracted_value}"
                        )
                
                logger.info(f"✅ Entity extraction passed for: {test_case['query'][:50]}...")
                
            except Exception as e:
                pytest.fail(f"Entity extraction failed for query '{test_case['query']}': {e}")

class TestPlannerMultiTopicDetection:
    """Test planner's multi-topic query handling"""
    
    @pytest.fixture
    def planner_function(self):
        from agent.nodes.planner import planner
        return planner
    
    @pytest.fixture
    def multi_topic_cases(self):
        """Multi-topic test cases"""
        return [
            {
                "query": "Analyze market risk, credit risk, and operational risk for Bank of America",
                "expected_subtasks": 3,
                "expected_topics": ["market risk", "credit risk", "operational risk"],
                "expected_company": "BAC"
            },
            {
                "query": "Compare profitability, efficiency ratios, and capital strength across JPMorgan, Wells Fargo, and Bank of America",
                "expected_subtasks": 9,  # 3 metrics × 3 companies
                "expected_topics": ["profitability", "efficiency ratios", "capital strength"],
                "expected_companies": ["JPM", "WFC", "BAC"]
            },
            {
                "query": "Evaluate regulatory compliance and competitive positioning for regional banks",
                "expected_subtasks": 2,
                "expected_topics": ["regulatory compliance", "competitive positioning"],
                "expected_scope": "regional banks"
            }
        ]
    
    def test_multi_topic_detection(self, planner_function, multi_topic_cases):
        """Test detection and handling of multi-topic queries"""
        
        for test_case in multi_topic_cases:
            try:
                initial_state = {
                    "query_raw": test_case["query"],
                    "metadata": {},
                    "route": "",
                    "fallback": [],
                    "retrievals": [],
                    "valid": False,
                    "final_answer": "",
                    "citations": []
                }
                
                result_state = planner_function(initial_state)
                
                # Should route to multi-topic processing
                assert result_state.get("route") == "multi", (
                    f"Multi-topic query should route to 'multi', got '{result_state.get('route')}'\n"
                    f"Query: {test_case['query']}"
                )
                
                # Check subtask creation
                subtasks = result_state.get("subtasks", [])
                expected_count = test_case["expected_subtasks"]
                
                assert len(subtasks) == expected_count, (
                    f"Expected {expected_count} subtasks, got {len(subtasks)}\n"
                    f"Subtasks: {subtasks}\n"
                    f"Query: {test_case['query']}"
                )
                
                # Validate topic extraction
                extracted_topics = result_state.get("metadata", {}).get("topics", [])
                expected_topics = test_case["expected_topics"]
                
                for expected_topic in expected_topics:
                    found = any(expected_topic.lower() in str(topic).lower() 
                              for topic in extracted_topics)
                    assert found, (
                        f"Expected topic '{expected_topic}' not found\n"
                        f"Extracted topics: {extracted_topics}\n"
                        f"Query: {test_case['query']}"
                    )
                
                logger.info(f"✅ Multi-topic detection passed: {len(subtasks)} subtasks created")
                
            except Exception as e:
                pytest.fail(f"Multi-topic detection failed for query '{test_case['query']}': {e}")

class TestPlannerPerformance:
    """Test planner performance and error handling"""
    
    @pytest.fixture
    def planner_function(self):
        from agent.nodes.planner import planner
        return planner
    
    def test_planner_response_time(self, planner_function):
        """Test planner responds within acceptable time limits"""
        import time
        
        test_queries = [
            "What are Zions Bancorporation's capital ratios?",
            "Explain the competitive landscape for regional banks",
            "Analyze all risk factors for major US banks"
        ]
        
        for query in test_queries:
            initial_state = {
                "query_raw": query,
                "metadata": {},
                "route": "",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
            
            start_time = time.time()
            result_state = planner_function(initial_state)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Should respond within 500ms
            assert response_time < 0.5, (
                f"Planner response time too slow: {response_time:.3f}s\n"
                f"Expected: <0.5s\n"
                f"Query: {query}"
            )
            
            logger.info(f"✅ Response time OK: {response_time:.3f}s for query: {query[:30]}...")
    
    def test_planner_error_handling(self, planner_function):
        """Test planner handles malformed inputs gracefully"""
        
        error_test_cases = [
            {"query_raw": "", "description": "empty query"},
            {"query_raw": None, "description": "null query"},
            {"query_raw": "x" * 10000, "description": "extremely long query"},
            {"query_raw": "'; DROP TABLE companies; --", "description": "injection attempt"},
            {"query_raw": "🚀💸📊🏦", "description": "emoji-only query"}
        ]
        
        for test_case in error_test_cases:
            try:
                initial_state = {
                    "query_raw": test_case["query_raw"],
                    "metadata": {},
                    "route": "",
                    "fallback": [],
                    "retrievals": [],
                    "valid": False,
                    "final_answer": "",
                    "citations": []
                }
                
                result_state = planner_function(initial_state)
                
                # Should have some fallback route assigned
                route = result_state.get("route", "")
                assert route in ["rag", "hybrid", "cypher"], (
                    f"Invalid route '{route}' for {test_case['description']}"
                )
                
                # Should have fallback strategy
                fallback = result_state.get("fallback", [])
                assert len(fallback) > 0, (
                    f"No fallback strategy for {test_case['description']}"
                )
                
                logger.info(f"✅ Error handling passed: {test_case['description']}")
                
            except Exception as e:
                pytest.fail(f"Planner failed to handle {test_case['description']}: {e}")

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])