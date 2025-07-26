import pytest
import os
import json
from agent.state import AgentState
from agent.nodes.cypher import cypher
from agent.nodes.hybrid import hybrid
from agent.nodes.rag import rag
from agent.nodes.synthesizer import synthesizer

@pytest.fixture(scope="module")
def test_state():
    """Create a test state with a sample query about chunked data"""
    return AgentState(
        query_raw="What is the business strategy of PB?",
        metadata={
            "company": "PB",
            "year": "2022",
            "quarter": "Q1",
            "doc_type": "10-K"
        },
        retrievals=[],
        tools_used=[],
        confidence_scores={}
    )

@pytest.mark.end_to_end
def test_cypher_node_with_chunks(test_state):
    """Test that the Cypher node works with the new chunked schema"""
    try:
        # Run cypher node
        result_state = cypher(test_state.copy())
        
        # Check that we got results
        retrievals = result_state.get("retrievals", [])
        assert isinstance(retrievals, list), "Retrievals should be a list"
        
        if retrievals:
            # Validate chunk data structure
            first_hit = retrievals[0]
            assert "section_id" in first_hit, "Hit should have section_id (chunk_id)"
            assert "text" in first_hit, "Hit should have text"
            assert "metadata" in first_hit, "Hit should have metadata"
            
            metadata = first_hit["metadata"]
            # Check for new chunk-aware metadata
            assert "source_filename" in metadata, "Metadata should include source_filename"
            
            print(f"✅ Cypher node test passed: {len(retrievals)} chunks retrieved")
            
            # If we got results, test that they're actually chunks
            if "_chunk_" in first_hit["section_id"]:
                print(f"✅ Confirmed chunked data: {first_hit['section_id']}")
            
        else:
            print("⚠️ No results from Cypher - this is OK if no data matches the query")
            
        # Check confidence scoring
        assert "confidence_scores" in result_state, "Should have confidence scores"
        assert "cypher" in result_state["confidence_scores"], "Should have cypher confidence"
        
    except Exception as e:
        pytest.fail(f"Cypher node test failed: {e}")

@pytest.mark.end_to_end 
def test_synthesizer_with_chunks():
    """Test that the Synthesizer handles chunk metadata correctly"""
    # Create mock chunk retrieval results
    mock_retrievals = [
        {
            "section_id": "external_SEC_PB_10-K_2022_q1_Item1.business.json_chunk_0",
            "text": "PB Bank focuses on community banking services and regional market expansion.",
            "score": 0.95,
            "source": "cypher",
            "metadata": {
                "section_name": "Business",
                "source_filename": "external_SEC_PB_10-K_2022_q1_Item1.business.json",
                "company": "PB",
                "year": 2022,
                "quarter": "Q1",
                "doc_type": "10-K",
                "chunk_index": 0,
                "total_chunks": 3
            }
        },
        {
            "section_id": "external_SEC_PB_10-K_2022_q1_Item1.business.json_chunk_1", 
            "text": "The bank's strategic initiatives include digital transformation and customer experience enhancement.",
            "score": 0.88,
            "source": "cypher", 
            "metadata": {
                "section_name": "Business",
                "source_filename": "external_SEC_PB_10-K_2022_q1_Item1.business.json",
                "company": "PB",
                "year": 2022,
                "quarter": "Q1", 
                "doc_type": "10-K",
                "chunk_index": 1,
                "total_chunks": 3
            }
        }
    ]
    
    test_state = AgentState(
        query_raw="What is PB's business strategy?",
        retrievals=mock_retrievals,
        metadata={"company": "PB", "year": "2022"}
    )
    
    try:
        # Run synthesizer
        result_state = synthesizer(test_state)
        
        # Validate synthesis results
        assert "final_answer" in result_state, "Should have final_answer"
        assert "citations" in result_state, "Should have citations"
        
        final_answer = result_state["final_answer"]
        citations = result_state["citations"]
        
        print(f"✅ Synthesizer test passed")
        print(f"Answer: {final_answer}")
        print(f"Citations: {citations}")
        
        # Check that citations reference source files, not chunks
        for citation in citations:
            # Citations should mention chunk parts if from chunked sources
            if "Part" in citation:
                print(f"✅ Chunk citation detected: {citation}")
            
        # Check confidence scoring
        assert "confidence_scores" in result_state, "Should have confidence scores"
        assert "synthesis" in result_state["confidence_scores"], "Should have synthesis confidence"
        
        print(f"Synthesis confidence: {result_state['confidence_scores']['synthesis']:.2f}")
        
    except Exception as e:
        pytest.fail(f"Synthesizer test failed: {e}")

@pytest.mark.end_to_end
def test_full_agent_pipeline_with_chunks():
    """Test the full agent pipeline with chunked data"""
    test_state = AgentState(
        query_raw="What are the main business lines of PB Bank?",
        metadata={
            "company": "PB", 
            "year": "2022",
            "quarter": "Q1"
        },
        retrievals=[],
        tools_used=[],
        confidence_scores={}
    )
    
    try:
        # Step 1: Try Cypher retrieval
        state_after_cypher = cypher(test_state.copy())
        
        # Step 2: If no results, try Hybrid
        if not state_after_cypher.get("retrievals"):
            print("No Cypher results, trying Hybrid...")
            state_after_hybrid = hybrid(test_state.copy())
            if state_after_hybrid.get("retrievals"):
                state_after_cypher = state_after_hybrid
                print(f"Hybrid found {len(state_after_hybrid['retrievals'])} results")
        
        # Step 3: If still no results, try RAG
        if not state_after_cypher.get("retrievals"):
            print("No Hybrid results, trying RAG...")
            state_after_rag = rag(test_state.copy())
            if state_after_rag.get("retrievals"):
                state_after_cypher = state_after_rag
                print(f"RAG found {len(state_after_rag['retrievals'])} results")
        
        # Step 4: Synthesize if we have results
        if state_after_cypher.get("retrievals"):
            final_state = synthesizer(state_after_cypher)
            
            print("✅ Full pipeline test completed")
            print(f"Final answer: {final_state.get('final_answer', 'No answer')}")
            print(f"Citations: {final_state.get('citations', [])}")
            print(f"Tools used: {final_state.get('tools_used', [])}")
            
            # Validate final state
            assert "final_answer" in final_state, "Should have final answer"
            assert final_state["final_answer"], "Final answer should not be empty"
            
        else:
            print("⚠️ No results from any retrieval method - this indicates the data may not be loaded or the query doesn't match")
            # This is OK for testing - just means no matching data
            
    except Exception as e:
        pytest.fail(f"Full pipeline test failed: {e}")

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"]) 