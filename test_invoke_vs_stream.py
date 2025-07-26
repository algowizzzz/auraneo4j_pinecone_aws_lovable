#!/usr/bin/env python3
"""
Test the difference between graph.invoke() vs graph.stream() to see if
invoke() reproduces the placeholder issue that stream() doesn't show
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Q4 - The actual problematic query from E2E results
Q4_MORGAN_STANLEY = "From Morgan Stanley (MS) 2025 10-K, what are the net revenues, net income, and return on equity for 2024? Also include any forward-looking guidance or outlook mentioned."

def test_graph_invoke():
    """Test with graph.invoke() like the E2E framework uses"""
    print("🔍 TESTING graph.invoke() - E2E Framework Method")
    print("=" * 80)
    print(f"Query: {Q4_MORGAN_STANLEY}")
    print()
    
    try:
        from agent.graph import build_graph
        
        # Build the graph
        print("📦 Building LangGraph...")
        graph = build_graph()
        print("✅ Graph built successfully")
        
        # Create initial state (same as E2E framework)
        initial_state = {"query_raw": Q4_MORGAN_STANLEY}
        
        print("\n🚀 Executing with graph.invoke()...")
        start_time = time.time()
        
        # Use invoke() like the E2E framework
        result = graph.invoke(initial_state)
        
        execution_time = time.time() - start_time
        
        print(f"✅ Execution completed in {execution_time:.2f}s")
        
        # Analyze final result
        final_answer = result.get("final_answer", "") or result.get("master_answer", "")
        route = result.get("route", "unknown")
        retrievals = len(result.get("retrievals", []))
        
        print(f"\n📊 INVOKE() RESULTS:")
        print(f"  Route: {route}")
        print(f"  Retrievals: {retrievals}")
        print(f"  Answer length: {len(final_answer)}")
        
        # Check for placeholder values
        has_placeholders = ("XX" in final_answer or 
                          "placeholder" in final_answer.lower() or
                          "$XX" in final_answer)
        
        print(f"  Contains XX placeholders: {'❌ YES' if has_placeholders else '✅ NO'}")
        
        if has_placeholders:
            print(f"\n🚨 CONCLUSIVE EVIDENCE: Placeholders found with graph.invoke()!")
            
            # Show all placeholder instances
            import re
            placeholder_matches = list(re.finditer(r'XX[^X\s]*', final_answer))
            print(f"  Placeholder instances: {len(placeholder_matches)}")
            
            for i, match in enumerate(placeholder_matches):
                start = max(0, match.start() - 40)
                end = min(len(final_answer), match.end() + 40)
                context = final_answer[start:end]
                print(f"    {i+1}. ...{context}...")
        else:
            print(f"✅ No placeholders found with invoke() either")
        
        print(f"\n📄 Answer preview (first 300 chars):")
        print(f"{final_answer[:300]}...")
        
        return True, result, has_placeholders
        
    except Exception as e:
        print(f"❌ graph.invoke() test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, False

def test_graph_stream():
    """Test with graph.stream() for comparison"""
    print("\n🔍 TESTING graph.stream() - My Previous Method")
    print("=" * 80)
    
    try:
        from agent.graph import build_graph
        
        graph = build_graph()
        initial_state = {"query_raw": Q4_MORGAN_STANLEY}
        
        print("🚀 Executing with graph.stream()...")
        start_time = time.time()
        
        # Use stream() like my previous test
        result = None
        for step in graph.stream(initial_state):
            result = list(step.values())[0]
        
        execution_time = time.time() - start_time
        
        print(f"✅ Execution completed in {execution_time:.2f}s")
        
        # Analyze final result
        final_answer = result.get("final_answer", "") or result.get("master_answer", "")
        
        # Check for placeholder values
        has_placeholders = ("XX" in final_answer or 
                          "placeholder" in final_answer.lower() or
                          "$XX" in final_answer)
        
        print(f"\n📊 STREAM() RESULTS:")
        print(f"  Contains XX placeholders: {'❌ YES' if has_placeholders else '✅ NO'}")
        print(f"  Answer length: {len(final_answer)}")
        
        return True, result, has_placeholders
        
    except Exception as e:  
        print(f"❌ graph.stream() test failed: {e}")
        return False, None, False

def main():
    """Compare invoke() vs stream() methods"""
    print("🎯 COMPARING graph.invoke() vs graph.stream() for Placeholder Generation")
    print("=" * 90)
    
    # Test both methods
    invoke_success, invoke_result, invoke_has_placeholders = test_graph_invoke()
    stream_success, stream_result, stream_has_placeholders = test_graph_stream()
    
    # Summary comparison
    print(f"\n🎯 COMPARISON SUMMARY")
    print("=" * 50)
    print(f"  graph.invoke() placeholders: {'❌ YES' if invoke_has_placeholders else '✅ NO'}")
    print(f"  graph.stream() placeholders: {'❌ YES' if stream_has_placeholders else '✅ NO'}")
    
    if invoke_has_placeholders and not stream_has_placeholders:
        print(f"\n🚨 CONCLUSIVE EVIDENCE FOR ISSUE #1:")
        print(f"  ✅ graph.invoke() generates placeholders")
        print(f"  ✅ graph.stream() does NOT generate placeholders")
        print(f"  📋 Root cause: Difference in graph execution method")
    elif invoke_has_placeholders and stream_has_placeholders:
        print(f"\n📋 Both methods generate placeholders - issue is elsewhere")
    elif not invoke_has_placeholders and not stream_has_placeholders:
        print(f"\n📋 Neither method generates placeholders - issue may be intermittent")
    else:
        print(f"\n📋 Unexpected result pattern - needs further investigation")

if __name__ == "__main__":
    main()