#!/usr/bin/env python3
"""
UAT Testing UI - Interactive Interface for Business Users
Simple Streamlit interface to test SEC Graph Agent responses
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
    page_title="SEC Graph Agent - UAT Testing",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def load_agent():
    """Load the SEC Graph Agent"""
    try:
        from agent.graph import build_graph
        return build_graph()
    except Exception as e:
        st.error(f"Failed to load agent: {e}")
        return None

def main():
    st.title("📊 SEC Graph Agent - UAT Testing Interface")
    st.markdown("---")
    
    # Load agent
    with st.spinner("Loading SEC Graph Agent..."):
        agent = load_agent()
    
    if not agent:
        st.error("❌ Failed to load the agent. Please check your environment setup.")
        return
    
    st.success("✅ SEC Graph Agent loaded successfully!")
    
    # Sidebar with predefined test queries
    st.sidebar.header("🧪 Predefined Test Queries")
    
    test_queries = {
        "Q1 - Goldman Sachs Balance Sheet": "From Goldman Sachs (GS) 2025 10-K filing, what are the total assets, total deposits, and shareholders' equity as of year-end? Provide the specific balance sheet figures and any notable changes mentioned.",
        
        "Q2 - Bank of America MD&A": "Based on Bank of America (BAC) 2025 10-K MD&A section, what were the key factors that management highlighted as driving their financial performance? Include specific commentary on revenue trends and expense management.",
        
        "Q3 - Wells Fargo Risk Factors": "What are the primary risk factors disclosed in Wells Fargo (WFC) 2025 10-K filing? Focus on credit risk, operational risk, and any new risk factors identified for 2025.",
        
        "Q4 - Morgan Stanley Metrics": "From Morgan Stanley (MS) 2025 10-K, what are the net revenues, net income, and return on equity for 2024? Also include any forward-looking guidance or outlook mentioned.",
        
        "Q5 - Truist Capital": "According to Truist Financial (TFC) 2025 10-K filing, what are their Tier 1 capital ratio, liquidity coverage ratio, and any regulatory capital requirements mentioned? Include management's commentary on capital adequacy."
    }
    
    selected_query = st.sidebar.selectbox(
        "Choose a test query:",
        ["Custom Query"] + list(test_queries.keys())
    )
    
    # Main query input
    col1, col2 = st.columns([2, 1])
    
    with col1:
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
    
    with col2:
        st.header("⚙️ Settings")
        
        # Company filter
        companies = ["", "GS", "MS", "BAC", "WFC", "TFC", "JPM", "KEY", "ZION", "FITB", "RF"]
        company_filter = st.selectbox("Company Filter (optional):", companies)
        
        # Year filter
        years = ["", "2024", "2025"]
        year_filter = st.selectbox("Year Filter (optional):", years)
        
        # Show debug info
        show_debug = st.checkbox("Show Debug Information", value=False)
    
    # Execute query button
    if st.button("🚀 Execute Query", type="primary"):
        if not query.strip():
            st.warning("Please enter a query first.")
            return
        
        # Build metadata
        metadata = {}
        if company_filter:
            metadata["company"] = company_filter
        if year_filter:
            metadata["year"] = year_filter
        
        # Execute query
        with st.spinner("Processing query..."):
            start_time = time.time()
            
            try:
                # Create initial state
                initial_state = {
                    "query_raw": query,
                    "metadata": metadata
                }
                
                # Execute through agent
                result = agent.invoke(initial_state)
                execution_time = time.time() - start_time
                
                # Display results
                st.markdown("---")
                st.header("📋 Results")
                
                # Main answer
                final_answer = result.get("final_answer", "") or result.get("master_answer", "")
                
                if final_answer:
                    st.subheader("💡 Answer")
                    st.write(final_answer)
                    
                    # Check for issues
                    issues = []
                    if "XX" in final_answer or "placeholder" in final_answer.lower():
                        issues.append("⚠️ Contains placeholder values")
                    
                    if issues:
                        st.warning("Issues detected:")
                        for issue in issues:
                            st.write(f"- {issue}")
                    else:
                        st.success("✅ No issues detected")
                    
                    # Document Sources Section
                    retrievals = result.get("retrievals", [])
                    if retrievals:
                        st.markdown("---")
                        st.subheader("📄 Document Sources Used")
                        
                        # Extract unique documents and their details
                        documents = {}
                        for hit in retrievals:
                            doc_id = hit.get("id", "unknown")
                            metadata = hit.get("metadata", {})
                            
                            # Extract document info
                            filename = metadata.get("filename", doc_id)
                            company = metadata.get("company", "Unknown")
                            form_type = metadata.get("form_type", "Unknown")
                            
                            # Parse filename for better display
                            if "_" in filename:
                                parts = filename.split("_")
                                if len(parts) >= 3:
                                    doc_company = parts[0].upper()
                                    doc_type = parts[1].upper()
                                    doc_date = parts[2]
                                    
                                    # Format date
                                    if len(doc_date) == 8:  # YYYYMMDD
                                        formatted_date = f"{doc_date[:4]}-{doc_date[4:6]}-{doc_date[6:8]}"
                                    else:
                                        formatted_date = doc_date
                                    
                                    doc_title = f"{doc_company} {doc_type} Filing ({formatted_date})"
                                else:
                                    doc_title = filename
                            else:
                                doc_title = filename
                            
                            # Count chunks per document
                            if doc_title not in documents:
                                documents[doc_title] = {
                                    "company": company,
                                    "form_type": form_type,
                                    "filename": filename,
                                    "chunks": 0,
                                    "avg_score": 0,
                                    "scores": []
                                }
                            
                            documents[doc_title]["chunks"] += 1
                            documents[doc_title]["scores"].append(hit.get("score", 0))
                        
                        # Calculate average scores
                        for doc_info in documents.values():
                            if doc_info["scores"]:
                                doc_info["avg_score"] = sum(doc_info["scores"]) / len(doc_info["scores"])
                        
                        # Display document list
                        st.write(f"**Total Documents Used: {len(documents)}**")
                        
                        # Create expandable sections for each document
                        for doc_title, doc_info in sorted(documents.items(), key=lambda x: x[1]["avg_score"], reverse=True):
                            with st.expander(f"📋 {doc_title} ({doc_info['chunks']} chunks, avg score: {doc_info['avg_score']:.3f})"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"**Company:** {doc_info['company']}")
                                with col2:
                                    st.write(f"**Form Type:** {doc_info['form_type']}")
                                with col3:
                                    st.write(f"**Filename:** {doc_info['filename']}")
                                
                                # Show chunk details for this document
                                doc_chunks = [hit for hit in retrievals if hit.get("metadata", {}).get("filename", hit.get("id")) == doc_info["filename"]]
                                if doc_chunks:
                                    st.write("**Chunks used from this document:**")
                                    for i, chunk in enumerate(doc_chunks[:3]):  # Show top 3 chunks
                                        chunk_id = chunk.get("id", "unknown")
                                        score = chunk.get("score", 0)
                                        text_preview = chunk.get("text", "")[:150]
                                        st.write(f"• Chunk {i+1} (Score: {score:.3f}): {text_preview}...")
                                
                        # Company distribution summary
                        company_counts = {}
                        for doc_info in documents.values():
                            company = doc_info["company"]
                            company_counts[company] = company_counts.get(company, 0) + 1
                        
                        st.write("**Documents by Company:**")
                        for company, count in sorted(company_counts.items()):
                            st.write(f"• {company}: {count} document(s)")
                        
                        # Validate company filtering
                        if company_filter and company_counts:
                            expected_company = company_filter
                            other_companies = [c for c in company_counts.keys() if c.upper() != expected_company.upper() and c != "Unknown"]
                            if other_companies:
                                st.warning(f"⚠️ Cross-company contamination detected: Found documents from {other_companies} when filtering for {expected_company}")
                            else:
                                st.success(f"✅ Clean company filtering: All documents are from {expected_company}")
                    
                else:
                    st.error("❌ No answer generated")
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Execution Time", f"{execution_time:.2f}s")
                
                with col2:
                    retrievals = len(result.get("retrievals", []))
                    st.metric("Retrievals", retrievals)
                
                with col3:
                    route = result.get("route", "unknown")
                    st.metric("Route", route)
                
                with col4:
                    valid = result.get("valid", False)
                    st.metric("Valid", "✅" if valid else "❌")
                
                # Debug information
                if show_debug:
                    st.markdown("---")
                    st.header("🔧 Debug Information")
                    
                    # Retrievals
                    retrievals = result.get("retrievals", [])
                    if retrievals:
                        st.subheader("📄 Retrieved Documents")
                        
                        # Company analysis
                        companies_found = {}
                        for hit in retrievals:
                            company = hit.get("metadata", {}).get("company", "Unknown")
                            companies_found[company] = companies_found.get(company, 0) + 1
                        
                        st.write("**Company Distribution:**")
                        for company, count in companies_found.items():
                            st.write(f"- {company}: {count} documents")
                        
                        # Top retrievals
                        st.write("**Top 5 Retrievals:**")
                        for i, hit in enumerate(retrievals[:5]):
                            with st.expander(f"Document {i+1} - Score: {hit.get('score', 0):.3f}"):
                                st.write(f"**ID:** {hit.get('id', 'unknown')}")
                                st.write(f"**Company:** {hit.get('metadata', {}).get('company', 'Unknown')}")
                                st.write(f"**Text Preview:** {hit.get('text', '')[:200]}...")
                    
                    # Full state
                    with st.expander("Full Agent State"):
                        st.json(result, expanded=False)
                
                # Save test result
                test_result = {
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "metadata": metadata,
                    "execution_time": execution_time,
                    "route": route,
                    "retrievals_count": len(result.get("retrievals", [])),
                    "has_placeholder": "XX" in final_answer if final_answer else False,
                    "company_distribution": {}
                }
                
                # Analyze company distribution
                for hit in result.get("retrievals", []):
                    company = hit.get("metadata", {}).get("company", "Unknown")
                    test_result["company_distribution"][company] = test_result["company_distribution"].get(company, 0) + 1
                
                # Add to session state for tracking
                if "test_results" not in st.session_state:
                    st.session_state.test_results = []
                st.session_state.test_results.append(test_result)
                
            except Exception as e:
                st.error(f"❌ Error executing query: {str(e)}")
                if show_debug:
                    st.exception(e)
    
    # Test history
    if "test_results" in st.session_state and st.session_state.test_results:
        st.markdown("---")
        st.header("📊 Test History")
        
        # Summary metrics
        results = st.session_state.test_results
        total_tests = len(results)
        avg_time = sum(r["execution_time"] for r in results) / total_tests
        placeholder_count = sum(1 for r in results if r["has_placeholder"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tests", total_tests)
        with col2:
            st.metric("Avg Response Time", f"{avg_time:.2f}s")
        with col3:
            st.metric("Placeholder Issues", placeholder_count)
        
        # Export results
        if st.button("📥 Export Test Results"):
            results_json = json.dumps(st.session_state.test_results, indent=2)
            st.download_button(
                label="Download JSON",
                data=results_json,
                file_name=f"uat_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        # Clear history
        if st.button("🗑️ Clear History"):
            st.session_state.test_results = []
            st.rerun()

if __name__ == "__main__":
    main()