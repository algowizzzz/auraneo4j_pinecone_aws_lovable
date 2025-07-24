"""
Business Validation Framework for SEC Graph LangGraph Agent
Creates structured output files for business review of agent responses
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BusinessValidationFramework:
    """Framework for creating structured business validation outputs"""
    
    def __init__(self, output_dir: str = "business_validation_outputs"):
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Test queries organized by business use case
        self.test_queries = {
            "basic_company_info": [
                "What is Zions Bancorporation's business model?",
                "Describe JPMorgan's core business segments",
                "What are Bank of America's primary revenue sources?"
            ],
            "financial_metrics": [
                "What are Zions Bancorporation's capital ratios in 2025 Q1?",
                "What were Wells Fargo's key financial metrics in 2024?",
                "How did JPMorgan's profitability change from 2023 to 2024?"
            ],
            "risk_analysis": [
                "What are the top risks reported by Wells Fargo in 2024?",
                "Compare market risk vs credit risk for regional banks",
                "Analyze Zions Bancorporation's risk management strategy"
            ],
            "regulatory_compliance": [
                "What regulatory requirements does Bank of America face?",
                "How does Wells Fargo comply with Basel III requirements?",
                "What are the key regulatory challenges for regional banks?"
            ],
            "competitive_analysis": [
                "How does Zions compare to other regional banks in terms of business strategy?",
                "What are common digital banking strategies across major banks?",
                "Compare capital management strategies across different bank sizes"
            ],
            "multi_topic_analysis": [
                "Analyze market risk, credit risk, and operational risk for JPMorgan Chase",
                "Compare Bank of America and Wells Fargo across business model, risks, and performance",
                "Evaluate the regulatory environment and competitive positioning of regional banks"
            ]
        }
    
    def create_test_session(self, session_name: str = None) -> str:
        """Create a new test session directory"""
        if session_name is None:
            session_name = f"session_{self.timestamp}"
        
        session_dir = os.path.join(self.output_dir, session_name)
        os.makedirs(session_dir, exist_ok=True)
        
        # Create session metadata
        metadata = {
            "session_name": session_name,
            "created_at": datetime.now().isoformat(),
            "total_categories": len(self.test_queries),
            "total_queries": sum(len(queries) for queries in self.test_queries.values()),
            "status": "created"
        }
        
        with open(os.path.join(session_dir, "session_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Created test session: {session_dir}")
        return session_dir
    
    def run_query_test(self, query: str, category: str, session_dir: str, agent_function=None) -> Dict[str, Any]:
        """Run a single query test and save structured output"""
        
        test_id = f"{category}_{hash(query) % 10000:04d}"
        timestamp = datetime.now().isoformat()
        
        # Test result structure
        test_result = {
            "test_id": test_id,
            "category": category,
            "query": query,
            "timestamp": timestamp,
            "technical_metrics": {},
            "business_evaluation": {
                "accuracy": None,
                "completeness": None,
                "relevance": None,
                "clarity": None,
                "citations": None,
                "business_value": None,
                "notes": ""
            },
            "agent_response": None,
            "error": None,
            "execution_time": None
        }
        
        try:
            import time
            start_time = time.time()
            
            if agent_function:
                # Run actual agent
                response = agent_function(query)
                test_result["agent_response"] = response
            else:
                # Placeholder for manual testing
                test_result["agent_response"] = {
                    "answer": f"[PLACEHOLDER] Response for: {query}",
                    "citations": ["[PLACEHOLDER] Citation needed"],
                    "confidence": 0.0,
                    "route_taken": "placeholder"
                }
            
            execution_time = time.time() - start_time
            test_result["execution_time"] = execution_time
            test_result["technical_metrics"]["response_time"] = execution_time
            
        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"Query test failed: {e}")
        
        # Save individual test result
        output_file = os.path.join(session_dir, f"{test_id}.json")
        with open(output_file, "w") as f:
            json.dump(test_result, f, indent=2)
        
        # Create human-readable version
        human_readable_file = os.path.join(session_dir, f"{test_id}_readable.txt")
        self._create_human_readable_output(test_result, human_readable_file)
        
        return test_result
    
    def _create_human_readable_output(self, test_result: Dict[str, Any], output_file: str):
        """Create human-readable output for business review"""
        
        content = f"""
SEC GRAPH AGENT - BUSINESS VALIDATION TEST
==========================================

Test ID: {test_result['test_id']}
Category: {test_result['category'].upper()}
Timestamp: {test_result['timestamp']}

QUERY:
------
{test_result['query']}

AGENT RESPONSE:
--------------
{json.dumps(test_result.get('agent_response', {}), indent=2)}

TECHNICAL METRICS:
-----------------
Execution Time: {test_result.get('execution_time', 'N/A')} seconds
Error: {test_result.get('error', 'None')}

BUSINESS EVALUATION FRAMEWORK:
-----------------------------
Please rate each aspect from 1-5 (5 = Excellent, 1 = Poor):

[ ] ACCURACY: Does the response contain factually correct information?
    Comments: ___________________________________________________

[ ] COMPLETENESS: Does the response fully address the query?
    Comments: ___________________________________________________

[ ] RELEVANCE: Is the information relevant to the business question?
    Comments: ___________________________________________________

[ ] CLARITY: Is the response clear and well-structured?
    Comments: ___________________________________________________

[ ] CITATIONS: Are proper sources cited and verifiable?
    Comments: ___________________________________________________

[ ] BUSINESS VALUE: Would this response be valuable to a financial analyst?
    Comments: ___________________________________________________

OVERALL ASSESSMENT:
------------------
[ ] PASS: Response meets business requirements
[ ] FAIL: Response needs significant improvement
[ ] PARTIAL: Response has value but needs refinement

REVIEWER NOTES:
______________________________________________________________
______________________________________________________________
______________________________________________________________

RECOMMENDATIONS FOR IMPROVEMENT:
______________________________________________________________
______________________________________________________________
______________________________________________________________

Reviewed by: ______________________ Date: ________________
"""
        
        with open(output_file, "w") as f:
            f.write(content)
    
    def run_full_test_suite(self, session_name: str = None, agent_function=None) -> str:
        """Run the complete test suite for business validation"""
        
        session_dir = self.create_test_session(session_name)
        
        results_summary = {
            "session_dir": session_dir,
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "categories": {},
            "start_time": datetime.now().isoformat()
        }
        
        logger.info("Starting full business validation test suite...")
        
        for category, queries in self.test_queries.items():
            logger.info(f"Testing category: {category}")
            category_results = []
            
            for query in queries:
                logger.info(f"  Testing query: {query[:50]}...")
                result = self.run_query_test(query, category, session_dir, agent_function)
                category_results.append(result)
                
                results_summary["total_tests"] += 1
                if result.get("error") is None:
                    results_summary["successful_tests"] += 1
                else:
                    results_summary["failed_tests"] += 1
            
            results_summary["categories"][category] = {
                "query_count": len(queries),
                "results": category_results
            }
        
        results_summary["end_time"] = datetime.now().isoformat()
        
        # Save summary
        summary_file = os.path.join(session_dir, "test_summary.json")
        with open(summary_file, "w") as f:
            json.dump(results_summary, f, indent=2)
        
        # Create business review instructions
        instructions_file = os.path.join(session_dir, "BUSINESS_REVIEW_INSTRUCTIONS.md")
        self._create_business_review_instructions(instructions_file, results_summary)
        
        logger.info(f"Test suite completed. Results saved to: {session_dir}")
        logger.info(f"Total tests: {results_summary['total_tests']}")
        logger.info(f"Successful: {results_summary['successful_tests']}")
        logger.info(f"Failed: {results_summary['failed_tests']}")
        
        return session_dir
    
    def _create_business_review_instructions(self, output_file: str, summary: Dict[str, Any]):
        """Create instructions for business reviewers"""
        
        content = f"""
# SEC Graph Agent - Business Validation Review Instructions

## Overview
This directory contains {summary['total_tests']} test cases across {len(summary['categories'])} business categories.
Each test represents a typical query that a financial analyst might ask about SEC filings.

## Review Process

### 1. Individual Test Review
- Review each `*_readable.txt` file
- Fill out the business evaluation framework
- Focus on practical business value, not just technical correctness

### 2. Category Assessment
Review responses by category:

"""
        
        for category, data in summary["categories"].items():
            content += f"**{category.upper()}** ({data['query_count']} tests)\n"
            content += f"- Focus: Business relevance for {category.replace('_', ' ')}\n"
            content += f"- Files: Look for {category}_*.txt files\n\n"
        
        content += """
### 3. Rating Guidelines

**ACCURACY (1-5)**
- 5: Factually correct information from SEC filings
- 3: Mostly correct with minor inaccuracies
- 1: Incorrect or misleading information

**COMPLETENESS (1-5)**
- 5: Fully addresses all aspects of the query
- 3: Addresses main points but misses some details
- 1: Incomplete or partial response

**RELEVANCE (1-5)**
- 5: Highly relevant to the business question
- 3: Generally relevant with some tangential information
- 1: Off-topic or irrelevant response

**CLARITY (1-5)**
- 5: Clear, well-structured, easy to understand
- 3: Generally clear with some confusing parts
- 1: Unclear, poorly structured, hard to follow

**CITATIONS (1-5)**
- 5: Proper citations with specific SEC filing references
- 3: Some citations but not comprehensive
- 1: No citations or incorrect citations

**BUSINESS VALUE (1-5)**
- 5: High value for financial analysis and decision-making
- 3: Some value but could be more actionable
- 1: Low value for business purposes

### 4. Key Questions for Reviewers

1. **Would you use this response in a client presentation?**
2. **Does the response demonstrate understanding of banking/finance?**
3. **Are the sources credible and properly attributed?**
4. **Is the language appropriate for professional financial analysis?**
5. **What improvements would make this response more valuable?**

### 5. Summary Report

After reviewing individual tests, please create a summary report addressing:

- Overall quality assessment
- Best performing categories
- Areas needing improvement
- Specific recommendations for enhancement
- Business readiness assessment

## Next Steps

1. Complete individual test reviews
2. Compile category summaries
3. Create overall assessment
4. Provide improvement recommendations
5. Sign off on business readiness (or identify blockers)

---
**Generated:** {summary['start_time']}
**Total Tests:** {summary['total_tests']}
**Session:** {os.path.basename(summary['session_dir'])}
"""
        
        with open(output_file, "w") as f:
            f.write(content)

def main():
    """Run the business validation framework"""
    framework = BusinessValidationFramework()
    
    # Create test session
    session_dir = framework.run_full_test_suite("initial_validation")
    
    print(f"\n✅ Business validation framework created!")
    print(f"📁 Output directory: {session_dir}")
    print(f"📝 Review instructions: {os.path.join(session_dir, 'BUSINESS_REVIEW_INSTRUCTIONS.md')}")
    print(f"\n🔍 Next steps:")
    print(f"1. Run real agent tests to populate responses")
    print(f"2. Review *_readable.txt files for business validation")
    print(f"3. Complete evaluation frameworks")
    print(f"4. Compile business readiness assessment")

if __name__ == "__main__":
    main()