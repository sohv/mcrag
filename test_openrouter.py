#!/usr/bin/env python3
"""
Test script for OpenRouter integration
Run this to verify OpenRouter API configuration works
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from llm_services import LLMService

async def test_openrouter():
    """Test OpenRouter integration with all models"""
    
    # Load environment
    load_dotenv()
    
    print("Testing OpenRouter integration...")
    print(f"OpenRouter API Key: {'✓ Set' if os.getenv('OPENROUTER_API_KEY') else '✗ Missing'}")
    print(f"OpenRouter URL: {os.getenv('OPENROUTER_URL', 'Default')}")
    print()
    
    # Initialize service
    llm_service = LLMService()
    
    # Check model availability
    print("Checking model availability...")
    availability = await llm_service.check_llm_availability()
    
    for role, available in availability.items():
        model = llm_service.models[role]
        status = "✓ Available" if available else "✗ Unavailable"
        print(f"  {role.upper()}: {model} - {status}")
    
    print()
    
    # Test generator if available
    if availability.get('generator', False):
        print("Testing code generation...")
        try:
            code, explanation, time_taken = await llm_service.get_generator_response(
                "Write a simple Python function that calculates factorial", 
                "python"
            )
            print(f"  Generator response time: {time_taken:.2f}s")
            print(f"  Generated code preview: {code[:100]}...")
            print("  ✓ Generator test successful")
        except Exception as e:
            print(f"  ✗ Generator test failed: {e}")
    else:
        print("  ⚠ Skipping generator test (unavailable)")
    
    print()
    
    # Test critic if available
    if availability.get('critic1', False):
        print("Testing code review...")
        try:
            test_code = "def factorial(n):\n    return n * factorial(n-1) if n > 1 else 1"
            review, suggestions, severity, confidence, time_taken = await llm_service.get_critic_review(
                test_code, "Write a factorial function", "python", "gpt-4o"
            )
            print(f"  Critic response time: {time_taken:.2f}s")
            print(f"  Found {len(suggestions)} suggestions")
            print(f"  Severity: {severity}/5, Confidence: {confidence:.2f}")
            print("  ✓ Critic test successful")
        except Exception as e:
            print(f"  ✗ Critic test failed: {e}")
    else:
        print("  ⚠ Skipping critic test (unavailable)")
    
    print()
    print("OpenRouter integration test complete!")

if __name__ == "__main__":
    asyncio.run(test_openrouter())