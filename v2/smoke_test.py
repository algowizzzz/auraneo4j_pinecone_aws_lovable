#!/usr/bin/env python3
"""
Smoke test for Enhanced Iterative Planner v2
Quick validation that core components can be imported and initialized
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """Test that all core components can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Test model imports
        from v2.agent.models.metadata import StandardizedMetadata, CritiqueResult
        print("  ✅ Models imported successfully")
        
        # Test state imports
        from v2.agent.state_v2 import AgentStateV2, AgentStateManager
        print("  ✅ State management imported successfully")
        
        # Test LLM helpers
        from v2.agent.utils.llm_helpers import llm_extract_query_info
        print("  ✅ LLM helpers imported successfully")
        
        # Test retrieval functions
        from v2.agent.nodes.retrieval_functions import simplified_rag
        print("  ✅ Retrieval functions imported successfully")
        
        # Test planner
        from v2.agent.nodes.simple_chat_planner import SimpleChatPlanner
        print("  ✅ SimpleChatPlanner imported successfully")
        
        # Test graph
        from v2.agent.graph_v2 import create_v2_agent
        print("  ✅ Graph components imported successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_state_creation():
    """Test that agent state can be created"""
    print("\n🧪 Testing state creation...")
    
    try:
        from v2.agent.state_v2 import AgentStateManager
        
        # Create initial state
        state = AgentStateManager.create_initial_state("Test query")
        
        # Verify required fields
        assert state["query_raw"] == "Test query"
        assert state["iteration_count"] == 0
        assert state["is_complete"] == False
        assert isinstance(state["accumulated_chunks"], list)
        assert isinstance(state["planner_decisions"], list)
        
        print("  ✅ State creation successful")
        return True
        
    except Exception as e:
        print(f"  ❌ State creation failed: {e}")
        return False


def test_llm_helpers():
    """Test LLM helper functions (without making API calls)"""
    print("\n🧪 Testing LLM helper setup...")
    
    try:
        from v2.agent.utils.llm_helpers import (
            llm_detect_introspection,
            generate_data_inventory_response,
            generate_capabilities_response
        )
        
        # Test introspection detection (no API call)
        is_introspection = llm_detect_introspection("what data do you have?")
        assert is_introspection == True
        
        is_not_introspection = llm_detect_introspection("what is BAC's revenue?")
        assert is_not_introspection == False
        
        # Test response generators (no API call)
        data_response = generate_data_inventory_response()
        assert len(data_response) > 0
        
        capabilities_response = generate_capabilities_response()
        assert len(capabilities_response) > 0
        
        print("  ✅ LLM helpers working correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ LLM helpers test failed: {e}")
        return False


def test_graph_creation():
    """Test that the graph can be created (without compilation)"""
    print("\n🧪 Testing graph creation...")
    
    try:
        from v2.agent.graph_v2 import create_enhanced_agent_graph
        
        # Create graph structure (don't compile to avoid dependencies)
        workflow = create_enhanced_agent_graph()
        
        # Basic validation
        assert workflow is not None
        print("  ✅ Graph structure created successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Graph creation failed: {e}")
        return False


def test_environment():
    """Test environment setup"""
    print("\n🧪 Testing environment...")
    
    required_vars = [
        "OPENAI_API_KEY",
        "NEO4J_URI", 
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD",
        "PINECONE_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"  ⚠️  Missing environment variables: {missing_vars}")
        print("  ℹ️  Agent will work with mock data, but full functionality requires these")
    else:
        print("  ✅ All environment variables present")
    
    return True


def main():
    """Run all smoke tests"""
    print("🚀 Enhanced Iterative Planner v2 - Smoke Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_state_creation,
        test_llm_helpers,
        test_graph_creation,
        test_environment
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  💥 Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 SMOKE TEST RESULTS")
    print("=" * 30)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All smoke tests passed! v2 agent is ready for testing.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())