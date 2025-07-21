#!/usr/bin/env python3
"""
Comprehensive Backend Test Suite for Multi-LLM Code Review System
Tests all API endpoints and core functionality
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://5fb3f7ee-427d-44c2-880d-f98bdbda17b9.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.submission_id = None
        self.session_id = None
        
    async def setup(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def teardown(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            async with self.session.get(f"{BACKEND_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    if "Multi-LLM Code Review System API" in data.get("message", ""):
                        self.log_test("Root endpoint", True, "API is accessible")
                        return True
                    else:
                        self.log_test("Root endpoint", False, f"Unexpected message: {data}")
                        return False
                else:
                    self.log_test("Root endpoint", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Root endpoint", False, f"Connection error: {str(e)}")
            return False
    
    async def test_submit_code(self):
        """Test code submission endpoint"""
        test_code = '''def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# This is inefficient recursive implementation
print(fibonacci(10))'''
        
        payload = {
            "original_code": test_code,
            "language": "python",
            "description": "A simple fibonacci function that needs optimization"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/submit-code",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "id" in data and "status" in data:
                        self.submission_id = data["id"]
                        self.log_test("Submit code", True, f"Submission created with ID: {self.submission_id}")
                        return True
                    else:
                        self.log_test("Submit code", False, "Missing required fields in response", data)
                        return False
                else:
                    error_data = await response.text()
                    self.log_test("Submit code", False, f"HTTP {response.status}", error_data)
                    return False
        except Exception as e:
            self.log_test("Submit code", False, f"Request error: {str(e)}")
            return False
    
    async def test_start_review(self):
        """Test starting review process"""
        if not self.submission_id:
            self.log_test("Start review", False, "No submission ID available")
            return False
        
        try:
            async with self.session.post(f"{BACKEND_URL}/start-review/{self.submission_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    if "session_id" in data and "status" in data:
                        self.session_id = data["session_id"]
                        self.log_test("Start review", True, f"Review started with session ID: {self.session_id}")
                        return True
                    else:
                        self.log_test("Start review", False, "Missing required fields in response", data)
                        return False
                else:
                    error_data = await response.text()
                    self.log_test("Start review", False, f"HTTP {response.status}", error_data)
                    return False
        except Exception as e:
            self.log_test("Start review", False, f"Request error: {str(e)}")
            return False
    
    async def test_review_status(self):
        """Test getting review status"""
        if not self.session_id:
            self.log_test("Review status", False, "No session ID available")
            return False
        
        try:
            async with self.session.get(f"{BACKEND_URL}/review-status/{self.session_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["session_id", "status", "consensus_score", "has_coder_feedback", 
                                     "has_critic1_feedback", "has_critic2_feedback", "human_feedback_count"]
                    
                    if all(field in data for field in required_fields):
                        self.log_test("Review status", True, f"Status: {data['status']}")
                        return True
                    else:
                        missing = [f for f in required_fields if f not in data]
                        self.log_test("Review status", False, f"Missing fields: {missing}", data)
                        return False
                else:
                    error_data = await response.text()
                    self.log_test("Review status", False, f"HTTP {response.status}", error_data)
                    return False
        except Exception as e:
            self.log_test("Review status", False, f"Request error: {str(e)}")
            return False
    
    async def wait_for_review_completion(self, max_wait_time: int = 120):
        """Wait for review to complete"""
        if not self.session_id:
            return False
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                async with self.session.get(f"{BACKEND_URL}/review-status/{self.session_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get("status")
                        
                        if status == "completed":
                            self.log_test("Review completion", True, f"Review completed in {time.time() - start_time:.1f}s")
                            return True
                        elif status == "failed":
                            self.log_test("Review completion", False, "Review failed")
                            return False
                        
                        # Still in progress, wait a bit
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(5)
            except Exception as e:
                print(f"Error checking status: {e}")
                await asyncio.sleep(5)
        
        self.log_test("Review completion", False, f"Timeout after {max_wait_time}s")
        return False
    
    async def test_review_result(self):
        """Test getting complete review result"""
        if not self.session_id:
            self.log_test("Review result", False, "No session ID available")
            return False
        
        try:
            async with self.session.get(f"{BACKEND_URL}/review-result/{self.session_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["session", "submission", "final_recommendations"]
                    
                    if all(field in data for field in required_fields):
                        has_coder = data.get("coder_feedback") is not None
                        has_critics = len(data.get("critic_feedbacks", [])) > 0
                        
                        details = f"Coder feedback: {has_coder}, Critics: {len(data.get('critic_feedbacks', []))}"
                        self.log_test("Review result", True, details)
                        return True
                    else:
                        missing = [f for f in required_fields if f not in data]
                        self.log_test("Review result", False, f"Missing fields: {missing}", data)
                        return False
                else:
                    error_data = await response.text()
                    self.log_test("Review result", False, f"HTTP {response.status}", error_data)
                    return False
        except Exception as e:
            self.log_test("Review result", False, f"Request error: {str(e)}")
            return False
    
    async def test_human_feedback(self):
        """Test adding human feedback"""
        if not self.session_id:
            self.log_test("Human feedback", False, "No session ID available")
            return False
        
        payload = {
            "feedback_text": "The LLM suggestions look good, but I think we should also consider adding input validation for negative numbers.",
            "rating": 4
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/human-feedback/{self.session_id}",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "message" in data and "feedback_id" in data:
                        self.log_test("Human feedback", True, f"Feedback added: {data['feedback_id']}")
                        return True
                    else:
                        self.log_test("Human feedback", False, "Missing required fields in response", data)
                        return False
                else:
                    error_data = await response.text()
                    self.log_test("Human feedback", False, f"HTTP {response.status}", error_data)
                    return False
        except Exception as e:
            self.log_test("Human feedback", False, f"Request error: {str(e)}")
            return False
    
    async def test_get_submissions(self):
        """Test getting all submissions"""
        try:
            async with self.session.get(f"{BACKEND_URL}/submissions") as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        submission_count = len(data)
                        self.log_test("Get submissions", True, f"Retrieved {submission_count} submissions")
                        return True
                    else:
                        self.log_test("Get submissions", False, "Response is not a list", data)
                        return False
                else:
                    error_data = await response.text()
                    self.log_test("Get submissions", False, f"HTTP {response.status}", error_data)
                    return False
        except Exception as e:
            self.log_test("Get submissions", False, f"Request error: {str(e)}")
            return False
    
    async def test_llm_feedbacks(self):
        """Test getting LLM feedbacks for a session"""
        if not self.session_id:
            self.log_test("LLM feedbacks", False, "No session ID available")
            return False
        
        try:
            async with self.session.get(f"{BACKEND_URL}/llm-feedbacks/{self.session_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        feedback_count = len(data)
                        self.log_test("LLM feedbacks", True, f"Retrieved {feedback_count} LLM feedbacks")
                        return True
                    else:
                        self.log_test("LLM feedbacks", False, "Response is not a list", data)
                        return False
                else:
                    error_data = await response.text()
                    self.log_test("LLM feedbacks", False, f"HTTP {response.status}", error_data)
                    return False
        except Exception as e:
            self.log_test("LLM feedbacks", False, f"Request error: {str(e)}")
            return False
    
    async def test_error_handling(self):
        """Test error handling with invalid inputs"""
        tests_passed = 0
        total_tests = 0
        
        # Test invalid submission ID
        total_tests += 1
        try:
            async with self.session.post(f"{BACKEND_URL}/start-review/invalid-id") as response:
                if response.status == 404:
                    tests_passed += 1
                    print("✅ Invalid submission ID handled correctly")
                else:
                    print(f"❌ Invalid submission ID: Expected 404, got {response.status}")
        except Exception as e:
            print(f"❌ Invalid submission ID test failed: {e}")
        
        # Test invalid session ID
        total_tests += 1
        try:
            async with self.session.get(f"{BACKEND_URL}/review-status/invalid-session") as response:
                if response.status == 404:
                    tests_passed += 1
                    print("✅ Invalid session ID handled correctly")
                else:
                    print(f"❌ Invalid session ID: Expected 404, got {response.status}")
        except Exception as e:
            print(f"❌ Invalid session ID test failed: {e}")
        
        # Test invalid code submission
        total_tests += 1
        try:
            payload = {"original_code": "", "language": "invalid_language"}
            async with self.session.post(
                f"{BACKEND_URL}/submit-code",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [400, 422]:  # Bad request or validation error
                    tests_passed += 1
                    print("✅ Invalid code submission handled correctly")
                else:
                    print(f"❌ Invalid code submission: Expected 400/422, got {response.status}")
        except Exception as e:
            print(f"❌ Invalid code submission test failed: {e}")
        
        success = tests_passed == total_tests
        self.log_test("Error handling", success, f"{tests_passed}/{total_tests} error cases handled correctly")
        return success
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Multi-LLM Code Review Backend Tests")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Basic connectivity
            if not await self.test_root_endpoint():
                print("❌ Cannot connect to backend. Stopping tests.")
                return
            
            # Core workflow tests
            await self.test_submit_code()
            await self.test_start_review()
            await self.test_review_status()
            
            # Wait for review to complete (this tests the LLM integration)
            print("⏳ Waiting for LLM review to complete...")
            review_completed = await self.wait_for_review_completion()
            
            if review_completed:
                await self.test_review_result()
                await self.test_human_feedback()
            
            # Additional endpoint tests
            await self.test_get_submissions()
            await self.test_llm_feedbacks()
            
            # Error handling
            await self.test_error_handling()
            
        finally:
            await self.teardown()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! Backend is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the details above.")
            
        return passed == total

async def main():
    """Main test runner"""
    tester = BackendTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())