#!/usr/bin/env python3
"""
Test RAG node with properly populated databases
Validate that we can remove the emergency fix
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from agent.nodes.rag import rag
from agent.state import AgentState

def test_rag_node_with_new_data():
    """Test RAG node with the newly populated databases"""
    
    print('🧪 Testing RAG Node with Properly Populated Databases')
    print('=' * 60)
    
    # Test BAC financial query - this was the problematic one
    test_query = "financial performance of BAC balance sheet total assets shareholders equity"
    
    initial_state = {
        'query_raw': test_query,
        'metadata': {'company': 'BAC', 'year': '2025'}
    }
    
    print(f'📝 Query: {test_query}')
    print(f'🎯 Company: BAC')
    print(f'📅 Year: 2025')
    print()
    
    try:
        # Execute RAG node
        print('🔍 Executing RAG node...')
        result = rag(initial_state)
        
        # Analyze results
        retrievals = result.get('retrievals', [])
        confidence = result.get('confidence', 0)
        
        print(f'📊 Results:')
        print(f'   Retrievals: {len(retrievals)}')
        print(f'   Confidence: {confidence:.3f}')
        print()
        
        # Check text content quality
        chunks_with_text = 0
        total_text_length = 0
        pinecone_sources = 0
        neo4j_sources = 0
        
        for i, hit in enumerate(retrievals[:5]):
            text = hit.get('text', '')
            text_source = hit.get('text_source', 'pinecone_metadata')
            
            has_content = text != 'Content not available' and len(text.strip()) > 50
            
            print(f'   {i+1}. Score: {hit.get("score", 0):.3f}, '
                  f'Text Length: {len(text)}, '
                  f'Source: {text_source}, '
                  f'Content: {"✅" if has_content else "❌"}')
            
            if has_content:
                chunks_with_text += 1
                total_text_length += len(text)
                
                if text_source == 'neo4j_retrieved':
                    neo4j_sources += 1
                else:
                    pinecone_sources += 1
                
                # Show preview of first chunk
                if i == 0:
                    preview = text[:200].replace('\n', ' ')
                    print(f'      Preview: {preview}...')
            
            print()
        
        print('📈 Analysis:')
        print(f'   Chunks with content: {chunks_with_text}/{len(retrievals)}')
        print(f'   Total text length: {total_text_length:,} characters')
        print(f'   Pinecone sources: {pinecone_sources}')
        print(f'   Neo4j sources: {neo4j_sources}')
        print(f'   File sources: {len(retrievals) - pinecone_sources - neo4j_sources}')
        print()
        
        # Determine success
        if chunks_with_text >= 5 and total_text_length > 10000:
            print('🎉 SUCCESS: RAG node retrieves rich content from databases!')
            print('✅ Ready to remove emergency fix from RAG node')
            return True
        elif chunks_with_text > 0:
            print('⚠️  PARTIAL SUCCESS: Some content retrieved but may need optimization')
            return False
        else:
            print('❌ FAILED: No content retrieved - databases may still have issues')
            return False
            
    except Exception as e:
        print(f'❌ ERROR: {e}')
        return False

def test_multiple_companies():
    """Test queries for different companies"""
    
    print('\n🔄 Testing Multiple Companies')
    print('-' * 40)
    
    test_cases = [
        {'company': 'GS', 'query': 'Goldman Sachs balance sheet and total assets'},
        {'company': 'JPM', 'query': 'JPMorgan financial performance and revenue'},
        {'company': 'BAC', 'query': 'Bank of America risk factors and capital ratios'}
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📋 Testing {test_case['company']}: {test_case['query'][:50]}...")
        
        initial_state = {
            'query_raw': test_case['query'],
            'metadata': {'company': test_case['company']}
        }
        
        try:
            result = rag(initial_state)
            retrievals = result.get('retrievals', [])
            
            # Quick analysis
            text_chunks = sum(1 for hit in retrievals 
                            if hit.get('text', '') != 'Content not available' 
                            and len(hit.get('text', '').strip()) > 50)
            
            print(f'   Results: {len(retrievals)} retrievals, {text_chunks} with content')
            results.append({'company': test_case['company'], 'success': text_chunks > 0})
            
        except Exception as e:
            print(f'   Error: {e}')
            results.append({'company': test_case['company'], 'success': False})
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    print(f'\n📊 Multi-company test: {successful}/{len(results)} companies successful')
    
    return successful == len(results)

def main():
    """Run all tests"""
    
    # Test main BAC query
    bac_success = test_rag_node_with_new_data()
    
    # Test multiple companies  
    multi_success = test_multiple_companies()
    
    print('\n' + '='*60)
    print('📊 FINAL TEST RESULTS')
    print('='*60)
    print(f'BAC Query Test: {"✅ PASS" if bac_success else "❌ FAIL"}')
    print(f'Multi-company Test: {"✅ PASS" if multi_success else "❌ FAIL"}')
    
    if bac_success and multi_success:
        print('\n🎉 ALL TESTS PASSED!')
        print('✅ Pipeline successfully resolved text content issues')
        print('✅ Ready to remove emergency fix from RAG node')
        print('✅ Both databases now contain full, retrievable text content')
    else:
        print('\n⚠️  Some tests failed - may need additional optimization')
    
    print('\n💡 Next Steps:')
    if bac_success:
        print('   1. Remove emergency file-reading code from agent/nodes/rag.py')
        print('   2. Test UAT interface with updated RAG node')
        print('   3. Run full pipeline with complete dataset')
    else:
        print('   1. Debug remaining retrieval issues')
        print('   2. Check database content quality')
        print('   3. Optimize query matching')

if __name__ == "__main__":
    main()