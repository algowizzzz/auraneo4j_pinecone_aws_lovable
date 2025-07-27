#!/usr/bin/env python3
"""
Enhanced UAT Testing UI - V1 vs V2 Agent Comparison
Streamlit interface to test both existing agent and Enhanced Iterative Planner v2
"""

import streamlit as st
import sys
import os
import time
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set page config
st.set_page_config(
    page_title="SEC Graph Agent - V1 vs V2 Comparison",
    page_icon="⚡",
    layout="wide"
)

@st.cache_resource
def load_v1_agent():
    """Load the existing (v1) SEC Graph Agent"""
    try:
        from agent.graph import build_graph
        return build_graph()
    except Exception as e:
        st.error(f"Failed to load V1 agent: {e}")
        return None

@st.cache_resource
def load_v2_agent():
    """Load the Enhanced Iterative Planner (v2) Agent"""
    try:
        from v2 import create_v2_agent
        return create_v2_agent()
    except Exception as e:
        st.error(f"Failed to load V2 agent: {e}")
        return None

def format_v1_result(result, execution_time):
    """Format V1 agent result for display"""
    return {
        "success": bool(result.get("final_answer") or result.get("master_answer")),
        "execution_time": execution_time,
        "final_answer": result.get("final_answer", "") or result.get("master_answer", ""),
        "route": result.get("route", "unknown"),
        "retrievals": len(result.get("retrievals", [])),
        "tools_used": result.get("tools_used", []),
        "metadata": result.get("metadata", {}),
        "raw_result": result
    }

def format_v2_result(result, execution_time):
    """Format V2 agent result for display"""
    return {
        "success": result.get("is_complete", False),
        "execution_time": execution_time,
        "final_answer": result.get("final_answer", ""),
        "planner_mode": result.get("planner_mode", "unknown"),
        "route": result.get("route", "unknown"),
        "chunks": len(result.get("accumulated_chunks", [])),
        "iterations": result.get("iteration_count", 0),
        "completion_reason": result.get("completion_reason", ""),
        "planner_decisions": result.get("planner_decisions", []),
        "metadata": result.get("plan_metadata", {}),
        "progressive_stats": result.get("progressive_stats", {}),
        "error_messages": result.get("error_messages", []),
        "pending_clarification": result.get("pending_clarification"),
        "raw_result": result
    }

def display_v2_chunks(v2_result):
    """Display the chunks retrieved by v2 agent in a user-friendly format"""
    chunks = v2_result.get("accumulated_chunks", [])
    
    if not chunks:
        st.write("No chunks retrieved")
        return
    
    # Group chunks by route/source for better organization
    chunks_by_route = {}
    for chunk in chunks:
        # Check both locations for source info
        route = chunk.get("metadata", {}).get("source") or chunk.get("source", "unknown")
        if route not in chunks_by_route:
            chunks_by_route[route] = []
        chunks_by_route[route].append(chunk)
    
    # Display chunks organized by route
    for route, route_chunks in chunks_by_route.items():
        st.write(f"**📊 From {route.upper()} ({len(route_chunks)} chunks):**")
        
        for i, chunk in enumerate(route_chunks, 1):
            metadata = chunk.get("metadata", {})
            text = chunk.get("text", "No text available")
            score = chunk.get("score", 0.0)
            
            # Create a concise header for each chunk
            chunk_info = []
            if metadata.get("company"):
                chunk_info.append(f"Company: {metadata['company']}")
            if metadata.get("year"):
                chunk_info.append(f"Year: {metadata['year']}")
            if metadata.get("doc_type"):
                chunk_info.append(f"Doc: {metadata['doc_type']}")
            if metadata.get("section_name"):
                # Truncate long section names
                section = metadata['section_name']
                if len(section) > 50:
                    section = section[:47] + "..."
                chunk_info.append(f"Section: {section}")
            elif metadata.get("source_filename"):
                chunk_info.append(f"File: {metadata['source_filename']}")
            
            chunk_header = " | ".join(chunk_info) if chunk_info else f"Chunk {i}"
            
            with st.container():
                st.write(f"**{i}.** {chunk_header} (Score: {score:.3f})")
                
                # Show a preview of the text (first 200 characters)
                text_preview = text[:200] + "..." if len(text) > 200 else text
                st.write(f"*Preview:* {text_preview}")
                
                # Option to view full text
                if len(text) > 200:
                    with st.expander(f"View full chunk {i} text ({len(text)} characters)"):
                        st.text(text)
                
                st.write("")  # Add spacing
        
        st.write("")  # Add spacing between routes


def display_comparison_results(v1_formatted, v2_formatted, v2_raw=None):
    """Display side-by-side comparison of results"""
    
    # Success and timing comparison
    st.subheader("⚡ Performance Comparison")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        v1_status = "✅" if v1_formatted["success"] else "❌"
        st.metric("V1 Success", v1_status)
    
    with col2:
        v2_status = "✅" if v2_formatted["success"] else "❌"
        st.metric("V2 Success", v2_status)
    
    with col3:
        st.metric("V1 Time", f"{v1_formatted['execution_time']:.2f}s")
    
    with col4:
        st.metric("V2 Time", f"{v2_formatted['execution_time']:.2f}s")
    
    # Routing and approach comparison
    st.subheader("🛣️ Routing & Approach")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**V1 Agent (Traditional)**")
        st.write(f"• Route: {v1_formatted['route']}")
        st.write(f"• Retrievals: {v1_formatted['retrievals']}")
        st.write(f"• Tools: {', '.join(v1_formatted['tools_used']) if v1_formatted['tools_used'] else 'None'}")
    
    with col2:
        st.write("**V2 Agent (Enhanced Iterative Planner)**")
        st.write(f"• Mode: {v2_formatted['planner_mode']}")
        st.write(f"• Route: {v2_formatted['route']}")
        st.write(f"• Iterations: {v2_formatted['iterations']}")
        st.write(f"• Chunks: {v2_formatted['chunks']}")
        st.write(f"• Completion: {v2_formatted['completion_reason']}")
    
    # Answer comparison
    st.subheader("💬 Answer Comparison")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**V1 Answer:**")
        if v1_formatted["final_answer"]:
            st.write(v1_formatted["final_answer"])
        else:
            st.write("*No answer generated*")
    
    with col2:
        st.write("**V2 Answer:**")
        if v2_formatted["final_answer"]:
            st.write(v2_formatted["final_answer"])
        else:
            st.write("*No answer generated*")
    
    # V2 Specific Features
    if v2_formatted["planner_decisions"]:
        st.subheader("🧠 V2 Planner Decisions")
        with st.expander("View Planner Decision Log"):
            for i, decision in enumerate(v2_formatted["planner_decisions"], 1):
                st.write(f"**{i}. {decision['decision_type'].title()}**: {decision['decision']}")
                st.write(f"   *Reasoning*: {decision['reasoning']}")
                st.write(f"   *Iteration*: {decision['iteration']}")
                st.write("")
    
    # V2 Chunks Used
    if v2_formatted["chunks"] > 0 and v2_raw:
        st.subheader("📄 V2 Chunks Retrieved")
        with st.expander(f"View {v2_formatted['chunks']} Retrieved Chunks"):
            display_v2_chunks(v2_raw)
    
    # Pending clarifications
    if v2_formatted["pending_clarification"]:
        st.subheader("❓ V2 Clarification Request")
        clarification = v2_formatted["pending_clarification"]
        st.warning(f"**Question**: {clarification['question']}")
        if clarification.get("options"):
            st.write(f"**Options**: {', '.join(clarification['options'])}")
        st.write(f"**Context**: {clarification['context']}")
    
    # Error handling
    if v2_formatted["error_messages"]:
        st.subheader("⚠️ V2 Error Messages")
        for error in v2_formatted["error_messages"]:
            st.error(error)

def main():
    st.title("⚡ SEC Graph Agent - V1 vs V2 Comparison")
    st.markdown("Compare the traditional agent with the Enhanced Iterative Planner v2")
    st.markdown("---")
    
    # Agent loading
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 V1 Agent (Traditional)")
        with st.spinner("Loading V1 agent..."):
            v1_agent = load_v1_agent()
        
        if v1_agent:
            st.success("✅ V1 Agent loaded")
        else:
            st.error("❌ V1 Agent failed to load")
    
    with col2:
        st.subheader("⚡ V2 Agent (Enhanced Iterative Planner)")
        with st.spinner("Loading V2 agent..."):
            v2_agent = load_v2_agent()
        
        if v2_agent:
            st.success("✅ V2 Agent loaded")
        else:
            st.error("❌ V2 Agent failed to load")
    
    if not (v1_agent or v2_agent):
        st.error("❌ No agents available. Please check your environment setup.")
        return
    
    # Sidebar with predefined test queries
    st.sidebar.header("🧪 Test Queries")
    
    test_queries = {
        "Introspection Query": "What data do you have available?",
        "Simple Factual": "What is BAC's CET1 ratio in 2024?", 
        "Comprehensive Analysis": "Comprehensive analysis of BAC risk factors from 2024",
        "Comparison Query": "Compare JPM and GS revenue trends",
        "Semantic Query": "What are the main risks for investment banks?",
        "Goldman Sachs Balance Sheet": "From Goldman Sachs (GS) 2025 10-K filing, what are the total assets, total deposits, and shareholders' equity?",
        "Bank of America MD&A": "Based on Bank of America (BAC) 2025 10-K MD&A section, what were the key factors driving financial performance?",
        "Wells Fargo Risk Factors": "What are the primary risk factors in Wells Fargo (WFC) 2025 10-K filing?"
    }
    
    selected_query = st.sidebar.selectbox(
        "Choose a test query:",
        ["Custom Query"] + list(test_queries.keys())
    )
    
    # Agent selection
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Agent Selection")
    run_v1 = st.sidebar.checkbox("Run V1 Agent", value=bool(v1_agent))
    run_v2 = st.sidebar.checkbox("Run V2 Agent", value=bool(v2_agent))
    
    if not (run_v1 or run_v2):
        st.warning("Please select at least one agent to run.")
        return
    
    # Main query input
    st.header("🔍 Query Input")
    
    if selected_query == "Custom Query":
        query = st.text_area(
            "Enter your question about SEC filings:",
            height=100,
            placeholder="e.g., What are JPMorgan's main risk factors in their 2024 10-K?"
        )
    else:
        query = st.text_area(
            "Query (editable):",
            value=test_queries[selected_query],
            height=100
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_filter = st.selectbox(
                "Company Filter (optional):", 
                ["", "GS", "MS", "BAC", "WFC", "TFC", "JPM", "KEY", "ZION", "FITB", "RF"]
            )
            
        with col2:
            year_filter = st.selectbox("Year Filter (optional):", ["", "2024", "2025"])
        
        show_raw_results = st.checkbox("Show Raw Results", value=False)
    
    # Execute query button
    if st.button("🚀 Execute Comparison", type="primary"):
        if not query.strip():
            st.warning("Please enter a query first.")
            return
        
        # Build metadata for V1
        metadata = {}
        if company_filter:
            metadata["company"] = company_filter
        if year_filter:
            metadata["year"] = year_filter
        
        results = {}
        
        # Execute V1 Agent
        if run_v1 and v1_agent:
            st.markdown("---")
            st.header("🔧 V1 Agent Execution")
            
            with st.spinner("Running V1 agent..."):
                try:
                    start_time = time.time()
                    initial_state = {"query_raw": query, "metadata": metadata}
                    v1_result = v1_agent.invoke(initial_state)
                    v1_time = time.time() - start_time
                    
                    results["v1"] = format_v1_result(v1_result, v1_time)
                    st.success(f"✅ V1 completed in {v1_time:.2f}s")
                    
                except Exception as e:
                    st.error(f"❌ V1 execution failed: {e}")
                    results["v1"] = {"success": False, "error": str(e), "execution_time": 0}
        
        # Execute V2 Agent
        if run_v2 and v2_agent:
            st.header("⚡ V2 Agent Execution")
            
            with st.spinner("Running V2 Enhanced Iterative Planner..."):
                try:
                    # Import V2 execution function
                    from v2 import run_v2_agent
                    
                    start_time = time.time()
                    v2_result = run_v2_agent(query)
                    v2_time = time.time() - start_time
                    
                    results["v2"] = format_v2_result(v2_result, v2_time)
                    results["v2_raw"] = v2_result  # Store raw result for chunk display
                    st.success(f"✅ V2 completed in {v2_time:.2f}s")
                    
                except Exception as e:
                    st.error(f"❌ V2 execution failed: {e}")
                    results["v2"] = {"success": False, "error": str(e), "execution_time": 0}
        
        # Display comparison results
        if results:
            st.markdown("---")
            st.header("📊 Comparison Results")
            
            if "v1" in results and "v2" in results:
                v2_raw = results.get("v2_raw")
                display_comparison_results(results["v1"], results["v2"], v2_raw)
            
            elif "v1" in results:
                st.subheader("🔧 V1 Results")
                if results["v1"]["success"]:
                    st.write(results["v1"]["final_answer"])
                else:
                    st.error(f"V1 failed: {results['v1'].get('error', 'Unknown error')}")
            
            elif "v2" in results:
                st.subheader("⚡ V2 Results")
                if results["v2"]["success"]:
                    st.write(results["v2"]["final_answer"])
                    
                    # Show V2 specific info
                    st.write(f"**Mode**: {results['v2']['planner_mode']}")
                    st.write(f"**Iterations**: {results['v2']['iterations']}")
                    st.write(f"**Chunks**: {results['v2']['chunks']}")
                else:
                    st.error(f"V2 failed: {results['v2'].get('error', 'Unknown error')}")
            
            # Show raw results if requested
            if show_raw_results:
                st.markdown("---")
                st.header("🔍 Raw Results")
                
                for agent_name, result in results.items():
                    if "raw_result" in result:
                        with st.expander(f"{agent_name.upper()} Raw Result"):
                            st.json(result["raw_result"])

    # Help section
    with st.sidebar.expander("ℹ️ Help"):
        st.markdown("""
        **V1 Agent**: Traditional LangGraph routing
        - Fixed routing based on initial planning
        - Single-pass retrieval and synthesis
        - Standard error handling
        
        **V2 Agent**: Enhanced Iterative Planner
        - Dynamic mode detection (semantic vs structured)
        - Iterative metadata discovery
        - Progressive retrieval with self-critique
        - Adaptive query refinement
        - User clarification requests
        - Introspection query handling
        
        **Test Query Types**:
        - *Introspection*: Should be instant with V2
        - *Simple Factual*: Small, specific data requests
        - *Comprehensive*: Deep analysis requiring iteration
        - *Comparison*: Multi-entity analysis
        """)

if __name__ == "__main__":
    main()