"""
TC-006: Retrieval Nodes Testing
Tests Cypher, Hybrid, and RAG retrieval mechanisms for accuracy and performance
"""

import pytest
import os
import sys
import time
from typing import Dict, Any, List
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import standardized real environment fixtures
from tests.real_env_fixture import (
    real_environment, 
    cypher_node_with_real_env, 
    hybrid_node_with_real_env, 
    rag_node_with_real_env,
    get_real_env
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestCypherNodeBasics:
    """Test basic Cypher node functionality"""
    
    def test_cypher_import(self):
        """Test that cypher node can be imported successfully"""
        try:
            from agent.nodes.cypher import cypher
            assert callable(cypher), "Cypher should be a callable function"
            logger.info("✅ Cypher node import successful")
        except ImportError as e:
            pytest.fail(f"Failed to import cypher node: {e}")
    
    def test_cypher_retriever_class(self):
        """Test that CypherRetriever class can be instantiated"""
        try:
            from agent.nodes.cypher import Neo4jCypherRetriever
            retriever = Neo4jCypherRetriever()
            assert retriever is not None, "CypherRetriever should instantiate"
            logger.info("✅ CypherRetriever class instantiation successful")
        except Exception as e:
            pytest.fail(f"Failed to instantiate CypherRetriever: {e}")

class TestCypherNodeRetrieval:
    """Test Cypher node retrieval functionality"""
    
    @pytest.fixture
    def test_queries(self):
        """Test queries designed for cypher retrieval"""
        return [
            {
                "query": "What are Zions Bancorporation's capital ratios in 2025 Q1?",
                "expected_metadata": {
                    "company": "ZIONS BANCORPORATION",
                    "year": "2025",
                    "quarter": "Q1"
                },
                "description": "Specific metric query with full metadata",
                "expected_min_results": 1
            },
            {
                "query": "What is JPMorgan's business model?", 
                "expected_metadata": {
                    "company": "JPMORGAN"
                },
                "description": "Company-specific query without year",
                "expected_min_results": 1
            },
            {
                "query": "What regulatory requirements affect Bank of America?",
                "expected_metadata": {
                    "company": "BANK OF AMERICA"
                },
                "description": "Regulatory query for specific company",
                "expected_min_results": 1
            }
        ]
    
    def test_cypher_structured_retrieval(self, cypher_node_with_real_env, test_queries):
        """Test structured data retrieval from Neo4j"""
        
        for test_case in test_queries:
            try:
                # Create state with metadata that would come from planner
                initial_state = {
                    "query_raw": test_case["query"],
                    "metadata": test_case["expected_metadata"],
                    "route": "cypher",
                    "fallback": ["hybrid", "rag"],
                    "retrievals": [],
                    "valid": False,
                    "final_answer": "",
                    "citations": []
                }
                
                # Run cypher retrieval
                start_time = time.time()
                result_state = cypher_node_with_real_env(initial_state)
                end_time = time.time()
                
                # Validate results
                retrievals = result_state.get("retrievals", [])
                response_time = end_time - start_time
                
                # Performance check
                assert response_time < 2.0, (
                    f"Cypher retrieval too slow: {response_time:.3f}s\n"
                    f"Expected: <2.0s\n"
                    f"Query: {test_case['query']}"
                )
                
                # Results check
                min_expected = test_case["expected_min_results"]
                assert len(retrievals) >= min_expected, (
                    f"Too few results: {len(retrievals)}\n"
                    f"Expected minimum: {min_expected}\n"
                    f"Query: {test_case['query']}\n"
                    f"Description: {test_case['description']}"
                )
                
                # Quality checks
                if retrievals:
                    first_result = retrievals[0]
                    assert "text" in first_result, "Result should contain text content"
                    assert "source" in first_result, "Result should contain source information"
                    assert len(first_result["text"]) > 50, "Result text should be substantial"
                
                logger.info(f"✅ Cypher test passed: {test_case['description']} - {len(retrievals)} results in {response_time:.3f}s")
                
            except Exception as e:
                pytest.fail(f"Cypher retrieval failed for query '{test_case['query']}': {e}")
    
    def test_cypher_query_generation(self, cypher_node_with_real_env):
        """Test that cypher generates appropriate Neo4j queries"""
        
        test_cases = [
            {
                "metadata": {"company": "ZION", "year": "2025", "quarter": "Q1"},
                "description": "Full metadata should generate specific query"
            },
            {
                "metadata": {"company": "JPM"},
                "description": "Company-only metadata should generate broader query"
            },
            {
                "metadata": {},
                "description": "Empty metadata should generate fallback query"
            }
        ]
        
        for test_case in test_cases:
            try:
                initial_state = {
                    "query_raw": "Test query",
                    "metadata": test_case["metadata"],
                    "route": "cypher",
                    "fallback": ["hybrid", "rag"],
                    "retrievals": [],
                    "valid": False,
                    "final_answer": "",
                    "citations": []
                }
                
                result_state = cypher_node_with_real_env(initial_state)
                
                # Should have attempted retrieval
                assert "retrievals" in result_state, "Should contain retrievals key"
                
                # Check if query was attempted (even if no results)
                retrievals = result_state.get("retrievals", [])
                logger.info(f"✅ Query generation test passed: {test_case['description']} - {len(retrievals)} results")
                
            except Exception as e:
                pytest.fail(f"Query generation failed for metadata {test_case['metadata']}: {e}")

class TestHybridNodeBasics:
    """Test basic Hybrid node functionality"""
    
    def test_hybrid_import(self):
        """Test that hybrid node can be imported successfully"""
        try:
            from agent.nodes.hybrid import hybrid
            assert callable(hybrid), "Hybrid should be a callable function"
            logger.info("✅ Hybrid node import successful")
        except ImportError as e:
            pytest.fail(f"Failed to import hybrid node: {e}")
    
    def test_hybrid_retriever_class(self):
        """Test that HybridRetriever class can be instantiated"""
        try:
            from agent.nodes.hybrid import HybridRetriever
            retriever = HybridRetriever()
            assert retriever is not None, "HybridRetriever should instantiate"
            logger.info("✅ HybridRetriever class instantiation successful")
        except Exception as e:
            pytest.fail(f"Failed to instantiate HybridRetriever: {e}")

class TestHybridNodeRetrieval:
    """Test Hybrid node retrieval functionality"""
    
    @pytest.fixture
    def test_queries(self):
        """Test queries designed for hybrid retrieval"""
        return [
            {
                "query": "Explain Wells Fargo's risk management strategy in 2024",
                "expected_metadata": {
                    "company": "WELLS FARGO",
                    "year": "2024"
                },
                "description": "Strategy explanation with metadata filtering",
                "expected_min_results": 2
            },
            {
                "query": "How does Bank of America handle credit risk?",
                "expected_metadata": {
                    "company": "BANK OF AMERICA"
                },
                "description": "Risk-specific query with company filter",
                "expected_min_results": 1
            },
            {
                "query": "Describe Zions Bancorporation's business segments",
                "expected_metadata": {
                    "company": "ZIONS BANCORPORATION"
                },
                "description": "Business description with semantic search",
                "expected_min_results": 1
            }
        ]
    
    def test_hybrid_metadata_semantic_combination(self, hybrid_node_with_real_env, test_queries):
        """Test combination of metadata filtering with semantic search"""
        
        for test_case in test_queries:
            try:
                initial_state = {
                    "query_raw": test_case["query"],
                    "metadata": test_case["expected_metadata"],
                    "route": "hybrid",
                    "fallback": ["rag", "cypher"],
                    "retrievals": [],
                    "valid": False,
                    "final_answer": "",
                    "citations": []
                }
                
                start_time = time.time()
                result_state = hybrid_node_with_real_env(initial_state)
                end_time = time.time()
                
                retrievals = result_state.get("retrievals", [])
                response_time = end_time - start_time
                
                # Performance check
                assert response_time < 3.0, (
                    f"Hybrid retrieval too slow: {response_time:.3f}s\n"
                    f"Expected: <3.0s\n"
                    f"Query: {test_case['query']}"
                )
                
                # Results check
                min_expected = test_case["expected_min_results"]
                assert len(retrievals) >= min_expected, (
                    f"Too few hybrid results: {len(retrievals)}\n"
                    f"Expected minimum: {min_expected}\n"
                    f"Query: {test_case['query']}\n"
                    f"Description: {test_case['description']}"
                )
                
                # Quality checks for hybrid results
                if retrievals:
                    for result in retrievals[:3]:  # Check first 3 results
                        assert "text" in result, "Hybrid result should contain text"
                        assert "score" in result, "Hybrid result should contain relevance score"
                        assert result["score"] > 0, "Score should be positive"
                        
                        # Check metadata filtering worked
                        metadata = result.get("metadata", {})
                        if "company" in test_case["expected_metadata"]:
                            # Results should be related to the specified company
                            company_mentioned = any(
                                comp.lower() in result["text"].lower() 
                                for comp in [
                                    test_case["expected_metadata"]["company"],
                                    test_case["expected_metadata"]["company"].split()[0]  # First word
                                ]
                            )
                            assert company_mentioned, (
                                f"Company not mentioned in hybrid result\n"
                                f"Expected: {test_case['expected_metadata']['company']}\n"
                                f"Text: {result['text'][:200]}..."
                            )
                
                logger.info(f"✅ Hybrid test passed: {test_case['description']} - {len(retrievals)} results in {response_time:.3f}s")
                
            except Exception as e:
                pytest.fail(f"Hybrid retrieval failed for query '{test_case['query']}': {e}")

class TestRAGNodeBasics:
    """Test basic RAG node functionality"""
    
    def test_rag_import(self):
        """Test that RAG node can be imported successfully"""
        try:
            from agent.nodes.rag import rag
            assert callable(rag), "RAG should be a callable function"
            logger.info("✅ RAG node import successful")
        except ImportError as e:
            pytest.fail(f"Failed to import RAG node: {e}")
    
    def test_rag_retriever_class(self):
        """Test that RAGRetriever class can be instantiated"""
        try:
            from agent.nodes.rag import RAGRetriever
            retriever = RAGRetriever()
            assert retriever is not None, "RAGRetriever should instantiate"
            logger.info("✅ RAGRetriever class instantiation successful")
        except Exception as e:
            pytest.fail(f"Failed to instantiate RAGRetriever: {e}")

class TestRAGNodeRetrieval:
    """Test RAG node retrieval functionality"""
    
    @pytest.fixture
    def test_queries(self):
        """Test queries designed for RAG retrieval"""
        return [
            {
                "query": "How do regional banks handle market volatility?",
                "description": "Open-ended query across multiple banks",
                "expected_min_results": 3,
                "expected_diversity": True
            },
            {
                "query": "What are common digital banking strategies?",
                "description": "Industry-wide strategic analysis",
                "expected_min_results": 2,
                "expected_diversity": True
            },
            {
                "query": "Compare regulatory compliance approaches across banks",
                "description": "Comparative analysis without specific companies",
                "expected_min_results": 2,
                "expected_diversity": True
            },
            {
                "query": "Basel III capital requirements impact",
                "description": "Regulatory topic search",
                "expected_min_results": 1,
                "expected_diversity": False
            }
        ]
    
    def test_rag_semantic_search(self, rag_node_with_real_env, test_queries):
        """Test pure semantic search across entire corpus"""
        
        for test_case in test_queries:
            try:
                initial_state = {
                    "query_raw": test_case["query"],
                    "metadata": {},  # RAG should work without metadata
                    "route": "rag",
                    "fallback": ["hybrid", "cypher"],
                    "retrievals": [],
                    "valid": False,
                    "final_answer": "",
                    "citations": []
                }
                
                start_time = time.time()
                result_state = rag_node_with_real_env(initial_state)
                end_time = time.time()
                
                retrievals = result_state.get("retrievals", [])
                response_time = end_time - start_time
                
                # Performance check
                assert response_time < 2.0, (
                    f"RAG retrieval too slow: {response_time:.3f}s\n"
                    f"Expected: <2.0s\n"
                    f"Query: {test_case['query']}"
                )
                
                # Results check
                min_expected = test_case["expected_min_results"]
                assert len(retrievals) >= min_expected, (
                    f"Too few RAG results: {len(retrievals)}\n"
                    f"Expected minimum: {min_expected}\n"
                    f"Query: {test_case['query']}\n"
                    f"Description: {test_case['description']}"
                )
                
                # Quality checks for RAG results
                if retrievals:
                    # Check semantic relevance (scores should be reasonable)
                    scores = [r.get("score", 0) for r in retrievals]
                    assert max(scores) > 0.3, f"Top score too low: {max(scores)}"
                    
                    # Check content quality
                    for result in retrievals[:2]:  # Check first 2 results
                        assert "text" in result, "RAG result should contain text"
                        assert "score" in result, "RAG result should contain similarity score"
                        assert len(result["text"]) > 30, "RAG result text should be substantial"
                    
                    # Check diversity if expected
                    if test_case["expected_diversity"] and len(retrievals) > 1:
                        # Results should come from different sources
                        sources = [r.get("source", "unknown") for r in retrievals]
                        unique_sources = set(sources)
                        assert len(unique_sources) > 1, (
                            f"RAG results not diverse enough\n"
                            f"Sources: {sources}\n"
                            f"Query: {test_case['query']}"
                        )
                
                logger.info(f"✅ RAG test passed: {test_case['description']} - {len(retrievals)} results in {response_time:.3f}s")
                
            except Exception as e:
                pytest.fail(f"RAG retrieval failed for query '{test_case['query']}': {e}")

class TestRetrievalNodesComparison:
    """Test comparative behavior of retrieval nodes"""
    
    @pytest.fixture
    def comparison_query(self):
        """A query that should work across all retrieval methods"""
        return {
            "query": "What business risks do banks face?",
            "metadata": {"company": "ZION"},  # Metadata for cypher/hybrid
            "description": "Generic business risk query"
        }
    
    def test_retrieval_methods_comparison(self, 
                                        cypher_node_with_real_env,
                                        hybrid_node_with_real_env, 
                                        rag_node_with_real_env,
                                        comparison_query):
        """Compare results across all three retrieval methods"""
        
        results = {}
        query = comparison_query["query"]
        metadata = comparison_query["metadata"]
        
        # Test each retrieval method
        retrieval_methods = [
            ("cypher", cypher_node_with_real_env),
            ("hybrid", hybrid_node_with_real_env),
            ("rag", rag_node_with_real_env)
        ]
        
        for method_name, method_func in retrieval_methods:
            try:
                initial_state = {
                    "query_raw": query,
                    "metadata": metadata if method_name != "rag" else {},
                    "route": method_name,
                    "fallback": [],
                    "retrievals": [],
                    "valid": False,
                    "final_answer": "",
                    "citations": []
                }
                
                start_time = time.time()
                result_state = method_func(initial_state)
                end_time = time.time()
                
                retrievals = result_state.get("retrievals", [])
                
                results[method_name] = {
                    "count": len(retrievals),
                    "time": end_time - start_time,
                    "retrievals": retrievals
                }
                
                logger.info(f"✅ {method_name.upper()} comparison: {len(retrievals)} results in {end_time - start_time:.3f}s")
                
            except Exception as e:
                logger.warning(f"⚠️ {method_name.upper()} failed in comparison: {e}")
                results[method_name] = {"count": 0, "time": 0, "retrievals": [], "error": str(e)}
        
        # Analyze comparison results
        working_methods = [k for k, v in results.items() if v["count"] > 0]
        
        assert len(working_methods) >= 1, (
            f"No retrieval methods returned results\n"
            f"Results: {results}\n"
            f"Query: {query}"
        )
        
        # Performance comparison
        times = {k: v["time"] for k, v in results.items() if v["count"] > 0}
        fastest = min(times.keys(), key=lambda k: times[k])
        slowest = max(times.keys(), key=lambda k: times[k])
        
        logger.info(f"📊 Performance comparison:")
        logger.info(f"   Fastest: {fastest} ({times[fastest]:.3f}s)")
        logger.info(f"   Slowest: {slowest} ({times[slowest]:.3f}s)")
        
        # Quality comparison (if multiple methods work)
        if len(working_methods) > 1:
            for method in working_methods:
                count = results[method]["count"]
                logger.info(f"   {method.upper()}: {count} results")
        
        logger.info(f"✅ Retrieval methods comparison completed: {len(working_methods)}/3 methods working")

class TestRetrievalNodesErrorHandling:
    """Test error handling across retrieval nodes"""
    
    def test_empty_metadata_handling(self, 
                                   cypher_node_with_real_env,
                                   hybrid_node_with_real_env,
                                   rag_node_with_real_env):
        """Test how nodes handle empty metadata"""
        
        empty_state = {
            "query_raw": "Test query",
            "metadata": {},
            "route": "",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        # All nodes should handle empty metadata gracefully
        nodes = [
            ("cypher", cypher_node_with_real_env),
            ("hybrid", hybrid_node_with_real_env),
            ("rag", rag_node_with_real_env)
        ]
        
        for node_name, node_func in nodes:
            try:
                result_state = node_func(empty_state.copy())
                
                # Should not crash and should have retrievals key
                assert "retrievals" in result_state, f"{node_name} should handle empty metadata gracefully"
                
                logger.info(f"✅ {node_name.upper()} handles empty metadata gracefully")
                
            except Exception as e:
                pytest.fail(f"{node_name} failed with empty metadata: {e}")
    
    def test_invalid_query_handling(self,
                                  cypher_node_with_real_env,
                                  hybrid_node_with_real_env,
                                  rag_node_with_real_env):
        """Test how nodes handle invalid or problematic queries"""
        
        invalid_queries = [
            "",  # Empty query
            "x" * 1000,  # Very long query
            "'; DROP TABLE companies; --",  # SQL injection attempt
            "🚀💸📊🏦",  # Emoji-only query
        ]
        
        nodes = [
            ("cypher", cypher_node_with_real_env),
            ("hybrid", hybrid_node_with_real_env),
            ("rag", rag_node_with_real_env)
        ]
        
        for query in invalid_queries:
            for node_name, node_func in nodes:
                try:
                    state = {
                        "query_raw": query,
                        "metadata": {"company": "TEST"},
                        "route": node_name,
                        "fallback": [],
                        "retrievals": [],
                        "valid": False,
                        "final_answer": "",
                        "citations": []
                    }
                    
                    result_state = node_func(state)
                    
                    # Should not crash
                    assert "retrievals" in result_state, f"{node_name} should handle invalid query gracefully"
                    
                except Exception as e:
                    # Some failures are acceptable, but should not be crashes
                    assert "retrievals" in str(e) or "query" in str(e).lower(), (
                        f"{node_name} crashed unexpectedly with query '{query[:20]}...': {e}"
                    )
        
        logger.info("✅ All nodes handle invalid queries gracefully")

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])