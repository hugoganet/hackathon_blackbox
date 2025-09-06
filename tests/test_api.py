#!/usr/bin/env python3
"""
Test script to verify that the Blackbox API works correctly
"""

import sys
from backend.main import BlackboxMentor, load_env_file

def _run_api_test():
    """Internal function to run the API test"""
    print("🔍 Testing Blackbox API...")
    
    # Load environment variables
    load_env_file()
    
    try:
        # Initialize the mentor with existing agent file
        mentor = BlackboxMentor("agents/agent-mentor-strict.md")
        print("✅ Mentor Agent initialized successfully")
        
        # Test 1: Simple question
        test_question = "Explain to me in one sentence what Python is"
        print(f"❓ Test 1: {test_question}")
        
        print("⏳ Calling Blackbox API...")
        response = mentor.call_blackbox_api(test_question)
        
        if response.startswith("❌"):
            print(f"❌ API Error: {response}")
            return False
        
        print(f"✅ Response received ({len(response)} characters)")
        print(f"📝 Response: {response[:200]}{'...' if len(response) > 200 else ''}")
        print()
        
        # Test 2: Development mentoring question
        test_question2 = "How to get started well in web development?"
        print(f"❓ Test 2: {test_question2}")
        
        print("⏳ Calling Blackbox API...")
        response2 = mentor.call_blackbox_api(test_question2)
        
        if response2.startswith("❌"):
            print(f"❌ API Error: {response2}")
            return False
            
        print(f"✅ Response received ({len(response2)} characters)")
        print(f"📝 Response: {response2[:300]}{'...' if len(response2) > 300 else ''}")
        
        # Test passed successfully - but still return True for main() compatibility
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

def test_api():
    """Pytest wrapper for the API test"""
    result = _run_api_test()
    assert result == True, "API test failed"

if __name__ == "__main__":
    success = _run_api_test()
    sys.exit(0 if success else 1)