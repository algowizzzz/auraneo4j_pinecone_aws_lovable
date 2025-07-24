#!/usr/bin/env python3
"""
Debug script to test environment variable loading in pytest context
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

def test_env_loading():
    """Test environment variable loading"""
    print("🔍 Testing Environment Variable Loading in Debug Script...")
    print("=" * 60)
    
    required_vars = {
        'NEO4J_URI': os.getenv('NEO4J_URI'),
        'NEO4J_USERNAME': os.getenv('NEO4J_USERNAME'),  
        'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD'),
        'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }
    
    for var_name, value in required_vars.items():
        if value:
            if 'KEY' in var_name or 'PASSWORD' in var_name:
                print(f"✅ {var_name}: {value[:20]}...")
            else:
                print(f"✅ {var_name}: {value}")
        else:
            print(f"❌ {var_name}: NOT SET")
    
    print("\n🔍 Checking .env file path...")
    print(f"Current working directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")
    
    if os.path.exists('.env'):
        print(f".env file size: {os.path.getsize('.env')} bytes")
    
    print("\n🔍 Testing Neo4j connection...")
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv('NEO4J_URI')
        username = os.getenv('NEO4J_USERNAME')
        password = os.getenv('NEO4J_PASSWORD')
        
        if uri and username and password:
            driver = GraphDatabase.driver(uri, auth=(username, password))
            with driver.session() as session:
                result = session.run("RETURN 'Debug test successful' as message")
                record = result.single()
                print(f"✅ Neo4j connection successful: {record['message']}")
            driver.close()
        else:
            print("❌ Missing Neo4j credentials")
            
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")

if __name__ == "__main__":
    test_env_loading()