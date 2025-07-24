import os
import json
from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase
from pinecone_integration import PineconeVectorStore
from sentence_transformers import SentenceTransformer
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class HybridSearchEngine:
    """
    Hybrid search engine combining Neo4j graph queries with Pinecone vector search
    for comprehensive financial document analysis
    """
    
    def __init__(self, 
                 neo4j_uri: str,
                 neo4j_user: str, 
                 neo4j_password: str,
                 pinecone_index: Optional[str] = None):
        
        # Initialize Neo4j connection
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Initialize Pinecone
        self.pinecone_store = None
        if pinecone_index:
            try:
                self.pinecone_store = PineconeVectorStore(index_name=pinecone_index)
                logger.info(f"Initialized Pinecone vector store: {pinecone_index}")
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone: {e}")
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def close(self):
        """Close database connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()

    def search_company_timeline(self, 
                              company: str, 
                              start_year: int, 
                              end_year: int,
                              section_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for company documents across a timeline using both graph and vector search
        """
        results = {
            'graph_results': [],
            'vector_results': [],
            'combined_insights': {}
        }
        
        # Graph-based temporal search
        with self.neo4j_driver.session() as session:
            graph_query = """
            MATCH (c:Company {name: $company})-[:HAS_YEAR]->(y:Year)
            WHERE y.value >= $start_year AND y.value <= $end_year
            MATCH (y)-[:HAS_QUARTER]->(q:Quarter)-[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)
            """ + (f"WHERE s.section CONTAINS '{section_type}'" if section_type else "") + """
            RETURN y.value as year, q.label as quarter, d.document_type as doc_type, 
                   s.section as section_name, s.text as text, s.financial_entities as entities
            ORDER BY y.value, q.label
            """
            
            graph_result = session.run(graph_query, 
                                     company=company, 
                                     start_year=start_year, 
                                     end_year=end_year)
            
            for record in graph_result:
                results['graph_results'].append({
                    'year': record['year'],
                    'quarter': record['quarter'],
                    'document_type': record['doc_type'],
                    'section_name': record['section_name'],
                    'text': record['text'][:500] + "..." if len(record['text']) > 500 else record['text'],
                    'financial_entities': json.loads(record['entities']) if record['entities'] else {}
                })
        
        # Vector-based semantic search
        if self.pinecone_store:
            vector_results = self.pinecone_store.search_by_company_and_timeframe(
                company=company,
                start_year=start_year,
                end_year=end_year,
                section_type=section_type,
                top_k=20
            )
            results['vector_results'] = vector_results
        
        # Generate combined insights
        results['combined_insights'] = self._generate_timeline_insights(results)
        
        return results

    def search_competitive_analysis(self, 
                                  companies: List[str], 
                                  concepts: List[str],
                                  year: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform competitive analysis across multiple companies for specific concepts
        """
        results = {
            'company_comparisons': {},
            'concept_analysis': {},
            'market_insights': []
        }
        
        # Graph-based competitive queries
        with self.neo4j_driver.session() as session:
            for company in companies:
                query = """
                MATCH (c:Company {name: $company})-[:HAS_YEAR]->(y:Year)
                """ + (f"WHERE y.value = {year}" if year else "") + """
                MATCH (y)-[:HAS_QUARTER]->(q:Quarter)-[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)
                RETURN c.name as company, y.value as year, s.section as section, 
                       s.text as text, s.financial_entities as entities
                """
                
                company_result = session.run(query, company=company)
                company_data = []
                
                for record in company_result:
                    text = record['text'].lower()
                    # Check if any concepts are mentioned
                    concept_mentions = {concept: concept.lower() in text for concept in concepts}
                    if any(concept_mentions.values()):
                        company_data.append({
                            'year': record['year'],
                            'section': record['section'],
                            'text_snippet': record['text'][:300] + "...",
                            'concept_mentions': concept_mentions,
                            'financial_entities': json.loads(record['entities']) if record['entities'] else {}
                        })
                
                results['company_comparisons'][company] = company_data
        
        # Vector-based concept search
        if self.pinecone_store:
            concept_results = self.pinecone_store.search_by_financial_concepts(
                concepts=concepts,
                companies=companies,
                top_k=30
            )
            
            # Group results by company
            for result in concept_results:
                company = result['metadata'].get('company', 'Unknown')
                if company not in results['concept_analysis']:
                    results['concept_analysis'][company] = []
                results['concept_analysis'][company].append(result)
        
        return results

    def search_risk_factors(self, 
                          company: Optional[str] = None,
                          risk_types: Optional[List[str]] = None,
                          time_period: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        Search for risk factors across companies and time periods
        """
        default_risk_types = ['credit risk', 'operational risk', 'market risk', 'liquidity risk', 
                             'regulatory risk', 'cybersecurity risk', 'interest rate risk']
        
        search_risks = risk_types or default_risk_types
        results = {
            'risk_analysis': {},
            'temporal_trends': {},
            'risk_correlations': []
        }
        
        # Graph-based risk search
        with self.neo4j_driver.session() as session:
            base_query = """
            MATCH (c:Company)-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)
            -[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)
            WHERE s.financial_entities IS NOT NULL
            """
            
            if company:
                base_query += f" AND c.name = '{company}'"
            
            if time_period:
                base_query += f" AND y.value >= {time_period[0]} AND y.value <= {time_period[1]}"
            
            base_query += """
            RETURN c.name as company, y.value as year, s.section as section,
                   s.text as text, s.financial_entities as entities
            """
            
            risk_result = session.run(base_query)
            
            for record in risk_result:
                text = record['text'].lower()
                company_name = record['company']
                year = record['year']
                
                # Check for risk mentions
                risk_mentions = {}
                for risk_type in search_risks:
                    if risk_type.lower() in text:
                        risk_mentions[risk_type] = True
                        # Extract risk context
                        sentences = record['text'].split('.')
                        risk_context = []
                        for sentence in sentences:
                            if risk_type.lower() in sentence.lower():
                                risk_context.append(sentence.strip())
                        risk_mentions[f"{risk_type}_context"] = risk_context[:2]  # Top 2 mentions
                
                if risk_mentions:
                    if company_name not in results['risk_analysis']:
                        results['risk_analysis'][company_name] = {}
                    if year not in results['risk_analysis'][company_name]:
                        results['risk_analysis'][company_name][year] = []
                    
                    results['risk_analysis'][company_name][year].append({
                        'section': record['section'],
                        'risk_mentions': risk_mentions
                    })
        
        # Vector-based risk search
        if self.pinecone_store:
            for risk_type in search_risks:
                filter_dict = {}
                if company:
                    filter_dict['company'] = {'$eq': company}
                if time_period:
                    filter_dict['year'] = {'$gte': time_period[0], '$lte': time_period[1]}
                
                risk_results = self.pinecone_store.similarity_search(
                    query=f"{risk_type} financial risk exposure management",
                    top_k=15,
                    filter_dict=filter_dict
                )
                
                results['temporal_trends'][risk_type] = risk_results
        
        return results

    def search_financial_metrics(self, 
                                companies: List[str],
                                metrics: List[str] = None,
                                years: List[int] = None) -> Dict[str, Any]:
        """
        Search for financial metrics and performance indicators
        """
        default_metrics = ['assets', 'revenue', 'net income', 'capital ratio', 'deposits', 
                          'loans', 'return on equity', 'efficiency ratio']
        
        search_metrics = metrics or default_metrics
        results = {
            'metric_trends': {},
            'comparative_analysis': {},
            'performance_insights': []
        }
        
        with self.neo4j_driver.session() as session:
            for company in companies:
                query = """
                MATCH (c:Company {name: $company})-[:HAS_YEAR]->(y:Year)
                """ + (f"WHERE y.value IN {years}" if years else "") + """
                MATCH (y)-[:HAS_QUARTER]->(q:Quarter)-[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)
                RETURN c.name as company, y.value as year, q.label as quarter,
                       s.section as section, s.text as text
                ORDER BY y.value, q.label
                """
                
                metric_result = session.run(query, company=company)
                company_metrics = {}
                
                for record in metric_result:
                    text = record['text'].lower()
                    year = record['year']
                    quarter = record['quarter']
                    
                    # Extract metric mentions
                    metric_mentions = {}
                    for metric in search_metrics:
                        if metric.lower() in text:
                            # Extract sentences with metrics
                            sentences = record['text'].split('.')
                            metric_contexts = []
                            for sentence in sentences:
                                if metric.lower() in sentence.lower():
                                    metric_contexts.append(sentence.strip())
                            
                            metric_mentions[metric] = metric_contexts[:3]  # Top 3 mentions
                    
                    if metric_mentions:
                        period_key = f"{year}_{quarter}"
                        if period_key not in company_metrics:
                            company_metrics[period_key] = {}
                        company_metrics[period_key].update(metric_mentions)
                
                results['metric_trends'][company] = company_metrics
        
        return results

    def _generate_timeline_insights(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from timeline search results"""
        insights = {
            'document_count_by_year': {},
            'common_themes': [],
            'trend_analysis': {}
        }
        
        # Analyze graph results
        for result in search_results.get('graph_results', []):
            year = result['year']
            if year not in insights['document_count_by_year']:
                insights['document_count_by_year'][year] = 0
            insights['document_count_by_year'][year] += 1
        
        # Analyze vector results for themes
        vector_results = search_results.get('vector_results', [])
        if vector_results:
            # Extract common financial entities
            all_entities = []
            for result in vector_results:
                metadata = result.get('metadata', {})
                entities_str = metadata.get('financial_entities', '{}')
                try:
                    entities = json.loads(entities_str)
                    all_entities.extend(entities.keys())
                except:
                    continue
            
            # Count entity frequency
            entity_counts = {}
            for entity in all_entities:
                entity_counts[entity] = entity_counts.get(entity, 0) + 1
            
            # Get top themes
            insights['common_themes'] = sorted(entity_counts.items(), 
                                             key=lambda x: x[1], 
                                             reverse=True)[:5]
        
        return insights

    def hybrid_search(self, 
                     query: str,
                     companies: Optional[List[str]] = None,
                     years: Optional[List[int]] = None,
                     sections: Optional[List[str]] = None,
                     top_k: int = 20) -> Dict[str, Any]:
        """
        Perform hybrid search combining graph traversal and vector similarity
        """
        results = {
            'graph_matches': [],
            'vector_matches': [],
            'hybrid_score': {},
            'query': query
        }
        
        # Graph-based search using fulltext
        with self.neo4j_driver.session() as session:
            graph_query = """
            CALL db.index.fulltext.queryNodes('section_text_index', $query) 
            YIELD node, score
            MATCH (node)<-[:HAS_SECTION]-(d:Document)<-[:HAS_DOC]-(q:Quarter)<-[:HAS_QUARTER]-(y:Year)<-[:HAS_YEAR]-(c:Company)
            """
            
            filters = []
            if companies:
                filters.append(f"c.name IN {companies}")
            if years:
                filters.append(f"y.value IN {years}")
            if sections:
                section_filter = " OR ".join([f"node.section CONTAINS '{section}'" for section in sections])
                filters.append(f"({section_filter})")
            
            if filters:
                graph_query += " WHERE " + " AND ".join(filters)
            
            graph_query += """
            RETURN c.name as company, y.value as year, q.label as quarter, 
                   d.document_type as doc_type, node.section as section,
                   node.text as text, score
            ORDER BY score DESC
            LIMIT $top_k
            """
            
            try:
                graph_result = session.run(graph_query, query=query, top_k=top_k)
                for record in graph_result:
                    results['graph_matches'].append({
                        'company': record['company'],
                        'year': record['year'],
                        'quarter': record['quarter'],
                        'document_type': record['doc_type'],
                        'section': record['section'],
                        'text_snippet': record['text'][:400] + "...",
                        'graph_score': record['score']
                    })
            except Exception as e:
                logger.warning(f"Graph fulltext search failed: {e}")
        
        # Vector-based search
        if self.pinecone_store:
            filter_dict = {}
            if companies:
                filter_dict['company'] = {'$in': companies}
            if years:
                filter_dict['year'] = {'$in': years}
            
            vector_results = self.pinecone_store.similarity_search(
                query=query,
                top_k=top_k,
                filter_dict=filter_dict
            )
            results['vector_matches'] = vector_results
        
        return results


if __name__ == "__main__":
    # Test the hybrid search engine
    logging.basicConfig(level=logging.INFO)
    
    # Configuration
    NEO4J_URI = "neo4j://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "newpassword"
    PINECONE_INDEX = os.getenv('PINECONE_INDEX_NAME', 'sec-rag-index')
    
    try:
        search_engine = HybridSearchEngine(
            neo4j_uri=NEO4J_URI,
            neo4j_user=NEO4J_USER,
            neo4j_password=NEO4J_PASSWORD,
            pinecone_index=PINECONE_INDEX
        )
        
        # Test search
        results = search_engine.hybrid_search(
            query="banking operations risk management",
            companies=["ZION", "BAC"],
            top_k=5
        )
        
        logger.info(f"Found {len(results['graph_matches'])} graph matches")
        logger.info(f"Found {len(results['vector_matches'])} vector matches")
        
    except Exception as e:
        logger.error(f"Error testing search engine: {e}")
    finally:
        if 'search_engine' in locals():
            search_engine.close()