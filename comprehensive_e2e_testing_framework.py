#!/usr/bin/env python3
"""
Business-Focused E2E Testing Framework

Simple script to execute business queries and output responses for evaluation.
Focus: Query → Response pairs for business assessment.
"""

import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import logging
import io
from contextlib import redirect_stdout, redirect_stderr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def business_e2e_testing():
    """Execute business-focused E2E testing"""
    print("🚀 BUSINESS-FOCUSED E2E TESTING")
    print("=" * 80)
    print("SEC GRAPH AGENT - QUERY & RESPONSE EVALUATION")
    print("=" * 80)
    
    try:
        # Import and build the agent graph
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import logging
        from agent.graph import build_graph
        
        logger.info("Building LangGraph state machine...")
        graph = build_graph()
        logger.info("✅ Graph compilation successful!")
        
        def run_agent(query):
            """Execute agent with query and return results"""
            return graph.invoke({"query_raw": query})
        
        # Updated E2E Test Queries (Available Companies Only)
        test_queries = [
            {
                "id": "Q1_BALANCE_SHEET_2025",
                "query": "From Goldman Sachs (GS) 2025 10-K filing, what are the total assets, total deposits, and shareholders' equity as of year-end? Provide the specific balance sheet figures and any notable changes mentioned.",
                "business_context": "Goldman Sachs (GS) 2025 10-K - Balance sheet analysis for total assets, deposits, and shareholders' equity"
            },
            {
                "id": "Q2_MDA_ANALYSIS_2025", 
                "query": "Based on Bank of America (BAC) 2025 10-K MD&A section, what were the key factors that management highlighted as driving their financial performance? Include specific commentary on revenue trends and expense management.",
                "business_context": "Bank of America (BAC) 2025 10-K - Management Discussion & Analysis focusing on revenue trends and expense management"
            },
            {
                "id": "Q3_RISK_FACTORS_2025",
                "query": "What are the primary risk factors disclosed in Wells Fargo (WFC) 2025 10-K filing? Focus on credit risk, operational risk, and any new risk factors identified for 2025.",
                "business_context": "Wells Fargo (WFC) 2025 10-K - Risk factor analysis covering credit, operational, and new 2025 risks"
            },
            {
                "id": "Q4_FINANCIAL_METRICS_2025",
                "query": "From Morgan Stanley (MS) 2025 10-K, what are the net revenues, net income, and return on equity for 2024? Also include any forward-looking guidance or outlook mentioned.",
                "business_context": "Morgan Stanley (MS) 2025 10-K - Key financial metrics including net revenues, net income, and ROE"
            },
            {
                "id": "Q5_CAPITAL_LIQUIDITY_2025",
                "query": "According to Truist Financial (TFC) 2025 10-K filing, what are their Tier 1 capital ratio, liquidity coverage ratio, and any regulatory capital requirements mentioned? Include management's commentary on capital adequacy.",
                "business_context": "Truist Financial (TFC) 2025 10-K - Capital ratios, liquidity coverage, and regulatory requirements"
            }
        ]
        
        results = []
        detailed_results = []
        
        print(f"📋 Testing {len(test_queries)} business queries...")
        print()
        
        for i, test_query in enumerate(test_queries, 1):
            query_id = test_query["id"]
            query_text = test_query["query"]
            business_context = test_query["business_context"]
            
            print(f"🔍 QUERY {i}/5: {query_id}")
            print(f"Business Context: {business_context}")
            print("-" * 80)
            print(f"QUERY:")
            print(f"{query_text}")
            print("-" * 80)

            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            # Execute the agent
            start_time = time.time()
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    result = run_agent(query_text)
                
                execution_time = time.time() - start_time
                execution_minutes = execution_time / 60
                
                # Extract the response
                final_answer = result.get("final_answer", "No response generated")
                
                print(f"RESPONSE:")
                print(f"{final_answer}")
                print("-" * 80)
                print(f"⏱️ Execution Time: {execution_minutes:.2f} minutes")
                print("=" * 80)
                print()

                # Combine stdout and stderr logs
                stdout_logs = stdout_capture.getvalue()
                stderr_logs = stderr_capture.getvalue()
                logs = ""
                if stdout_logs.strip():
                    logs += f"STDOUT:\n{stdout_logs}\n"
                if stderr_logs.strip():
                    logs += f"STDERR:\n{stderr_logs}"
                logs = logs.strip()
                
                # Store for file output
                results.append({
                    "query_id": query_id,
                    "business_context": business_context,
                    "query": query_text,
                    "response": final_answer,
                    "execution_time_minutes": round(execution_minutes, 2)
                })

                detailed_results.append({
                    "query_id": query_id,
                    "business_context": business_context,
                    "query": query_text,
                    "response": final_answer,
                    "logs": logs,
                    "execution_time_minutes": round(execution_minutes, 2)
                })
                
            except Exception as e:
                error_msg = f"ERROR: {str(e)}"
                # Combine stdout and stderr logs for error case
                stdout_logs = stdout_capture.getvalue()
                stderr_logs = stderr_capture.getvalue()
                logs = ""
                if stdout_logs.strip():
                    logs += f"STDOUT:\n{stdout_logs}\n"
                if stderr_logs.strip():
                    logs += f"STDERR:\n{stderr_logs}"
                logs = logs.strip()
                print(f"RESPONSE:")
                print(f"{error_msg}")
                print("-" * 80)
                print("=" * 80)
                print()
                
                results.append({
                    "query_id": query_id,
                    "business_context": business_context,
                    "query": query_text,
                    "response": error_msg,
                    "execution_time_minutes": 0
                })

                detailed_results.append({
                    "query_id": query_id,
                    "business_context": business_context,
                    "query": query_text,
                    "response": error_msg,
                    "logs": logs,
                    "execution_time_minutes": 0
                })
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        results_file = f"business_e2e_results_{timestamp}.json"
        detailed_results_file = f"business_e2e_detailed_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "total_queries": len(test_queries),
                "results": results
            }, f, indent=2)

        with open(detailed_results_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "total_queries": len(test_queries),
                "results": detailed_results
            }, f, indent=2)
        
        print(f"📁 Results saved to: {results_file}")
        print(f"📁 Detailed logs saved to: {detailed_results_file}")
        print("🎯 Business Evaluation: Review query-response pairs above for business relevance and quality")
        
        return True
        
    except Exception as e:
        logger.error(f"E2E testing failed: {e}")
        return False

if __name__ == "__main__":
    business_e2e_testing()