#!/usr/bin/env python3
"""
Capture Complete Demo Responses
Execute demo queries end-to-end and capture full responses, document references, and routing details
"""

import os
import sys
import time
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def capture_complete_response(query, scenario_name):
    """Execute a query through the complete pipeline and capture all details"""
    print(f"\n{'='*60}")
    print(f"🎯 {scenario_name}")
    print(f"{'='*60}")
    print(f"Query: {query}")
    
    try:
        # Import required modules
        from agent.nodes.planner import planner
        from agent.nodes.rag import rag
        from agent.nodes.hybrid import hybrid
        from agent.nodes.validator import validator
        from agent.nodes.synthesizer import synthesizer
        
        # Initialize state
        state = {
            "query_raw": query,
            "metadata": {},
            "route": "",
            "fallback": [],
            "retrievals": [],
            "valid": False,
            "final_answer": "",
            "citations": []
        }
        
        # Step 1: Planning
        print(f"\n📋 Step 1: Query Planning")
        start_time = time.time()
        planner_result = planner(state)
        planner_time = time.time() - start_time
        
        route = planner_result.get("route", "unknown")
        metadata = planner_result.get("metadata", {})
        fallback = planner_result.get("fallback", [])
        
        print(f"  ✅ Route Selected: {route}")
        print(f"  📊 Metadata Extracted: {metadata}")
        print(f"  🔄 Fallback Strategy: {fallback}")
        print(f"  ⏱️  Planning Time: {planner_time:.2f}s")
        
        # Step 2: Retrieval
        print(f"\n🔍 Step 2: Information Retrieval")
        retrieval_start = time.time()
        
        if route == "rag":
            retrieval_result = rag(planner_result)
        elif route == "hybrid":
            retrieval_result = hybrid(planner_result)
        else:
            retrieval_result = rag(planner_result)  # Default fallback
        
        retrieval_time = time.time() - retrieval_start
        retrievals = retrieval_result.get("retrievals", [])
        
        print(f"  ✅ Retrieval Method: {route}")
        print(f"  📊 Documents Found: {len(retrievals)}")
        print(f"  ⏱️  Retrieval Time: {retrieval_time:.2f}s")
        
        # Show top results with document references
        if retrievals:
            print(f"\n  📄 Top Document Sources:")
            for i, hit in enumerate(retrievals[:3], 1):
                score = hit.get("score", 0)
                source = hit.get("source", "unknown")
                metadata_hit = hit.get("metadata", {})
                company = metadata_hit.get("company", "Unknown")
                year = metadata_hit.get("year", "Unknown")
                section = metadata_hit.get("section_name", "Unknown")
                
                print(f"    {i}. Score: {score:.3f} | {company} {year} | {section}")
                print(f"       Source: {source}")
                
                # Show excerpt
                text = hit.get("text", "")
                if text:
                    excerpt = text[:150].replace("\\n", " ").strip()
                    print(f"       Excerpt: {excerpt}...")
                print()
        
        # Step 3: Validation  
        print(f"🔍 Step 3: Response Validation")
        validation_start = time.time()
        
        try:
            validation_result = validator(retrieval_result)
            validation_time = time.time() - validation_start
            
            is_valid = validation_result.get("valid", False)
            confidence_scores = validation_result.get("confidence_scores", {})
            
            print(f"  ✅ Validation Result: {'PASSED' if is_valid else 'NEEDS IMPROVEMENT'}")
            print(f"  📊 Confidence Scores: {confidence_scores}")
            print(f"  ⏱️  Validation Time: {validation_time:.2f}s")
            
        except Exception as e:
            print(f"  ⚠️  Validation Error: {e}")
            validation_result = retrieval_result
            validation_time = 0
            is_valid = len(retrievals) > 0
        
        # Step 4: Response Synthesis
        print(f"\n✨ Step 4: Response Generation")
        synthesis_start = time.time()
        
        try:
            final_result = synthesizer(validation_result)
            synthesis_time = time.time() - synthesis_start
            
            final_answer = final_result.get("final_answer", "")
            citations = final_result.get("citations", [])
            
            print(f"  ✅ Response Generated: {len(final_answer)} characters")
            print(f"  📚 Citations: {len(citations)} sources")
            print(f"  ⏱️  Synthesis Time: {synthesis_time:.2f}s")
            
        except Exception as e:
            print(f"  ⚠️  Synthesis Error: {e}")
            synthesis_time = 0
            
            # Generate simple response from retrievals
            if retrievals:
                final_answer = f"Based on {len(retrievals)} SEC filing documents, here are the key findings:\\n\\n"
                for i, hit in enumerate(retrievals[:2], 1):
                    company = hit.get("metadata", {}).get("company", "Unknown")
                    text = hit.get("text", "")[:200]
                    final_answer += f"{i}. {company}: {text}...\\n\\n"
                
                citations = [f"{hit.get('metadata', {}).get('company', 'Unknown')} {hit.get('metadata', {}).get('year', 'Unknown')} SEC 10-K Filing" 
                           for hit in retrievals[:3]]
            else:
                final_answer = "No relevant information found in SEC filings for this query."
                citations = []
        
        # Calculate total time
        total_time = planner_time + retrieval_time + validation_time + synthesis_time
        
        # Summary
        print(f"\n📊 Complete Response Summary")
        print(f"{'='*60}")
        print(f"Query: {query}")
        print(f"Route: {route}")
        print(f"Documents: {len(retrievals)}")
        print(f"Valid: {is_valid}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"\\nGenerated Response:")
        print(f"{'-'*40}")
        print(final_answer)
        print(f"{'-'*40}")
        print(f"\\nDocument Citations:")
        for i, citation in enumerate(citations[:5], 1):
            print(f"  {i}. {citation}")
        
        # Return structured data
        return {
            "scenario": scenario_name,
            "query": query,
            "route": route,
            "metadata": metadata,
            "fallback": fallback,
            "retrievals_count": len(retrievals),
            "retrievals": retrievals[:5],  # Top 5 for demo
            "response": final_answer,
            "citations": citations,
            "performance": {
                "planning_time": planner_time,
                "retrieval_time": retrieval_time,
                "validation_time": validation_time,
                "synthesis_time": synthesis_time,
                "total_time": total_time
            },
            "validation": {
                "valid": is_valid,
                "confidence_scores": confidence_scores if 'confidence_scores' in locals() else {}
            }
        }
        
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        return {
            "scenario": scenario_name,
            "query": query,
            "error": str(e)
        }

def run_demo_scenarios():
    """Run all demo scenarios and capture complete responses"""
    print("🎬 Capturing Complete Demo Responses")
    print("=" * 70)
    
    # Demo scenarios
    scenarios = [
        {
            "name": "Company Intelligence Analysis",
            "query": "What are Prosperity Bancshares business lines and operations?",
            "business_value": "M&A due diligence and company profiling"
        },
        {
            "name": "Temporal Strategic Evolution",
            "query": "How has Zions Bancorporation business strategy evolved from 2021 to 2025?",
            "business_value": "Investment analysis and strategic trend identification"
        },
        {
            "name": "Competitive Intelligence",
            "query": "What business lines does KeyCorp operate?",
            "business_value": "Market research and competitive positioning"
        }
    ]
    
    demo_results = []
    
    for scenario in scenarios:
        print(f"\\n{'='*20} Processing Scenario {'='*20}")
        result = capture_complete_response(scenario["query"], scenario["name"])
        result["business_value"] = scenario["business_value"]
        demo_results.append(result)
        
        # Brief pause between scenarios
        time.sleep(1)
    
    return demo_results

def save_demo_results(results):
    """Save demo results to files for review"""
    print(f"\\n💾 Saving Demo Results")
    print("=" * 50)
    
    # Save raw data
    results_file = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/demo_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"  ✅ Raw results saved: {results_file}")
    
    # Save formatted summary
    summary_file = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/DEMO_RESULTS_SUMMARY.md"
    
    with open(summary_file, 'w') as f:
        f.write("# Business Demo Results Summary\\n\\n")
        f.write("Complete responses captured from SEC Graph LangGraph Agent\\n\\n")
        
        for i, result in enumerate(results, 1):
            if "error" in result:
                f.write(f"## Scenario {i}: {result['scenario']} - ERROR\\n")
                f.write(f"Error: {result['error']}\\n\\n")
                continue
                
            f.write(f"## Scenario {i}: {result['scenario']}\\n\\n")
            f.write(f"**Query:** {result['query']}\\n\\n")
            f.write(f"**Business Value:** {result['business_value']}\\n\\n")
            f.write(f"**System Response:**\\n")
            f.write(f"- Route: {result['route']}\\n")
            f.write(f"- Documents Found: {result['retrievals_count']}\\n")
            f.write(f"- Response Time: {result['performance']['total_time']:.2f}s\\n")
            f.write(f"- Validation: {'✅' if result['validation']['valid'] else '⚠️'}\\n\\n")
            
            f.write(f"**Generated Response:**\\n")
            f.write(f"```\\n{result['response']}\\n```\\n\\n")
            
            f.write(f"**Document Citations:**\\n")
            for j, citation in enumerate(result['citations'][:3], 1):
                f.write(f"{j}. {citation}\\n")
            f.write("\\n")
            
            f.write(f"**Top Document Sources:**\\n")
            for j, retrieval in enumerate(result['retrievals'][:3], 1):
                metadata = retrieval.get('metadata', {})
                company = metadata.get('company', 'Unknown')
                year = metadata.get('year', 'Unknown')
                section = metadata.get('section_name', 'Unknown')
                score = retrieval.get('score', 0)
                f.write(f"{j}. {company} {year} - {section} (Score: {score:.3f})\\n")
            f.write("\\n---\\n\\n")
    
    print(f"  ✅ Summary saved: {summary_file}")
    
    return results_file, summary_file

if __name__ == "__main__":
    # Run demo scenarios
    results = run_demo_scenarios()
    
    # Save results
    results_file, summary_file = save_demo_results(results)
    
    # Final summary
    print(f"\\n🎯 Demo Capture Complete")
    print("=" * 50)
    successful = sum(1 for r in results if "error" not in r)
    total = len(results)
    
    print(f"  Scenarios Captured: {successful}/{total}")
    print(f"  Results File: {results_file}")
    print(f"  Summary File: {summary_file}")
    
    if successful == total:
        print(f"\\n🚀 All demo scenarios captured successfully!")
        print(f"   Ready to create enhanced business demo script!")
    else:
        print(f"\\n⚠️  Some scenarios had issues - check results for details")