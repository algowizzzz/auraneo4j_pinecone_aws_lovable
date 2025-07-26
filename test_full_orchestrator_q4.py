#!/usr/bin/env python3
"""
Test full orchestrator flow with Q4 Morgan Stanley query to find exactly 
where XX placeholder values get injected
"""

import os
import sys
import time
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Q4 - The actual problematic query from E2E results
Q4_MORGAN_STANLEY = "From Morgan Stanley (MS) 2025 10-K, what are the net revenues, net income, and return on equity for 2024? Also include any forward-looking guidance or outlook mentioned."

def test_full_orchestrator_step_by_step():
    """Run Q4 through full orchestrator and capture each step"""
    print("🔍 FULL ORCHESTRATOR FLOW - Q4 Morgan Stanley Query")
    print("=" * 80)
    print(f"Query: {Q4_MORGAN_STANLEY}")
    print()
    
    try:
        # Import the graph and run it
        from agent.graph import build_graph
        
        # Build the graph
        print("📦 Building LangGraph...")
        graph = build_graph()
        print("✅ Graph built successfully")
        
        # Create initial state
        initial_state = {
            "query_raw": Q4_MORGAN_STANLEY,
            "metadata": {},
            "route": "",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": [],
            "sub_tasks": [],
            "master_answer": ""
        }
        
        print("\n🚀 Starting full orchestrator execution...")
        print("=" * 60)
        
        # Run the graph and capture intermediate states
        start_time = time.time()
        
        result = None
        step_count = 0
        
        for step in graph.stream(initial_state):
            step_count += 1
            node_name = list(step.keys())[0]
            node_output = step[node_name]
            
            print(f"\n📋 STEP {step_count}: {node_name.upper()}")
            print("-" * 40)
            
            # Show key outputs from each step
            if node_name == "planner":
                print(f"  Route: {node_output.get('route')}")
                print(f"  Metadata: {node_output.get('metadata')}")
                print(f"  Fallback: {node_output.get('fallback')}")
                
            elif node_name in ["rag", "cypher", "hybrid"]:
                retrievals = node_output.get('retrievals', [])
                print(f"  Retrievals: {len(retrievals)} chunks found")
                
                # Show first few retrieval previews
                for i, hit in enumerate(retrievals[:3]):
                    chunk_id = hit.get('id', 'unknown')
                    company = hit.get('metadata', {}).get('company', 'Unknown')
                    score = hit.get('score', 0)
                    text_preview = hit.get('text', '')[:80]
                    print(f"    {i+1}. {chunk_id} | {company} | {score:.3f}")
                    print(f"       {text_preview}...")
                
            elif node_name == "validator":
                print(f"  Valid: {node_output.get('valid')}")
                print(f"  Validation decision: {node_output.get('validation_decision', 'N/A')}")
                
            elif node_name in ["synthesizer", "master_synth"]:
                final_answer = node_output.get('final_answer', '') or node_output.get('master_answer', '')
                
                # Check for placeholder values in the answer
                has_placeholders = ("XX" in final_answer or 
                                  "placeholder" in final_answer.lower() or
                                  "$XX" in final_answer)
                
                print(f"  Answer length: {len(final_answer)} characters")
                print(f"  Contains XX placeholders: {'❌ YES' if has_placeholders else '✅ NO'}")
                
                if has_placeholders:
                    print(f"  🚨 PLACEHOLDER DETECTED IN {node_name.upper()}!")
                    # Show context around placeholders
                    import re
                    placeholder_matches = re.finditer(r'XX+', final_answer)
                    for match in placeholder_matches:
                        start = max(0, match.start() - 50)
                        end = min(len(final_answer), match.end() + 50)
                        context = final_answer[start:end]
                        print(f"    Context: ...{context}...")
                
                print(f"  Answer preview: {final_answer[:150]}...")
                
                # Check data coverage section
                if "Data Coverage:" in final_answer:
                    coverage_section = final_answer.split("Data Coverage:")[1][:200]
                    print(f"  📊 Data Coverage: {coverage_section}...")
            
            result = node_output
        
        execution_time = time.time() - start_time
        
        print(f"\n🎯 ORCHESTRATOR EXECUTION COMPLETE")
        print("=" * 60)
        print(f"  Total steps: {step_count}")
        print(f"  Execution time: {execution_time:.2f}s")
        
        # Final analysis
        final_answer = result.get("final_answer", "") or result.get("master_answer", "")
        
        has_placeholders = ("XX" in final_answer or 
                          "placeholder" in final_answer.lower() or
                          "$XX" in final_answer)
        
        print(f"\n🔍 FINAL ANALYSIS:")
        print(f"  Final answer length: {len(final_answer)}")
        print(f"  Contains placeholders: {'❌ YES' if has_placeholders else '✅ NO'}")
        
        if has_placeholders:
            print(f"\n🚨 CONCLUSIVE EVIDENCE: Placeholders found in final orchestrator output!")
            
            # Show all placeholder instances
            import re
            placeholder_matches = list(re.finditer(r'XX+[^X]*', final_answer))
            print(f"  Placeholder instances: {len(placeholder_matches)}")
            
            for i, match in enumerate(placeholder_matches):
                start = max(0, match.start() - 30)
                end = min(len(final_answer), match.end() + 30)
                context = final_answer[start:end]
                print(f"    {i+1}. ...{context}...")
        else:
            print(f"✅ No placeholders found - issue may be intermittent or elsewhere")
        
        return True, result
        
    except Exception as e:
        print(f"❌ Full orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """Run full orchestrator analysis"""
    success, result = test_full_orchestrator_step_by_step()
    
    if success:
        print(f"\n✅ Full orchestrator flow analysis complete")
        print(f"📋 Evidence gathered for Issue #1 root cause identification")
    else:
        print(f"\n❌ Full orchestrator flow analysis failed")

if __name__ == "__main__":
    main()