#!/usr/bin/env python3
"""
Quick OpenAI API Test - Verify API key is working before E2E testing
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_openai_api():
    """Test OpenAI API connectivity"""
    print("🔑 Testing OpenAI API Key...")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenAI API Response: {result}")
        
        if "successful" in result.lower():
            print("🎉 OpenAI API key is working correctly!")
            return True
        else:
            print("⚠️  API responded but unexpected content")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_api()
    exit(0 if success else 1)