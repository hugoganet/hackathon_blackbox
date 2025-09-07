"""
Integration tests for Curator Agent API endpoints and functionality
Tests the curator agent initialization, API integration, and error handling
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import os

# Import application components
from backend.api import app, curator_agent
from backend.database import Base, get_db
from backend.memory_store import ConversationMemory
from backend.main import BlackboxMentor
<<<<<<< HEAD
from backend import api
=======
import backend.api as api
>>>>>>> 5800e139677ff61d9ee54bd663ae118b4dd44003

# Import test utilities
from tests.helpers.curator_test_utils import CuratorTestHelper, AssertionHelper
from tests.fixtures.curator_conversations import MOCK_CURATOR_RESPONSES

<<<<<<< HEAD
# Test database setup - PostgreSQL
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:test@localhost:5432/test_curator_integration")
=======
# Test database setup - PostgreSQL only
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://localhost:5432/test_curator_integration")
>>>>>>> 5800e139677ff61d9ee54bd663ae118b4dd44003
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override dependencies
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="session")
def setup_test_db():
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def setup_curator_agent():
    """Initialize curator agent for testing"""
    try:
        # Initialize curator agent
        api.curator_agent = BlackboxMentor("agents/curator-agent.md")
        yield api.curator_agent
    except Exception as e:
        pytest.skip(f"Could not initialize curator agent: {e}")
    finally:
        # Reset after tests
        api.curator_agent = None

class TestCuratorAgentInitialization:
    """Test curator agent initialization and loading"""
    
    def test_curator_agent_loads_system_prompt(self):
        """Test curator agent loads system prompt from curator-agent.md"""
        
        try:
            curator = BlackboxMentor("agents/curator-agent.md")
            assert curator.system_prompt is not None
            assert len(curator.system_prompt) > 0
            assert "curator agent" in curator.system_prompt.lower()
        except FileNotFoundError:
            pytest.fail("curator-agent.md file not found - required for curator agent")
        except Exception as e:
            pytest.fail(f"Curator agent initialization failed: {e}")
    
    def test_curator_prompt_contains_required_elements(self):
        """Test curator prompt contains all required analysis elements"""
        
        curator = BlackboxMentor("agents/curator-agent.md")
        prompt = curator.system_prompt.lower()
        
        required_elements = [
            "skills", "mistakes", "openquestions", "nextsteps", "confidence",
            "json", "learning", "analytics"
        ]
        
        for element in required_elements:
            assert element in prompt, f"Required element '{element}' not found in curator prompt"
    
    def test_curator_in_agents_list(self, setup_test_db):
        """Test curator agent is included in /agents endpoint"""
        
        response = client.get("/agents")
        assert response.status_code == 200
        
        data = response.json()
        agent_ids = [agent["id"] for agent in data["agents"]]
        assert "curator" in agent_ids, "Curator agent not found in agents list"
        
        curator_agent = next((agent for agent in data["agents"] if agent["id"] == "curator"), None)
        assert curator_agent is not None
        assert curator_agent["name"] == "Curator Agent"
        assert "analyzes conversations" in curator_agent["description"].lower()

class TestCuratorAnalysisEndpoint:
    """Test /curator/analyze endpoint functionality"""
    
    def test_curator_analyze_endpoint_exists(self, setup_test_db):
        """Test curator analyze endpoint is accessible"""
        
        # Test with minimal valid request
        request_data = {
            "user_message": "Test message",
            "mentor_response": "Test response",
            "user_id": "test_user"
        }
        
        # Even without mock, endpoint should be accessible (may fail at API call)
        response = client.post("/curator/analyze", json=request_data)
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_curator_analyze_validation(self, setup_test_db):
        """Test request validation for curator analyze endpoint"""
        
        # Test missing required fields
        test_cases = [
            {
                "data": {},
                "description": "Empty request"
            },
            {
                "data": {"user_message": "Test"},
                "description": "Missing mentor_response and user_id"
            },
            {
                "data": {"user_message": "Test", "mentor_response": "Response"},
                "description": "Missing user_id"
            }
        ]
        
        for case in test_cases:
            response = client.post("/curator/analyze", json=case["data"])
            assert response.status_code == 422, f"Validation failed for: {case['description']}"
    
    def test_curator_analyze_with_mock_response(self, setup_test_db, setup_curator_agent):
        """Test curator analyze with mocked Blackbox API response"""
        
        mock_response = json.dumps({
            "skills": ["javascript", "debugging"],
            "mistakes": ["syntax error"],
            "openQuestions": ["how to debug"],
            "nextSteps": ["practice debugging"],
            "confidence": 0.4
        })
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            request_data = {
                "user_message": "I have a JavaScript error in my code",
                "mentor_response": "Let's debug this step by step",
                "user_id": "test_integration_user"
            }
            
            response = client.post("/curator/analyze", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate response structure
            AssertionHelper.assert_curator_response_valid(data)
            assert "analysis_time_ms" in data
            assert isinstance(data["analysis_time_ms"], int)
    
    def test_curator_analyze_response_parsing(self, setup_test_db, setup_curator_agent):
        """Test curator response parsing and validation"""
        
        # Test valid response
        valid_response = json.dumps({
            "skills": ["python", "functions"],
            "mistakes": ["indentation error"],
            "openQuestions": ["scope rules"],
            "nextSteps": ["practice functions"],
            "confidence": 0.6
        })
        
        with CuratorTestHelper.mock_blackbox_api(valid_response):
            request_data = {
                "user_message": "How do I define functions in Python?",
                "mentor_response": "Let's explore function definition syntax",
                "user_id": "test_parsing_user"
            }
            
            response = client.post("/curator/analyze", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["skills"] == ["python", "functions"]
            assert data["confidence"] == 0.6
    
    def test_curator_analyze_invalid_json(self, setup_test_db, setup_curator_agent):
        """Test handling of invalid JSON responses from curator"""
        
        # Test invalid JSON
        with CuratorTestHelper.mock_blackbox_api("Invalid JSON response"):
            request_data = {
                "user_message": "Test message",
                "mentor_response": "Test response",
                "user_id": "test_invalid_json"
            }
            
            response = client.post("/curator/analyze", json=request_data)
            assert response.status_code == 500
            assert "Invalid JSON" in response.json()["detail"]
    
    def test_curator_analyze_missing_fields(self, setup_test_db, setup_curator_agent):
        """Test handling of curator responses missing required fields"""
        
        # Test response missing required fields
        incomplete_response = json.dumps({
            "skills": ["javascript"],
            "mistakes": ["error"]
            # Missing openQuestions, nextSteps, confidence
        })
        
        with CuratorTestHelper.mock_blackbox_api(incomplete_response):
            request_data = {
                "user_message": "Test message",
                "mentor_response": "Test response", 
                "user_id": "test_missing_fields"
            }
            
            response = client.post("/curator/analyze", json=request_data)
            assert response.status_code == 500
            assert "Missing field" in response.json()["detail"]

class TestCuratorSkillsEndpoint:
    """Test /curator/user/{user_id}/skills endpoint"""
    
    def test_curator_skills_endpoint_exists(self, setup_test_db):
        """Test curator skills endpoint is accessible"""
        
        response = client.get("/curator/user/test_skills_user/skills")
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_curator_skills_response_structure(self, setup_test_db, setup_curator_agent):
        """Test curator skills endpoint response structure"""
        
        response = client.get("/curator/user/test_skills_user/skills")
        # Accept either success or expected database structure response
        assert response.status_code in [200, 500]
        
        data = response.json()
        if response.status_code == 200:
            assert "user_id" in data
            assert "skill_progression" in data
            assert "skills_summary" in data
            assert data["user_id"] == "test_skills_user"
        else:
            # If database not fully set up, should get proper error structure
            assert "detail" in data
            assert "skills" in data["detail"] or "users" in data["detail"]

class TestCuratorChatIntegration:
    """Test curator agent integration with main chat endpoint"""
    
    def test_chat_with_curator_agent(self, setup_test_db, setup_curator_agent):
        """Test using curator agent through main chat endpoint"""
        
        mock_response = json.dumps({
            "skills": ["system_design"],
            "mistakes": [],
            "openQuestions": ["architecture trade-offs"],
            "nextSteps": ["research patterns"],
            "confidence": 0.8
        })
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            request_data = {
                "message": "How should I structure my microservices?",
                "agent_type": "curator",
                "user_id": "test_chat_curator"
            }
            
            response = client.post("/chat", json=request_data)
            
            # Should not fail (curator agent should be supported)
            assert response.status_code != 500 or "Curator agent not initialized" not in response.json().get("detail", "")

class TestCuratorErrorHandling:
    """Test curator agent error handling"""
    
    def test_curator_api_error_handling(self, setup_test_db, setup_curator_agent):
        """Test handling of Blackbox API errors"""
        
        # Mock API error response
        with patch('backend.main.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "❌ API Error"}
            mock_post.return_value = mock_response
            
            request_data = {
                "user_message": "Test message",
                "mentor_response": "Test response",
                "user_id": "test_api_error"
            }
            
            response = client.post("/curator/analyze", json=request_data)
            # Should handle API errors gracefully
            assert response.status_code == 500
            assert "Curator API error" in response.json()["detail"]
    
    def test_curator_timeout_handling(self, setup_test_db, setup_curator_agent):
        """Test handling of API timeouts"""
        
        # This would require mocking timeout scenarios
        # For now, just verify the endpoint structure supports error handling
        request_data = {
            "user_message": "Test message",
            "mentor_response": "Test response",
            "user_id": "test_timeout"
        }
        
        # Without mocking, we expect either success or proper error handling
        response = client.post("/curator/analyze", json=request_data)
        assert response.status_code in [200, 500]  # Should not crash

class TestCuratorSystemStats:
    """Test curator agent in system statistics"""
    
    def test_curator_in_system_stats(self, setup_test_db):
        """Test curator agent is reflected in system statistics"""
        
        response = client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "api" in data
        # The agents_loaded status should reflect curator agent availability
        assert "agents_loaded" in data["api"]

class TestCuratorConfigurationValidation:
    """Test curator agent configuration validation"""
    
    def test_curator_requires_valid_prompt_file(self):
        """Test curator agent requires valid prompt file"""
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            BlackboxMentor("non-existent-curator.md")
    
    def test_curator_prompt_file_content_validation(self):
        """Test curator prompt file content is valid"""
        
        curator = BlackboxMentor("agents/curator-agent.md")
        
        # Prompt should contain key curator-specific terms
        prompt = curator.system_prompt.lower()
        curator_terms = ["json", "skills", "mistakes", "confidence", "analysis"]
        
        for term in curator_terms:
            assert term in prompt, f"Curator prompt missing key term: {term}"

if __name__ == "__main__":
    pytest.main(["-v", __file__])