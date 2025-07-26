#!/usr/bin/env python3
"""
Test Planner and Synthesizer nodes with Q1 and Q4 problematic queries
"""

import os
import sys
import time
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The actual problematic queries from E2E results
Q1_GOLDMAN_SACHS = "From Goldman Sachs (GS) 2025 10-K filing, what are the total assets, total deposits, and shareholders' equity as of year-end? Provide the specific balance sheet figures and any notable changes mentioned."

Q4_MORGAN_STANLEY = "From Morgan Stanley (MS) 2025 10-K, what are the net revenues, net income, and return on equity for 2024? Also include any forward-looking guidance or outlook mentioned."

def test_planner_with_problematic_queries():
    """Test Planner node with Q1 and Q4"""
    print("🧪 Testing Planner Node with Q1 (Goldman Sachs) and Q4 (Morgan Stanley)")
    print("=" * 70)
    
    try:
        from agent.nodes.planner import planner
        
        # Test Q1 - Goldman Sachs
        print("\n📋 Q1 - Goldman Sachs Query:")
        print(f"Query: {Q1_GOLDMAN_SACHS}")
        
        state_q1 = {
            "query_raw": Q1_GOLDMAN_SACHS,
            "metadata": {},
            "route": "",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        start_time = time.time()
        result_q1 = planner(state_q1)
        execution_time = time.time() - start_time
        
        print(f"✅ Q1 Planner Results in {execution_time:.2f}s:")
        print(f"  Route: {result_q1.get('route')}")
        print(f"  Metadata: {result_q1.get('metadata')}")
        print(f"  Fallback: {result_q1.get('fallback')}")
        print(f"  Sub-tasks: {result_q1.get('sub_tasks', [])}")
        
        # Test Q4 - Morgan Stanley
        print(f"\n📋 Q4 - Morgan Stanley Query:")
        print(f"Query: {Q4_MORGAN_STANLEY}")
        
        state_q4 = {
            "query_raw": Q4_MORGAN_STANLEY,
            "metadata": {},
            "route": "",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        start_time = time.time()
        result_q4 = planner(state_q4)
        execution_time = time.time() - start_time
        
        print(f"✅ Q4 Planner Results in {execution_time:.2f}s:")
        print(f"  Route: {result_q4.get('route')}")
        print(f"  Metadata: {result_q4.get('metadata')}")
        print(f"  Fallback: {result_q4.get('fallback')}")
        print(f"  Sub-tasks: {result_q4.get('sub_tasks', [])}")
        
        return True, result_q1, result_q4
        
    except Exception as e:
        print(f"❌ Planner test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_synthesizer_with_sample_data():
    """Test Synthesizer with sample retrieved data to check for placeholder generation"""
    print("\n🧪 Testing Synthesizer Node with Sample Retrieved Data")
    print("=" * 70)
    
    try:
        from agent.nodes.synthesizer import synthesizer
        
        # Create mock retrieved data for Q4 Morgan Stanley
        mock_ms_retrievals = [
            {
                "id": "ms_10k_20240222_chunk_24",
                "text": "Morgan Stanley reported strong financial performance with net revenues increasing year-over-year. Our business divisions continued to show resilience in challenging market conditions.",
                "score": 0.85,
                "metadata": {"company": "MS", "year": "2024", "form_type": "10K"}
            },
            {
                "id": "ms_10k_20240222_chunk_19", 
                "text": "The firm maintained disciplined expense management while investing in technology and talent acquisition. Return on equity remained at competitive levels compared to industry peers.",
                "score": 0.80,
                "metadata": {"company": "MS", "year": "2024", "form_type": "10K"}
            }
        ]
        
        # Test Q4 synthesis
        print(f"\n📋 Q4 - Morgan Stanley Synthesis Test:")
        
        state_q4 = {
            "query_raw": Q4_MORGAN_STANLEY,
            "metadata": {"company": "MS", "year": "2025"},
            "route": "synthesizer",
            "retrievals": mock_ms_retrievals,
            "valid": True,
            "final_answer": "",
            "citations": []
        }
        
        start_time = time.time()
        result_q4 = synthesizer(state_q4)
        execution_time = time.time() - start_time
        
        final_answer = result_q4.get("final_answer", "")
        
        print(f"✅ Q4 Synthesizer Results in {execution_time:.2f}s:")
        print(f"📄 Final Answer Preview: {final_answer[:200]}...")
        
        # Check for placeholder values
        has_placeholders = ("XX" in final_answer or 
                          "placeholder" in final_answer.lower() or
                          "$XX" in final_answer)
        
        print(f"🔍 Contains placeholders: {'❌ YES' if has_placeholders else '✅ NO'}")
        
        # Check data coverage reporting
        if "Data Coverage:" in final_answer:
            coverage_section = final_answer.split("Data Coverage:")[1][:100]
            print(f"📊 Data Coverage: {coverage_section}")
        
        return True, result_q4
        
    except Exception as e:
        print(f"❌ Synthesizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """Run Planner and Synthesizer tests"""
    print("🔍 PLANNER & SYNTHESIZER TESTING - Q1 & Q4 PROBLEMATIC QUERIES")
    print("=" * 80)
    
    # Test Planner
    planner_success, q1_plan, q4_plan = test_planner_with_problematic_queries()
    
    # Test Synthesizer  
    synth_success, q4_synth = test_synthesizer_with_sample_data()
    
    # Summary
    print(f"\n🎯 PLANNER & SYNTHESIZER TEST SUMMARY")
    print("=" * 50)
    
    planner_status = "✅ PASS" if planner_success else "❌ FAIL"
    synth_status = "✅ PASS" if synth_success else "❌ FAIL"
    
    print(f"  PLANNER: {planner_status}")
    print(f"  SYNTHESIZER: {synth_status}")
    
    if planner_success and synth_success:
        print(f"\n✅ Both nodes functional - analyzing for root causes...")
    else:
        print(f"\n⚠️  Issues found in planner/synthesizer nodes")

if __name__ == "__main__":
    main()