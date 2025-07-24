"""
Main Entry Point for SEC Graph LangGraph Agent
Based on specifications from langrgaph_agent_readme
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main execution function"""
    try:
        # Import and build the graph
        from agent.graph import build_graph, create_debug_trace
        
        logger.info("Building LangGraph state machine...")
        graph = build_graph()
        logger.info("✅ Graph compilation successful!")
        
        # Get user query
        if len(sys.argv) > 1:
            question = " ".join(sys.argv[1:])
        else:
            question = input("Ask SEC-GPT> ")
        
        if not question.strip():
            logger.warning("No question provided")
            return
        
        logger.info(f"Processing query: {question}")
        
        # Execute the graph
        result = graph.invoke({"query_raw": question})
        
        # Display results
        print("\n" + "="*60)
        
        if "master_answer" in result:
            print("📊 Multi-topic Analysis:")
            print(result["master_answer"])
        elif "final_answer" in result:
            print("📋 Analysis:")
            print(result["final_answer"])
        else:
            print("❌ No answer generated")
        
        # Display debug information
        debug_info = create_debug_trace(result)
        print(f"\n🔍 Debug Trace:")
        print(f"  Route taken: {debug_info['route_taken']}")
        print(f"  Tools used: {', '.join(debug_info['tools_used'])}")
        print(f"  Fallbacks triggered: {debug_info['fallbacks_triggered']}")
        print(f"  Multi-topic query: {debug_info['multi_topic']}")
        
        # Display citations if available
        if result.get("citations"):
            print(f"\n📚 Sources: {', '.join(result['citations'])}")
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()