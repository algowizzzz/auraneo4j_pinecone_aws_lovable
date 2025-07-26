#!/usr/bin/env python3
"""
Simple UAT Tester - Command Line Interface
Alternative to Streamlit for quick testing
"""

import os
import sys
import time
import json
from datetime import datetime

# Add current directory to path  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SimpleUATTester:
    def __init__(self):
        self.agent = None
        self.test_results = []
        
    def load_agent(self):
        """Load the SEC Graph Agent"""
        try:
            print("🔄 Loading SEC Graph Agent...")
            from agent.graph import build_graph
            self.agent = build_graph()
            print("✅ Agent loaded successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to load agent: {e}")
            return False
    
    def get_test_queries(self):
        """Predefined test queries"""
        return {
            "1": {
                "name": "Goldman Sachs Balance Sheet",
                "query": "From Goldman Sachs (GS) 2025 10-K filing, what are the total assets, total deposits, and shareholders' equity as of year-end? Provide the specific balance sheet figures and any notable changes mentioned.",
                "metadata": {"company": "GS", "year": "2025"}
            },
            "2": {
                "name": "Bank of America MD&A", 
                "query": "Based on Bank of America (BAC) 2025 10-K MD&A section, what were the key factors that management highlighted as driving their financial performance? Include specific commentary on revenue trends and expense management.",
                "metadata": {"company": "BAC", "year": "2025"}
            },
            "3": {
                "name": "Wells Fargo Risk Factors",
                "query": "What are the primary risk factors disclosed in Wells Fargo (WFC) 2025 10-K filing? Focus on credit risk, operational risk, and any new risk factors identified for 2025.",
                "metadata": {"company": "WFC", "year": "2025"}
            },
            "4": {
                "name": "Morgan Stanley Metrics",
                "query": "From Morgan Stanley (MS) 2025 10-K, what are the net revenues, net income, and return on equity for 2024? Also include any forward-looking guidance or outlook mentioned.",
                "metadata": {"company": "MS", "year": "2025"}
            },
            "5": {
                "name": "Truist Capital",
                "query": "According to Truist Financial (TFC) 2025 10-K filing, what are their Tier 1 capital ratio, liquidity coverage ratio, and any regulatory capital requirements mentioned? Include management's commentary on capital adequacy.",
                "metadata": {"company": "TFC", "year": "2025"}
            }
        }
    
    def test_query(self, query, metadata=None):
        """Test a single query"""
        if not self.agent:
            print("❌ Agent not loaded. Run load_agent() first.")
            return None
        
        print(f"\n🔍 Testing Query: {query[:80]}...")
        print("-" * 80)
        
        start_time = time.time()
        
        try:
            # Create initial state
            initial_state = {
                "query_raw": query,
                "metadata": metadata or {}
            }
            
            # Execute query
            result = self.agent.invoke(initial_state)
            execution_time = time.time() - start_time
            
            # Analyze results
            final_answer = result.get("final_answer", "") or result.get("master_answer", "")
            retrievals = result.get("retrievals", [])
            route = result.get("route", "unknown")
            
            # Check for issues
            issues = []
            if "XX" in final_answer or "placeholder" in final_answer.lower():
                issues.append("⚠️ Contains placeholder values")
            
            # Analyze company distribution
            company_dist = {}
            for hit in retrievals:
                company = hit.get("metadata", {}).get("company", "Unknown")
                company_dist[company] = company_dist.get(company, 0) + 1
            
            # Check for cross-company contamination
            if metadata and metadata.get("company"):
                expected_company = metadata["company"]
                other_companies = [c for c in company_dist.keys() if c != expected_company and c != "Unknown"]
                if other_companies:
                    issues.append(f"⚠️ Cross-company contamination: {other_companies}")
            
            # Display results
            print(f"⏱️  Execution Time: {execution_time:.2f}s")
            print(f"🛣️  Route: {route}")
            print(f"📄 Retrievals: {len(retrievals)}")
            print(f"🏢 Company Distribution: {company_dist}")
            
            # Document sources analysis
            if retrievals:
                documents = {}
                for hit in retrievals:
                    filename = hit.get("metadata", {}).get("filename", hit.get("id", "unknown"))
                    company = hit.get("metadata", {}).get("company", "Unknown")
                    
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
                    
                    if doc_title not in documents:
                        documents[doc_title] = {"company": company, "chunks": 0}
                    documents[doc_title]["chunks"] += 1
                
                print(f"📋 Document Sources ({len(documents)} documents):")
                for doc_title, doc_info in sorted(documents.items(), key=lambda x: x[1]["chunks"], reverse=True):
                    print(f"   • {doc_title} ({doc_info['chunks']} chunks)")
            
            if issues:
                print(f"⚠️  Issues Found:")
                for issue in issues:
                    print(f"   {issue}")
            else:
                print("✅ No issues detected!")
            
            print(f"\n💡 Answer:")
            print("-" * 40)
            print(final_answer[:500] + "..." if len(final_answer) > 500 else final_answer)
            print("-" * 40)
            
            # Save test result
            test_result = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "metadata": metadata,
                "execution_time": execution_time,
                "route": route,
                "retrievals_count": len(retrievals),
                "company_distribution": company_dist,
                "issues": issues,
                "has_placeholders": any("placeholder" in issue.lower() for issue in issues)
            }
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def run_all_tests(self):
        """Run all predefined test queries"""
        queries = self.get_test_queries()
        
        print(f"\n🧪 Running All UAT Tests ({len(queries)} queries)")
        print("=" * 80)
        
        for key, test_case in queries.items():
            print(f"\n📋 Test {key}: {test_case['name']}")
            self.test_query(test_case["query"], test_case["metadata"])
            
            # Wait a moment between tests
            time.sleep(1)
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        if not self.test_results:
            print("No test results available.")
            return
        
        print(f"\n📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        avg_time = sum(r["execution_time"] for r in self.test_results) / total_tests
        tests_with_issues = sum(1 for r in self.test_results if r["issues"])
        tests_with_placeholders = sum(1 for r in self.test_results if r["has_placeholders"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Average Response Time: {avg_time:.2f}s")
        print(f"Tests with Issues: {tests_with_issues}")
        print(f"Tests with Placeholders: {tests_with_placeholders}")
        
        if tests_with_issues == 0:
            print("🎉 All tests passed without issues!")
        else:
            print(f"⚠️  {tests_with_issues} tests had issues - review above")
    
    def export_results(self, filename=None):
        """Export test results to JSON"""
        if not filename:
            filename = f"uat_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"📁 Results exported to: {filename}")
    
    def interactive_mode(self):
        """Interactive testing mode"""
        queries = self.get_test_queries()
        
        while True:
            print(f"\n🧪 SEC Graph Agent - UAT Testing")
            print("=" * 40)
            print("Predefined Tests:")
            for key, test_case in queries.items():
                print(f"  {key}: {test_case['name']}")
            print("  c: Custom query")
            print("  a: Run all tests")
            print("  s: Show summary")
            print("  e: Export results")
            print("  q: Quit")
            
            choice = input("\nChoose an option: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == 'a':
                self.run_all_tests()
            elif choice == 's':
                self.print_summary()
            elif choice == 'e':
                self.export_results()
            elif choice == 'c':
                query = input("Enter your query: ").strip()
                if query:
                    company = input("Company filter (optional): ").strip()
                    year = input("Year filter (optional): ").strip()
                    
                    metadata = {}
                    if company:
                        metadata["company"] = company.upper()
                    if year:
                        metadata["year"] = year
                    
                    self.test_query(query, metadata)
            elif choice in queries:
                test_case = queries[choice]
                self.test_query(test_case["query"], test_case["metadata"])
            else:
                print("Invalid choice. Please try again.")

def main():
    tester = SimpleUATTester()
    
    # Load agent
    if not tester.load_agent():
        return
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            tester.run_all_tests()
            tester.export_results()
        elif sys.argv[1].isdigit() and sys.argv[1] in tester.get_test_queries():
            test_case = tester.get_test_queries()[sys.argv[1]]
            tester.test_query(test_case["query"], test_case["metadata"])
        else:
            print("Usage: python simple_uat_tester.py [all|1|2|3|4|5]")
    else:
        # Interactive mode
        tester.interactive_mode()

if __name__ == "__main__":
    main()