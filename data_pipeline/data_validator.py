import json
import os
import glob
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of data validation"""
    file_path: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

class SECDataValidator:
    """
    Comprehensive data validation and quality assurance for SEC filing JSON files
    """
    
    def __init__(self):
        self.filename_pattern = re.compile(
            r"external_SEC_([A-Z]+)_([0-9A-Z-]+)_(\d{4})_(q\d)_(.*?)(_part_\d+)?\.json", 
            re.IGNORECASE
        )
        
        # Define required fields for SEC documents
        self.required_fields = {
            'domain', 'subdomain', 'Company', 'Document type', 
            'year', 'quarter', 'section', 'text'
        }
        
        # Define expected value ranges and formats
        self.validation_rules = {
            'year': {'type': str, 'min_year': 2020, 'max_year': 2025},
            'quarter': {'type': str, 'pattern': r'^q[1-4]$'},
            'domain': {'type': str, 'expected': 'external'},
            'subdomain': {'type': str, 'expected': 'SEC'},
            'Document type': {'type': str, 'allowed': ['10-K', '10-Q', '8-K']},
            'text': {'type': str, 'min_length': 10},
            'section': {'type': str, 'min_length': 1}
        }
        
        # Known company tickers for validation
        self.known_companies = {
            'BAC', 'BK', 'BOKF', 'BPOP', 'CBSH', 'CFG', 'CFR', 'CMA', 
            'EWBC', 'FCNCA', 'FHN', 'FITB', 'JPM', 'KEY', 'MTB', 'ONB', 
            'PB', 'PNFP', 'RF', 'SNV', 'SSB', 'TFC', 'UMBF', 'USB', 
            'WAL', 'WBS', 'WFC', 'WTFC', 'ZION'
        }

    def validate_filename(self, file_path: str) -> Tuple[bool, List[str], Dict[str, str]]:
        """Validate filename format and extract metadata"""
        basename = os.path.basename(file_path)
        errors = []
        metadata = {}
        
        match = self.filename_pattern.search(basename)
        if not match:
            errors.append(f"Filename doesn't match expected pattern: {basename}")
            return False, errors, metadata
        
        company, doc_type, year, quarter, section, part = match.groups()
        
        # Validate extracted components
        if company.upper() not in self.known_companies:
            errors.append(f"Unknown company ticker: {company}")
        
        try:
            year_int = int(year)
            if not (2020 <= year_int <= 2025):
                errors.append(f"Year out of expected range: {year}")
        except ValueError:
            errors.append(f"Invalid year format: {year}")
        
        if not re.match(r'^q[1-4]$', quarter.lower()):
            errors.append(f"Invalid quarter format: {quarter}")
        
        if doc_type.upper() not in ['10-K', '10-Q', '8-K']:
            errors.append(f"Unexpected document type: {doc_type}")
        
        metadata = {
            'company': company.upper(),
            'document_type': doc_type.upper(),
            'year': year,
            'quarter': quarter.lower(),
            'section': section,
            'part': part
        }
        
        return len(errors) == 0, errors, metadata

    def validate_json_structure(self, file_path: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate JSON file structure and content"""
        errors = []
        warnings = []
        content = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {e}")
            return False, errors, {}
        except UnicodeDecodeError as e:
            errors.append(f"Encoding error: {e}")
            return False, errors, {}
        except Exception as e:
            errors.append(f"Error reading file: {e}")
            return False, errors, {}
        
        # Check required fields
        missing_fields = self.required_fields - set(content.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
        
        # Validate field values
        for field, rules in self.validation_rules.items():
            if field not in content:
                continue
                
            value = content[field]
            
            # Type validation
            if rules.get('type') and not isinstance(value, rules['type']):
                errors.append(f"Field '{field}' should be {rules['type'].__name__}, got {type(value).__name__}")
                continue
            
            # Pattern validation
            if rules.get('pattern') and isinstance(value, str):
                if not re.match(rules['pattern'], value.lower()):
                    errors.append(f"Field '{field}' doesn't match pattern {rules['pattern']}: {value}")
            
            # Expected value validation
            if rules.get('expected') and value != rules['expected']:
                warnings.append(f"Field '{field}' expected '{rules['expected']}', got '{value}'")
            
            # Allowed values validation
            if rules.get('allowed') and value not in rules['allowed']:
                errors.append(f"Field '{field}' value '{value}' not in allowed values: {rules['allowed']}")
            
            # Length validation
            if rules.get('min_length') and isinstance(value, str):
                if len(value) < rules['min_length']:
                    errors.append(f"Field '{field}' too short (min {rules['min_length']}): {len(value)} chars")
            
            # Year range validation
            if field == 'year':
                try:
                    year_int = int(value)
                    if not (rules['min_year'] <= year_int <= rules['max_year']):
                        errors.append(f"Year {year_int} out of range ({rules['min_year']}-{rules['max_year']})")
                except ValueError:
                    errors.append(f"Year field is not a valid integer: {value}")
        
        return len(errors) == 0, errors + warnings, content

    def validate_content_quality(self, content: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate content quality and consistency"""
        errors = []
        warnings = []
        
        text = content.get('text', '')
        
        # Text quality checks
        if len(text) < 100:
            warnings.append(f"Text content is very short: {len(text)} characters")
        
        if len(text) > 1000000:  # 1MB of text
            warnings.append(f"Text content is very long: {len(text)} characters")
        
        # Check for placeholder or template text
        placeholder_indicators = [
            '[placeholder]', '[insert]', '[tbd]', '[todo]', 
            'lorem ipsum', 'sample text', 'example text'
        ]
        
        text_lower = text.lower()
        for indicator in placeholder_indicators:
            if indicator in text_lower:
                warnings.append(f"Possible placeholder text detected: {indicator}")
        
        # Check for excessive repetition
        words = text_lower.split()
        if len(words) > 100:
            word_counts = Counter(words)
            most_common = word_counts.most_common(1)[0]
            if most_common[1] > len(words) * 0.1:  # Word appears more than 10% of the time
                warnings.append(f"Excessive word repetition: '{most_common[0]}' appears {most_common[1]} times")
        
        # Check for proper sentence structure
        sentences = text.split('.')
        if len(sentences) < 5 and len(text) > 500:
            warnings.append("Text might lack proper sentence structure (few periods relative to length)")
        
        # Validate metadata consistency
        filename_company = content.get('Company', '').upper()
        filename_year = content.get('year', '')
        filename_quarter = content.get('quarter', '').lower()
        
        # Cross-validate with optional fields
        if 'filing_date' in content:
            filing_date = content['filing_date']
            try:
                # Parse filing date and check consistency with year
                if filing_date:
                    filing_year = filing_date.split('-')[0]
                    if filing_year != str(filename_year):
                        warnings.append(f"Filing date year {filing_year} doesn't match document year {filename_year}")
            except Exception:
                warnings.append(f"Invalid filing_date format: {filing_date}")
        
        return errors, warnings

    def check_duplicates(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """Check for duplicate documents based on content hash"""
        content_hashes = defaultdict(list)
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    text = content.get('text', '')
                    
                    # Create a simple hash of the text content
                    text_hash = hash(text.strip())
                    content_hashes[text_hash].append(file_path)
                    
            except Exception as e:
                logger.warning(f"Error reading {file_path} for duplicate check: {e}")
        
        # Find duplicates
        duplicates = {str(hash_val): paths for hash_val, paths in content_hashes.items() if len(paths) > 1}
        return duplicates

    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate a single file comprehensively"""
        errors = []
        warnings = []
        metadata = {}
        
        # Step 1: Validate filename
        filename_valid, filename_errors, filename_metadata = self.validate_filename(file_path)
        errors.extend(filename_errors)
        metadata.update(filename_metadata)
        
        # Step 2: Validate JSON structure
        json_valid, json_errors, content = self.validate_json_structure(file_path)
        errors.extend(json_errors)
        
        # Step 3: Validate content quality (only if JSON is valid)
        if json_valid and content:
            content_errors, content_warnings = self.validate_content_quality(content)
            errors.extend(content_errors)
            warnings.extend(content_warnings)
            
            # Add content metadata
            if 'text' in content:
                metadata['text_length'] = len(content['text'])
                metadata['word_count'] = len(content['text'].split())
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            file_path=file_path,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )

    def validate_directory(self, directory: str, pattern: str = "*.json") -> Dict[str, Any]:
        """Validate all files in a directory"""
        file_pattern = os.path.join(directory, pattern)
        file_paths = glob.glob(file_pattern)
        
        logger.info(f"Validating {len(file_paths)} files in {directory}")
        
        results = {
            'total_files': len(file_paths),
            'valid_files': 0,
            'invalid_files': 0,
            'files_with_warnings': 0,
            'validation_results': [],
            'summary': {},
            'duplicates': {}
        }
        
        # Validate each file
        for file_path in file_paths:
            result = self.validate_file(file_path)
            results['validation_results'].append(result)
            
            if result.is_valid:
                results['valid_files'] += 1
            else:
                results['invalid_files'] += 1
            
            if result.warnings:
                results['files_with_warnings'] += 1
        
        # Check for duplicates
        results['duplicates'] = self.check_duplicates(file_paths)
        
        # Generate summary statistics
        all_errors = []
        all_warnings = []
        companies = set()
        years = set()
        quarters = set()
        
        for result in results['validation_results']:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            
            if result.metadata:
                if 'company' in result.metadata:
                    companies.add(result.metadata['company'])
                if 'year' in result.metadata:
                    years.add(result.metadata['year'])
                if 'quarter' in result.metadata:
                    quarters.add(result.metadata['quarter'])
        
        # Error/warning frequency analysis
        error_counts = Counter(all_errors)
        warning_counts = Counter(all_warnings)
        
        results['summary'] = {
            'unique_companies': len(companies),
            'companies': sorted(list(companies)),
            'unique_years': len(years),
            'years': sorted(list(years)),
            'unique_quarters': len(quarters),
            'quarters': sorted(list(quarters)),
            'most_common_errors': error_counts.most_common(5),
            'most_common_warnings': warning_counts.most_common(5),
            'duplicate_groups': len(results['duplicates'])
        }
        
        return results

    def generate_validation_report(self, validation_results: Dict[str, Any], output_path: str):
        """Generate a comprehensive validation report"""
        report = {
            'validation_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_files': validation_results['total_files'],
                'valid_files': validation_results['valid_files'],
                'invalid_files': validation_results['invalid_files'],
                'files_with_warnings': validation_results['files_with_warnings'],
                'success_rate': validation_results['valid_files'] / validation_results['total_files'] * 100
            },
            'data_overview': validation_results['summary'],
            'validation_details': [],
            'duplicates': validation_results['duplicates']
        }
        
        # Include detailed results for invalid files
        for result in validation_results['validation_results']:
            if not result.is_valid or result.warnings:
                report['validation_details'].append({
                    'file': os.path.basename(result.file_path),
                    'valid': result.is_valid,
                    'errors': result.errors,
                    'warnings': result.warnings,
                    'metadata': result.metadata
                })
        
        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Validation report saved to {output_path}")
        return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Configuration
    DATA_DIRECTORY = "zion_10k_md&a_chunked"
    REPORT_PATH = "validation_report.json"
    
    validator = SECDataValidator()
    
    try:
        # Validate all files in directory
        logger.info(f"Starting validation of files in {DATA_DIRECTORY}")
        results = validator.validate_directory(DATA_DIRECTORY)
        
        # Print summary
        print(f"\n=== Validation Summary ===")
        print(f"Total files: {results['total_files']}")
        print(f"Valid files: {results['valid_files']}")
        print(f"Invalid files: {results['invalid_files']}")
        print(f"Files with warnings: {results['files_with_warnings']}")
        print(f"Success rate: {results['valid_files']/results['total_files']*100:.1f}%")
        
        # Print company overview
        summary = results['summary']
        print(f"\n=== Data Overview ===")
        print(f"Companies: {summary['unique_companies']} ({', '.join(summary['companies'][:10])}{'...' if len(summary['companies']) > 10 else ''})")
        print(f"Years: {summary['unique_years']} ({', '.join(summary['years'])})")
        print(f"Quarters: {summary['unique_quarters']} ({', '.join(summary['quarters'])})")
        
        if results['duplicates']:
            print(f"Duplicate groups found: {summary['duplicate_groups']}")
        
        # Generate detailed report
        validator.generate_validation_report(results, REPORT_PATH)
        
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        raise