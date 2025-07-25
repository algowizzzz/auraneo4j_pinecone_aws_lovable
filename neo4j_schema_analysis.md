# Neo4j Schema Analysis & Fix Plan

## Problem Identified

**Current Status**: Cypher node shows "⚠️ Partial" performance due to schema mismatch

## Expected Schema (from cypher.py)

The cypher node expects this exact graph structure:
```
(Company)-[:HAS_YEAR]->(Year)-[:HAS_QUARTER]->(Quarter)-[:HAS_DOC]->(Document)-[:HAS_SECTION]->(Section)
```

### Required Node Properties:
- **Company**: `name` (should match ticker from company_mapping.py)
- **Year**: `value` (integer year)
- **Quarter**: `label` (e.g., "Q1", "Q2", "Q3", "Q4")
- **Document**: `document_type` (e.g., "10-K", "10-Q")
- **Section**: `filename`, `text`, `section`, `financial_entities`

### Required Relationships:
- `Company -[:HAS_YEAR]-> Year`
- `Year -[:HAS_QUARTER]-> Quarter`
- `Quarter -[:HAS_DOC]-> Document`
- `Document -[:HAS_SECTION]-> Section`

## Current Schema (from enhanced_graph_schema.py)

The enhanced schema includes additional financial entities but may not have the basic hierarchical structure:

### Additional Entities:
- **Product**: Financial products (loans, deposits, securities)
- **RiskFactor**: Risk categories (credit, market, operational)
- **Metric**: Financial metrics (capital ratios, profitability)
- **BusinessLine**: Business segments (retail, commercial, investment)
- **Regulation**: Regulatory frameworks (Dodd-Frank, Basel, CCAR)

### Additional Relationships:
- `Section -[:MENTIONS_PRODUCT]-> Product`
- `Section -[:IDENTIFIES_RISK]-> RiskFactor`
- `Section -[:REPORTS_METRIC]-> Metric`
- `Section -[:DESCRIBES_BUSINESS_LINE]-> BusinessLine`
- `Section -[:REFERENCES_REGULATION]-> Regulation`

## Schema Mismatch Issues

1. **Missing Hierarchical Structure**: The basic Company→Year→Quarter→Document→Section hierarchy may not exist
2. **Company Name Inconsistency**: Company nodes may use full names instead of tickers
3. **Missing Temporal Structure**: Year/Quarter nodes may not be properly created
4. **Document Organization**: SEC JSON files may not be organized into Document/Section nodes

## Solution Plan

### Step 1: Validate Current Database State
```bash
# Connect to Neo4j and check current structure
python3 diagnose_neo4j_schema.py
```

### Step 2: Run Graph Population Pipeline
```bash
# Execute the integrated graph builder
python3 data_pipeline/create_graph_v5_integrated.py
```

### Step 3: Fix Company Name Mapping
- Ensure Company nodes use ticker symbols (WFC, JPM, BAC) not full names
- Integrate with existing company_mapping.py system

### Step 4: Validate Schema Structure
- Test that the exact hierarchy exists: Company→Year→Quarter→Document→Section
- Verify all 155 SEC JSON files are properly loaded
- Check that cypher queries can execute successfully

### Step 5: Optimize Performance
- Add indexes on frequently queried properties
- Test query performance for business scenarios

## Expected Cypher Query Examples

After fixes, these queries should work:
```cypher
// Get Wells Fargo 2025 Q1 data
MATCH (c:Company {name: "WFC"})-[:HAS_YEAR]->(y:Year {value: 2025})
      -[:HAS_QUARTER]->(q:Quarter {label: "Q1"})
      -[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)
RETURN s.text, s.section
LIMIT 10

// Get all risk factors for any company in 2024
MATCH (c:Company)-[:HAS_YEAR]->(y:Year {value: 2024})
      -[:HAS_QUARTER]->(q:Quarter)
      -[:HAS_DOC]->(d:Document)-[:HAS_SECTION]->(s:Section)
      -[:IDENTIFIES_RISK]->(r:RiskFactor)
RETURN c.name, r.name, r.type
```

## Success Criteria

✅ **Schema Validation**: All expected node types and relationships exist
✅ **Data Population**: 155 SEC files loaded into hierarchical structure
✅ **Company Mapping**: Company nodes use ticker symbols consistently
✅ **Query Performance**: Cypher queries execute in <500ms
✅ **Business Integration**: Cypher node achieves "✅ Working" status

## Implementation Priority

1. **High**: Run create_graph_v5_integrated.py to populate database
2. **High**: Fix company name mapping in graph creation
3. **Medium**: Add performance indexes
4. **Medium**: Validate with business test queries

This plan addresses the core schema mismatch preventing cypher node functionality.