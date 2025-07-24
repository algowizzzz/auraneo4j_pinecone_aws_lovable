"""
Test script to verify LangGraph compilation
Run this after installing dependencies: pip install -r requirements.txt
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_compilation():
    """Test that the LangGraph compiles successfully"""
    try:
        from agent.graph import build_graph, build_single_topic_graph
        from agent.state import AgentState
        
        print("📋 Testing LangGraph compilation...")
        
        # Test main graph
        main_graph = build_graph()
        print("✅ Main graph compilation successful!")
        
        # Test single-topic graph  
        single_graph = build_single_topic_graph()
        print("✅ Single-topic graph compilation successful!")
        
        # Test state creation
        test_state = AgentState(query_raw="Test query")
        print("✅ AgentState creation successful!")
        
        print(f"\n📊 Graph Structure:")
        print(f"  Main graph nodes: {len(main_graph.nodes)}")
        print(f"  Single graph nodes: {len(single_graph.nodes)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Please install dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Compilation error: {e}")
        return False

if __name__ == "__main__":
    success = test_compilation()
    sys.exit(0 if success else 1)