"""
Parallel Runner Node - Multi-topic Query Handling
Implements concurrent processing of sub-tasks with map-reduce pattern
"""

from agent.state import AgentState
from agent.nodes.planner import planner
from agent.nodes.cypher import cypher
from agent.nodes.hybrid import hybrid
from agent.nodes.rag import rag
from agent.nodes.validator import validator
from agent.nodes.synthesizer import synthesizer
import asyncio
import logging
from typing import List, Dict, Any
import copy

logger = logging.getLogger(__name__)

def _extract_sub_topics(query: str) -> List[str]:
    """
    Extract individual topics from a multi-topic query.
    Handles various separators and conjunction patterns.
    """
    # Common separators and conjunctions
    separators = [' and ', ' & ', ' + ', ', ', ';']
    
    # Start with the original query
    topics = [query.strip()]
    
    # Split by each separator
    for separator in separators:
        new_topics = []
        for topic in topics:
            if separator in topic.lower():
                split_topics = [t.strip() for t in topic.split(separator) if t.strip()]
                new_topics.extend(split_topics)
            else:
                new_topics.append(topic)
        topics = new_topics
    
    # Filter out very short topics and duplicates
    filtered_topics = []
    seen = set()
    for topic in topics:
        if len(topic) > 10 and topic.lower() not in seen:  # Minimum meaningful length
            filtered_topics.append(topic)
            seen.add(topic.lower())
    
    # If we couldn't extract meaningful sub-topics, return the original
    if not filtered_topics:
        return [query]
    
    return filtered_topics

def _create_sub_task(topic: str, original_metadata: Dict[str, Any], task_id: int) -> Dict[str, Any]:
    """
    Create a sub-task for a specific topic.
    """
    return {
        "id": task_id,
        "topic": topic,
        "query": topic,
        "metadata": copy.deepcopy(original_metadata),
        "status": "pending"
    }

def _determine_optimal_route_for_topic(topic: str, metadata: Dict[str, Any]) -> str:
    """
    Determine the best retrieval route for a specific topic.
    Uses simplified routing logic optimized for sub-topics.
    """
    topic_lower = topic.lower()
    
    # Check for structured query indicators
    structured_indicators = ['total', 'amount', 'value', 'ratio', 'percentage', 'number of']
    if any(indicator in topic_lower for indicator in structured_indicators) and metadata:
        return "cypher"
    
    # Check for hybrid-friendly queries (some metadata + explanation needed)
    if metadata and ('explain' in topic_lower or 'describe' in topic_lower or 'analysis' in topic_lower):
        return "hybrid"
    
    # Default to RAG for conceptual/broad topics
    return "rag"

async def _execute_sub_task(sub_task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single sub-task asynchronously.
    Returns the sub-task with results populated.
    """
    try:
        logger.info(f"Executing sub-task {sub_task['id']}: '{sub_task['topic'][:50]}...'")
        
        # Create isolated state for this sub-task
        sub_state = AgentState(
            query_raw=sub_task["query"],
            metadata=sub_task["metadata"],
            route=_determine_optimal_route_for_topic(sub_task["topic"], sub_task["metadata"]),
            fallback=["rag"],  # Simple fallback for sub-tasks
            retrievals=[],
            valid=False,
            final_answer="",
            citations=[]
        )
        
        # Execute the determined route
        route = sub_state["route"]
        
        if route == "cypher":
            sub_state = cypher(sub_state)
        elif route == "hybrid":
            sub_state = hybrid(sub_state)
        else:  # rag
            sub_state = rag(sub_state)
        
        # Validate results
        sub_state = validator(sub_state)
        
        # If validation fails and we have a fallback, try it
        if not sub_state.get("valid", False) and sub_state.get("fallback"):
            fallback_route = sub_state["fallback"][0]
            logger.info(f"Sub-task {sub_task['id']} validation failed, trying fallback: {fallback_route}")
            
            if fallback_route == "rag":
                sub_state = rag(sub_state)
            elif fallback_route == "hybrid":
                sub_state = hybrid(sub_state)
            
            # Re-validate
            sub_state = validator(sub_state)
        
        # Synthesize if validation passed
        if sub_state.get("valid", False):
            sub_state = synthesizer(sub_state)
            sub_task["status"] = "completed"
            sub_task["final_answer"] = sub_state.get("final_answer", "")
            sub_task["citations"] = sub_state.get("citations", [])
            sub_task["confidence"] = sub_state.get("confidence_scores", {}).get("synthesis", 0.0)
        else:
            sub_task["status"] = "failed"
            sub_task["final_answer"] = f"Unable to find sufficient information about {sub_task['topic']}."
            sub_task["citations"] = []
            sub_task["confidence"] = 0.0
        
        # Store retrieval details for debugging
        sub_task["retrievals_count"] = len(sub_state.get("retrievals", []))
        sub_task["route_used"] = route
        
        logger.info(f"Sub-task {sub_task['id']} completed with status: {sub_task['status']}")
        
    except Exception as e:
        logger.error(f"Sub-task {sub_task['id']} failed: {e}")
        sub_task["status"] = "error"
        sub_task["final_answer"] = f"Error processing {sub_task['topic']}: {str(e)}"
        sub_task["citations"] = []
        sub_task["confidence"] = 0.0
    
    return sub_task

async def _execute_sub_tasks_parallel(sub_tasks: List[Dict[str, Any]], max_concurrent: int = 3) -> List[Dict[str, Any]]:
    """
    Execute sub-tasks in parallel with concurrency control.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_execute(sub_task):
        async with semaphore:
            return await _execute_sub_task(sub_task)
    
    # Execute all sub-tasks concurrently
    logger.info(f"Starting parallel execution of {len(sub_tasks)} sub-tasks (max concurrent: {max_concurrent})")
    
    results = await asyncio.gather(*[limited_execute(task) for task in sub_tasks])
    
    logger.info(f"Parallel execution completed: {sum(1 for r in results if r['status'] == 'completed')} successful, {sum(1 for r in results if r['status'] == 'failed')} failed")
    
    return results

def parallel_runner(state: AgentState) -> AgentState:
    """
    Parallel runner node - handles multi-topic queries with concurrent processing.
    
    Process:
    1. Extract sub-topics from complex query
    2. Create sub-tasks for each topic
    3. Execute sub-tasks in parallel
    4. Collect results for master synthesis
    
    Features:
    - Concurrent sub-task execution
    - Individual routing optimization per sub-topic
    - Fallback handling for failed sub-tasks
    - Comprehensive result aggregation
    """
    try:
        query = state.get("query_raw", "")
        metadata = state.get("metadata", {})
        
        logger.info(f"Parallel runner processing multi-topic query: '{query[:50]}...'")
        
        # Extract sub-topics from the query
        sub_topics = _extract_sub_topics(query)
        
        if len(sub_topics) <= 1:
            # Not actually a multi-topic query, route to single topic handling
            logger.warning(f"Query identified as multi-topic but only {len(sub_topics)} topics found. Routing to RAG.")
            state["route"] = "rag"
            return state
        
        logger.info(f"Extracted {len(sub_topics)} sub-topics: {[t[:30]+'...' for t in sub_topics]}")
        
        # Create sub-tasks
        sub_tasks = []
        for i, topic in enumerate(sub_topics):
            sub_task = _create_sub_task(topic, metadata, i + 1)
            sub_tasks.append(sub_task)
        
        # Execute sub-tasks in parallel
        try:
            # Run the async execution in the current thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            completed_tasks = loop.run_until_complete(_execute_sub_tasks_parallel(sub_tasks))
            loop.close()
        except Exception as async_error:
            logger.error(f"Async execution failed, falling back to sequential: {async_error}")
            # Fallback to sequential execution
            completed_tasks = []
            for sub_task in sub_tasks:
                # Convert async function to sync for fallback
                import threading
                result = [None]
                def sync_execute():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result[0] = loop.run_until_complete(_execute_sub_task(sub_task))
                    loop.close()
                
                thread = threading.Thread(target=sync_execute)
                thread.start()
                thread.join()
                completed_tasks.append(result[0])
        
        # Collect successful results
        successful_tasks = [task for task in completed_tasks if task["status"] == "completed"]
        
        if not successful_tasks:
            # All sub-tasks failed
            state["final_answer"] = "I was unable to find sufficient information for any of the requested topics."
            state["citations"] = []
            logger.warning("All sub-tasks failed in parallel execution")
            return state
        
        # Prepare data for master synthesis
        sub_summaries = [task["final_answer"] for task in successful_tasks]
        state["sub_summaries"] = sub_summaries
        state["sub_tasks"] = successful_tasks
        
        # Store parallel execution metadata
        state["parallel_execution"] = {
            "total_subtasks": len(sub_tasks),
            "successful_subtasks": len(successful_tasks),
            "failed_subtasks": len(sub_tasks) - len(successful_tasks),
            "execution_method": "parallel"
        }
        
        # Track tool usage and confidence
        if "tools_used" not in state:
            state["tools_used"] = []
        state["tools_used"].append("parallel_runner")
        
        if "confidence_scores" not in state:
            state["confidence_scores"] = {}
        
        # Calculate overall confidence for parallel execution
        if successful_tasks:
            avg_confidence = sum(task["confidence"] for task in successful_tasks) / len(successful_tasks)
            coverage_ratio = len(successful_tasks) / len(sub_tasks)
            overall_confidence = avg_confidence * coverage_ratio
        else:
            overall_confidence = 0.0
        
        state["confidence_scores"]["parallel_execution"] = overall_confidence
        
        logger.info(f"Parallel runner completed: {len(successful_tasks)}/{len(sub_tasks)} successful sub-tasks, confidence: {overall_confidence:.2f}")
        
        # Set route to master synthesis
        state["route"] = "master_synth"
        
    except Exception as e:
        logger.error(f"Parallel runner error: {e}")
        state["final_answer"] = "I encountered an error while processing the multi-topic query."
        state["citations"] = []
        if "error_messages" not in state:
            state["error_messages"] = []
        state["error_messages"].append(f"Parallel runner error: {str(e)}")
    
    return state

def get_parallel_execution_summary(state: AgentState) -> Dict[str, Any]:
    """
    Get summary of parallel execution results for debugging/monitoring.
    """
    parallel_data = state.get("parallel_execution", {})
    
    return {
        "total_subtasks": parallel_data.get("total_subtasks", 0),
        "successful_subtasks": parallel_data.get("successful_subtasks", 0),
        "success_rate": parallel_data.get("successful_subtasks", 0) / max(1, parallel_data.get("total_subtasks", 1)),
        "execution_confidence": state.get("confidence_scores", {}).get("parallel_execution", 0.0),
        "sub_tasks_details": state.get("sub_tasks", [])
    }