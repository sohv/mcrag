#!/usr/bin/env python3
"""
Frontend Demo Test Script
Tests the Multi-LLM Code Review System by submitting sample code
"""

import json

# Sample test codes for different languages
TEST_CODES = {
    "python": {
        "code": '''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
print(fibonacci(10))''',
        "description": "A simple recursive Fibonacci implementation that could be optimized"
    },
    
    "javascript": {
        "code": '''function findMax(arr) {
    let max = arr[0];
    for (let i = 1; i < arr.length; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}

console.log(findMax([1, 5, 3, 9, 2]));''',
        "description": "Find maximum value in array - could use built-in methods"
    },
    
    "java": {
        "code": '''public class Calculator {
    public static int add(int a, int b) {
        return a + b;
    }
    
    public static void main(String[] args) {
        System.out.println(add(5, 3));
    }
}''',
        "description": "Basic calculator class that could use better error handling"
    },
    
    "cpp": {
        "code": '''#include <iostream>
using namespace std;

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    cout << factorial(5) << endl;
    return 0;
}''',
        "description": "Recursive factorial that could benefit from iterative approach"
    }
}

def print_test_instructions():
    """Print instructions for testing the frontend"""
    print("Multi-LLM Code Review System - Frontend Test Guide")
    print("=" * 60)
    print()
    
    print("Test Scenarios:")
    print("-" * 20)
    
    for lang, data in TEST_CODES.items():
        print(f"\n{lang.upper()} Test:")
        print(f"Description: {data['description']}")
        print("Code to test:")
        print("```")
        print(data['code'])
        print("```")
        print()
    
    print("🧪 Testing Steps:")
    print("-" * 20)
    print("1. Start the backend server (see backend README)")
    print("2. Start the frontend development server:")
    print("   cd frontend && npm start")
    print("3. Open http://localhost:3000 in your browser")
    print("4. Test each scenario:")
    print("   - Select language from dropdown")
    print("   - Copy description into the description field")
    print("   - Copy code into the code textarea")
    print("   - Click 'Submit for Review'")
    print("   - Watch the progress indicators")
    print("   - Review the LLM feedback")
    print("   - Add human feedback")
    print()
    
    print("Expected Results:")
    print("-" * 20)
    print("- Gemini (Coder): Provides improvement suggestions")
    print("- GPT-4o (Critic 1): Validates technical accuracy")
    print("- DeepSeek R1 (Critic 2): Offers practical considerations")
    print("- System generates consensus score")
    print("- Final recommendations synthesize all feedback")
    print()
    
    print("What to Look For:")
    print("-" * 20)
    print("- Real-time progress updates")
    print("- Clear feedback from each LLM")
    print("- Suggested code improvements")
    print("- Processing time metrics")
    print("- Consensus scoring")
    print("- Human feedback integration")
    print()
    
    print("Troubleshooting:")
    print("-" * 20)
    print("- Check that backend is running on correct port")
    print("- Verify REACT_APP_BACKEND_URL in frontend/.env")
    print("- Monitor browser console for errors")
    print("- Check backend logs for API issues")
    print()

def generate_test_data_json():
    """Generate JSON file with test data for easy copying"""
    with open('frontend_test_data.json', 'w') as f:
        json.dump(TEST_CODES, f, indent=2)
    print("Test data saved to 'frontend_test_data.json'")
    print("   You can copy code samples from this file for testing")

if __name__ == "__main__":
    print_test_instructions()
    generate_test_data_json()
    
    print("\nQuick Start:")
    print("1. Run: cd frontend && npm start")
    print("2. Open: http://localhost:3000")
    print("3. Test with the code samples above!")
