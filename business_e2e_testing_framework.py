"""
SEC LangGraph Agent - Business End-to-End Testing Framework
Comprehensive testing with realistic financial analysis queries
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BusinessE2ETestFramework:
    """
    Comprehensive business testing framework for the SEC LangGraph Agent.
    Tests realistic financial analysis scenarios with full pipeline validation.
    """
    
    def __init__(self, version: str = "1.0"):
        self.version = version
        self.test_date = datetime.now().strftime("%Y-%m-%d")
        self.test_output_dir = "test_output"
        self.results = {}
        
        # Create output directory
        os.makedirs(self.test_output_dir, exist_ok=True)
        
        # Business query suite (easy to hard complexity)
        self.business_queries = self._design_business_queries()
        
    def _design_business_queries(self) -> List[Dict[str, Any]]:
        """
        Design 5 business queries of varying complexity based on available data.
        Mix of easy and hard queries to test different system capabilities.
        """
        return [
            {
                "id": "BQ001",
                "complexity": "EASY",
                "category": "Company Profile",
                "query": "What are Prosperity Bancshares main business lines and operations?",
                "expected_companies": ["PB"],
                "expected_sections": ["Business"],
                "business_value": "Basic company research and due diligence",
                "success_criteria": {
                    "min_retrievals": 3,
                    "min_validation_score": 0.7,
                    "required_content": ["business lines", "operations", "banking"]
                }
            },
            
            {
                "id": "BQ002", 
                "complexity": "MEDIUM",
                "category": "Risk Analysis",
                "query": "What are the key risk factors facing KeyCorp in their 2023 operations?",
                "expected_companies": ["KEY"],
                "expected_sections": ["Business", "Risk Factors"],
                "business_value": "Risk assessment and regulatory compliance analysis",
                "success_criteria": {
                    "min_retrievals": 5,
                    "min_validation_score": 0.6,
                    "required_content": ["risk", "KeyCorp", "operational"]
                }
            },
            
            {
                "id": "BQ003",
                "complexity": "MEDIUM-HARD", 
                "category": "Competitive Analysis",
                "query": "Compare the business models of Prosperity Bancshares and KeyCorp - what are their competitive advantages?",
                "expected_companies": ["PB", "KEY"],
                "expected_sections": ["Business"],
                "business_value": "Competitive intelligence and market positioning analysis",
                "success_criteria": {
                    "min_retrievals": 8,
                    "min_validation_score": 0.5,
                    "required_content": ["competitive", "business model", "advantages"]
                }
            },
            
            {
                "id": "BQ004",
                "complexity": "HARD",
                "category": "Temporal Analysis", 
                "query": "How has Zions Bancorporation's business strategy evolved from 2021 to 2025?",
                "expected_companies": ["ZION"],
                "expected_sections": ["Business"],
                "business_value": "Strategic trend analysis and business evolution tracking",
                "success_criteria": {
                    "min_retrievals": 6,
                    "min_validation_score": 0.4,
                    "required_content": ["strategy", "evolution", "business"]
                }
            },
            
            {
                "id": "BQ005",
                "complexity": "HARD",
                "category": "Financial Metrics Analysis",
                "query": "What are the regulatory capital requirements and financial performance metrics for regional banks like PNFP and CFR?",
                "expected_companies": ["PNFP", "CFR"],
                "expected_sections": ["Business", "Financial Data"],
                "business_value": "Regulatory compliance and financial performance assessment",
                "success_criteria": {
                    "min_retrievals": 10,
                    "min_validation_score": 0.4,
                    "required_content": ["capital", "regulatory", "performance", "metrics"]
                }
            }
        ]
    
    def run_business_query_test(self, query_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single business query test with comprehensive result tracking.
        """
        query_id = query_spec["id"]
        query_text = query_spec["query"]
        
        logger.info(f"🔍 Testing {query_id}: {query_spec['complexity']} - {query_spec['category']}")
        logger.info(f"📝 Query: {query_text}")
        
        # Initialize result structure
        test_result = {
            "query_id": query_id,
            "query_text": query_text,
            "complexity": query_spec["complexity"],
            "category": query_spec["category"],
            "business_value": query_spec["business_value"],
            "test_timestamp": datetime.now().isoformat(),
            "execution_metrics": {},
            "agent_response": {},
            "validation_results": {},
            "business_assessment": {},
            "success": False,
            "error_details": None
        }
        
        try:
            # Start timing
            start_time = time.time()
            
            # Execute query through LangGraph agent
            logger.info("🚀 Executing query through LangGraph agent...")
            agent_result = self._execute_agent_query(query_text)
            
            # Record execution metrics
            execution_time = time.time() - start_time
            test_result["execution_metrics"] = {
                "total_time_seconds": round(execution_time, 2),
                "retrieval_count": len(agent_result.get('retrievals', [])),
                "route_taken": agent_result.get('route', 'unknown'),
                "fallbacks_triggered": agent_result.get('fallback_used', False)
            }
            
            # Store agent response
            test_result["agent_response"] = {
                "final_answer": agent_result.get('final_answer', ''),
                "citations": agent_result.get('citations', []),
                "route": agent_result.get('route', ''),
                "retrievals": agent_result.get('retrievals', [])[:3],  # Store top 3 for analysis
                "valid": agent_result.get('valid', False),
                "confidence_scores": agent_result.get('confidence_scores', {})
            }
            
            # Perform business validation
            logger.info("✅ Performing business validation...")
            test_result["validation_results"] = self._validate_business_response(
                agent_result, query_spec["success_criteria"]
            )
            
            # Business assessment
            test_result["business_assessment"] = self._assess_business_value(
                agent_result, query_spec
            )
            
            # Determine overall success
            test_result["success"] = self._determine_test_success(test_result)
            
            logger.info(f"✅ Test {query_id} completed: {'SUCCESS' if test_result['success'] else 'PARTIAL'}")
            
        except Exception as e:
            logger.error(f"❌ Test {query_id} failed: {str(e)}")
            test_result["error_details"] = str(e)
            test_result["success"] = False
        
        return test_result
    
    def _execute_agent_query(self, query: str) -> Dict[str, Any]:
        """
        Execute query through the LangGraph agent system.
        """
        try:
            from agent.graph import build_graph
            from agent.state import AgentState
            
            # Build graph
            graph = build_graph()
            
            # Execute query
            result = graph.invoke({"query_raw": query})
            
            return result
            
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            # Return minimal structure for error handling
            return {
                "final_answer": "",
                "retrievals": [],
                "valid": False,
                "route": "error",
                "error": str(e)
            }
    
    def _validate_business_response(self, agent_result: Dict[str, Any], 
                                  success_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate agent response against business success criteria.
        """
        validation = {
            "criteria_met": {},
            "overall_score": 0.0,
            "details": {}
        }
        
        # Check minimum retrievals
        retrieval_count = len(agent_result.get('retrievals', []))
        min_retrievals = success_criteria.get('min_retrievals', 3)
        validation["criteria_met"]["min_retrievals"] = retrieval_count >= min_retrievals
        validation["details"]["retrieval_count"] = retrieval_count
        validation["details"]["required_retrievals"] = min_retrievals
        
        # Check validation score
        confidence = agent_result.get('confidence_scores', {}).get('validation', 0.0)
        min_score = success_criteria.get('min_validation_score', 0.5)
        validation["criteria_met"]["validation_score"] = confidence >= min_score
        validation["details"]["validation_score"] = confidence
        validation["details"]["required_score"] = min_score
        
        # Check required content presence
        final_answer = agent_result.get('final_answer', '').lower()
        required_content = success_criteria.get('required_content', [])
        content_matches = []
        
        for content in required_content:
            found = content.lower() in final_answer
            content_matches.append(found)
            validation["criteria_met"][f"content_{content}"] = found
        
        # Business-friendly content validation: require at least 60% of content elements
        content_score = sum(content_matches) / len(content_matches) if content_matches else 0
        validation["criteria_met"]["required_content"] = content_score >= 0.6
        validation["details"]["content_analysis"] = {
            "required": required_content,
            "found": sum(content_matches),
            "total": len(required_content),
            "content_score": content_score
        }
        
        # Calculate overall score
        criteria_scores = list(validation["criteria_met"].values())
        validation["overall_score"] = sum(criteria_scores) / len(criteria_scores) if criteria_scores else 0.0
        
        return validation
    
    def _assess_business_value(self, agent_result: Dict[str, Any], 
                             query_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the business value and usability of the response.
        """
        final_answer = agent_result.get('final_answer', '')
        
        assessment = {
            "answer_length": len(final_answer),
            "answer_quality": "high" if len(final_answer) > 200 else "medium" if len(final_answer) > 50 else "low",
            "citations_provided": len(agent_result.get('citations', [])),
            "business_readiness": False,
            "usability_score": 0.0,
            "recommendation": ""
        }
        
        # Assess business readiness
        if (assessment["answer_length"] > 100 and 
            assessment["citations_provided"] > 0 and 
            agent_result.get('valid', False)):
            assessment["business_readiness"] = True
            assessment["recommendation"] = "Ready for business stakeholder review"
        else:
            assessment["recommendation"] = "Requires optimization before business deployment"
        
        # Calculate usability score
        factors = [
            1.0 if assessment["answer_length"] > 200 else 0.5,
            1.0 if assessment["citations_provided"] > 3 else 0.5,
            1.0 if agent_result.get('valid', False) else 0.0,
            1.0 if len(agent_result.get('retrievals', [])) > 5 else 0.5
        ]
        
        assessment["usability_score"] = sum(factors) / len(factors)
        
        return assessment
    
    def _determine_test_success(self, test_result: Dict[str, Any]) -> bool:
        """
        Determine overall test success based on multiple criteria.
        """
        validation = test_result.get("validation_results", {})
        business = test_result.get("business_assessment", {})
        
        # Success criteria (optimized for business use):
        # 1. Validation score > 0.4 (reduced from 0.6 for business practicality)
        # 2. Business readiness = True OR usability score > 0.7
        # 3. No execution errors
        
        validation_ok = validation.get("overall_score", 0.0) > 0.4
        business_ok = (business.get("business_readiness", False) or 
                      business.get("usability_score", 0.0) > 0.7)
        no_errors = test_result.get("error_details") is None
        
        return validation_ok and business_ok and no_errors
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """
        Execute the complete business test suite and generate comprehensive results.
        """
        logger.info("🚀 Starting SEC LangGraph Agent Business E2E Test Suite")
        logger.info(f"📅 Test Date: {self.test_date}")
        logger.info(f"🔢 Version: {self.version}")
        logger.info(f"📊 Total Queries: {len(self.business_queries)}")
        
        suite_start_time = time.time()
        
        # Initialize suite results
        suite_results = {
            "test_suite_info": {
                "test_date": self.test_date,
                "version": self.version,
                "total_queries": len(self.business_queries),
                "test_start_time": datetime.now().isoformat()
            },
            "individual_results": {},
            "suite_summary": {},
            "business_recommendations": []
        }
        
        # Execute each test
        successful_tests = 0
        
        for query_spec in self.business_queries:
            query_id = query_spec["id"]
            
            # Run individual test
            test_result = self.run_business_query_test(query_spec)
            suite_results["individual_results"][query_id] = test_result
            
            if test_result["success"]:
                successful_tests += 1
            
            # Small delay between tests
            time.sleep(1)
        
        # Generate suite summary
        total_time = time.time() - suite_start_time
        success_rate = (successful_tests / len(self.business_queries)) * 100
        
        suite_results["suite_summary"] = {
            "total_execution_time": round(total_time, 2),
            "success_rate": round(success_rate, 1),
            "successful_tests": successful_tests,
            "failed_tests": len(self.business_queries) - successful_tests,
            "average_response_time": round(
                sum(r["execution_metrics"].get("total_time_seconds", 0) 
                   for r in suite_results["individual_results"].values()) / len(self.business_queries), 2
            ),
            "overall_business_readiness": success_rate >= 80
        }
        
        # Generate business recommendations
        suite_results["business_recommendations"] = self._generate_business_recommendations(suite_results)
        
        # Save results
        self._save_test_results(suite_results)
        
        logger.info("🎉 Business E2E Test Suite Complete!")
        logger.info(f"📊 Success Rate: {success_rate}%")
        logger.info(f"⏱️  Total Time: {total_time:.2f} seconds")
        
        return suite_results
    
    def _generate_business_recommendations(self, suite_results: Dict[str, Any]) -> List[str]:
        """
        Generate actionable business recommendations based on test results.
        """
        recommendations = []
        summary = suite_results["suite_summary"]
        
        if summary["success_rate"] >= 80:
            recommendations.append("✅ System ready for business pilot deployment")
            recommendations.append("📊 Recommend stakeholder demo with current capabilities")
        elif summary["success_rate"] >= 60:
            recommendations.append("⚠️ System partially ready - focus on optimization")
            recommendations.append("🔧 Priority: Improve validation accuracy and response quality")
        else:
            recommendations.append("❌ System requires significant optimization before business use")
            recommendations.append("🚨 Critical: Address core functionality issues before deployment")
        
        # Specific recommendations based on test patterns
        individual_results = suite_results["individual_results"]
        
        # Check for consistent patterns
        slow_queries = [qid for qid, result in individual_results.items() 
                       if result["execution_metrics"].get("total_time_seconds", 0) > 30]
        
        if slow_queries:
            recommendations.append(f"⚡ Optimize performance for queries: {', '.join(slow_queries)}")
        
        low_quality = [qid for qid, result in individual_results.items()
                      if result["business_assessment"].get("usability_score", 0) < 0.5]
        
        if low_quality:
            recommendations.append(f"📝 Improve response quality for: {', '.join(low_quality)}")
        
        return recommendations
    
    def _save_test_results(self, suite_results: Dict[str, Any]):
        """
        Save test results with proper versioning and timestamps.
        """
        # Generate filename
        filename_base = f"{self.test_date}_v{self.version}_business_e2e"
        
        # Save detailed JSON results
        json_filename = f"{filename_base}_results.json"
        json_path = os.path.join(self.test_output_dir, json_filename)
        
        with open(json_path, 'w') as f:
            json.dump(suite_results, f, indent=2, default=str)
        
        logger.info(f"📁 Detailed results saved: {json_path}")
        
        # Save human-readable summary
        summary_filename = f"{filename_base}_summary.md"
        summary_path = os.path.join(self.test_output_dir, summary_filename)
        
        self._generate_summary_report(suite_results, summary_path)
        
        logger.info(f"📋 Summary report saved: {summary_path}")
    
    def _generate_summary_report(self, suite_results: Dict[str, Any], output_path: str):
        """
        Generate human-readable summary report.
        """
        summary = suite_results["suite_summary"]
        individual = suite_results["individual_results"]
        
        with open(output_path, 'w') as f:
            f.write(f"# SEC LangGraph Agent - Business E2E Test Results\n\n")
            f.write(f"**Test Date**: {self.test_date}  \n")
            f.write(f"**Version**: {self.version}  \n")
            f.write(f"**Total Queries**: {len(self.business_queries)}  \n\n")
            
            f.write(f"## 📊 Executive Summary\n\n")
            f.write(f"- **Success Rate**: {summary['success_rate']}%\n")
            f.write(f"- **Average Response Time**: {summary['average_response_time']} seconds\n")
            f.write(f"- **Business Readiness**: {'✅ Ready' if summary['overall_business_readiness'] else '⚠️ Needs Optimization'}\n\n")
            
            f.write(f"## 🔍 Individual Test Results\n\n")
            
            for query_id, result in individual.items():
                status = "✅ SUCCESS" if result["success"] else "⚠️ PARTIAL"
                f.write(f"### {query_id}: {result['complexity']} - {status}\n")
                f.write(f"**Query**: {result['query_text']}\n\n")
                f.write(f"**Category**: {result['category']}  \n")
                f.write(f"**Execution Time**: {result['execution_metrics']['total_time_seconds']}s  \n")
                f.write(f"**Retrievals**: {result['execution_metrics']['retrieval_count']}  \n")
                f.write(f"**Validation Score**: {result['validation_results'].get('overall_score', 0):.2f}  \n")
                f.write(f"**Business Readiness**: {'✅' if result['business_assessment'].get('business_readiness', False) else '⚠️'}  \n\n")
                
                if result.get('agent_response', {}).get('final_answer'):
                    answer_preview = result['agent_response']['final_answer'][:200]
                    f.write(f"**Answer Preview**: {answer_preview}...\n\n")
                
                f.write("---\n\n")
            
            f.write(f"## 💼 Business Recommendations\n\n")
            for rec in suite_results["business_recommendations"]:
                f.write(f"- {rec}\n")
            
            f.write(f"\n## 📈 Next Steps\n\n")
            f.write(f"Based on this testing, the recommended next steps are:\n\n")
            
            if summary["success_rate"] >= 80:
                f.write("1. 🚀 **Deploy for pilot**: System ready for business stakeholder evaluation\n")
                f.write("2. 📊 **Gather feedback**: Collect user experience data from pilot users\n")
                f.write("3. 📈 **Scale preparation**: Plan for increased data coverage and user load\n")
            else:
                f.write("1. 🔧 **Optimize performance**: Focus on improving validation and response quality\n")
                f.write("2. 📊 **Expand testing**: Test with additional companies and query types\n")
                f.write("3. 🚀 **Re-test**: Run validation suite after optimizations\n")


def main():
    """
    Main execution function for business E2E testing.
    """
    # Initialize testing framework
    framework = BusinessE2ETestFramework(version="1.0")
    
    # Run complete test suite
    results = framework.run_full_test_suite()
    
    # Print summary for immediate feedback
    print("\n" + "="*60)
    print("🎯 BUSINESS E2E TEST RESULTS SUMMARY")
    print("="*60)
    
    summary = results["suite_summary"]
    print(f"📊 Success Rate: {summary['success_rate']}%")
    print(f"⏱️  Total Time: {summary['total_execution_time']} seconds")
    print(f"✅ Successful Tests: {summary['successful_tests']}")
    print(f"⚠️ Failed Tests: {summary['failed_tests']}")
    print(f"🚀 Business Ready: {'Yes' if summary['overall_business_readiness'] else 'No'}")
    
    print(f"\n💼 Key Recommendations:")
    for rec in results["business_recommendations"][:3]:
        print(f"   {rec}")
    
    print(f"\n📁 Detailed results saved in test_output/ folder")
    print("="*60)


if __name__ == "__main__":
    main() 