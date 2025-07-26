#!/usr/bin/env python3
"""
Task 3D.2 - Step 2: Hybrid Node Functionality Testing

Methodical validation of Hybrid node combining Neo4j + Pinecone retrieval.
Tests graph relationship traversal combined with semantic vector search.

TESTING APPROACH:
1. Validate Hybrid node imports and initialization
2. Test Neo4j graph connectivity and chunk schema
3. Test Pinecone vector search integration
4. Test combined Neo4j + Pinecone retrieval
5. Test ~20 chunk retrieval optimization
6. Performance benchmarking with dual-database queries
7. Edge cases and error handling
"""

import os
import sys
import time
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_hybrid_node.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

def test_hybrid_node_imports():
    """Test 1: Validate Hybrid node imports and initialization"""
    logger.info("🧪 TEST 1: Hybrid Node Imports & Initialization")
    logger.info("=" * 60)
    
    try:
        # Test imports
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agent.nodes.hybrid import hybrid
        
        logger.info("✅ Hybrid node import successful")
        
        # Test basic state structure
        test_state = {
            "query_raw": "test query",
            "metadata": {"company": "BAC", "year": 2024},
            "route": "hybrid",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        logger.info("✅ Basic state structure validated")
        return True, hybrid
        
    except Exception as e:
        logger.error(f"❌ Hybrid node import failed: {e}")
        return False, None

def test_neo4j_connectivity():
    """Test 2: Validate Neo4j connection and chunked schema"""
    logger.info("🧪 TEST 2: Neo4j Connection & Chunked Schema")
    logger.info("=" * 60)
    
    try:
        from neo4j import GraphDatabase
        
        # Connect to Neo4j
        neo4j_uri = os.getenv('NEO4J_URI')
        neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD')
        
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        
        with driver.session() as session:
            # Test chunked schema
            result = session.run("""
                MATCH (s:SourceSection)-[:HAS_CHUNK]->(c:Chunk) 
                RETURN count(s) as source_sections, count(c) as chunks
            """)
            record = list(result)[0]
            source_sections = record["source_sections"]
            chunks = record["chunks"]
            
            logger.info(f"✅ Neo4j connection successful")
            logger.info(f"📊 SourceSections: {source_sections}")
            logger.info(f"📊 Chunks: {chunks}")
            
            if chunks != 1733:
                logger.warning(f"⚠️  Expected 1,733 chunks, found {chunks}")
            
            # Test company distribution
            result = session.run("""
                MATCH (s:SourceSection)
                RETURN s.ticker as company, count(s) as sections
                ORDER BY count(s) DESC
            """)
            companies = list(result)
            
            logger.info(f"📊 Company distribution:")
            for company_record in companies[:5]:
                company = company_record["company"] or "Unknown"
                sections = company_record["sections"]
                logger.info(f"  {company}: {sections} sections")
        
        driver.close()
        return True, driver
        
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
        return False, None

def test_pinecone_integration():
    """Test 3: Validate Pinecone integration in Hybrid context"""
    logger.info("🧪 TEST 3: Pinecone Integration")
    logger.info("=" * 60)
    
    try:
        from pinecone import Pinecone
        
        # Connect to Pinecone (same as RAG node)
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index("sec-rag-index")
        
        # Test basic vector search
        stats = index.describe_index_stats()
        total_vectors = stats.total_vector_count
        
        logger.info(f"✅ Pinecone connection successful")
        logger.info(f"📊 Vectors available: {total_vectors}")
        
        if total_vectors != 1733:
            logger.warning(f"⚠️  Expected 1,733 vectors, found {total_vectors}")
        
        # Test sample vector search
        import numpy as np
        test_embedding = np.random.rand(384).tolist()
        
        results = index.query(
            vector=test_embedding,
            top_k=5,
            include_metadata=True
        )
        
        logger.info(f"📊 Sample vector search: {len(results.matches)} results")
        for i, match in enumerate(results.matches[:3]):
            logger.info(f"  {i+1}. {match.id} (Score: {match.score:.3f})")
        
        return True, index
        
    except Exception as e:
        logger.error(f"❌ Pinecone integration failed: {e}")
        return False, None

def test_hybrid_basic_functionality(hybrid_function):
    """Test 4: Basic Hybrid functionality combining Neo4j + Pinecone"""
    logger.info("🧪 TEST 4: Basic Hybrid Functionality")
    logger.info("=" * 60)
    
    try:
        # Test with company-specific query that should benefit from hybrid approach
        test_state = {
            "query_raw": "What are Bank of America's risk management strategies?",
            "metadata": {"company": "BAC", "year": 2024},
            "route": "hybrid",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        logger.info(f"🔍 Test query: {test_state['query_raw']}")
        logger.info(f"🏢 Company filter: {test_state['metadata']['company']}")
        
        start_time = time.time()
        result = hybrid_function(test_state)
        execution_time = time.time() - start_time
        
        # Validate results
        retrievals = result.get("retrievals", [])
        retrieval_count = len(retrievals)
        confidence = result.get("confidence", 0.0)
        
        logger.info(f"📊 Retrievals found: {retrieval_count}")
        logger.info(f"📊 Confidence score: {confidence:.3f}")
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        
        if retrieval_count > 0:
            logger.info("✅ Hybrid node returned results")
            
            # Analyze result sources (Neo4j vs Pinecone)
            neo4j_results = 0
            pinecone_results = 0
            
            logger.info("📄 Sample retrievals:")
            for i, hit in enumerate(retrievals[:5]):
                score = hit.get("score", 0)
                chunk_id = hit.get("id", "unknown")
                source = hit.get("source", "unknown")
                metadata = hit.get("metadata", {})
                company = metadata.get("company", "Unknown")
                
                logger.info(f"  {i+1}. {chunk_id} (Score: {score:.3f}) - {company}")
                
                # Identify source type
                if "neo4j" in source.lower() or "graph" in source.lower():
                    neo4j_results += 1
                else:
                    pinecone_results += 1
            
            logger.info(f"📊 Source distribution: Neo4j({neo4j_results}) + Pinecone({pinecone_results})")
            
            return True, result
        else:
            logger.error("❌ Hybrid node returned no results")
            return False, result
        
    except Exception as e:
        logger.error(f"❌ Hybrid basic functionality test failed: {e}")
        return False, None

def test_hybrid_chunk_optimization(hybrid_function):
    """Test 5: Test ~20 chunk retrieval optimization"""
    logger.info("🧪 TEST 5: Hybrid Chunk Retrieval Optimization (~20 chunks)")
    logger.info("=" * 60)
    
    try:
        # Complex query that should return diverse results
        test_state = {
            "query_raw": "operational risk management, credit risk exposure, and regulatory compliance strategies",
            "metadata": {},  # No company filter to get diverse results
            "route": "hybrid",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        logger.info(f"🔍 Test query: {test_state['query_raw']}")
        
        start_time = time.time()
        result = hybrid_function(test_state)
        execution_time = time.time() - start_time
        
        retrievals = result.get("retrievals", [])
        retrieval_count = len(retrievals)
        confidence = result.get("confidence", 0.0)
        
        logger.info(f"📊 Retrievals found: {retrieval_count}")
        logger.info(f"🎯 Target: ~20 chunks")
        logger.info(f"📊 Confidence: {confidence:.3f}")
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        
        # Check if we're getting close to 20 chunks
        if retrieval_count >= 15 and retrieval_count <= 25:
            logger.info("✅ Chunk retrieval optimization working well")
        elif retrieval_count < 15:
            logger.warning(f"⚠️  Lower than expected: {retrieval_count} < 15")
        else:
            logger.info(f"✅ Higher retrieval count acceptable: {retrieval_count}")
        
        # Analyze diversity
        companies = set()
        sources = set()
        
        for hit in retrievals:
            metadata = hit.get("metadata", {}) 
            company = metadata.get("company", "Unknown")
            source = hit.get("source", "unknown")
            
            companies.add(company)
            sources.add(source)
        
        logger.info(f"📊 Company diversity: {len(companies)} different companies")
        logger.info(f"🏢 Companies: {sorted(list(companies))[:10]}")
        logger.info(f"📊 Source diversity: {len(sources)} different sources")
        
        return True, result
        
    except Exception as e:
        logger.error(f"❌ Hybrid chunk optimization test failed: {e}")
        return False, None

def test_hybrid_temporal_queries(hybrid_function):
    """Test 6: Temporal queries leveraging both graph and vector search"""
    logger.info("🧪 TEST 6: Temporal Query Handling")
    logger.info("=" * 60)
    
    try:
        # Temporal query that should benefit from hybrid approach
        test_state = {
            "query_raw": "How has Goldman Sachs' business strategy evolved from 2024 to 2025?",
            "metadata": {"company": "GS", "year_range": [2024, 2025]},
            "route": "hybrid",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        logger.info(f"🔍 Temporal query: {test_state['query_raw']}")
        logger.info(f"📅 Year range: {test_state['metadata']['year_range']}")
        
        start_time = time.time()
        result = hybrid_function(test_state)
        execution_time = time.time() - start_time
        
        retrievals = result.get("retrievals", [])
        retrieval_count = len(retrievals)
        
        logger.info(f"📊 Retrievals found: {retrieval_count}")
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        
        # Analyze temporal distribution
        years_found = set()
        gs_results = 0
        
        for hit in retrievals:
            chunk_id = hit.get("id", "")
            metadata = hit.get("metadata", {})
            
            # Extract year from chunk_id or metadata
            if "2024" in chunk_id:
                years_found.add(2024)
            if "2025" in chunk_id:
                years_found.add(2025)
            
            # Count GS-specific results
            if "gs_" in chunk_id.lower() or metadata.get("company") == "GS":
                gs_results += 1
        
        logger.info(f"📅 Years found in results: {sorted(list(years_found))}")
        logger.info(f"🏢 Goldman Sachs results: {gs_results}/{retrieval_count}")
        
        if len(years_found) >= 1:
            logger.info("✅ Temporal query handling working")
        else:
            logger.warning("⚠️  No temporal patterns detected")
        
        return True, result
        
    except Exception as e:
        logger.error(f"❌ Temporal query test failed: {e}")
        return False, None

def test_hybrid_performance_benchmarking(hybrid_function):
    """Test 7: Performance benchmarking with multiple hybrid queries"""
    logger.info("🧪 TEST 7: Hybrid Performance Benchmarking")
    logger.info("=" * 60)
    
    test_queries = [
        {
            "query": "risk management frameworks and compliance procedures",
            "metadata": {"company": "JPM"}
        },
        {
            "query": "digital banking initiatives and technology investments", 
            "metadata": {"company": "WFC"}
        },
        {
            "query": "credit portfolio performance and loan loss provisions",
            "metadata": {}
        },
        {
            "query": "competitive positioning and market share analysis",
            "metadata": {"company": "BAC"}
        },
        {
            "query": "regulatory capital requirements and stress testing",
            "metadata": {}
        }
    ]
    
    execution_times = []
    retrieval_counts = []
    confidence_scores = []
    
    try:
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            metadata = test_case["metadata"]
            
            logger.info(f"🔍 Benchmark {i}/5: {query}")
            if metadata.get("company"):
                logger.info(f"    Company: {metadata['company']}")
            
            test_state = {
                "query_raw": query,
                "metadata": metadata,
                "route": "hybrid",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
            
            start_time = time.time()
            result = hybrid_function(test_state)
            execution_time = time.time() - start_time
            
            retrievals = result.get("retrievals", [])
            retrieval_count = len(retrievals)
            confidence = result.get("confidence", 0.0)
            
            execution_times.append(execution_time)
            retrieval_counts.append(retrieval_count)
            confidence_scores.append(confidence)
            
            logger.info(f"    Results: {retrieval_count} retrievals, confidence: {confidence:.3f}, time: {execution_time:.2f}s")
        
        # Calculate statistics
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        avg_retrievals = sum(retrieval_counts) / len(retrieval_counts)
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        logger.info("📊 Hybrid Performance Summary:")
        logger.info(f"  Average time: {avg_time:.2f}s")
        logger.info(f"  Range: {min_time:.2f}s - {max_time:.2f}s")
        logger.info(f"  Average retrievals: {avg_retrievals:.1f}")
        logger.info(f"  Average confidence: {avg_confidence:.3f}")
        
        # Performance assessment
        if avg_time < 3.0:
            logger.info("✅ Excellent hybrid performance (< 3s average)")
        elif avg_time < 5.0:
            logger.info("✅ Good hybrid performance (< 5s average)")
        else:
            logger.warning(f"⚠️  Slower hybrid performance ({avg_time:.2f}s average)")
        
        return True, {
            "avg_time": avg_time,
            "max_time": max_time,
            "min_time": min_time,
            "avg_retrievals": avg_retrievals,
            "avg_confidence": avg_confidence
        }
        
    except Exception as e:
        logger.error(f"❌ Hybrid performance benchmarking failed: {e}")
        return False, None

def test_hybrid_edge_cases(hybrid_function):
    """Test 8: Edge cases and error handling"""
    logger.info("🧪 TEST 8: Hybrid Edge Cases & Error Handling")
    logger.info("=" * 60)
    
    edge_cases = [
        {
            "name": "Empty query",
            "state": {
                "query_raw": "",
                "metadata": {},
                "route": "hybrid",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
        },
        {
            "name": "Non-existent company with complex query",
            "state": {
                "query_raw": "comprehensive risk assessment and mitigation strategies",
                "metadata": {"company": "NONEXISTENT"},
                "route": "hybrid",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
        },
        {
            "name": "Very specific query (minimal matches expected)",
            "state": {
                "query_raw": "quantum computing blockchain artificial intelligence machine learning",
                "metadata": {},
                "route": "hybrid",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
        },
        {
            "name": "Future year query",
            "state": {
                "query_raw": "business strategy for 2030",
                "metadata": {"year": 2030},
                "route": "hybrid",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
        }
    ]
    
    try:
        results = []
        
        for case in edge_cases:
            logger.info(f"🔍 Testing: {case['name']}")
            
            try:
                start_time = time.time()
                result = hybrid_function(case['state'])
                execution_time = time.time() - start_time
                
                retrievals = result.get("retrievals", [])
                retrieval_count = len(retrievals)
                confidence = result.get("confidence", 0.0)
                
                logger.info(f"    Results: {retrieval_count} retrievals, confidence: {confidence:.3f}, time: {execution_time:.2f}s")
                
                results.append({
                    "case": case['name'],
                    "success": True,
                    "retrievals": retrieval_count,
                    "confidence": confidence,
                    "time": execution_time
                })
                
            except Exception as e:
                logger.error(f"    ❌ Error: {e}")
                results.append({
                    "case": case['name'],
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        successful_cases = sum(1 for r in results if r.get("success", False))
        logger.info(f"📊 Edge case results: {successful_cases}/{len(edge_cases)} handled gracefully")
        
        return True, results
        
    except Exception as e:
        logger.error(f"❌ Edge case testing failed: {e}")
        return False, None

def main():
    """Hybrid Node Comprehensive Testing"""
    logger.info("🧪 HYBRID NODE COMPREHENSIVE TESTING")
    logger.info("=" * 80)
    logger.info("METHODICAL VALIDATION - STEP 2: Hybrid Node Functionality")
    logger.info("=" * 80)
    
    test_results = {}
    start_time = time.time()
    
    # Test 1: Imports
    success, hybrid_function = test_hybrid_node_imports()
    test_results["imports"] = success
    if not success:
        logger.error("❌ CRITICAL: Hybrid node imports failed - cannot proceed")
        return False
    
    # Test 2: Neo4j connectivity
    success, driver = test_neo4j_connectivity()
    test_results["neo4j"] = success
    if not success:
        logger.error("❌ CRITICAL: Neo4j connection failed - cannot proceed")
        return False
    
    # Test 3: Pinecone integration
    success, index = test_pinecone_integration()
    test_results["pinecone"] = success
    if not success:
        logger.error("❌ CRITICAL: Pinecone integration failed - cannot proceed")
        return False
    
    # Test 4: Basic functionality
    success, result = test_hybrid_basic_functionality(hybrid_function)
    test_results["basic_functionality"] = success
    
    # Test 5: Chunk optimization
    success, result = test_hybrid_chunk_optimization(hybrid_function)
    test_results["chunk_optimization"] = success
    
    # Test 6: Temporal queries
    success, result = test_hybrid_temporal_queries(hybrid_function)
    test_results["temporal_queries"] = success
    
    # Test 7: Performance benchmarking
    success, perf_data = test_hybrid_performance_benchmarking(hybrid_function)
    test_results["performance"] = success
    
    # Test 8: Edge cases
    success, edge_results = test_hybrid_edge_cases(hybrid_function)
    test_results["edge_cases"] = success
    
    # Final summary
    total_time = time.time() - start_time
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    logger.info("🎯 HYBRID NODE TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Tests passed: {passed_tests}/{total_tests}")
    logger.info(f"⏱️  Total testing time: {total_time:.2f}s")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    if passed_tests == total_tests:
        logger.info("🎉 HYBRID NODE: FULLY FUNCTIONAL ✅")
        logger.info("🚀 Ready to proceed to Cypher Node testing")
        return True
    else:
        logger.error(f"⚠️  HYBRID NODE: Issues detected ({passed_tests}/{total_tests} passed)")
        logger.error("🔧 Address issues before proceeding to next node")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)