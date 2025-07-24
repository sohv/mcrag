#!/usr/bin/env python3
"""
Quick test script to verify DeepSeek R1 integration
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append('backend')

# Load environment variables from backend/.env
def load_env_file():
    """Load environment variables from backend/.env file"""
    env_file = Path('backend/.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value

# Load .env before importing LLM service
load_env_file()

from llm_services import LLMService

async def test_deepseek_integration():
    """Test DeepSeek R1 API integration"""
    print("Testing DeepSeek R1 Integration")
    print("=" * 40)
    
    # Check if API key is available
    deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
    if not deepseek_key:
        print("[FAIL] DEEPSEEK_API_KEY not found in backend/.env file")
        print("Please add it to backend/.env: DEEPSEEK_API_KEY=your_api_key")
        return False
    
    print(f"[PASS] DeepSeek API key found (ending in: ...{deepseek_key[-8:]})")
    
    # Initialize LLM service
    llm_service = LLMService()
    
    # Test availability check
    print("\nTesting API availability...")
    availability = await llm_service.check_llm_availability()
    
    if availability.get("deepseek-r1", False):
        print("[PASS] DeepSeek R1 API is available")
    else:
        print("[FAIL] DeepSeek R1 API is not available")
        return False
    
    # Test actual review functionality
    print("\nTesting code review functionality...")
    
    test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""
    
    test_prompt = "Create a Fibonacci function"
    
    try:
        review_text, suggestions, severity, confidence, processing_time = await llm_service.get_critic_review(
            code=test_code,
            original_prompt=test_prompt,
            language="python",
            model_name="deepseek-r1"
        )
        
        print(f"[PASS] Review generated successfully in {processing_time:.2f}s")
        print(f"Severity: {severity}/5, Confidence: {confidence:.2f}")
        print(f"Suggestions: {len(suggestions)} items")
        print(f"\nReview preview:")
        print(review_text[:200] + "..." if len(review_text) > 200 else review_text)
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Review generation failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_deepseek_integration())
    if success:
        print("\nDeepSeek R1 integration test PASSED!")
    else:
        print("\nDeepSeek R1 integration test FAILED!")
    
    sys.exit(0 if success else 1)
