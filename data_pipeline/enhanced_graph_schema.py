import json
import re
from typing import Dict, List, Any, Set, Tuple
from neo4j import GraphDatabase
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class FinancialEntityExtractor:
    """Extract and classify financial entities from SEC filings"""
    
    def __init__(self):
        # Define financial entity patterns and categories
        self.entity_patterns = {
            'products': {
                'loans': r'\b(?:loan|loans|lending|credit|mortgage|mortgages)\b',
                'deposits': r'\b(?:deposit|deposits|depository|savings|checking)\b',
                'securities': r'\b(?:securities|bonds|treasury|investment|investments)\b',
                'cards': r'\b(?:card|cards|credit card|debit card)\b',
                'derivatives': r'\b(?:derivative|derivatives|swap|swaps|option|options)\b'
            },
            'risks': {
                'credit_risk': r'\b(?:credit risk|default|charge.*off|provision|allowance)\b',
                'market_risk': r'\b(?:market risk|interest.*rate.*risk|volatility)\b',
                'operational_risk': r'\b(?:operational risk|cyber|fraud|compliance)\b',
                'liquidity_risk': r'\b(?:liquidity|funding|cash flow)\b',
                'regulatory_risk': r'\b(?:regulatory|regulation|compliance|examination)\b'
            },
            'metrics': {
                'capital_ratios': r'\b(?:capital ratio|tier 1|tier1|leverage ratio|risk.*weighted)\b',
                'profitability': r'\b(?:roe|roa|return.*equity|return.*assets|net.*income|revenue)\b',
                'efficiency': r'\b(?:efficiency.*ratio|expense.*ratio|cost.*income)\b',
                'asset_quality': r'\b(?:npl|non.*performing|charge.*off|provision)\b'
            },
            'business_lines': {
                'retail_banking': r'\b(?:retail|consumer|personal|individual|branch)\b',
                'commercial_banking': r'\b(?:commercial|business|corporate|middle.*market)\b',
                'investment_banking': r'\b(?:investment.*bank|capital.*market|underwriting|advisory)\b',
                'wealth_management': r'\b(?:wealth|trust|private.*bank|asset.*management)\b'
            },
            'regulations': {
                'dodd_frank': r'\b(?:dodd.*frank|volcker|stress.*test)\b',
                'basel': r'\b(?:basel|capital.*requirement|risk.*weight)\b',
                'ccar': r'\b(?:ccar|comprehensive.*capital|stress.*test)\b',
                'cfpb': r'\b(?:cfpb|consumer.*protection)\b'
            }
        }
        
        # Industry and sector classifications
        self.industry_mappings = {
            'regional_bank': ['community', 'regional', 'local', 'state'],
            'money_center_bank': ['money center', 'global', 'international', 'nationwide'],
            'investment_bank': ['investment', 'securities', 'broker', 'dealer'],
            'specialty_finance': ['specialty', 'niche', 'focused']
        }

    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract financial entities from text with context"""
        entities = defaultdict(list)
        text_lower = text.lower()
        
        for category, patterns in self.entity_patterns.items():
            for entity_type, pattern in patterns.items():
                matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
                
                for match in matches:
                    # Extract context around the match
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()
                    
                    entities[category].append({
                        'type': entity_type,
                        'text': match.group(),
                        'context': context,
                        'position': {'start': match.start(), 'end': match.end()}
                    })
        
        return dict(entities)

    def classify_company_type(self, text: str, company_name: str) -> Dict[str, Any]:
        """Classify company type based on business description"""
        text_lower = text.lower()
        
        classification = {
            'primary_type': 'commercial_bank',  # default
            'business_lines': [],
            'geographic_scope': 'regional',  # default
            'asset_size_category': 'unknown',
            'specializations': []
        }
        
        # Determine primary type
        for bank_type, keywords in self.industry_mappings.items():
            for keyword in keywords:
                if keyword in text_lower:
                    classification['primary_type'] = bank_type
                    break
        
        # Identify business lines
        business_line_indicators = {
            'retail_banking': ['retail', 'consumer', 'branch', 'personal'],
            'commercial_banking': ['commercial', 'business', 'corporate'],
            'investment_banking': ['investment', 'capital markets', 'underwriting'],
            'wealth_management': ['wealth', 'trust', 'private banking'],
            'mortgage_banking': ['mortgage', 'home loan', 'residential'],
            'credit_card': ['credit card', 'card services']
        }
        
        for line, indicators in business_line_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                classification['business_lines'].append(line)
        
        # Geographic scope
        geographic_indicators = {
            'local': ['local', 'community', 'hometown'],
            'regional': ['regional', 'state', 'multi-state'],
            'national': ['national', 'nationwide', 'coast-to-coast'],
            'international': ['international', 'global', 'worldwide']
        }
        
        for scope, indicators in geographic_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                classification['geographic_scope'] = scope
                break
        
        # Asset size (look for numerical indicators)
        asset_patterns = [
            (r'\$(\d+(?:\.\d+)?)\s*billion', 'large'),
            (r'\$(\d+(?:\.\d+)?)\s*million', 'small'),
            (r'assets.*\$(\d+(?:\.\d+)?)\s*billion', 'large'),
            (r'assets.*\$(\d+(?:\.\d+)?)\s*million', 'small')
        ]
        
        for pattern, size_category in asset_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                amount = float(matches[0])
                if 'billion' in pattern:
                    if amount >= 50:
                        classification['asset_size_category'] = 'large'
                    elif amount >= 10:
                        classification['asset_size_category'] = 'medium'
                    else:
                        classification['asset_size_category'] = 'small'
                break
        
        return classification


class EnhancedGraphSchemaManager:
    """Manage enhanced Neo4j schema for financial analysis"""
    
    def __init__(self, driver):
        self.driver = driver
        self.entity_extractor = FinancialEntityExtractor()

    def create_enhanced_constraints_and_indexes(self):
        """Create enhanced constraints and indexes for financial entities"""
        with self.driver.session() as session:
            session.execute_write(self._create_enhanced_schema_tx)

    @staticmethod
    def _create_enhanced_schema_tx(tx):
        # Enhanced entity constraints
        constraints = [
            # Financial entities
            "CREATE CONSTRAINT unique_product IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT unique_risk_factor IF NOT EXISTS FOR (r:RiskFactor) REQUIRE r.name IS UNIQUE",
            "CREATE CONSTRAINT unique_metric IF NOT EXISTS FOR (m:Metric) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT unique_business_line IF NOT EXISTS FOR (bl:BusinessLine) REQUIRE bl.name IS UNIQUE",
            "CREATE CONSTRAINT unique_regulation IF NOT EXISTS FOR (reg:Regulation) REQUIRE reg.name IS UNIQUE",
            
            # Industry and market entities
            "CREATE CONSTRAINT unique_industry IF NOT EXISTS FOR (i:Industry) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT unique_market IF NOT EXISTS FOR (m:Market) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT unique_competitor IF NOT EXISTS FOR (c:Competitor) REQUIRE c.name IS UNIQUE",
            
            # Temporal entities for trends
            "CREATE CONSTRAINT unique_trend IF NOT EXISTS FOR (t:Trend) REQUIRE (t.company, t.metric, t.period) IS UNIQUE",
            "CREATE CONSTRAINT unique_event IF NOT EXISTS FOR (e:Event) REQUIRE (e.company, e.date, e.type) IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                tx.run(constraint)
            except Exception as e:
                logger.warning(f"Constraint creation warning: {e}")
        
        # Enhanced indexes for performance
        indexes = [
            # Financial entity indexes
            "CREATE INDEX product_category_index IF NOT EXISTS FOR (p:Product) ON (p.category, p.type)",
            "CREATE INDEX risk_severity_index IF NOT EXISTS FOR (r:RiskFactor) ON (r.severity, r.category)",
            "CREATE INDEX metric_value_index IF NOT EXISTS FOR (m:Metric) ON (m.value, m.unit)",
            "CREATE INDEX business_line_revenue_index IF NOT EXISTS FOR (bl:BusinessLine) ON (bl.revenue_contribution)",
            
            # Temporal indexes
            "CREATE INDEX trend_period_index IF NOT EXISTS FOR (t:Trend) ON (t.start_period, t.end_period)",
            "CREATE INDEX event_date_index IF NOT EXISTS FOR (e:Event) ON (e.date, e.impact_level)",
            
            # Company classification indexes
            "CREATE INDEX company_type_index IF NOT EXISTS FOR (c:Company) ON (c.bank_type, c.asset_size_category)",
            "CREATE INDEX company_geography_index IF NOT EXISTS FOR (c:Company) ON (c.geographic_scope, c.primary_markets)",
            
            # Text search indexes
            "CREATE FULLTEXT INDEX entity_text_index IF NOT EXISTS FOR (n:Product|RiskFactor|BusinessLine|Regulation) ON EACH [n.description, n.context]"
        ]
        
        for index in indexes:
            try:
                tx.run(index)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")

    def create_financial_entities(self, section_data: Dict[str, Any], extracted_entities: Dict[str, List[Dict[str, Any]]]):
        """Create financial entities and relationships"""
        with self.driver.session() as session:
            session.execute_write(self._create_financial_entities_tx, section_data, extracted_entities)

    @staticmethod
    def _create_financial_entities_tx(tx, section_data, extracted_entities):
        section_filename = section_data['section_filename']
        
        # Create entities for each category
        for category, entities in extracted_entities.items():
            for entity in entities:
                entity_type = entity['type']
                entity_text = entity['text']
                context = entity['context']
                
                # Create the appropriate entity node based on category
                if category == 'products':
                    query = """
                    MATCH (s:Section {filename: $section_filename})
                    MERGE (p:Product {name: $entity_name})
                    ON CREATE SET
                        p.type = $entity_type,
                        p.category = $category,
                        p.description = $context
                    MERGE (s)-[:MENTIONS_PRODUCT]->(p)
                    """
                elif category == 'risks':
                    query = """
                    MATCH (s:Section {filename: $section_filename})
                    MERGE (r:RiskFactor {name: $entity_name})
                    ON CREATE SET
                        r.type = $entity_type,
                        r.category = $category,
                        r.description = $context,
                        r.severity = 'medium'
                    MERGE (s)-[:IDENTIFIES_RISK]->(r)
                    """
                elif category == 'metrics':
                    query = """
                    MATCH (s:Section {filename: $section_filename})
                    MERGE (m:Metric {name: $entity_name})
                    ON CREATE SET
                        m.type = $entity_type,
                        m.category = $category,
                        m.description = $context
                    MERGE (s)-[:REPORTS_METRIC]->(m)
                    """
                elif category == 'business_lines':
                    query = """
                    MATCH (s:Section {filename: $section_filename})
                    MERGE (bl:BusinessLine {name: $entity_name})
                    ON CREATE SET
                        bl.type = $entity_type,
                        bl.category = $category,
                        bl.description = $context
                    MERGE (s)-[:DESCRIBES_BUSINESS_LINE]->(bl)
                    """
                elif category == 'regulations':
                    query = """
                    MATCH (s:Section {filename: $section_filename})
                    MERGE (reg:Regulation {name: $entity_name})
                    ON CREATE SET
                        reg.type = $entity_type,
                        reg.category = $category,
                        reg.description = $context
                    MERGE (s)-[:REFERENCES_REGULATION]->(reg)
                    """
                else:
                    continue  # Skip unknown categories
                
                tx.run(query, 
                      section_filename=section_filename,
                      entity_name=entity_text,
                      entity_type=entity_type,
                      category=category,
                      context=context)

    def enhance_company_classification(self, company_name: str, text: str):
        """Enhance company node with detailed classification"""
        classification = self.entity_extractor.classify_company_type(text, company_name)
        
        with self.driver.session() as session:
            session.execute_write(self._update_company_classification_tx, company_name, classification)

    @staticmethod
    def _update_company_classification_tx(tx, company_name, classification):
        query = """
        MATCH (c:Company {name: $company_name})
        SET c.bank_type = $primary_type,
            c.geographic_scope = $geographic_scope,
            c.asset_size_category = $asset_size_category,
            c.business_lines = $business_lines,
            c.specializations = $specializations,
            c.classification_updated = datetime()
        
        // Create industry relationships
        WITH c
        MERGE (i:Industry {name: $primary_type})
        MERGE (c)-[:OPERATES_IN_INDUSTRY]->(i)
        
        // Create market relationships based on geographic scope
        WITH c
        MERGE (m:Market {name: $geographic_scope})
        ON CREATE SET m.type = 'geographic'
        MERGE (c)-[:OPERATES_IN_MARKET]->(m)
        """
        
        tx.run(query,
               company_name=company_name,
               primary_type=classification['primary_type'],
               geographic_scope=classification['geographic_scope'],
               asset_size_category=classification['asset_size_category'],
               business_lines=classification['business_lines'],
               specializations=classification['specializations'])

    def create_competitive_relationships(self):
        """Create competitive relationships between similar companies"""
        with self.driver.session() as session:
            session.execute_write(self._create_competitive_relationships_tx)

    @staticmethod
    def _create_competitive_relationships_tx(tx):
        # Create competitive relationships based on industry and market overlap
        query = """
        MATCH (c1:Company)-[:OPERATES_IN_INDUSTRY]->(i:Industry)<-[:OPERATES_IN_INDUSTRY]-(c2:Company)
        WHERE c1 <> c2
        MATCH (c1)-[:OPERATES_IN_MARKET]->(m:Market)<-[:OPERATES_IN_MARKET]-(c2)
        MERGE (c1)-[:COMPETES_WITH {basis: 'industry_market_overlap'}]->(c2)
        """
        tx.run(query)
        
        # Create peer relationships based on asset size
        query = """
        MATCH (c1:Company), (c2:Company)
        WHERE c1 <> c2 
        AND c1.asset_size_category = c2.asset_size_category
        AND c1.asset_size_category <> 'unknown'
        MERGE (c1)-[:PEER_COMPANY {basis: 'asset_size'}]->(c2)
        """
        tx.run(query)

    def create_temporal_trend_analysis(self):
        """Create trend analysis relationships across time periods"""
        with self.driver.session() as session:
            session.execute_write(self._create_trend_analysis_tx)

    @staticmethod
    def _create_trend_analysis_tx(tx):
        # Create metric trends across years for each company
        query = """
        MATCH (c:Company)-[:HAS_YEAR]->(y:Year)-[:HAS_QUARTER]->(q:Quarter)
        -[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)-[:REPORTS_METRIC]->(m:Metric)
        WITH c, m, y, count(s) as mention_count
        ORDER BY c.name, m.name, y.value
        WITH c, m, collect({year: y.value, mentions: mention_count}) as yearly_data
        WHERE size(yearly_data) >= 2
        
        CREATE (t:Trend {
            company: c.name,
            metric: m.name,
            period: yearly_data[0].year + '-' + yearly_data[-1].year,
            data_points: yearly_data,
            created: datetime()
        })
        
        MERGE (c)-[:HAS_TREND]->(t)
        MERGE (t)-[:TRACKS_METRIC]->(m)
        """
        tx.run(query)

    def create_risk_correlation_network(self):
        """Create risk correlation relationships"""
        with self.driver.session() as session:
            session.execute_write(self._create_risk_correlations_tx)

    @staticmethod
    def _create_risk_correlations_tx(tx):
        # Find risks mentioned together in the same sections
        query = """
        MATCH (s:Section)-[:IDENTIFIES_RISK]->(r1:RiskFactor)
        MATCH (s)-[:IDENTIFIES_RISK]->(r2:RiskFactor)
        WHERE r1 <> r2
        WITH r1, r2, count(s) as co_occurrence_count
        WHERE co_occurrence_count >= 2
        MERGE (r1)-[:CORRELATED_WITH {strength: co_occurrence_count}]->(r2)
        """
        tx.run(query)

    def get_enhanced_schema_stats(self) -> Dict[str, Any]:
        """Get statistics about the enhanced schema"""
        with self.driver.session() as session:
            stats = {}
            
            # Count entities by type
            entity_counts = session.run("""
            MATCH (n)
            WHERE n:Product OR n:RiskFactor OR n:Metric OR n:BusinessLine OR n:Regulation
            OR n:Industry OR n:Market OR n:Trend
            RETURN labels(n)[0] as entity_type, count(n) as count
            ORDER BY count DESC
            """)
            
            stats['entity_counts'] = {record['entity_type']: record['count'] for record in entity_counts}
            
            # Count relationships
            relationship_counts = session.run("""
            MATCH ()-[r]->()
            WHERE type(r) IN ['MENTIONS_PRODUCT', 'IDENTIFIES_RISK', 'REPORTS_METRIC', 
                              'DESCRIBES_BUSINESS_LINE', 'REFERENCES_REGULATION', 
                              'COMPETES_WITH', 'PEER_COMPANY', 'CORRELATED_WITH']
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
            """)
            
            stats['relationship_counts'] = {record['relationship_type']: record['count'] for record in relationship_counts}
            
            # Company classification stats
            company_stats = session.run("""
            MATCH (c:Company)
            WHERE c.bank_type IS NOT NULL
            RETURN c.bank_type as bank_type, c.asset_size_category as size_category, 
                   c.geographic_scope as scope, count(*) as count
            """)
            
            stats['company_classifications'] = [dict(record) for record in company_stats]
            
            return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test the enhanced schema
    from neo4j import GraphDatabase
    
    URI = "neo4j://localhost:7687"
    USER = "neo4j"
    PASSWORD = "newpassword"
    
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    schema_manager = EnhancedGraphSchemaManager(driver)
    
    try:
        logger.info("Creating enhanced schema...")
        schema_manager.create_enhanced_constraints_and_indexes()
        
        logger.info("Schema enhancement complete!")
        
        # Get stats
        stats = schema_manager.get_enhanced_schema_stats()
        logger.info(f"Enhanced schema stats: {stats}")
        
    except Exception as e:
        logger.error(f"Error creating enhanced schema: {e}")
    finally:
        driver.close()