#!/usr/bin/env python3
"""
Credential Verification Script for SEC Graph APIs
Tests each API service individually to identify connectivity issues
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_neo4j_connection():
    """Test Neo4j Aura connection"""
    print("\n🔍 Testing Neo4j Aura Connection...")
    print("=" * 50)
    
    # Get credentials
    uri = os.getenv('NEO4J_URI')
    username = os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')
    
    print(f"URI: {uri}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    
    try:
        from neo4j import GraphDatabase
        
        # Test connection
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Verify with simple query
        with driver.session() as session:
            result = session.run("RETURN 'Neo4j connection successful!' as message, timestamp() as time")
            record = result.single()
            print(f"✅ SUCCESS: {record['message']}")
            print(f"   Server time: {record['time']}")
            
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print("   Possible issues:")
        print("   - Instance is paused/stopped (check Neo4j Aura console)")
        print("   - Incorrect credentials")
        print("   - Network connectivity issues")
        return False

def test_pinecone_connection():
    """Test Pinecone connection"""
    print("\n🔍 Testing Pinecone Connection...")
    print("=" * 50)
    
    # Get credentials
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'sec-graph-index')
    
    print(f"API Key: {api_key[:20]}..." if api_key else "NOT SET")
    print(f"Index Name: {index_name}")
    
    try:
        from pinecone import Pinecone
        
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        
        # List indexes
        indexes = pc.list_indexes()
        index_names = [idx.name for idx in indexes]
        
        print(f"✅ SUCCESS: Connected to Pinecone")
        print(f"   Available indexes: {index_names}")
        
        # Check if our target index exists
        if index_name in index_names:
            print(f"   ✅ Target index '{index_name}' exists")
            
            # Get index stats
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"   Index stats: {stats.total_vector_count} vectors, {stats.dimension} dimensions")
        else:
            print(f"   ⚠️  Target index '{index_name}' not found")
            print(f"   Available indexes: {index_names}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print("   Possible issues:")
        print("   - Invalid API key")
        print("   - API key expired")
        print("   - Wrong Pinecone environment/project")
        return False

def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n🔍 Testing OpenAI API Connection...")
    print("=" * 50)
    
    # Get credentials
    api_key = os.getenv('OPENAI_API_KEY')
    
    print(f"API Key: {api_key[:20]}..." if api_key else "NOT SET")
    
    try:
        from openai import OpenAI
        
        # Initialize client
        client = OpenAI(api_key=api_key)
        
        # Test with simple completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'OpenAI connection successful!' and the current date."}
            ],
            max_tokens=50,
            temperature=0
        )
        
        content = response.choices[0].message.content.strip()
        print(f"✅ SUCCESS: {content}")
        
        # Test model access
        models = client.models.list()
        model_ids = [model.id for model in models.data]
        
        # Check for required models
        required_models = ['gpt-4o-mini', 'gpt-4o', 'text-embedding-3-small']
        available_required = [model for model in required_models if model in model_ids]
        
        print(f"   Available required models: {available_required}")
        
        # Test embeddings if available
        if 'text-embedding-3-small' in model_ids:
            embeddings_response = client.embeddings.create(
                model="text-embedding-3-small",
                input="Test embedding"
            )
            embedding_dim = len(embeddings_response.data[0].embedding)
            print(f"   ✅ Embeddings working (dimension: {embedding_dim})")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print("   Possible issues:")
        print("   - Invalid API key")
        print("   - API key expired")
        print("   - Insufficient credits")
        print("   - Rate limiting")
        return False

def test_environment_loading():
    """Test environment variable loading"""
    print("\n🔍 Testing Environment Variable Loading...")
    print("=" * 50)
    
    required_vars = {
        'NEO4J_URI': os.getenv('NEO4J_URI'),
        'NEO4J_USERNAME': os.getenv('NEO4J_USERNAME'),
        'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD'),
        'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }
    
    all_set = True
    for var_name, value in required_vars.items():
        if value:
            if 'KEY' in var_name or 'PASSWORD' in var_name:
                print(f"✅ {var_name}: {value[:10]}...")
            else:
                print(f"✅ {var_name}: {value}")
        else:
            print(f"❌ {var_name}: NOT SET")
            all_set = False
    
    return all_set

def main():
    """Run all credential verification tests"""
    print("🔐 SEC Graph API Credential Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test environment loading
    env_ok = test_environment_loading()
    
    if not env_ok:
        print("\n❌ Environment variables not properly loaded. Check .env file.")
        return
    
    # Test each service
    results = {
        'Neo4j': test_neo4j_connection(),
        'Pinecone': test_pinecone_connection(),
        'OpenAI': test_openai_connection()
    }
    
    # Summary
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    for service, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{service:15} {status}")
    
    total_success = sum(results.values())
    print(f"\nOverall: {total_success}/3 services working")
    
    if total_success == 3:
        print("🎉 All APIs are working! Ready to proceed with testing.")
    else:
        print("⚠️  Some APIs need attention before proceeding.")
        print("\nNext steps:")
        if not results['Neo4j']:
            print("- Check Neo4j Aura console for instance status")
        if not results['Pinecone']:
            print("- Verify Pinecone API key in your dashboard")
        if not results['OpenAI']:
            print("- Check OpenAI API key and account credits")

if __name__ == "__main__":
    main()