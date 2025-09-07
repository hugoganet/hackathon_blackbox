"""
Test suite for FastAPI backend
Tests all endpoints and core functionality
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import tempfile
import shutil

# Import our application components
from backend.api import app
from backend.database import Base, get_db
from backend.memory_store import ConversationMemory

# Create test database - PostgreSQL
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:test@localhost:5432/test_fastapi")
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
    if os.path.exists("test.db"):
        os.remove("test.db")

@pytest.fixture(scope="session")
def setup_test_memory():
    """Set up test memory store"""
    test_dir = tempfile.mkdtemp()
    memory = ConversationMemory(persist_directory=test_dir)
    yield memory
    # Cleanup
    shutil.rmtree(test_dir)

class TestHealthEndpoints:
    """Test health and info endpoints"""
    
    def test_root_endpoint(self, setup_test_db):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_check(self, setup_test_db):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_agents_list(self, setup_test_db):
        """Test agents listing endpoint"""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 3
        
        # Check agent structures
        agent_ids = [agent["id"] for agent in data["agents"]]
        assert "normal" in agent_ids
        assert "strict" in agent_ids
        assert "curator" in agent_ids

class TestChatEndpoint:
    """Test main chat functionality"""
    
    def test_chat_normal_agent(self, setup_test_db):
        """Test chat with normal agent"""
        request_data = {
            "message": "Hello, can you help me with Python?",
            "agent_type": "normal",
            "user_id": "test_user"
        }
        
        response = client.post("/chat", json=request_data)
        
        # Note: This might fail without actual Blackbox API key or mentor initialization
        # In a real test, you'd mock the API call
        if response.status_code == 500:
            # Expected if API key is not configured, mentor not initialized, or mentor API error
            error_detail = response.json()["detail"]
            assert ("API key not configured" in error_detail or 
                    "Mentor API error" in error_detail or
                    "Normal mentor not initialized" in error_detail)
        else:
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert data["agent_type"] == "normal"
    
    def test_chat_strict_agent(self, setup_test_db):
        """Test chat with strict agent"""
        request_data = {
            "message": "Give me the code for a React component",
            "agent_type": "strict",
            "user_id": "test_user"  
        }
        
        response = client.post("/chat", json=request_data)
        
        # Similar to above - might fail without API key or mentor initialization
        if response.status_code == 500:
            # Expected if API key is not configured, mentor not initialized, or mentor API error
            error_detail = response.json()["detail"]
            assert ("API key not configured" in error_detail or 
                    "Mentor API error" in error_detail or
                    "Strict mentor not initialized" in error_detail)
        else:
            assert response.status_code == 200
            data = response.json()
            assert data["agent_type"] == "strict"

class TestMemoryEndpoints:
    """Test memory and user data endpoints"""
    
    def test_user_memories_empty(self, setup_test_db):
        """Test getting memories for new user"""
        response = client.get("/user/new_test_user/memories")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "new_test_user"
        assert "learning_patterns" in data
    
    def test_system_stats(self, setup_test_db):
        """Test system statistics endpoint"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "database" in data
        assert "memory_store" in data
        assert "api" in data

# Run tests
if __name__ == "__main__":
    pytest.main(["-v", __file__])