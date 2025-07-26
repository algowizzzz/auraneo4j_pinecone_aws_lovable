#!/usr/bin/env python3
"""
Business Intelligence Test - Single Query Validation
Test the full pipeline with OpenAI API working
"""

import os
import sys
import time
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def test_business_intelligence():
    """Test full business intelligence pipeline"""
    print("🧠 BUSINESS INTELLIGENCE PIPELINE TEST")
    print("=" * 60)
    
    try:
        # Import and build the agent graph
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agent.graph import build_graph
        
        logger.info("Building LangGraph state machine...")
        graph = build_graph()
        logger.info("✅ Graph compilation successful!")
        
        # Test query focused on Bank of America risk management
        test_query = "Analyze Bank of America's operational risk management framework. What are their key risk controls and mitigation strategies?"
        
        print(f"🔍 Test Query: {test_query}")
        print("-" * 60)
        
        # Execute the agent
        start_time = time.time()
        result = graph.invoke({"query_raw": test_query})
        execution_time = time.time() - start_time
        
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        print()
        
        # Analyze results
        final_answer = result.get("final_answer", "")
        master_answer = result.get("master_answer", "")
        citations = result.get("citations", [])
        tools_used = result.get("tools_used", [])
        retrievals = result.get("retrievals", [])
        route = result.get("route", "")
        
        answer = master_answer if master_answer else final_answer
        
        print("📊 PIPELINE RESULTS:")
        print(f"  Route taken: {route}")
        print(f"  Tools used: {tools_used}")
        print(f"  Retrievals: {len(retrievals)} chunks")
        print(f"  Citations: {len(citations)}")
        print(f"  Answer length: {len(answer)} characters")
        print()
        
        if answer:
            print("✅ GENERATED ANSWER:")
            print("-" * 40)
            print(answer[:500] + "..." if len(answer) > 500 else answer)
            print("-" * 40)
            print()
        
        if citations:
            print("📚 CITATIONS:")
            for i, citation in enumerate(citations[:5], 1):
                print(f"  {i}. {citation}")
            print()
        
        # Success criteria
        success = (
            len(answer) > 100 and
            len(retrievals) > 0 and
            len(tools_used) > 0
        )
        
        if success:
            print("🎉 BUSINESS INTELLIGENCE TEST: SUCCESS!")
            print("✅ Full pipeline working - OpenAI integration successful")
            return True
        else:
            print("⚠️  BUSINESS INTELLIGENCE TEST: PARTIAL SUCCESS")
            print("🔧 Some components may need attention")
            return False
            
    except Exception as e:
        print(f"❌ Business intelligence test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_business_intelligence()
    if success:
        print("\n🚀 Ready for comprehensive E2E testing!")
    else:
        print("\n🔧 Pipeline issues need resolution before full testing")
    exit(0 if success else 1)