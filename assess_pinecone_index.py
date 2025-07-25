#!/usr/bin/env python3
"""
Pinecone Vector Index Assessment
Analyzes current Pinecone index state and identifies optimization opportunities
"""

import os
import sys
import json
import time
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_pinecone_connection():
    """Test Pinecone connection and index status"""
    print("🔗 Testing Pinecone Connection:")
    print("=" * 50)
    
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index')
    
    print(f"  API Key: {'Set' if api_key else 'Not set'}")
    print(f"  Index Name: {index_name}")
    
    if not api_key:
        print("  ❌ PINECONE_API_KEY not found in environment")
        return False, None, None
    
    try:
        from pinecone import Pinecone
        
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        
        # List available indexes
        indexes = pc.list_indexes()
        available_indexes = [idx.name for idx in indexes]
        
        print(f"  📋 Available indexes: {available_indexes}")
        
        if index_name in available_indexes:
            print(f"  ✅ Target index '{index_name}' exists")
            
            # Connect to index
            index = pc.Index(index_name)
            
            # Get index stats
            stats = index.describe_index_stats()
            print(f"  📊 Index stats:")
            print(f"    • Total vectors: {stats.total_vector_count:,}")
            print(f"    • Dimension: {stats.dimension}")
            print(f"    • Index fullness: {stats.index_fullness:.2%}")
            
            return True, pc, index
        else:
            print(f"  ❌ Target index '{index_name}' not found")
            return False, pc, None
            
    except Exception as e:
        print(f"  ❌ Pinecone connection failed: {e}")
        return False, None, None

def analyze_index_content(index):
    """Analyze the content and quality of vectors in the index"""
    print("\n📊 Index Content Analysis:")
    print("=" * 50)
    
    try:
        # Sample some vectors to analyze content
        sample_queries = [
            "capital ratios banking",
            "risk management financial", 
            "business operations",
            "Wells Fargo",
            "credit risk exposure",
            "regulatory compliance"
        ]
        
        print("  🔍 Testing sample financial queries:")
        
        for query in sample_queries:
            try:
                # Generate query embedding (we'll use a simple approach)
                from sentence_transformers import SentenceTransformer
                
                # Use the same model as in the pipeline
                model = SentenceTransformer('all-MiniLM-L6-v2')
                query_embedding = model.encode([query]).tolist()[0]
                
                # Search the index
                results = index.query(
                    vector=query_embedding,
                    top_k=5,
                    include_metadata=True
                )
                
                print(f"    • '{query}': {len(results.matches)} results")
                
                if results.matches:
                    top_result = results.matches[0]
                    score = top_result.score
                    metadata = top_result.metadata or {}
                    
                    print(f"      Top score: {score:.3f}")
                    print(f"      Company: {metadata.get('company', 'Unknown')}")
                    print(f"      Section: {metadata.get('section_name', 'Unknown')}")
                    
                    # Show snippet of text if available
                    text = metadata.get('text', '')
                    if text:
                        snippet = text[:100] + "..." if len(text) > 100 else text
                        print(f"      Text: {snippet}")
                else:
                    print(f"      ⚠️  No results found")
                    
            except Exception as e:
                print(f"    ❌ Query '{query}' failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Content analysis failed: {e}")
        return False

def check_sec_data_coverage(index):
    """Check how well SEC filing data is covered in the index"""
    print("\n📄 SEC Data Coverage Analysis:")
    print("=" * 50)
    
    try:
        # Test queries for specific companies we know are in the data
        company_queries = [
            ("Wells Fargo business operations", "WFC"),
            ("Zions Bancorporation capital", "ZION"), 
            ("KeyCorp risk factors", "KEY"),
            ("Prosperity Bank lending", "PB"),
            ("Commerce Bancshares", "CBSH")
        ]
        
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        coverage_results = {}
        
        for query, expected_company in company_queries:
            try:
                query_embedding = model.encode([query]).tolist()[0]
                results = index.query(
                    vector=query_embedding,
                    top_k=10,
                    include_metadata=True
                )
                
                # Check if results contain the expected company
                company_found = False
                relevant_scores = []
                
                for match in results.matches:
                    metadata = match.metadata or {}
                    result_company = metadata.get('company', '')
                    
                    if expected_company in result_company or result_company in expected_company:
                        company_found = True
                        relevant_scores.append(match.score)
                
                coverage_results[expected_company] = {
                    "query": query,
                    "found": company_found,
                    "total_results": len(results.matches),
                    "best_score": max(relevant_scores) if relevant_scores else 0,
                    "relevant_results": len(relevant_scores)
                }
                
                status = "✅" if company_found else "❌"
                print(f"  {status} {expected_company}: {query}")
                if company_found:
                    print(f"      Found {len(relevant_scores)} relevant results (best: {max(relevant_scores):.3f})")
                else:
                    print(f"      No relevant results in top 10")
                    
            except Exception as e:
                print(f"  ❌ {expected_company} query failed: {e}")
        
        # Summary
        found_companies = sum(1 for r in coverage_results.values() if r["found"])
        total_companies = len(coverage_results)
        coverage_rate = (found_companies / total_companies) * 100 if total_companies > 0 else 0
        
        print(f"\n  📊 Coverage Summary:")
        print(f"    • Companies found: {found_companies}/{total_companies} ({coverage_rate:.1f}%)")
        
        return coverage_results
        
    except Exception as e:
        print(f"  ❌ SEC coverage analysis failed: {e}")
        return {}

def analyze_financial_terminology_coverage(index):
    """Test how well financial terminology is covered"""
    print("\n💰 Financial Terminology Coverage:")
    print("=" * 50)
    
    financial_terms = [
        "capital adequacy ratio",
        "credit loss provisions", 
        "net interest margin",
        "operational risk management",
        "regulatory capital requirements",
        "stress testing results",
        "commercial real estate",
        "consumer banking services",
        "investment banking operations",
        "wealth management platform"
    ]
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        term_scores = {}
        
        for term in financial_terms:
            try:
                query_embedding = model.encode([term]).tolist()[0]
                results = index.query(
                    vector=query_embedding,
                    top_k=3,
                    include_metadata=True
                )
                
                if results.matches:
                    best_score = results.matches[0].score
                    term_scores[term] = best_score
                    
                    status = "✅" if best_score > 0.5 else "⚠️" if best_score > 0.3 else "❌"
                    print(f"  {status} {term}: {best_score:.3f}")
                else:
                    term_scores[term] = 0
                    print(f"  ❌ {term}: No results")
                    
            except Exception as e:
                print(f"  ❌ {term}: Query failed - {e}")
        
        # Summary statistics
        scores = list(term_scores.values())
        if scores:
            avg_score = sum(scores) / len(scores)
            high_quality = sum(1 for s in scores if s > 0.5)
            medium_quality = sum(1 for s in scores if 0.3 <= s <= 0.5)
            low_quality = sum(1 for s in scores if s < 0.3)
            
            print(f"\n  📊 Financial Term Quality:")
            print(f"    • Average score: {avg_score:.3f}")
            print(f"    • High quality (>0.5): {high_quality}/{len(scores)}")
            print(f"    • Medium quality (0.3-0.5): {medium_quality}/{len(scores)}")
            print(f"    • Low quality (<0.3): {low_quality}/{len(scores)}")
            
        return term_scores
        
    except Exception as e:
        print(f"  ❌ Financial terminology analysis failed: {e}")
        return {}

def generate_pinecone_optimization_recommendations(connection_ok, content_analysis, coverage_results, term_scores):
    """Generate specific recommendations for Pinecone optimization"""
    print("\n🔧 Pinecone Optimization Recommendations:")
    print("=" * 50)
    
    recommendations = []
    
    if not connection_ok:
        recommendations.extend([
            "1. HIGH: Fix Pinecone connection and API key configuration",
            "2. HIGH: Ensure target index exists and is accessible",
            "3. HIGH: Run vector population pipeline to populate index"
        ])
    else:
        if content_analysis:
            # Check coverage quality
            found_companies = sum(1 for r in coverage_results.values() if r["found"]) if coverage_results else 0
            total_companies = len(coverage_results) if coverage_results else 0
            coverage_rate = (found_companies / total_companies) * 100 if total_companies > 0 else 0
            
            if coverage_rate < 80:
                recommendations.append(f"1. HIGH: Improve company coverage - only {coverage_rate:.1f}% found")
            
            # Check financial term quality
            if term_scores:
                avg_score = sum(term_scores.values()) / len(term_scores)
                if avg_score < 0.4:
                    recommendations.append(f"2. HIGH: Improve financial terminology embeddings - avg score {avg_score:.3f}")
            
            # Performance recommendations
            recommendations.extend([
                "3. MEDIUM: Optimize search parameters (k-values, similarity thresholds)",
                "4. MEDIUM: Implement financial-specific query expansion",
                "5. MEDIUM: Add metadata filtering for improved precision",
                "6. LOW: Consider domain-specific embedding models for finance"
            ])
        else:
            recommendations.extend([
                "1. HIGH: Investigate content analysis failures",
                "2. HIGH: Verify embedding model compatibility",
                "3. MEDIUM: Check index population completeness"
            ])
    
    # Display recommendations
    for rec in recommendations:
        print(f"  {rec}")
    
    return recommendations

def create_pinecone_optimization_script():
    """Create script to optimize Pinecone configuration"""
    print("\n🛠️ Creating Pinecone Optimization Script:")
    print("=" * 50)
    
    script_content = '''#!/usr/bin/env python3
"""
Optimize Pinecone Vector Search
Implements financial-domain optimizations for better retrieval
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def optimize_pinecone_search():
    """Run Pinecone optimization for financial content"""
    print("🚀 Pinecone Vector Search Optimization")
    print("=" * 60)
    
    try:
        from data_pipeline.pinecone_integration import PineconeVectorStore
        
        # Initialize with optimized parameters
        vector_store = PineconeVectorStore(
            index_name=os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index'),
            embedding_model='all-MiniLM-L6-v2',
            dimension=384
        )
        
        print("✅ Connected to Pinecone vector store")
        
        # Test optimized search parameters
        financial_queries = [
            "capital adequacy requirements",
            "operational risk management framework", 
            "credit loss provisioning methodology",
            "regulatory compliance program",
            "business segment performance"
        ]
        
        print("\\n🔍 Testing Optimized Search Parameters:")
        
        for query in financial_queries:
            # Test different k-values and see impact
            for k in [3, 5, 10]:
                results = vector_store.search(
                    query_text=query,
                    k=k,
                    filter_metadata=None
                )
                
                print(f"  {query} (k={k}): {len(results)} results")
                if results:
                    best_score = max(r.get('score', 0) for r in results)
                    print(f"    Best score: {best_score:.3f}")
        
        print("\\n🎯 Optimization complete!")
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")

if __name__ == "__main__":
    optimize_pinecone_search()
'''
    
    script_path = "/Users/saadahmed/Desktop/Apps/AWS_Extra/SEC_Graph/optimize_pinecone.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"  ✅ Created optimization script: {os.path.basename(script_path)}")
    return script_path

def main():
    """Run complete Pinecone assessment"""
    print("🔍 Pinecone Vector Index Assessment")
    print("=" * 70)
    
    # Test connection
    connection_ok, pc, index = check_pinecone_connection()
    
    content_analysis = False
    coverage_results = {}
    term_scores = {}
    
    if connection_ok and index:
        # Analyze content
        content_analysis = analyze_index_content(index)
        coverage_results = check_sec_data_coverage(index)
        term_scores = analyze_financial_terminology_coverage(index)
    
    # Generate recommendations
    recommendations = generate_pinecone_optimization_recommendations(
        connection_ok, content_analysis, coverage_results, term_scores
    )
    
    # Create optimization script
    optimization_script = create_pinecone_optimization_script()
    
    # Summary
    print(f"\n🎯 Assessment Summary:")
    print("=" * 50)
    print(f"  Connection: {'✅ Working' if connection_ok else '❌ Failed'}")
    print(f"  Content Analysis: {'✅ Complete' if content_analysis else '❌ Failed'}")
    print(f"  Recommendations: {len(recommendations)} items")
    print(f"  Optimization Script: ✅ Created")
    
    if connection_ok:
        print(f"\\n🚀 Ready for Pinecone optimization!")
    else:
        print(f"\\n⚠️  Fix connection issues before optimization")

if __name__ == "__main__":
    main()