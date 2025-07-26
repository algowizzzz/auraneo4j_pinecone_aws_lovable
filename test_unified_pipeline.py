#!/usr/bin/env python3
"""
Test script for Unified SEC Pipeline
Validates environment, connections, and pipeline functionality
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_pipeline.unified_sec_pipeline import UnifiedSECPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_environment():
    """Test environment setup"""
    logger.info("🔍 Testing environment setup...")
    
    required_vars = ['NEO4J_URI', 'NEO4J_PASSWORD', 'PINECONE_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"❌ Missing environment variables: {missing}")
        return False
    
    logger.info("✅ Environment variables present")
    return True

def test_output_directory():
    """Test output directory structure"""
    logger.info("🔍 Testing output directory structure...")
    
    output_dir = Path("output")
    if not output_dir.exists():
        logger.error("❌ Output directory not found")
        return False
    
    # Count companies and files
    companies = [d for d in output_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    md_files = list(output_dir.glob("*/10-K/*/*.md"))
    
    logger.info(f"📁 Found {len(companies)} companies, {len(md_files)} markdown files")
    
    if len(md_files) == 0:
        logger.error("❌ No markdown files found")
        return False
    
    # Show sample files
    for i, file_path in enumerate(md_files[:3]):
        parts = file_path.parts
        logger.info(f"   Sample {i+1}: {parts[-3]}/{parts[-2]}/{parts[-1]}")
    
    logger.info("✅ Output directory structure valid")
    return True

def test_pipeline_initialization():
    """Test pipeline initialization"""
    logger.info("🔍 Testing pipeline initialization...")
    
    try:
        pipeline = UnifiedSECPipeline()
        logger.info("✅ Pipeline initialization successful")
        return True, pipeline
    except Exception as e:
        logger.error(f"❌ Pipeline initialization failed: {e}")
        return False, None

def test_connections(pipeline):
    """Test database connections"""
    logger.info("🔍 Testing database connections...")
    
    try:
        pipeline.initialize_connections()
        logger.info("✅ Database connections successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connections failed: {e}")
        return False
    finally:
        pipeline.close_connections()

def test_file_parsing(pipeline):
    """Test markdown file parsing"""
    logger.info("🔍 Testing file parsing...")
    
    # Find first markdown file
    output_dir = Path("output")
    md_files = list(output_dir.glob("*/10-K/*/*.md"))
    
    if not md_files:
        logger.error("❌ No files to test")
        return False
    
    test_file = str(md_files[0])
    logger.info(f"📄 Testing with: {test_file}")
    
    try:
        parsed_data = pipeline.parse_markdown_file(test_file)
        
        if not parsed_data:
            logger.error("❌ File parsing returned None")
            return False
        
        text_length = parsed_data['text_length']
        metadata = parsed_data['metadata']
        
        logger.info(f"   Text length: {text_length:,} characters")
        logger.info(f"   Metadata: {metadata}")
        
        if text_length < 1000:
            logger.warning("⚠️  Text seems short - might be parsing issue")
        
        logger.info("✅ File parsing successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ File parsing failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🧪 UNIFIED PIPELINE TESTING")
    logger.info("=" * 50)
    
    tests = [
        ("Environment Setup", test_environment),
        ("Output Directory", test_output_directory),
    ]
    
    # Run basic tests
    for test_name, test_func in tests:
        if not test_func():
            logger.error(f"❌ Test failed: {test_name}")
            return False
    
    # Test pipeline initialization
    success, pipeline = test_pipeline_initialization()
    if not success:
        return False
    
    # Test connections
    if not test_connections(pipeline):
        return False
    
    # Test file parsing
    if not test_file_parsing(pipeline):
        return False
    
    logger.info("\n🎉 ALL TESTS PASSED!")
    logger.info("✅ Ready to run unified pipeline")
    
    # Ask if user wants to run pipeline
    response = input("\n🚀 Run the pipeline now? (y/n): ").lower().strip()
    if response == 'y':
        logger.info("Starting pipeline execution...")
        
        try:
            pipeline = UnifiedSECPipeline()
            results = pipeline.run_pipeline(max_files=6)  # Test with 6 files
            
            if results['success']:
                logger.info("🎉 Pipeline completed successfully!")
            else:
                logger.error("❌ Pipeline completed with issues")
                
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Testing interrupted by user")
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        sys.exit(1)