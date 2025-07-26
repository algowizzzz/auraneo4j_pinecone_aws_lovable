#!/usr/bin/env python3
"""
Test the complete BAC financial query flow with the emergency fix
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from agent.graph import build_graph

def test_bac_financial_performance():
    """Test BAC financial performance query end-to-end"""
    
    print('🧪 Testing BAC Financial Performance Query - Full Orchestrator')
    print('=' * 70)
    
    # Build the agent
    print('🔄 Building SEC Graph Agent...')
    agent = build_graph()
    
    # Test query
    query = "financial performance of BAC balance sheet total assets shareholders equity"
    
    initial_state = {
        "query_raw": query,
        "metadata": {"company": "BAC", "year": "2025"}
    }
    
    print(f'📝 Query: {query}')
    print(f'🎯 Company Filter: BAC')
    print(f'📅 Year Filter: 2025')
    print()
    
    try:
        # Execute the full agent
        result = agent.invoke(initial_state)
        
        # Extract results
        final_answer = result.get("final_answer", "") or result.get("master_answer", "")
        retrievals = result.get("retrievals", [])
        route = result.get("route", "unknown")
        
        print(f'🛣️  Route: {route}')
        print(f'📄 Retrievals: {len(retrievals)}')
        print()
        
        # Check retrieval quality
        chunks_with_text = 0
        total_text_length = 0
        
        for hit in retrievals:
            text = hit.get('text', '')
            if text != 'Content not available' and len(text.strip()) > 10:
                chunks_with_text += 1
                total_text_length += len(text)
        
        print(f'📊 Text Quality Analysis:')
        print(f'   Chunks with text: {chunks_with_text}/{len(retrievals)}')
        print(f'   Total text retrieved: {total_text_length:,} characters')
        print(f'   Avg text per chunk: {total_text_length//max(1,chunks_with_text):,} chars')
        print()
        
        # Analyze the answer
        print(f'💡 Generated Answer:')
        print('-' * 50)
        print(final_answer[:1000] + "..." if len(final_answer) > 1000 else final_answer)
        print('-' * 50)
        print()
        
        # Check for quality indicators
        issues = []
        if "XX" in final_answer or "placeholder" in final_answer.lower():
            issues.append("❌ Contains placeholder values")
        
        if len(final_answer.strip()) < 100:
            issues.append("❌ Answer too short")
        
        if "Content not available" in final_answer:
            issues.append("❌ Contains 'Content not available'")
        
        # Look for financial content
        financial_indicators = []
        answer_lower = final_answer.lower()
        financial_terms = ["assets", "equity", "revenue", "income", "billion", "million", "$"]
        
        for term in financial_terms:
            if term in answer_lower:
                financial_indicators.append(term)
        
        print(f'📈 Quality Assessment:')
        if issues:
            for issue in issues:
                print(f'   {issue}')
        else:
            print('   ✅ No major issues detected')
        
        if financial_indicators:
            print(f'   ✅ Contains financial terms: {", ".join(financial_indicators)}')
        else:
            print('   ⚠️  No financial terms detected')
        
        print()
        
        # Success criteria
        success = (
            chunks_with_text >= 5 and
            len(issues) == 0 and
            len(financial_indicators) >= 2 and
            total_text_length > 10000
        )
        
        if success:
            print('🎉 SUCCESS: Emergency fix resolved the BAC financial query issue!')
            print('✅ Agent can now retrieve and analyze financial data from SEC filings')
        else:
            print('⚠️  PARTIAL SUCCESS: Some improvements but more work needed')
        
        return success
        
    except Exception as e:
        print(f'❌ ERROR: {e}')
        return False

if __name__ == "__main__":
    test_bac_financial_performance()