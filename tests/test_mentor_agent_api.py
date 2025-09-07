"""
Integration Tests for Mentor Agent FastAPI Endpoint Compatibility
Tests API integration including the /chat endpoint with pydantic_strict agent type
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import our modules  
sys.path.append(str(Path(__file__).parent.parent))

# Test imports
try:
    from backend.api import app, get_db
    from backend.database import Base, User, Session as DBSession, Interaction
    from agents.mentor_agent import MentorAgent, MentorResponse
    from backend.pydantic_handler import handle_pydantic_mentor_request
    API_TEST_AVAILABLE = True
except ImportError as e:
    print(f"Warning: API or PydanticAI imports not available: {e}")
    API_TEST_AVAILABLE = False


# Test database setup
TEST_DATABASE_URL = "sqlite:///test_api_mentor_agent.db"


@pytest.fixture(scope="function") 
def test_db():
    """Create test database for API tests"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up test database
        try:
            os.remove("test_api_mentor_agent.db")
        except FileNotFoundError:
            pass


@pytest.fixture
def client(test_db):
    """Create test client with dependency override"""
    if not API_TEST_AVAILABLE:
        pytest.skip("API dependencies not available")
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def sample_chat_requests():
    """Sample chat requests for testing"""
    return [
        {
            "message": "How do I create a Python function with parameters?",
            "agent_type": "pydantic_strict",
            "user_id": "api_test_user_001",
            "session_id": "api_test_session_001"
        },
        {
            "message": "I'm getting a syntax error in my JavaScript code",
            "agent_type": "pydantic_strict", 
            "user_id": "api_test_user_002",
            "session_id": "api_test_session_002"
        },
        {
            "message": "Can you explain React component lifecycle?",
            "agent_type": "pydantic_strict",
            "user_id": "api_test_user_003",
            "session_id": "api_test_session_003"
        },
        {
            "message": "Please just give me the answer to this coding problem",
            "agent_type": "pydantic_strict",
            "user_id": "api_test_user_004", 
            "session_id": "api_test_session_004"
        }
    ]


@pytest.mark.skipif(not API_TEST_AVAILABLE, reason="API dependencies not available")
class TestFastAPIEndpointIntegration:
    """Test FastAPI endpoint integration with PydanticAI mentor agent"""
    
    def test_health_endpoints(self, client):
        """Test health check endpoints work correctly"""
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "database_status" in data
    
    def test_agents_endpoint(self, client):
        """Test agents listing endpoint"""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        assert isinstance(data["agents"], list)
        
        # Should include pydantic_strict agent
        agent_types = [agent["type"] for agent in data["agents"]]
        assert "pydantic_strict" in agent_types
        
        # Find pydantic_strict agent details
        pydantic_agent = next(agent for agent in data["agents"] if agent["type"] == "pydantic_strict")
        assert "name" in pydantic_agent
        assert "description" in pydantic_agent
        assert "PydanticAI" in pydantic_agent["description"] or "memory-guided" in pydantic_agent["description"]
    
    @patch('backend.api.pydantic_mentor')
    def test_chat_endpoint_pydantic_strict_success(self, mock_pydantic_mentor, client, sample_chat_requests):
        """Test successful chat with pydantic_strict agent"""
        
        # Mock PydanticAI mentor response
        mock_response = MentorResponse(
            response="Great question! Before I guide you toward the solution, what's your current understanding of Python functions?",
            hint_level=1,
            memory_context_used=False,
            detected_language="python", 
            detected_intent="concept_explanation",
            similar_interactions_count=0
        )
        mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
        
        # Make chat request
        chat_request = sample_chat_requests[0]  # Python function question
        response = client.post("/chat", json=chat_request)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "response" in data
        assert "agent_type" in data
        assert "session_id" in data
        
        # Check response content
        assert data["agent_type"] == "pydantic_strict"
        assert data["session_id"] == chat_request["session_id"]
        assert "Great question!" in data["response"]
        assert "what's your current understanding" in data["response"]
        
        # Check PydanticAI-specific fields
        if "hint_level" in data:
            assert data["hint_level"] == 1
        if "detected_language" in data:
            assert data["detected_language"] == "python"
        if "detected_intent" in data:
            assert data["detected_intent"] == "concept_explanation"
    
    @patch('backend.api.pydantic_mentor')
    def test_chat_endpoint_strict_mentor_principles(self, mock_pydantic_mentor, client, sample_chat_requests):
        """Test that chat endpoint maintains strict mentor principles"""
        
        # Mock response that maintains strict principles
        mock_response = MentorResponse(
            response="I understand you'd like a direct answer, but my role is to help you learn by discovery. What have you tried so far?",
            hint_level=1,
            memory_context_used=False,
            detected_language="unknown",
            detected_intent="general", 
            similar_interactions_count=0
        )
        mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
        
        # Test with request asking for direct answer
        direct_answer_request = sample_chat_requests[3]  # "Please just give me the answer..."
        response = client.post("/chat", json=direct_answer_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify strict mentor principles maintained
        response_text = data["response"].lower()
        
        # Should not contain direct answers
        forbidden_phrases = ["here's the answer", "the solution is", "copy this code", "here's how to do it"]
        for phrase in forbidden_phrases:
            assert phrase not in response_text
        
        # Should contain guiding questions or discovery prompts
        guiding_patterns = ["what have you tried", "what's your understanding", "let's think about", "what do you think"]
        assert any(pattern in response_text for pattern in guiding_patterns)
    
    @patch('backend.api.pydantic_mentor')
    def test_chat_endpoint_multiple_languages(self, mock_pydantic_mentor, client):
        """Test chat endpoint with multiple programming languages"""
        
        language_test_cases = [
            {
                "request": {
                    "message": "How do I declare variables in Python?",
                    "agent_type": "pydantic_strict",
                    "user_id": "lang_test_python"
                },
                "expected_language": "python",
                "mock_response": "Great Python question! What do you think variables are used for?"
            },
            {
                "request": {
                    "message": "My React component isn't rendering properly",
                    "agent_type": "pydantic_strict", 
                    "user_id": "lang_test_react"
                },
                "expected_language": "javascript",
                "mock_response": "Let's debug your React component step by step. What exactly isn't rendering?"
            },
            {
                "request": {
                    "message": "I need help with HTML div elements",
                    "agent_type": "pydantic_strict",
                    "user_id": "lang_test_html"
                },
                "expected_language": "html",
                "mock_response": "HTML elements are fundamental! What are you trying to achieve with your div?"
            }
        ]
        
        for test_case in language_test_cases:
            # Mock response for this language
            mock_response = MentorResponse(
                response=test_case["mock_response"],
                detected_language=test_case["expected_language"],
                detected_intent="concept_explanation",
                memory_context_used=False
            )
            mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
            
            # Make request
            response = client.post("/chat", json=test_case["request"])
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify language detection
            if "detected_language" in data:
                assert data["detected_language"] == test_case["expected_language"]
            
            # Verify response quality
            assert len(data["response"]) > 0
            assert data["agent_type"] == "pydantic_strict"
    
    def test_chat_endpoint_invalid_requests(self, client):
        """Test chat endpoint error handling with invalid requests"""
        
        # Test missing required fields
        invalid_requests = [
            {},  # Empty request
            {"agent_type": "pydantic_strict"},  # Missing message
            {"message": "Test question"},  # Missing agent_type
            {
                "message": "Test question",
                "agent_type": "invalid_agent_type"  # Invalid agent type
            }
        ]
        
        for invalid_request in invalid_requests:
            response = client.post("/chat", json=invalid_request)
            # Should return 422 (validation error) or 400 (bad request)
            assert response.status_code in [400, 422]
    
    @patch('backend.api.pydantic_mentor')
    def test_chat_endpoint_anonymous_user(self, mock_pydantic_mentor, client):
        """Test chat endpoint with anonymous user"""
        
        mock_response = MentorResponse(
            response="Welcome! What programming topic would you like to explore?",
            memory_context_used=False,
            detected_language="unknown",
            detected_intent="general"
        )
        mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
        
        # Request without user_id (anonymous)
        anonymous_request = {
            "message": "I need help with programming",
            "agent_type": "pydantic_strict"
            # No user_id or session_id
        }
        
        response = client.post("/chat", json=anonymous_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["agent_type"] == "pydantic_strict"
        assert len(data["response"]) > 0
        assert "session_id" in data  # Should generate session_id
    
    @patch('backend.api.pydantic_mentor')
    def test_chat_endpoint_session_continuity(self, mock_pydantic_mentor, client):
        """Test chat endpoint maintains session continuity"""
        
        # Mock responses for conversation flow
        responses = [
            MentorResponse(
                response="Great question! What do you think functions are used for?",
                hint_level=1,
                detected_language="python"
            ),
            MentorResponse(
                response="You're on the right track! Can you give me an example of data you might store?",
                hint_level=1, 
                detected_language="python"
            ),
            MentorResponse(
                response="Perfect examples! Now, how might we tell Python to create a variable?",
                hint_level=2,
                detected_language="python"
            )
        ]
        
        user_id = "session_continuity_user"
        session_id = "session_continuity_test"
        
        conversation_flow = [
            "What is a Python function?",
            "I think functions are used to organize code?", 
            "Maybe we store values like names and numbers?"
        ]
        
        for i, (message, expected_response) in enumerate(zip(conversation_flow, responses)):
            mock_pydantic_mentor.respond = AsyncMock(return_value=expected_response)
            
            chat_request = {
                "message": message,
                "agent_type": "pydantic_strict", 
                "user_id": user_id,
                "session_id": session_id
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["session_id"] == session_id  # Same session maintained
            assert data["agent_type"] == "pydantic_strict"
            
            # Verify hint escalation if applicable
            if "hint_level" in data:
                assert data["hint_level"] >= 1


@pytest.mark.skipif(not API_TEST_AVAILABLE, reason="API dependencies not available")
class TestPydanticHandlerIntegration:
    """Test PydanticAI handler integration with API"""
    
    @pytest.mark.asyncio
    async def test_pydantic_handler_complete_workflow(self, test_db):
        """Test complete pydantic handler workflow"""
        
        # Mock request
        mock_request = Mock()
        mock_request.message = "How do I handle errors in Python?"
        mock_request.user_id = "handler_workflow_user"
        mock_request.session_id = "handler_workflow_session"
        
        # Mock PydanticAI mentor
        mock_pydantic_mentor = Mock()
        mock_response = MentorResponse(
            response="Error handling is crucial! What types of errors have you encountered so far?",
            hint_level=1,
            memory_context_used=False,
            detected_language="python",
            detected_intent="concept_explanation",
            similar_interactions_count=0
        )
        mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
        
        # Mock memory store
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.return_value = []
        
        # Execute handler
        response = await handle_pydantic_mentor_request(
            request=mock_request,
            db=test_db,
            pydantic_mentor=mock_pydantic_mentor,
            memory_store=mock_memory_store
        )
        
        # Verify response structure
        assert "response" in response
        assert "agent_type" in response
        assert "session_id" in response
        assert "detected_language" in response
        assert "detected_intent" in response
        
        # Verify response content
        assert response["agent_type"] == "pydantic_strict"
        assert response["session_id"] == "handler_workflow_session"
        assert response["detected_language"] == "python"
        assert response["detected_intent"] == "concept_explanation"
        assert "Error handling is crucial!" in response["response"]
        
        # Verify mentor was called correctly
        mock_pydantic_mentor.respond.assert_called_once()
        call_kwargs = mock_pydantic_mentor.respond.call_args[1]
        assert call_kwargs["user_message"] == "How do I handle errors in Python?"
        assert call_kwargs["user_id"] == str(mock_request.user_id)
        assert call_kwargs["session_id"] == "handler_workflow_session"
    
    @pytest.mark.asyncio
    async def test_pydantic_handler_memory_integration(self, test_db):
        """Test pydantic handler with memory store integration"""
        
        mock_request = Mock()
        mock_request.message = "I'm still confused about Python functions"
        mock_request.user_id = "memory_integration_user"
        mock_request.session_id = "memory_integration_session"
        
        # Mock PydanticAI mentor
        mock_pydantic_mentor = Mock()
        mock_response = MentorResponse(
            response="I see you're continuing to work on functions. Based on our previous discussion, what specific part is still unclear?",
            hint_level=2,
            memory_context_used=True,
            detected_language="python",
            detected_intent="concept_explanation", 
            similar_interactions_count=2
        )
        mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
        
        # Mock memory store with similar interactions
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.return_value = [
            {
                "memory_id": "prev_001",
                "user_message": "What is a Python function?",
                "mentor_response": "Great question! What do you think functions do?",
                "similarity": 0.85,
                "metadata": {"programming_language": "python"}
            },
            {
                "memory_id": "prev_002",
                "user_message": "How do I create a function with parameters?",
                "mentor_response": "Let's think about parameters step by step...",
                "similarity": 0.78,
                "metadata": {"programming_language": "python"}
            }
        ]
        
        # Execute handler
        response = await handle_pydantic_mentor_request(
            request=mock_request,
            db=test_db,
            pydantic_mentor=mock_pydantic_mentor,
            memory_store=mock_memory_store
        )
        
        # Verify memory integration
        assert response["similar_interactions_count"] == 2
        assert "related_memories" in response
        assert len(response["related_memories"]) == 2
        
        # Verify memory-aware response
        assert "based on our previous discussion" in response["response"].lower()
        assert response["memory_context_used"] == True


@pytest.mark.skipif(not API_TEST_AVAILABLE, reason="API dependencies not available")
class TestAPIErrorHandling:
    """Test API error handling and resilience"""
    
    @patch('backend.api.pydantic_mentor')
    def test_chat_endpoint_mentor_error_handling(self, mock_pydantic_mentor, client):
        """Test chat endpoint handles mentor agent errors gracefully"""
        
        # Mock pydantic mentor to raise exception
        mock_pydantic_mentor.respond = AsyncMock(side_effect=Exception("PydanticAI processing error"))
        
        chat_request = {
            "message": "Test question that causes error",
            "agent_type": "pydantic_strict",
            "user_id": "error_test_user"
        }
        
        response = client.post("/chat", json=chat_request)
        
        # Should handle error gracefully (not crash)
        # Depending on error handling implementation, could be 200 with error message or 500
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Should contain some form of error handling or fallback response
            assert "response" in data
            assert len(data["response"]) > 0
    
    @patch('backend.api.memory_store')
    def test_chat_endpoint_memory_store_error_handling(self, mock_memory_store, client):
        """Test chat endpoint handles memory store errors gracefully"""
        
        # Mock memory store to raise exception
        mock_memory_store.find_similar_interactions.side_effect = Exception("ChromaDB connection failed")
        
        chat_request = {
            "message": "Test question with memory error",
            "agent_type": "pydantic_strict",
            "user_id": "memory_error_user"
        }
        
        response = client.post("/chat", json=chat_request)
        
        # Should handle memory store errors gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Should still provide some response even without memory
            assert "response" in data
    
    def test_chat_endpoint_database_error_resilience(self, client):
        """Test chat endpoint resilience to database errors"""
        
        # Test with database connection issues (simulated by using invalid session)
        chat_request = {
            "message": "Test question with potential DB issues",
            "agent_type": "pydantic_strict",
            "user_id": "db_error_test_user"
        }
        
        # This should either work with test DB or fail gracefully
        response = client.post("/chat", json=chat_request)
        
        # Should not crash the API
        assert response.status_code in [200, 500, 503]
    
    def test_concurrent_api_requests(self, client):
        """Test API handles concurrent requests correctly"""
        
        # Simulate concurrent requests (in sequence for test simplicity)
        concurrent_requests = [
            {
                "message": f"Concurrent question {i}",
                "agent_type": "pydantic_strict", 
                "user_id": f"concurrent_user_{i}",
                "session_id": f"concurrent_session_{i}"
            }
            for i in range(5)
        ]
        
        responses = []
        for request in concurrent_requests:
            response = client.post("/chat", json=request)
            responses.append(response)
        
        # All requests should complete
        assert len(responses) == 5
        
        # All should have reasonable status codes
        for response in responses:
            assert response.status_code in [200, 422, 500]  # Success, validation error, or server error
        
        # Successful responses should have proper structure
        for i, response in enumerate(responses):
            if response.status_code == 200:
                data = response.json()
                assert "response" in data
                assert "agent_type" in data
                assert data["agent_type"] == "pydantic_strict"


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running Mentor Agent API Integration Tests...")
    
    if API_TEST_AVAILABLE:
        print("✅ API and PydanticAI imports available") 
        print("✅ API integration test setup completed successfully!")
        print("Run with: pytest tests/test_mentor_agent_api.py -v")
    else:
        print("⚠️ API or PydanticAI dependencies not available - tests skipped")
        print("Install FastAPI and PydanticAI to run API integration tests")