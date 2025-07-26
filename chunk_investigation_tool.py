#!/usr/bin/env python3
"""
Chunk Investigation Tool - Deep Dive into Retrieval Quality
Helps understand why certain chunks are/aren't being retrieved for specific queries
"""

import os
import sys
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ChunkInvestigator:
    def __init__(self):
        self.pc = None
        self.model = None
        self.initialize_connections()
    
    def initialize_connections(self):
        """Initialize Pinecone and embedding model"""
        try:
            from pinecone import Pinecone
            from sentence_transformers import SentenceTransformer
            
            # Connect to Pinecone
            pinecone_api_key = os.getenv('PINECONE_API_KEY')
            if not pinecone_api_key:
                print("❌ PINECONE_API_KEY not found")
                return False
            
            self.pc = Pinecone(api_key=pinecone_api_key)
            self.index = self.pc.Index("sec-rag-index")
            
            # Initialize embedding model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            print("✅ Connected to Pinecone and loaded embedding model")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            return False
    
    def investigate_query_retrieval(self, query: str, company_filter: str = None, top_k: int = 50):
        """Deep investigation of what chunks are being retrieved for a query"""
        
        print(f"\n🔍 INVESTIGATING QUERY RETRIEVAL")
        print("=" * 80)
        print(f"Query: {query}")
        print(f"Company Filter: {company_filter}")
        print(f"Retrieving top {top_k} chunks...")
        print()
        
        # Create query embedding
        query_embedding = self.model.encode([query])[0].tolist()
        
        # Search Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )
        
        print(f"📊 RETRIEVAL RESULTS: {len(results.matches)} chunks found")
        print("-" * 60)
        
        # Analyze results
        all_chunks = []
        company_chunks = []
        
        for i, match in enumerate(results.matches):
            chunk_data = {
                "rank": i + 1,
                "id": match.id,
                "score": float(match.score),
                "metadata": dict(match.metadata) if match.metadata else {}
            }
            
            # Extract company from ID or metadata
            company = "Unknown"
            if match.metadata and match.metadata.get("company"):
                company = match.metadata["company"]
            elif "_" in match.id:
                company = match.id.split("_")[0].upper()
            
            chunk_data["company"] = company
            all_chunks.append(chunk_data)
            
            # Filter by company if specified
            if not company_filter or company.upper() == company_filter.upper():
                company_chunks.append(chunk_data)
        
        # Analysis 1: Company Distribution
        print("📊 COMPANY DISTRIBUTION:")
        company_counts = {}
        for chunk in all_chunks:
            company = chunk["company"]
            company_counts[company] = company_counts.get(company, 0) + 1
        
        for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {company}: {count} chunks")
        
        if company_filter:
            filtered_count = len(company_chunks)
            print(f"\n🎯 FILTERED RESULTS: {filtered_count} chunks from {company_filter}")
            
            if filtered_count == 0:
                print(f"❌ NO CHUNKS FOUND for company {company_filter}")
                print("   This explains why the response was generic!")
                return
        
        # Analysis 2: Score Distribution
        scores = [chunk["score"] for chunk in (company_chunks if company_filter else all_chunks)]
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print(f"\n📈 SCORE ANALYSIS:")
            print(f"   Average Score: {avg_score:.3f}")
            print(f"   Score Range: {min_score:.3f} - {max_score:.3f}")
            
            # Flag low scores
            if avg_score < 0.5:
                print(f"⚠️  Low average score suggests poor semantic match!")
        
        # Analysis 3: Top Chunks Content Analysis
        top_chunks = (company_chunks if company_filter else all_chunks)[:10]
        
        print(f"\n📄 TOP {len(top_chunks)} CHUNKS ANALYSIS:")
        print("-" * 60)
        
        for chunk in top_chunks:
            print(f"\n{chunk['rank']}. ID: {chunk['id']}")
            print(f"   Company: {chunk['company']}")
            print(f"   Score: {chunk['score']:.3f}")
            
            # Analyze metadata
            metadata = chunk["metadata"]
            if metadata:
                print("   Metadata:")
                for key, value in metadata.items():
                    if key in ["text", "content"]:
                        # Show text preview
                        text_preview = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                        print(f"     {key}: {text_preview}")
                    else:
                        print(f"     {key}: {value}")
            
            # Check if this looks like financial data
            text_content = metadata.get("text", "") or metadata.get("content", "")
            if text_content:
                financial_indicators = self.analyze_financial_content(text_content)
                if financial_indicators:
                    print(f"   💰 Financial Content: {financial_indicators}")
            
            print()
    
    def analyze_financial_content(self, text: str) -> List[str]:
        """Analyze if text contains financial/tabular content"""
        indicators = []
        text_lower = text.lower()
        
        # Check for financial keywords
        financial_terms = [
            "revenue", "income", "profit", "loss", "assets", "liabilities", 
            "equity", "cash flow", "earnings", "ebitda", "net income",
            "total assets", "shareholders", "balance sheet", "income statement"
        ]
        
        for term in financial_terms:
            if term in text_lower:
                indicators.append(f"Contains '{term}'")
        
        # Check for numerical patterns (financial figures)
        import re
        
        # Dollar amounts
        dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
        dollar_matches = re.findall(dollar_pattern, text)
        if dollar_matches:
            indicators.append(f"Dollar amounts: {len(dollar_matches)}")
        
        # Percentages
        percent_pattern = r'\d+(?:\.\d+)?%'
        percent_matches = re.findall(percent_pattern, text)
        if percent_matches:
            indicators.append(f"Percentages: {len(percent_matches)}")
        
        # Large numbers (billions/millions)
        large_num_pattern = r'\d+(?:\.\d+)?\s*(?:billion|million|trillion)'
        large_num_matches = re.findall(large_num_pattern, text_lower)
        if large_num_matches:
            indicators.append(f"Large numbers: {len(large_num_matches)}")
        
        # Table-like content (multiple numbers in lines)
        lines_with_numbers = []
        for line in text.split('\n'):
            if re.search(r'\d+', line):
                lines_with_numbers.append(line)
        
        if len(lines_with_numbers) > 3:
            indicators.append(f"Tabular data: {len(lines_with_numbers)} lines")
        
        return indicators
    
    def compare_queries(self, query1: str, query2: str, company: str = None):
        """Compare retrieval results for two different queries"""
        
        print(f"\n🔄 COMPARING QUERY RETRIEVALS")
        print("=" * 80)
        print(f"Query 1: {query1}")
        print(f"Query 2: {query2}")
        print(f"Company: {company}")
        print()
        
        # Get embeddings for both queries
        embeddings = self.model.encode([query1, query2])
        
        results1 = self.index.query(vector=embeddings[0].tolist(), top_k=20, include_metadata=True)
        results2 = self.index.query(vector=embeddings[1].tolist(), top_k=20, include_metadata=True)
        
        # Analyze overlap
        ids1 = set(match.id for match in results1.matches)
        ids2 = set(match.id for match in results2.matches)
        
        overlap = ids1.intersection(ids2)
        unique1 = ids1 - ids2
        unique2 = ids2 - ids1
        
        print(f"📊 OVERLAP ANALYSIS:")
        print(f"   Common chunks: {len(overlap)}")
        print(f"   Unique to Query 1: {len(unique1)}")
        print(f"   Unique to Query 2: {len(unique2)}")
        
        if overlap:
            print(f"\n🔗 SHARED CHUNKS:")
            for chunk_id in list(overlap)[:5]:
                print(f"   • {chunk_id}")
        
        if unique1:
            print(f"\n🎯 UNIQUE TO QUERY 1 ('{query1[:30]}...'):")
            for chunk_id in list(unique1)[:5]:
                print(f"   • {chunk_id}")
        
        if unique2:
            print(f"\n🎯 UNIQUE TO QUERY 2 ('{query2[:30]}...'):")
            for chunk_id in list(unique2)[:5]:
                print(f"   • {chunk_id}")
    
    def suggest_better_query(self, original_query: str, company: str = None):
        """Suggest better query formulations for financial data"""
        
        print(f"\n💡 QUERY OPTIMIZATION SUGGESTIONS")
        print("=" * 80)
        print(f"Original Query: {original_query}")
        print()
        
        suggestions = [
            f"{company} consolidated income statement financial results" if company else "consolidated income statement financial results",
            f"{company} balance sheet total assets liabilities equity" if company else "balance sheet total assets liabilities equity", 
            f"{company} cash flow statement operating investing financing" if company else "cash flow statement operating investing financing",
            f"{company} net revenue income profit earnings financial metrics" if company else "net revenue income profit earnings financial metrics",
            f"{company} financial performance ratios return on equity assets" if company else "financial performance ratios return on equity assets"
        ]
        
        print("🎯 Try these more specific queries:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        print(f"\n🔍 Let's test the first suggestion:")
        if suggestions:
            self.investigate_query_retrieval(suggestions[0], company, top_k=10)

def main():
    investigator = ChunkInvestigator()
    
    if not investigator.pc:
        print("❌ Failed to initialize. Check your environment setup.")
        return
    
    print("🔍 CHUNK INVESTIGATION TOOL")
    print("=" * 50)
    
    # Test the problematic BAC query
    print("\n📋 INVESTIGATING YOUR BAC FINANCIAL PERFORMANCE QUERY:")
    investigator.investigate_query_retrieval(
        query="financial performance of BAC",
        company_filter="BAC",
        top_k=30
    )
    
    # Suggest better queries
    investigator.suggest_better_query("financial performance of BAC", "BAC")
    
    # Compare with a more specific query
    print("\n🔄 COMPARING WITH MORE SPECIFIC QUERY:")
    investigator.compare_queries(
        query1="financial performance of BAC",
        query2="BAC consolidated income statement net revenue total assets",
        company="BAC"
    )

if __name__ == "__main__":
    main()