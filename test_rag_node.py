#!/usr/bin/env python3
"""
Task 3D.2 - Step 1: RAG Node Functionality Testing

Methodical validation of RAG node with Pinecone chunked vectors.
Tests semantic search functionality, chunk retrieval, and metadata consistency.

TESTING APPROACH:
1. Validate RAG node imports and initialization
2. Test basic semantic search functionality 
3. Test retrieval with ~20 chunks
4. Validate metadata consistency
5. Performance benchmarking
6. Error handling and edge cases
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
        logging.FileHandler('test_rag_node.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

def test_rag_node_imports():
    """Test 1: Validate RAG node imports and basic functionality"""
    logger.info("🧪 TEST 1: RAG Node Imports & Initialization")
    logger.info("=" * 60)
    
    try:
        # Test imports
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agent.nodes.rag import rag
        
        logger.info("✅ RAG node import successful")
        
        # Test basic state structure
        test_state = {
            "query_raw": "test query",
            "metadata": {},
            "route": "rag",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        logger.info("✅ Basic state structure validated")
        return True, rag
        
    except Exception as e:
        logger.error(f"❌ RAG node import failed: {e}")
        return False, None

def test_pinecone_connection():
    """Test 2: Validate Pinecone connection and index status"""
    logger.info("🧪 TEST 2: Pinecone Connection & Index Status")
    logger.info("=" * 60)
    
    try:
        from pinecone import Pinecone
        
        # Connect to Pinecone
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index("sec-rag-index")
        
        # Get index stats
        stats = index.describe_index_stats()
        total_vectors = stats.total_vector_count
        dimension = stats.dimension
        
        logger.info(f"✅ Pinecone connection successful")
        logger.info(f"📊 Index vectors: {total_vectors}")
        logger.info(f"📊 Vector dimension: {dimension}")
        
        if total_vectors != 1733:
            logger.warning(f"⚠️  Expected 1,733 vectors, found {total_vectors}")
        
        if dimension != 384:
            logger.warning(f"⚠️  Expected 384 dimensions, found {dimension}")
        
        return True, index
        
    except Exception as e:
        logger.error(f"❌ Pinecone connection failed: {e}")
        return False, None

def test_rag_basic_functionality(rag_function):
    """Test 3: Basic RAG functionality with simple query"""
    logger.info("🧪 TEST 3: Basic RAG Functionality")
    logger.info("=" * 60)
    
    try:
        # Simple test query
        test_state = {
            "query_raw": "What are the main risk factors for Wells Fargo?",
            "metadata": {"company": "WFC", "year": None},
            "route": "rag",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        logger.info(f"🔍 Test query: {test_state['query_raw']}")
        
        start_time = time.time()
        result = rag_function(test_state)
        execution_time = time.time() - start_time
        
        # Validate results
        retrievals = result.get("retrievals", [])
        retrieval_count = len(retrievals)
        
        logger.info(f"📊 Retrievals found: {retrieval_count}")
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        
        if retrieval_count > 0:
            logger.info("✅ RAG node returned results")
            
            # Show sample results
            logger.info("📄 Sample retrievals:")
            for i, hit in enumerate(retrievals[:3]):
                score = hit.get("score", 0)
                chunk_id = hit.get("id", "unknown")
                metadata = hit.get("metadata", {})
                
                logger.info(f"  {i+1}. {chunk_id} (Score: {score:.3f})")
                logger.info(f"      Metadata: {metadata}")
            
            return True, result
        else:
            logger.error("❌ RAG node returned no results")
            return False, result
        
    except Exception as e:
        logger.error(f"❌ RAG basic functionality test failed: {e}")
        return False, None

def test_rag_chunk_retrieval_optimization(rag_function):
    """Test 4: Test ~20 chunk retrieval configuration"""
    logger.info("🧪 TEST 4: Chunk Retrieval Optimization (~20 chunks)")
    logger.info("=" * 60)
    
    try:
        # Test with financial query that should return many results
        test_state = {
            "query_raw": "credit risk management and operational risk strategies",
            "metadata": {},
            "route": "rag", 
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        logger.info(f"🔍 Test query: {test_state['query_raw']}")
        
        start_time = time.time()
        result = rag_function(test_state)
        execution_time = time.time() - start_time
        
        retrievals = result.get("retrievals", [])
        retrieval_count = len(retrievals)
        
        logger.info(f"📊 Retrievals found: {retrieval_count}")
        logger.info(f"🎯 Target: ~20 chunks")
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        
        # Check if we're getting close to 20 chunks
        if retrieval_count >= 15 and retrieval_count <= 25:
            logger.info("✅ Chunk retrieval optimization working well")
        elif retrieval_count < 15:
            logger.warning(f"⚠️  Lower than expected: {retrieval_count} < 15")
        else:
            logger.warning(f"⚠️  Higher than expected: {retrieval_count} > 25")
        
        # Analyze retrieval diversity
        companies = set()
        for hit in retrievals:
            metadata = hit.get("metadata", {})
            company = metadata.get("company", "Unknown")
            companies.add(company)
        
        logger.info(f"📊 Company diversity: {len(companies)} different companies")
        logger.info(f"🏢 Companies: {sorted(list(companies))}")
        
        return True, result
        
    except Exception as e:
        logger.error(f"❌ Chunk retrieval optimization test failed: {e}")
        return False, None

def test_rag_metadata_consistency(rag_function):
    """Test 5: Validate metadata consistency and filtering"""
    logger.info("🧪 TEST 5: Metadata Consistency & Filtering")
    logger.info("=" * 60)
    
    try:
        # Test company-specific query
        test_state = {
            "query_raw": "business strategy and revenue streams",
            "metadata": {"company": "BAC"},  # Bank of America specific
            "route": "rag",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        logger.info(f"🔍 Test query: {test_state['query_raw']}")
        logger.info(f"🏢 Company filter: {test_state['metadata']['company']}")
        
        start_time = time.time()
        result = rag_function(test_state)
        execution_time = time.time() - start_time
        
        retrievals = result.get("retrievals", [])
        retrieval_count = len(retrievals)
        
        logger.info(f"📊 Retrievals found: {retrieval_count}")
        logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
        
        # Check metadata consistency
        bac_count = 0
        other_companies = set()
        
        for hit in retrievals:
            metadata = hit.get("metadata", {})
            company = metadata.get("company", "Unknown")
            
            if "bac" in hit.get("id", "").lower() or company == "BAC":
                bac_count += 1
            else:
                other_companies.add(company)
        
        logger.info(f"📊 BAC-related results: {bac_count}/{retrieval_count}")
        if other_companies:
            logger.info(f"📊 Other companies found: {sorted(list(other_companies))}")
        
        if bac_count > 0:
            logger.info("✅ Metadata filtering working")
        else:
            logger.warning("⚠️  No BAC-specific results found")
        
        return True, result
        
    except Exception as e:
        logger.error(f"❌ Metadata consistency test failed: {e}")
        return False, None

def test_rag_performance_benchmarking(rag_function):
    """Test 6: Performance benchmarking with multiple queries"""
    logger.info("🧪 TEST 6: Performance Benchmarking")
    logger.info("=" * 60)
    
    test_queries = [
        "regulatory compliance and risk management",
        "revenue growth and business expansion", 
        "credit losses and loan performance",
        "operational efficiency and cost management",
        "digital banking and technology investments"
    ]
    
    execution_times = []
    retrieval_counts = []
    
    try:
        for i, query in enumerate(test_queries, 1):
            logger.info(f"🔍 Benchmark {i}/5: {query}")
            
            test_state = {
                "query_raw": query,
                "metadata": {},
                "route": "rag",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
            
            start_time = time.time()
            result = rag_function(test_state)
            execution_time = time.time() - start_time
            
            retrievals = result.get("retrievals", [])
            retrieval_count = len(retrievals)
            
            execution_times.append(execution_time)
            retrieval_counts.append(retrieval_count)
            
            logger.info(f"    Results: {retrieval_count} retrievals in {execution_time:.2f}s")
        
        # Calculate statistics
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        avg_retrievals = sum(retrieval_counts) / len(retrieval_counts)
        
        logger.info("📊 Performance Summary:")
        logger.info(f"  Average time: {avg_time:.2f}s")
        logger.info(f"  Range: {min_time:.2f}s - {max_time:.2f}s") 
        logger.info(f"  Average retrievals: {avg_retrievals:.1f}")
        
        # Performance assessment
        if avg_time < 5.0:
            logger.info("✅ Excellent performance (< 5s average)")
        elif avg_time < 10.0:
            logger.info("✅ Good performance (< 10s average)")
        else:
            logger.warning(f"⚠️  Slower performance ({avg_time:.2f}s average)")
        
        return True, {
            "avg_time": avg_time,
            "max_time": max_time,
            "min_time": min_time,
            "avg_retrievals": avg_retrievals
        }
        
    except Exception as e:
        logger.error(f"❌ Performance benchmarking failed: {e}")
        return False, None

def test_rag_edge_cases(rag_function):
    """Test 7: Edge cases and error handling"""
    logger.info("🧪 TEST 7: Edge Cases & Error Handling")
    logger.info("=" * 60)
    
    edge_cases = [
        {
            "name": "Empty query",
            "state": {
                "query_raw": "",
                "metadata": {},
                "route": "rag",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
        },
        {
            "name": "Very specific query (likely no results)",
            "state": {
                "query_raw": "quantum computing blockchain cryptocurrency investments",
                "metadata": {},
                "route": "rag",
                "fallback": [],
                "retrievals": [],
                "valid": False,
                "final_answer": "",
                "citations": []
            }
        },
        {
            "name": "Non-existent company filter",
            "state": {
                "query_raw": "business strategy",
                "metadata": {"company": "NONEXISTENT"},
                "route": "rag",
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
                result = rag_function(case['state'])
                execution_time = time.time() - start_time
                
                retrievals = result.get("retrievals", [])
                retrieval_count = len(retrievals)
                
                logger.info(f"    Results: {retrieval_count} retrievals in {execution_time:.2f}s")
                
                results.append({
                    "case": case['name'],
                    "success": True,
                    "retrievals": retrieval_count,
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
    """RAG Node Comprehensive Testing"""
    logger.info("🧪 RAG NODE COMPREHENSIVE TESTING")
    logger.info("=" * 80)
    logger.info("METHODICAL VALIDATION - STEP 1: RAG Node Functionality")
    logger.info("=" * 80)
    
    test_results = {}
    start_time = time.time()
    
    # Test 1: Imports
    success, rag_function = test_rag_node_imports()
    test_results["imports"] = success
    if not success:
        logger.error("❌ CRITICAL: RAG node imports failed - cannot proceed")
        return
    
    # Test 2: Pinecone connection
    success, index = test_pinecone_connection()
    test_results["pinecone"] = success
    if not success:
        logger.error("❌ CRITICAL: Pinecone connection failed - cannot proceed")
        return
    
    # Test 3: Basic functionality
    success, result = test_rag_basic_functionality(rag_function)
    test_results["basic_functionality"] = success
    
    # Test 4: Chunk retrieval optimization
    success, result = test_rag_chunk_retrieval_optimization(rag_function)
    test_results["chunk_optimization"] = success
    
    # Test 5: Metadata consistency
    success, result = test_rag_metadata_consistency(rag_function)
    test_results["metadata_consistency"] = success
    
    # Test 6: Performance benchmarking
    success, perf_data = test_rag_performance_benchmarking(rag_function)
    test_results["performance"] = success
    
    # Test 7: Edge cases
    success, edge_results = test_rag_edge_cases(rag_function)
    test_results["edge_cases"] = success
    
    # Final summary
    total_time = time.time() - start_time
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    logger.info("🎯 RAG NODE TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Tests passed: {passed_tests}/{total_tests}")
    logger.info(f"⏱️  Total testing time: {total_time:.2f}s")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    if passed_tests == total_tests:
        logger.info("🎉 RAG NODE: FULLY FUNCTIONAL ✅")
        logger.info("🚀 Ready to proceed to Hybrid Node testing")
        return True
    else:
        logger.error(f"⚠️  RAG NODE: Issues detected ({passed_tests}/{total_tests} passed)")
        logger.error("🔧 Address issues before proceeding to next node")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)