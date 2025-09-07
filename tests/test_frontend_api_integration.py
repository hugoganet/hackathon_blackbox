"""
Frontend API Integration Tests
Tests to validate that the frontend can properly consume all backend API endpoints
Ensures API contract compatibility and CORS configuration
"""

import pytest
import requests
from typing import Dict, Any
import json
import time


class TestFrontendAPIIntegration:
    """Test frontend API consumption from backend perspective"""
    
    # Test configuration
    API_BASE_URL = "http://localhost:8000"
    FRONTEND_ORIGIN = "http://localhost:3000"
    TEST_USER_ID = "frontend-integration-test-user"
    
    @pytest.fixture(autouse=True)
    def setup_headers(self):
        """Setup common headers for frontend requests"""
        self.headers = {
            "Content-Type": "application/json",
            "Origin": self.FRONTEND_ORIGIN,
            "User-Agent": "Frontend-Integration-Test/1.0"
        }
    
    def test_cors_configuration(self):
        """Test that CORS is properly configured for frontend origin"""
        response = requests.options(
            f"{self.API_BASE_URL}/chat",
            headers={
                "Origin": self.FRONTEND_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == self.FRONTEND_ORIGIN
        assert "POST" in response.headers.get("Access-Control-Allow-Methods", "")
        assert "Content-Type" in response.headers.get("Access-Control-Allow-Headers", "")
    
    def test_core_system_endpoints(self):
        """Test core system endpoints that frontend relies on"""
        
        # Test health check
        response = requests.get(f"{self.API_BASE_URL}/health", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data
        
        # Test root endpoint
        response = requests.get(f"{self.API_BASE_URL}/", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Test agents endpoint
        response = requests.get(f"{self.API_BASE_URL}/agents", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) > 0
        assert all("id" in agent and "name" in agent for agent in data["agents"])
        
        # Test system stats
        response = requests.get(f"{self.API_BASE_URL}/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "memory_store" in data
        assert "api" in data
    
    def test_chat_endpoint_frontend_compatibility(self):
        """Test chat endpoint with frontend-compatible request/response formats"""
        
        # Test basic chat request
        chat_request = {
            "message": "Hello, this is a test from frontend integration",
            "agent_type": "normal",
            "user_id": self.TEST_USER_ID
        }
        
        response = requests.post(
            f"{self.API_BASE_URL}/chat",
            headers=self.headers,
            json=chat_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure matches frontend expectations
        assert "response" in data
        assert "agent_type" in data
        assert "session_id" in data
        assert isinstance(data["response"], str)
        assert data["agent_type"] in ["normal", "strict", "pydantic_strict", "curator"]
        
        # Test all agent types that frontend supports
        agent_types = ["normal", "strict", "pydantic_strict", "curator"]
        for agent_type in agent_types:
            request_data = {
                "message": f"Test message for {agent_type} agent",
                "agent_type": agent_type,
                "user_id": self.TEST_USER_ID
            }
            
            response = requests.post(
                f"{self.API_BASE_URL}/chat",
                headers=self.headers,
                json=request_data
            )
            
            # Should not fail for any supported agent type
            assert response.status_code == 200
            data = response.json()
            assert data["agent_type"] == agent_type
    
    def test_user_memory_endpoints(self):
        """Test user memory endpoints for frontend consumption"""
        
        # Test getting user memories
        response = requests.get(
            f"{self.API_BASE_URL}/user/{self.TEST_USER_ID}/memories",
            headers=self.headers,
            params={"limit": 10}
        )
        
        # Should return data even if user doesn't exist yet
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "memory_store_status" in data
    
    def test_curator_endpoints_frontend_integration(self):
        """Test curator analysis endpoints for frontend integration"""
        
        # Test conversation analysis
        analysis_request = {
            "user_message": "How do I use React hooks effectively?",
            "mentor_response": "What specific hooks are you interested in learning about?",
            "user_id": self.TEST_USER_ID,
            "session_id": "integration-test-session"
        }
        
        response = requests.post(
            f"{self.API_BASE_URL}/curator/analyze",
            headers=self.headers,
            json=analysis_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure for frontend
        assert "skills" in data
        assert "mistakes" in data
        assert "openQuestions" in data
        assert "nextSteps" in data
        assert "confidence" in data
        assert "analysis_time_ms" in data
        
        assert isinstance(data["skills"], list)
        assert isinstance(data["mistakes"], list)
        assert isinstance(data["openQuestions"], list)
        assert isinstance(data["nextSteps"], list)
        assert isinstance(data["confidence"], (int, float))
        assert 0 <= data["confidence"] <= 1
        
        # Test getting user skills
        response = requests.get(
            f"{self.API_BASE_URL}/curator/user/{self.TEST_USER_ID}/skills",
            headers=self.headers,
            params={"limit": 20}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "total_skills_tracked" in data
        assert "skill_progression" in data
        assert "skills_summary" in data
        assert "domains_summary" in data
    
    def test_flashcard_endpoints_full_workflow(self):
        """Test complete flashcard workflow that frontend would use"""
        
        # 1. Create a flashcard
        create_request = {
            "question": "What is the useState hook in React?",
            "answer": "A React hook that allows you to add state to functional components",
            "difficulty": 2,
            "card_type": "concept",
            "confidence_score": 0.7
        }
        
        response = requests.post(
            f"{self.API_BASE_URL}/flashcards/create",
            headers=self.headers,
            json=create_request
        )
        
        assert response.status_code == 200
        flashcard_data = response.json()
        
        # Validate response structure
        required_fields = ["id", "question", "answer", "difficulty", "card_type", 
                         "next_review_date", "review_count", "created_at"]
        for field in required_fields:
            assert field in flashcard_data
        
        flashcard_id = flashcard_data["id"]
        
        # 2. Get due flashcards for review
        response = requests.get(
            f"{self.API_BASE_URL}/flashcards/review/{self.TEST_USER_ID}",
            headers=self.headers,
            params={"limit": 20}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "flashcards" in data
        assert "total_due" in data
        assert isinstance(data["flashcards"], list)
        
        # 3. Submit a review
        review_request = {
            "flashcard_id": flashcard_id,
            "user_id": self.TEST_USER_ID,
            "success_score": 4,  # Good performance
            "response_time": 15  # 15 seconds
        }
        
        response = requests.post(
            f"{self.API_BASE_URL}/flashcards/review",
            headers=self.headers,
            json=review_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "next_review_date" in data
        assert "interval_days" in data
        assert "card_state" in data
        assert data["card_state"] in ["NEW", "LEARNING", "REVIEW", "MATURE"]
        
        # 4. Get flashcard statistics
        response = requests.get(
            f"{self.API_BASE_URL}/flashcards/stats/{self.TEST_USER_ID}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        stats_fields = ["total_flashcards", "due_flashcards", "recent_reviews", 
                       "average_score", "success_rate", "streak_days"]
        for field in stats_fields:
            assert field in data
        
        # 5. Get flashcard schedule
        response = requests.get(
            f"{self.API_BASE_URL}/flashcards/schedule/{self.TEST_USER_ID}",
            headers=self.headers,
            params={"days": 7}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "schedule" in data
        assert "total_upcoming" in data
        
        # 6. Cleanup - delete the test flashcard
        response = requests.delete(
            f"{self.API_BASE_URL}/flashcards/{flashcard_id}",
            headers=self.headers,
            params={"user_id": self.TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_batch_flashcard_operations(self):
        """Test batch operations for flashcards"""
        
        batch_request = {
            "flashcards": [
                {
                    "question": "What is JSX?",
                    "answer": "A syntax extension for JavaScript used in React",
                    "difficulty": 1,
                    "card_type": "definition"
                },
                {
                    "question": "What is the virtual DOM?",
                    "answer": "A programming concept where a virtual representation of UI is kept in memory",
                    "difficulty": 3,
                    "card_type": "concept"
                }
            ],
            "user_id": self.TEST_USER_ID
        }
        
        response = requests.post(
            f"{self.API_BASE_URL}/flashcards/batch",
            headers=self.headers,
            json=batch_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Cleanup batch created flashcards
        for flashcard in data:
            requests.delete(
                f"{self.API_BASE_URL}/flashcards/{flashcard['id']}",
                headers=self.headers,
                params={"user_id": self.TEST_USER_ID}
            )
    
    def test_error_handling_for_frontend(self):
        """Test error responses are frontend-friendly"""
        
        # Test 404 error
        response = requests.get(
            f"{self.API_BASE_URL}/nonexistent-endpoint",
            headers=self.headers
        )
        assert response.status_code == 404
        
        # Test invalid chat request
        response = requests.post(
            f"{self.API_BASE_URL}/chat",
            headers=self.headers,
            json={"invalid": "request"}  # Missing required fields
        )
        assert response.status_code in [400, 422]  # Should return validation error
        
        # Test invalid flashcard deletion
        response = requests.delete(
            f"{self.API_BASE_URL}/flashcards/nonexistent-id",
            headers=self.headers,
            params={"user_id": self.TEST_USER_ID}
        )
        assert response.status_code == 404
    
    def test_response_time_performance(self):
        """Test API response times are acceptable for frontend"""
        
        endpoints_to_test = [
            ("GET", "/health", {}),
            ("GET", "/agents", {}),
            ("GET", f"/user/{self.TEST_USER_ID}/memories", {"limit": 5}),
            ("GET", f"/flashcards/stats/{self.TEST_USER_ID}", {}),
        ]
        
        for method, endpoint, params in endpoints_to_test:
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(
                    f"{self.API_BASE_URL}{endpoint}",
                    headers=self.headers,
                    params=params
                )
            elif method == "POST":
                response = requests.post(
                    f"{self.API_BASE_URL}{endpoint}",
                    headers=self.headers,
                    json=params
                )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Assert response is successful and reasonably fast (< 5 seconds)
            assert response.status_code == 200
            assert response_time < 5.0, f"Endpoint {endpoint} took {response_time:.2f}s"
    
    def test_json_serialization_compatibility(self):
        """Test that all API responses are properly JSON serializable for frontend"""
        
        # Test various endpoints and ensure they return valid JSON
        endpoints = [
            "/health",
            "/agents", 
            f"/user/{self.TEST_USER_ID}/memories",
            "/stats"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.API_BASE_URL}{endpoint}", headers=self.headers)
            assert response.status_code == 200
            
            # Should be valid JSON
            data = response.json()
            
            # Should be re-serializable (no datetime objects, etc.)
            json_str = json.dumps(data)
            deserialized = json.loads(json_str)
            assert deserialized == data
    
    def test_content_type_headers(self):
        """Test that content-type headers are correctly set for frontend consumption"""
        
        response = requests.get(f"{self.API_BASE_URL}/health", headers=self.headers)
        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", "")
        
        # Test POST response content type
        response = requests.post(
            f"{self.API_BASE_URL}/chat",
            headers=self.headers,
            json={
                "message": "Test content type",
                "agent_type": "normal",
                "user_id": self.TEST_USER_ID
            }
        )
        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", "")


if __name__ == "__main__":
    # Can be run directly for quick testing
    test_instance = TestFrontendAPIIntegration()
    test_instance.setup_headers()
    
    print("Running basic connectivity test...")
    try:
        test_instance.test_core_system_endpoints()
        print("✅ Core endpoints working")
        
        test_instance.test_chat_endpoint_frontend_compatibility()
        print("✅ Chat endpoint compatible")
        
        test_instance.test_cors_configuration()
        print("✅ CORS properly configured")
        
        print("🎉 Frontend API integration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1)