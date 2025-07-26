#!/usr/bin/env python3
"""
Test the RAG node fix for retrieving text content from Neo4j
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from agent.nodes.rag import rag
from agent.state import AgentState

def test_rag_fix():
    """Test BAC query with the fixed RAG node"""
    
    # Test BAC query with the fixed RAG node
    initial_state = {
        'query_raw': 'financial performance of BAC balance sheet income statement',
        'metadata': {'company': 'BAC', 'year': '2025'}
    }

    print('🧪 Testing Fixed RAG Node with BAC Financial Query')
    print('=' * 60)

    # Execute RAG node
    result = rag(initial_state)

    # Analyze results
    retrievals = result.get('retrievals', [])
    print(f'📊 Retrieved {len(retrievals)} chunks')

    # Check for text content
    chunks_with_text = 0
    for i, hit in enumerate(retrievals[:5]):  # Check first 5
        text = hit.get('text', '')
        has_content = text != 'Content not available' and len(text.strip()) > 10
        print(f'   {i+1}. Chunk {hit.get("id", "unknown")[:30]}...: {len(text)} chars, Content: {"✅" if has_content else "❌"}')
        if has_content:
            chunks_with_text += 1
            # Show preview
            print(f'     Preview: {text[:150]}...')
            print()

    print(f'📈 Results: {chunks_with_text}/{min(len(retrievals), 5)} chunks have text content')

    if chunks_with_text > 0:
        print('🎉 SUCCESS: RAG node now retrieves text content from Neo4j!')
        return True
    else:
        print('❌ FAILED: Still no text content retrieved')
        return False

if __name__ == "__main__":
    test_rag_fix()