# Quick evaluation script for testing MCRAG system with a single test case.
# Useful for rapid testing and debugging.

import asyncio
import json
import requests
from datetime import datetime

# Quick test configuration
QUICK_TEST = {
    "id": "quick_test",
    "prompt": "Create a function to calculate the factorial of a number using recursion",
    "language": "python",
    "requirements": "Include input validation and handle edge cases",
    "expected_features": [
        "recursive function",
        "input validation", 
        "base case handling",
        "error handling"
    ]
}

BACKEND_URL = "http://localhost:8000"
API_URL = f"{BACKEND_URL}/api"


async def quick_evaluate():
    # Run a quick evaluation with a single test case.
    print("MCRAG Quick Evaluation")
    print("=" * 40)
    
    # Check if backend is available
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        if response.status_code != 200:
            print("FAILED: Backend not available")
            return
    except requests.RequestException:
        print("FAILED: Cannot connect to backend")
        return
    
    print("SUCCESS: Backend is available")
    
    # Submit test request
    print(f"Testing: Testing: {QUICK_TEST['prompt'][:50]}...")
    
    generation_request = {
        "user_prompt": QUICK_TEST['prompt'],
        "language": QUICK_TEST['language'],
        "requirements": QUICK_TEST['requirements']
    }
    
    start_time = datetime.now()
    
    # Submit request
    response = requests.post(f"{API_URL}/generate-code", json=generation_request)
    if response.status_code != 200:
        print(f"FAILED: Failed to submit request: {response.status_code}")
        return
    
    request_data = response.json()
    request_id = request_data['id']
    print(f"SUCCESS: Request submitted: {request_id}")
    
    # Poll for completion
    print("⏳ Waiting for completion...")
    session_id = None
    
    for attempt in range(60):  # 5 minute timeout
        await asyncio.sleep(5)
        
        response = requests.get(f"{API_URL}/generation-status/{request_id}")
        if response.status_code != 200:
            print(f"FAILED: Failed to check status: {response.status_code}")
            return
        
        status_data = response.json()
        status = status_data.get('status')
        
        print(f"  Status: {status}")
        
        if status == 'completed':
            session_id = status_data.get('session_id')
            break
        elif status == 'failed':
            print(f"FAILED: Generation failed: {status_data.get('error', 'Unknown error')}")
            return
    
    if not session_id:
        print("FAILED: Request timed out")
        return
    
    # Get result
    result_response = requests.get(f"{API_URL}/generation-result/{session_id}")
    if result_response.status_code != 200:
        print(f"FAILED: Failed to get result: {result_response.status_code}")
        return
    
    generation_data = result_response.json()
    end_time = datetime.now()
    
    # Display results
    print("\nSUCCESS: Generation completed!")
    print("=" * 40)
    
    processing_time = (end_time - start_time).total_seconds()
    print(f"⏱️  Processing time: {processing_time:.1f}s")
    
    final_code = generation_data['final_code']['generated_code']
    print(f"📏 Code length: {len(final_code)} chars, {len(final_code.split())} lines")
    
    iterations = generation_data.get('iterations', [])
    print(f"🔄 Iterations: {len(iterations)}")
    
    total_reviews = sum(len(iter_data.get('reviews', [])) for iter_data in iterations)
    print(f"Analyzing: Total reviews: {total_reviews}")
    
    print("\n📋 Generated Code:")
    print("-" * 40)
    print(final_code)
    print("-" * 40)
    
    # Basic quality check
    print("\nResults: Quick Quality Check:")
    checks = []
    
    # Check for expected features
    for feature in QUICK_TEST['expected_features']:
        if feature.lower() in final_code.lower():
            checks.append(f"SUCCESS: {feature}")
        else:
            checks.append(f"FAILED: {feature}")
    
    for check in checks:
        print(f"  {check}")
    
    # Syntax check for Python
    if QUICK_TEST['language'] == 'python':
        try:
            compile(final_code, '<string>', 'exec')
            print("  SUCCESS: Valid Python syntax")
        except SyntaxError as e:
            print(f"  FAILED: Syntax error: {e}")
    
    print(f"\nScore: Quick Score: {sum(1 for check in checks if 'SUCCESS:' in check)}/{len(checks)}")
    
    # Save quick result
    quick_result = {
        'test_case': QUICK_TEST,
        'processing_time': processing_time,
        'code_length': len(final_code),
        'iterations_count': len(iterations),
        'total_reviews': total_reviews,
        'generated_code': final_code,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('quick_evaluation_result.json', 'w') as f:
        json.dump(quick_result, f, indent=2)
    
    print("💾 Result saved to quick_evaluation_result.json")


if __name__ == "__main__":
    asyncio.run(quick_evaluate())
