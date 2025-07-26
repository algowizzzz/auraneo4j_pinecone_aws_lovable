# SEC Graph LangGraph Agent
# Based on specifications from langrgaph_agent_readme

__version__ = "1.0.0"

# Import core classes and functions for external access
from .state import AgentState, RetrievalHit, SubTask
from .graph import build_graph, build_single_topic_graph, create_debug_trace

# Import node functions for testing
from .nodes.planner import planner
from .nodes.cypher import cypher
from .nodes.hybrid import hybrid
from .nodes.rag import rag
from .nodes.validator import validator, route_decider
from .nodes.synthesizer import synthesizer
from .nodes.master_synth import master_synth
from .nodes.parallel_runner import parallel_runner

# Import enhanced integration
from .integration.enhanced_retrieval import EnhancedFinancialRetriever, get_enhanced_retriever

__all__ = [
    'AgentState', 'RetrievalHit', 'SubTask',
    'build_graph', 'build_single_topic_graph', 'create_debug_trace',
    'planner', 'cypher', 'hybrid', 'rag', 'validator', 'route_decider',
    'synthesizer', 'master_synth', 'parallel_runner',
    'EnhancedFinancialRetriever', 'get_enhanced_retriever'
]