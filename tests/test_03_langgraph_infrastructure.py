"""
TC-003: LangGraph Infrastructure Testing
Validates core LangGraph state machine compilation and routing
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAgentStateDefinition:
    """Test AgentState TypedDict definition and validation"""
    
    def test_agent_state_import(self):
        """Test AgentState can be imported"""
        try:
            from agent.state import AgentState, RetrievalHit
            assert AgentState is not None
            assert RetrievalHit is not None
        except ImportError as e:
            pytest.fail(f"Failed to import AgentState: {e}")
    
    def test_agent_state_creation(self, sample_agent_state):
        """Test AgentState can be created with required fields"""
        from agent.state import AgentState
        
        # Test basic creation
        state = AgentState(query_raw="Test query")
        assert state["query_raw"] == "Test query"
        
        # Test with full sample data
        full_state = AgentState(**sample_agent_state)
        assert full_state["query_raw"] == sample_agent_state["query_raw"]
        assert full_state["metadata"] == sample_agent_state["metadata"]
        assert full_state["route"] == sample_agent_state["route"]
    
    def test_retrieval_hit_structure(self, sample_retrieval_hits):
        """Test RetrievalHit structure"""
        from agent.state import RetrievalHit
        
        hit_data = sample_retrieval_hits[0]
        
        # Test RetrievalHit creation
        hit = RetrievalHit(
            section_id=hit_data["section_id"],
            text=hit_data["text"],
            score=hit_data["score"],
            source=hit_data["source"],
            metadata=hit_data["metadata"]
        )
        
        assert hit["section_id"] == hit_data["section_id"]
        assert hit["text"] == hit_data["text"]
        assert hit["score"] == hit_data["score"]
        assert hit["source"] == hit_data["source"]
        assert hit["metadata"] == hit_data["metadata"]
    
    def test_state_field_types(self):
        """Test AgentState field types"""
        from agent.state import AgentState
        
        state = AgentState(
            query_raw="test",
            metadata={"company": "ZION"},
            route="cypher", 
            fallback=["hybrid"],
            retrievals=[],
            valid=False,
            final_answer="",
            citations=[]
        )
        
        assert isinstance(state["query_raw"], str)
        assert isinstance(state["metadata"], dict)
        assert isinstance(state["route"], str)
        assert isinstance(state["fallback"], list)
        assert isinstance(state["retrievals"], list)
        assert isinstance(state["valid"], bool)
        assert isinstance(state["final_answer"], str)
        assert isinstance(state["citations"], list)

class TestGraphCompilation:
    """Test LangGraph compilation and structure"""
    
    def test_main_graph_import(self):
        """Test main graph functions can be imported"""
        try:
            from agent.graph import build_graph, build_single_topic_graph, create_debug_trace
            assert build_graph is not None
            assert build_single_topic_graph is not None
            assert create_debug_trace is not None
        except ImportError as e:
            pytest.fail(f"Failed to import graph functions: {e}")
    
    @patch('agent.nodes.planner.planner')
    @patch('agent.nodes.cypher.cypher')
    @patch('agent.nodes.hybrid.hybrid')
    @patch('agent.nodes.rag.rag')
    @patch('agent.nodes.validator.validator')
    @patch('agent.nodes.synthesizer.synthesizer')
    @patch('agent.nodes.master_synth.master_synth')
    @patch('agent.nodes.parallel_runner.parallel_runner')
    def test_main_graph_compilation(self, mock_parallel, mock_master, mock_synth, 
                                   mock_validator, mock_rag, mock_hybrid, 
                                   mock_cypher, mock_planner):
        """Test main graph compiles successfully"""
        from agent.graph import build_graph
        
        # Mock all node functions
        for mock_node in [mock_planner, mock_cypher, mock_hybrid, mock_rag, 
                         mock_validator, mock_synth, mock_master, mock_parallel]:
            mock_node.return_value = {"mock": "result"}
        
        try:
            graph = build_graph()
            assert graph is not None
            
            # Test graph has expected structure
            assert hasattr(graph, 'nodes'), "Graph missing nodes attribute"
            assert hasattr(graph, 'invoke'), "Graph missing invoke method"
            
        except Exception as e:
            pytest.fail(f"Main graph compilation failed: {e}")
    
    @patch('agent.nodes.cypher.cypher')
    @patch('agent.nodes.hybrid.hybrid')
    @patch('agent.nodes.rag.rag')
    @patch('agent.nodes.validator.validator')
    @patch('agent.nodes.synthesizer.synthesizer')
    def test_single_topic_graph_compilation(self, mock_synth, mock_validator, 
                                          mock_rag, mock_hybrid, mock_cypher):
        """Test single-topic graph compiles successfully"""
        from agent.graph import build_single_topic_graph
        
        # Mock all node functions
        for mock_node in [mock_cypher, mock_hybrid, mock_rag, mock_validator, mock_synth]:
            mock_node.return_value = {"mock": "result"}
        
        try:
            graph = build_single_topic_graph()
            assert graph is not None
            
        except Exception as e:
            pytest.fail(f"Single-topic graph compilation failed: {e}")
    
    def test_debug_trace_function(self, sample_agent_state):
        """Test debug trace creation"""
        from agent.graph import create_debug_trace
        
        # Add some debug information to state
        state = sample_agent_state.copy()
        state["tools_used"] = ["planner", "cypher", "validator", "synthesizer"]
        state["final_answer"] = "Test answer"
        
        debug_info = create_debug_trace(state)
        
        assert isinstance(debug_info, dict)
        assert "route_taken" in debug_info
        assert "tools_used" in debug_info
        assert "fallbacks_triggered" in debug_info
        assert "multi_topic" in debug_info
        assert "validation_passed" in debug_info

class TestNodeImports:
    """Test all node modules can be imported"""
    
    def test_planner_node_import(self):
        """Test planner node import"""
        try:
            from agent.nodes.planner import planner
            assert callable(planner), "Planner is not callable"
        except ImportError as e:
            pytest.fail(f"Failed to import planner node: {e}")
    
    def test_cypher_node_import(self):
        """Test cypher node import"""
        try:
            from agent.nodes.cypher import cypher
            assert callable(cypher), "Cypher is not callable"
        except ImportError as e:
            pytest.fail(f"Failed to import cypher node: {e}")
    
    def test_hybrid_node_import(self):
        """Test hybrid node import"""
        try:
            from agent.nodes.hybrid import hybrid
            assert callable(hybrid), "Hybrid is not callable"
        except ImportError as e:
            pytest.fail(f"Failed to import hybrid node: {e}")
    
    def test_rag_node_import(self):
        """Test RAG node import"""
        try:
            from agent.nodes.rag import rag
            assert callable(rag), "RAG is not callable"
        except ImportError as e:
            pytest.fail(f"Failed to import RAG node: {e}")
    
    def test_validator_node_import(self):
        """Test validator node import"""
        try:
            from agent.nodes.validator import validator, route_decider
            assert callable(validator), "Validator is not callable"
            assert callable(route_decider), "Route decider is not callable"
        except ImportError as e:
            pytest.fail(f"Failed to import validator node: {e}")
    
    def test_synthesizer_node_import(self):
        """Test synthesizer node import"""
        try:
            from agent.nodes.synthesizer import synthesizer
            assert callable(synthesizer), "Synthesizer is not callable"
        except ImportError as e:
            pytest.fail(f"Failed to import synthesizer node: {e}")
    
    def test_master_synth_node_import(self):
        """Test master synthesis node import"""
        try:
            from agent.nodes.master_synth import master_synth
            assert callable(master_synth), "Master synth is not callable"
        except ImportError as e:
            pytest.fail(f"Failed to import master synth node: {e}")
    
    def test_parallel_runner_node_import(self):
        """Test parallel runner node import"""
        try:
            from agent.nodes.parallel_runner import parallel_runner
            assert callable(parallel_runner), "Parallel runner is not callable"
        except ImportError as e:
            pytest.fail(f"Failed to import parallel runner node: {e}")

class TestNodeFunctionality:
    """Test basic node functionality (mocked)"""
    
    @patch('agent.nodes.planner._llm')
    def test_planner_node_basic(self, mock_llm, sample_agent_state):
        """Test planner node basic functionality"""
        from agent.nodes.planner import planner
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '{"route": "cypher", "fallback": ["hybrid"], "metadata": {"company": "ZION"}}'
        mock_llm.invoke.return_value = mock_response
        
        state = {"query_raw": "What are Zions capital ratios?"}
        
        try:
            result = planner(state)
            assert isinstance(result, dict)
            assert "route" in result
            assert "tools_used" in result
            assert "planner" in result["tools_used"]
        except Exception as e:
            pytest.fail(f"Planner node execution failed: {e}")
    
    @patch('agent.nodes.cypher.Neo4jCypherRetriever')
    def test_cypher_node_basic(self, mock_retriever, sample_agent_state):
        """Test cypher node basic functionality"""
        from agent.nodes.cypher import cypher
        
        # Mock retriever
        mock_instance = Mock()
        mock_instance.execute_cypher_retrieval.return_value = []
        mock_retriever.return_value = mock_instance
        
        state = sample_agent_state.copy()
        
        try:
            result = cypher(state)
            assert isinstance(result, dict)
            assert "retrievals" in result
            assert "tools_used" in result
            assert "cypher" in result["tools_used"]
        except Exception as e:
            pytest.fail(f"Cypher node execution failed: {e}")
    
    @patch('agent.nodes.validator._llm')
    def test_validator_node_basic(self, mock_llm, sample_agent_state):
        """Test validator node basic functionality"""
        from agent.nodes.validator import validator
        
        # Mock LLM response for reflection
        mock_response = Mock()
        mock_response.content = "8"  # Good reflection score
        mock_llm.invoke.return_value = mock_response
        
        state = sample_agent_state.copy()
        state["retrievals"] = [
            {"text": "Sample retrieval text", "score": 0.9}
        ]
        
        try:
            result = validator(state)
            assert isinstance(result, dict)
            assert "valid" in result
            assert "tools_used" in result
            assert "validator" in result["tools_used"]
        except Exception as e:
            pytest.fail(f"Validator node execution failed: {e}")
    
    @patch('agent.nodes.synthesizer._llm')
    def test_synthesizer_node_basic(self, mock_llm, sample_retrieval_hits):
        """Test synthesizer node basic functionality"""
        from agent.nodes.synthesizer import synthesizer
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "Zions Bancorporation maintains strong capital ratios [1]."
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "query_raw": "What are Zions capital ratios?",
            "retrievals": sample_retrieval_hits
        }
        
        try:
            result = synthesizer(state)
            assert isinstance(result, dict)
            assert "final_answer" in result
            assert "citations" in result
            assert "tools_used" in result
            assert "synthesizer" in result["tools_used"]
        except Exception as e:
            pytest.fail(f"Synthesizer node execution failed: {e}")

class TestEnhancedIntegration:
    """Test enhanced integration module"""
    
    def test_enhanced_integration_import(self):
        """Test enhanced integration can be imported"""
        try:
            from agent.integration.enhanced_retrieval import EnhancedFinancialRetriever
            from agent.integration.enhanced_retrieval import get_enhanced_retriever
            
            assert EnhancedFinancialRetriever is not None
            assert callable(get_enhanced_retriever)
            
        except ImportError as e:
            pytest.fail(f"Failed to import enhanced integration: {e}")
    
    @patch('agent.integration.enhanced_retrieval.FinancialEntityExtractor')
    @patch('neo4j.GraphDatabase.driver')
    def test_enhanced_retriever_creation(self, mock_driver, mock_extractor):
        """Test enhanced retriever can be created"""
        from agent.integration.enhanced_retrieval import EnhancedFinancialRetriever
        
        # Mock dependencies
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        mock_extractor_instance = Mock()
        mock_extractor.return_value = mock_extractor_instance
        
        try:
            retriever = EnhancedFinancialRetriever(
                neo4j_uri='bolt://localhost:7687',
                neo4j_user='neo4j',
                neo4j_password='test',
                pinecone_index=None  # Disable Pinecone for testing
            )
            
            assert retriever is not None
            assert hasattr(retriever, 'extract_financial_entities_from_query')
            assert hasattr(retriever, 'enhanced_cypher_search')
            assert hasattr(retriever, 'enhanced_pinecone_search')
            
        except Exception as e:
            pytest.fail(f"Enhanced retriever creation failed: {e}")

class TestRoutingLogic:
    """Test routing logic and conditional edges"""
    
    def test_route_decider_function(self):
        """Test route decider function"""
        from agent.nodes.validator import route_decider
        
        # Test validation passed
        state_passed = {"valid": True}
        result = route_decider(state_passed)
        assert result == "synthesizer"
        
        # Test validation failed with fallbacks
        state_fallback = {"valid": False, "fallback": ["hybrid", "rag"]}
        result = route_decider(state_fallback)
        assert result in ["hybrid", "rag"]
        
        # Test validation failed without fallbacks
        state_failed = {"valid": False, "fallback": []}
        result = route_decider(state_failed)
        assert result == "__end__"
    
    def test_state_management(self, sample_agent_state):
        """Test state management through nodes"""
        from agent.state import AgentState
        
        # Test state updates preserve structure
        state = AgentState(**sample_agent_state)
        
        # Simulate node updates
        state["tools_used"] = ["planner"]
        state["confidence_scores"] = {"planner": 0.9}
        
        assert "tools_used" in state
        assert "confidence_scores" in state
        assert state["query_raw"] == sample_agent_state["query_raw"]  # Original data preserved

class TestErrorHandling:
    """Test error handling in graph infrastructure"""
    
    def test_missing_node_handling(self):
        """Test handling of missing node imports"""
        # This test would check what happens if a node fails to import
        # For now, we just test that the import system doesn't crash
        
        try:
            # Test importing a non-existent node
            import importlib
            with pytest.raises(ModuleNotFoundError):
                importlib.import_module('agent.nodes.nonexistent_node')
        except Exception as e:
            # This is expected behavior
            pass
    
    def test_state_validation(self):
        """Test state validation and error recovery"""
        from agent.state import AgentState
        
        # Test with minimal required data
        minimal_state = AgentState(query_raw="test")
        assert minimal_state["query_raw"] == "test"
        
        # Test with None values (should be handled gracefully)
        try:
            state_with_none = AgentState(
                query_raw="test",
                metadata=None,
                retrievals=None
            )
            # Should not crash
            assert state_with_none["query_raw"] == "test"
        except Exception as e:
            # If it does crash, that's a bug we need to know about
            pytest.fail(f"State creation with None values failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])