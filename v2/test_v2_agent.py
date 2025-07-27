#!/usr/bin/env python3
"""
Terminal Testing Script for Enhanced Iterative Planner (v2)
Usage: python -m v2.test_v2_agent [--query "your query"]
"""

import sys
import argparse
import logging
import json
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from v2.agent.graph_v2 import run_v2_agent, stream_v2_agent
from v2.agent.state_v2 import AgentStateManager


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def format_state_summary(state) -> str:
    """Format state into a readable summary"""
    summary = []
    summary.append(f"🎯 Query: {state.get('query_raw', 'N/A')}")
    summary.append(f"🧠 Mode: {state.get('planner_mode', 'unknown')}")
    summary.append(f"🛣️  Route: {state.get('route', 'unknown')}")
    summary.append(f"🔄 Iterations: {state.get('iteration_count', 0)}")
    summary.append(f"📄 Chunks Retrieved: {len(state.get('accumulated_chunks', []))}")
    summary.append(f"✅ Complete: {state.get('is_complete', False)}")
    summary.append(f"⏱️  Execution Time: {state.get('execution_time', 0):.2f}s")
    
    if state.get('completion_reason'):
        summary.append(f"🎬 Completion Reason: {state['completion_reason']}")
    
    if state.get('error_messages'):
        summary.append(f"❌ Errors: {state['error_messages']}")
    
    if state.get('pending_clarification'):
        clarification = state['pending_clarification']
        summary.append(f"❓ Pending Clarification: {clarification['question']}")
    
    return "\n".join(summary)


def format_final_answer(state) -> str:
    """Format the final answer nicely"""
    if not state.get('final_answer'):
        return "❌ No final answer generated"
    
    answer = state['final_answer']
    
    # Add data coverage if available
    if state.get('data_coverage_summary'):
        answer += f"\n\n📊 Data Coverage: {state['data_coverage_summary']}"
    
    return answer


def interactive_mode():
    """Run in interactive mode for continuous testing"""
    print("🤖 Enhanced Iterative Planner v2 - Interactive Mode")
    print("Type 'quit', 'exit', or 'q' to exit")
    print("Type 'help' for commands")
    print("-" * 60)
    
    while True:
        try:
            query = input("\n💭 Enter your query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if query.lower() == 'help':
                print("Available commands:")
                print("  help - Show this help")
                print("  quit/exit/q - Exit interactive mode") 
                print("  debug:on - Enable debug logging")
                print("  debug:off - Disable debug logging")
                print("  stream:<query> - Stream the execution")
                continue
            
            if query.lower() == 'debug:on':
                logging.getLogger().setLevel(logging.DEBUG)
                print("🐛 Debug logging enabled")
                continue
                
            if query.lower() == 'debug:off':
                logging.getLogger().setLevel(logging.INFO)
                print("ℹ️  Debug logging disabled")
                continue
            
            if query.startswith('stream:'):
                query = query[7:].strip()
                print(f"\n🚀 Streaming execution for: {query}")
                print("-" * 40)
                
                for update in stream_v2_agent(query):
                    node_name = list(update.keys())[0]
                    state = update[node_name]
                    print(f"📡 Update from {node_name}:")
                    print(f"   Iteration: {state.get('iteration_count', 0)}")
                    print(f"   Chunks: {len(state.get('accumulated_chunks', []))}")
                    if state.get('last_critique'):
                        print(f"   Quality: {state['last_critique']['synthesis_quality']}")
                    print()
                
                continue
            
            if not query:
                print("⚠️  Please enter a non-empty query")
                continue
            
            print(f"\n🚀 Processing: {query}")
            print("-" * 40)
            
            start_time = time.time()
            final_state = run_v2_agent(query)
            end_time = time.time()
            
            print("\n📊 EXECUTION SUMMARY")
            print("=" * 40)
            print(format_state_summary(final_state))
            
            print(f"\n📝 FINAL ANSWER")
            print("=" * 40)
            print(format_final_answer(final_state))
            
            # Show planner decisions if in debug mode
            if logging.getLogger().level <= logging.DEBUG:
                decisions = final_state.get('planner_decisions', [])
                if decisions:
                    print(f"\n🧠 PLANNER DECISIONS")
                    print("=" * 40)
                    for i, decision in enumerate(decisions, 1):
                        print(f"{i}. {decision['decision_type']}: {decision['decision']}")
                        print(f"   Reasoning: {decision['reasoning']}")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if logging.getLogger().level <= logging.DEBUG:
                import traceback
                traceback.print_exc()


def batch_test_mode(queries: list):
    """Run batch testing on multiple queries"""
    print(f"🧪 Running batch test on {len(queries)} queries")
    print("=" * 60)
    
    results = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Testing: {query[:50]}...")
        
        try:
            start_time = time.time()
            final_state = run_v2_agent(query)
            end_time = time.time()
            
            result = {
                "query": query,
                "success": final_state.get('is_complete', False),
                "mode": final_state.get('planner_mode'),
                "route": final_state.get('route'),
                "iterations": final_state.get('iteration_count', 0),
                "chunks": len(final_state.get('accumulated_chunks', [])),
                "execution_time": end_time - start_time,
                "has_answer": bool(final_state.get('final_answer')),
                "errors": final_state.get('error_messages', [])
            }
            
            results.append(result)
            
            # Print summary
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['mode']}/{result['route']} - "
                  f"{result['iterations']} iter, {result['chunks']} chunks, "
                  f"{result['execution_time']:.1f}s")
            
            if result["errors"]:
                print(f"   ⚠️  Errors: {result['errors']}")
                
        except Exception as e:
            print(f"   💥 FAILED: {e}")
            results.append({
                "query": query,
                "success": False,
                "error": str(e)
            })
    
    # Print overall summary
    print(f"\n📊 BATCH TEST SUMMARY")
    print("=" * 40)
    
    successful = sum(1 for r in results if r.get("success", False))
    print(f"Success Rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    
    if successful > 0:
        avg_time = sum(r.get("execution_time", 0) for r in results if r.get("success")) / successful
        avg_chunks = sum(r.get("chunks", 0) for r in results if r.get("success")) / successful
        avg_iterations = sum(r.get("iterations", 0) for r in results if r.get("success")) / successful
        
        print(f"Avg Execution Time: {avg_time:.2f}s")
        print(f"Avg Chunks Retrieved: {avg_chunks:.1f}")
        print(f"Avg Iterations: {avg_iterations:.1f}")
    
    return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test Enhanced Iterative Planner v2")
    parser.add_argument("--query", "-q", help="Single query to test")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--batch", "-b", help="File containing queries for batch testing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--stream", "-s", action="store_true", help="Stream execution updates")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        if args.interactive:
            interactive_mode()
            
        elif args.batch:
            # Load queries from file
            with open(args.batch, 'r') as f:
                queries = [line.strip() for line in f if line.strip()]
            batch_test_mode(queries)
            
        elif args.query:
            # Single query mode
            query = args.query
            print(f"🚀 Testing single query: {query}")
            print("-" * 60)
            
            if args.stream:
                print("📡 Streaming execution...")
                for update in stream_v2_agent(query):
                    node_name = list(update.keys())[0]
                    state = update[node_name]
                    print(f"Update from {node_name}: {state.get('iteration_count', 0)} iterations")
            else:
                final_state = run_v2_agent(query)
                
                print("\n📊 EXECUTION SUMMARY")
                print("=" * 40)
                print(format_state_summary(final_state))
                
                print(f"\n📝 FINAL ANSWER")
                print("=" * 40)
                print(format_final_answer(final_state))
        else:
            # Default test queries
            default_queries = [
                "What is BAC's CET1 ratio in 2024?",
                "Compare JPM and GS revenue trends",
                "What data do you have available?",
                "Comprehensive analysis of Wells Fargo risk factors from 2024",
                "From BAC 2025 10-K filing, what are the main business segments?"
            ]
            
            print("🧪 Running default test suite")
            batch_test_mode(default_queries)
            
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()