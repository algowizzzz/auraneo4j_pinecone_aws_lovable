"""
Main LangGraph State Machine for SEC Query Reasoning Agent
Implements the 9-node architecture from langrgaph_agent_readme
"""

from langgraph.graph import StateGraph, START, END
from typing import Dict, Any
import logging

from agent.state import AgentState

logger = logging.getLogger(__name__)

def build_graph():
    """
    Build the complete LangGraph state machine for SEC query reasoning.
    
    Architecture:
    Start → Planner → [Cypher|Hybrid|RAG|Multi] → Validator → [Synthesizer|ParallelRunner] → End
    
    With conditional edges for:
    - Dynamic routing based on planner decisions
    - Validation-driven fallback mechanisms
    - Multi-topic parallel processing
    """
    
    g = StateGraph(AgentState)
    
    # Import nodes (will be implemented in subsequent tasks)
    from agent.nodes.planner import planner
    from agent.nodes.cypher import cypher
    from agent.nodes.hybrid import hybrid  
    from agent.nodes.rag import rag
    from agent.nodes.validator import validator
    from agent.nodes.synthesizer import synthesizer
    from agent.nodes.master_synth import master_synth
    from agent.nodes.parallel_runner import parallel_runner
    from agent.nodes.validator import route_decider
    
    # === Add all nodes ===
    g.add_node("planner", planner)
    g.add_node("cypher", cypher)
    g.add_node("hybrid", hybrid)
    g.add_node("rag", rag)
    g.add_node("validator", validator)
    g.add_node("synthesizer", synthesizer)
    g.add_node("master_synth", master_synth)
    g.add_node("parallel_runner", parallel_runner)
    
    # === Define the routing logic ===
    
    # Start with planner
    g.add_edge(START, "planner")
    
    # Planner routes to retrieval methods or parallel processing
    def planner_router(state: AgentState) -> str:
        """Route from planner based on route decision"""
        route = state.get("route", "rag")  # Default to rag
        if route == "multi":
            return "parallel_runner"
        return route
    
    g.add_conditional_edges(
        "planner",
        planner_router,
        ["cypher", "hybrid", "rag", "parallel_runner"],
    )
    
    # All single-topic retrieval routes go to validator
    for retrieval_node in ["cypher", "hybrid", "rag"]:
        g.add_edge(retrieval_node, "validator")
    
    # Validator implements sophisticated fallback logic
    g.add_conditional_edges(
        "validator",
        route_decider,
        ["synthesizer", "cypher", "hybrid", "rag", "__end__"],
    )
    
    # Single-topic synthesis goes to end
    g.add_edge("synthesizer", END)
    
    # Parallel processing for multi-topic queries
    g.add_edge("parallel_runner", "master_synth")
    g.add_edge("master_synth", END)
    
    return g.compile()

def build_single_topic_graph():
    """
    Build a single-topic DAG for use by parallel runner.
    This is used when processing multiple sub-tasks concurrently.
    """
    from agent.nodes.cypher import cypher
    from agent.nodes.hybrid import hybrid
    from agent.nodes.rag import rag
    from agent.nodes.validator import validator, route_decider
    from agent.nodes.synthesizer import synthesizer
    
    g = StateGraph(AgentState)
    
    # Add only the retrieval -> validation -> synthesis path
    g.add_node("cypher", cypher)
    g.add_node("hybrid", hybrid)
    g.add_node("rag", rag)
    g.add_node("validator", validator)
    g.add_node("synthesizer", synthesizer)
    
    # Entry point determined by pre-planned route
    def single_topic_router(state: AgentState) -> str:
        """Route for single topic graph based on pre-planned route"""
        return state.get("route", "rag")
    
    g.add_conditional_edges(
        START,
        single_topic_router,
        ["cypher", "hybrid", "rag"],
    )
    
    # All retrieval methods go to validator
    for node in ["cypher", "hybrid", "rag"]:
        g.add_edge(node, "validator")
    
    # Validator with fallback logic
    g.add_conditional_edges(
        "validator",
        route_decider,
        ["synthesizer", "cypher", "hybrid", "rag", "__end__"],
    )
    
    g.add_edge("synthesizer", END)
    
    return g

def create_debug_trace(state: AgentState) -> Dict[str, Any]:
    """Create a debug trace showing the path taken through the graph"""
    return {
        "route_taken": state.get("route", "unknown"),
        "tools_used": state.get("tools_used", []),
        "fallbacks_triggered": len(state.get("fallback", [])) > 0,
        "multi_topic": len(state.get("sub_tasks", [])) > 0,
        "validation_passed": state.get("valid", False),
        "final_output_type": "master_answer" if "master_answer" in state else "final_answer"
    }

if __name__ == "__main__":
    # Test graph compilation
    try:
        graph = build_graph()
        single_topic_graph = build_single_topic_graph() 
        logger.info("✅ LangGraph compilation successful")
        
        # Print graph structure for debugging
        logger.info("Graph nodes: %s", list(graph.nodes.keys()))
        logger.info("Single-topic graph nodes: %s", list(single_topic_graph.nodes.keys()))
        
    except Exception as e:
        logger.error("❌ Graph compilation failed: %s", e)
        raise