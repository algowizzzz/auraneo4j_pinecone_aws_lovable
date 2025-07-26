#!/usr/bin/env python3
"""
Comprehensive Planner Analysis - Identify Holistic Issues
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from agent.nodes.planner import planner

def test_planner_routing():
    """Test planner with various query types to identify routing issues"""
    
    test_cases = [
        # TABULAR DATA queries - current issue
        {
            "query": "From BAC 2025 10-K filing, balance sheet table",
            "expected_route": "Should be 'rag' or 'hybrid' to find specific table section",
            "expected_issue": "Currently routes to 'cypher' - doesn't find table content"
        },
        {
            "query": "Show me JPM's income statement numbers from 2024",
            "expected_route": "Should be 'rag' or 'hybrid'",
            "expected_issue": "Likely routes to 'cypher' incorrectly"
        },
        
        # SPECIFIC FACT queries - should work with cypher
        {
            "query": "What is Wells Fargo's CET1 ratio in 2024?",
            "expected_route": "cypher (single fact extraction)",
            "expected_issue": "Should work correctly"
        },
        
        # EXPLANATORY queries - should use hybrid
        {
            "query": "Explain BAC's risk management strategy",
            "expected_route": "hybrid (explanation/summary)",
            "expected_issue": "May incorrectly route to cypher"
        },
        
        # COMPARATIVE queries - should use hybrid/multi
        {
            "query": "Compare GS and MS revenue trends",
            "expected_route": "hybrid or multi (comparison)",
            "expected_issue": "May not handle comparison properly"
        },
        
        # OPEN-ENDED queries - should use rag
        {
            "query": "What are the main banking industry trends?",
            "expected_route": "rag (open-ended, no specific company)",
            "expected_issue": "Should work correctly"
        },
        
        # SECTION-SPECIFIC queries - core issue
        {
            "query": "From MS 2025 MD&A section, what are key highlights?",
            "expected_route": "Should be 'rag' or 'hybrid' to find MD&A section",
            "expected_issue": "May route to cypher and miss section content"
        }
    ]
    
    print("🔍 COMPREHENSIVE PLANNER ANALYSIS")
    print("=" * 60)
    
    routing_issues = []
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        print(f"\n{i}. Testing: {query[:60]}...")
        
        # Test the planner
        state = {"query_raw": query}
        try:
            result = planner(state)
            
            route = result.get("route", "unknown")
            metadata = result.get("metadata", {})
            fallback = result.get("fallback", [])
            
            print(f"   Route: {route}")
            print(f"   Company: {metadata.get('company', 'Not detected')}")
            print(f"   Year: {metadata.get('year', 'Not detected')}")
            print(f"   Fallback: {fallback}")
            print(f"   Expected: {test_case['expected_route']}")
            print(f"   Issue: {test_case['expected_issue']}")
            
            # Analyze if routing seems problematic
            if "cypher" in route and ("table" in query.lower() or "section" in query.lower()):
                routing_issues.append({
                    "query": query,
                    "issue": "Cypher route for section/table query - likely wrong",
                    "route": route
                })
            
        except Exception as e:
            print(f"   ERROR: {e}")
            routing_issues.append({
                "query": query,
                "issue": f"Planner failed: {e}",
                "route": "error"
            })
    
    return routing_issues

def analyze_routing_logic():
    """Analyze the routing logic rules for systemic issues"""
    
    print("\n🔍 ROUTING LOGIC ANALYSIS")
    print("=" * 40)
    
    issues_identified = [
        {
            "issue": "Overly Aggressive Cypher Routing",
            "description": "Rule 1 prefers cypher for 'specific fact, figure, or extract' but tabular data queries need semantic search first",
            "examples": ["balance sheet table", "income statement", "cash flow statement"],
            "fix_needed": "Distinguish between single facts vs. tabular/section data"
        },
        {
            "issue": "Section-Specific Query Handling",
            "description": "Queries asking for specific sections (MD&A, Risk Factors) should use semantic search to locate the section",
            "examples": ["MD&A section", "risk factors section", "business overview"],
            "fix_needed": "Route section queries to RAG/hybrid for semantic section finding"
        },
        {
            "issue": "Table/Tabular Data Recognition",
            "description": "Table queries need semantic search to find table sections, not structured Cypher queries",
            "examples": ["balance sheet table", "financial highlights", "key metrics table"],
            "fix_needed": "Add tabular data detection and route to RAG/hybrid"
        },
        {
            "issue": "Multi-step Query Handling",
            "description": "Some queries need multiple steps: 1) Find section 2) Extract data. Current routing doesn't handle this",
            "examples": ["From balance sheet, show assets", "In MD&A section, find revenue discussion"],
            "fix_needed": "Better support for multi-step retrieval workflows"
        },
        {
            "issue": "Fallback Strategy",
            "description": "Current fallback is generic. Should be context-aware based on query type",
            "examples": ["Table query fails in cypher → should try RAG", "Explanation fails in RAG → should try hybrid"],
            "fix_needed": "Intelligent fallback based on query type and failure mode"
        }
    ]
    
    for i, issue in enumerate(issues_identified, 1):
        print(f"\n{i}. {issue['issue']}")
        print(f"   Problem: {issue['description']}")
        print(f"   Examples: {', '.join(issue['examples'])}")
        print(f"   Fix Needed: {issue['fix_needed']}")
    
    return issues_identified

def main():
    """Run comprehensive planner analysis"""
    
    print("🧪 COMPREHENSIVE PLANNER ANALYSIS")
    print("Identifying systemic routing issues beyond just balance sheet queries")
    print()
    
    # Test actual routing behavior
    routing_issues = test_planner_routing()
    
    # Analyze routing logic
    logic_issues = analyze_routing_logic()
    
    print("\n" + "="*60)
    print("📊 ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"\n🔍 Routing Issues Found: {len(routing_issues)}")
    for issue in routing_issues:
        print(f"   • {issue['issue']} (Route: {issue['route']})")
    
    print(f"\n🧠 Logic Issues Identified: {len(logic_issues)}")
    for issue in logic_issues:
        print(f"   • {issue['issue']}")
    
    print("\n💡 KEY SYSTEMIC PROBLEMS:")
    print("   1. Over-reliance on Cypher for 'specific' queries")
    print("   2. Poor handling of section-specific requests")
    print("   3. No tabular data detection logic")
    print("   4. Generic fallback strategy")
    print("   5. Missing multi-step query workflow support")
    
    print("\n🛠️  COMPREHENSIVE FIX NEEDED:")
    print("   • Enhanced query classification (fact vs table vs section vs explanation)")
    print("   • Better semantic understanding of query intent")
    print("   • Context-aware fallback strategies")  
    print("   • Multi-step workflow routing")
    print("   • Tabular data specific handling")

if __name__ == "__main__":
    main()