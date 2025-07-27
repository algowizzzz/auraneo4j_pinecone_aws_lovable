"""
Enhanced Agent Graph (v2) - Planner-Centric Design
Simple graph structure where the SimpleChatPlanner is the main orchestrator
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, END

from .state_v2 import AgentStateV2, AgentStateManager
from .nodes.simple_chat_planner import simple_chat_planner

logger = logging.getLogger(__name__)


def should_continue(state: AgentStateV2) -> Literal["planner", "end"]:
    """
    Router function to determine if the planner should continue or end
    
    The planner handles all internal looping, so this mainly checks for:
    1. Completion status
    2. Pending clarifications
    3. Error conditions
    """
    
    # If marked as complete, end
    if state.get("is_complete", False):
        logger.info(f"Ending: Task completed - {state.get('completion_reason', 'No reason provided')}")
        return "end"
    
    # If there's a pending clarification, end (wait for user input)
    if state.get("pending_clarification"):
        logger.info("Ending: Pending user clarification")
        return "end"
    
    # If there are critical errors, end
    if state.get("error_messages"):
        error_count = len(state["error_messages"])
        if error_count > 3:  # Too many errors
            logger.error(f"Ending: Too many errors ({error_count})")
            return "end"
    
    # If we've exceeded iteration limits (safety check)
    if state.get("iteration_count", 0) > state.get("max_iterations", 10):
        logger.warning("Ending: Exceeded maximum iterations (safety check)")
        AgentStateManager.mark_complete(state, "Exceeded maximum iterations (safety)")
        return "end"
    
    # Continue with planner
    logger.debug("Continuing with planner")
    return "planner"


def create_enhanced_agent_graph() -> StateGraph:
    """
    Create the enhanced agent graph with planner-centric design
    
    Graph structure:
    START -> Planner -> [conditional loop back to Planner OR end]
    
    The SimpleChatPlanner handles all the complex logic internally:
    - Mode detection (semantic vs structured)
    - Metadata discovery
    - Progressive retrieval loops
    - Critique and adaptation cycles
    - User clarification requests
    """
    
    # Initialize the graph
    workflow = StateGraph(AgentStateV2)
    
    # Add the main planner node
    workflow.add_node("planner", simple_chat_planner)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Add conditional edges for looping/completion
    workflow.add_conditional_edges(
        "planner",
        should_continue,
        {
            "planner": "planner",  # Loop back to planner
            "end": END              # End execution
        }
    )
    
    return workflow


def create_v2_agent():
    """
    Create and compile the v2 agent graph
    
    Returns:
        Compiled LangGraph agent ready for execution
    """
    try:
        workflow = create_enhanced_agent_graph()
        agent = workflow.compile()
        
        logger.info("Enhanced Agent v2 created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create enhanced agent v2: {e}")
        raise


def run_v2_agent(query: str, **kwargs) -> AgentStateV2:
    """
    Convenience function to run the v2 agent with a query
    
    Args:
        query: User query string
        **kwargs: Additional parameters for state initialization
        
    Returns:
        Final agent state after execution
    """
    try:
        # Create initial state
        initial_state = AgentStateManager.create_initial_state(query)
        
        # Override any provided parameters
        for key, value in kwargs.items():
            if key in initial_state:
                initial_state[key] = value
        
        # Create and run agent
        agent = create_v2_agent()
        final_state = agent.invoke(initial_state)
        
        logger.info(f"Agent v2 execution completed for query: {query[:50]}...")
        return final_state
        
    except Exception as e:
        logger.error(f"Agent v2 execution failed: {e}")
        # Return error state
        error_state = AgentStateManager.create_initial_state(query)
        error_state["error_messages"] = [f"Execution failed: {str(e)}"]
        error_state["final_answer"] = f"I apologize, but I encountered an error while processing your query: {str(e)}"
        AgentStateManager.mark_complete(error_state, f"Error: {str(e)}")
        return error_state


def stream_v2_agent(query: str, **kwargs):
    """
    Stream the v2 agent execution (for real-time updates)
    
    Args:
        query: User query string
        **kwargs: Additional parameters for state initialization
        
    Yields:
        State updates during execution
    """
    try:
        # Create initial state
        initial_state = AgentStateManager.create_initial_state(query)
        
        # Override any provided parameters
        for key, value in kwargs.items():
            if key in initial_state:
                initial_state[key] = value
        
        # Create agent
        agent = create_v2_agent()
        
        # Stream execution
        for state_update in agent.stream(initial_state):
            yield state_update
            
    except Exception as e:
        logger.error(f"Agent v2 streaming failed: {e}")
        # Yield error state
        error_state = AgentStateManager.create_initial_state(query)
        error_state["error_messages"] = [f"Streaming failed: {str(e)}"]
        error_state["final_answer"] = f"I apologize, but I encountered an error: {str(e)}"
        AgentStateManager.mark_complete(error_state, f"Error: {str(e)}")
        yield {"planner": error_state}


# Example usage and testing functions
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_queries = [
        "What is BAC's CET1 ratio in 2024?",
        "Compare JPM and GS revenue trends",
        "What data do you have available?",
        "Comprehensive analysis of Wells Fargo risk factors"
    ]
    
    print("🧪 TESTING ENHANCED AGENT V2")
    print("=" * 50)
    
    agent = create_v2_agent()
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        
        try:
            # Create initial state
            initial_state = AgentStateManager.create_initial_state(query)
            
            # Run agent
            result = agent.invoke(initial_state)
            
            print(f"   Mode: {result.get('planner_mode', 'unknown')}")
            print(f"   Route: {result.get('route', 'unknown')}")
            print(f"   Iterations: {result.get('iteration_count', 0)}")
            print(f"   Chunks: {len(result.get('accumulated_chunks', []))}")
            print(f"   Complete: {result.get('is_complete', False)}")
            print(f"   Time: {result.get('execution_time', 0):.2f}s")
            
            if result.get("final_answer"):
                answer_preview = result["final_answer"][:100] + "..." if len(result["final_answer"]) > 100 else result["final_answer"]
                print(f"   Answer: {answer_preview}")
            
            if result.get("error_messages"):
                print(f"   Errors: {result['error_messages']}")
                
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print("\n✅ Enhanced Agent v2 testing complete")