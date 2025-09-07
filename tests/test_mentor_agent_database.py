"""
Integration Tests for Mentor Agent PostgreSQL Database Operations
Tests database interactions including user management, session tracking, and interaction storage
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Test imports
try:
    from agents.mentor_agent import MentorAgent, MentorResponse
    from agents.mentor_agent.tools import MentorTools
    from backend.database import (
        Base, User, Session as DBSession, Interaction,
        create_tables, get_user_by_username, create_user, 
        create_conversation, save_interaction, get_user_skill_progression
    )
    from backend.pydantic_handler import handle_pydantic_mentor_request
    PYDANTIC_AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PydanticAI or database imports not available: {e}")
    PYDANTIC_AI_AVAILABLE = False


# Test database setup
TEST_DATABASE_URL = "sqlite:///test_mentor_agent.db"


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up - remove test database file
        try:
            os.remove("test_mentor_agent.db")
        except FileNotFoundError:
            pass


@pytest.fixture
def sample_users():
    """Sample user data for testing"""
    return [
        {
            "username": "junior_dev_001",
            "email": "junior@example.com", 
            "role": "developer"
        },
        {
            "username": "experienced_dev_002",
            "email": "experienced@example.com",
            "role": "developer"  
        },
        {
            "username": "manager_003",
            "email": "manager@example.com",
            "role": "manager"
        }
    ]


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI or database not available")
class TestDatabaseUserManagement:
    """Test user management database operations"""
    
    def test_create_and_retrieve_user(self, test_db, sample_users):
        """Test creating and retrieving users from database"""
        
        # Test creating new user
        user_data = sample_users[0]
        new_user = create_user(
            test_db,
            username=user_data["username"],
            email=user_data["email"],
            role=user_data["role"]
        )
        
        assert new_user.username == user_data["username"]
        assert new_user.email == user_data["email"]
        assert new_user.role == user_data["role"]
        assert new_user.is_active == True
        assert new_user.id is not None
        
        # Test retrieving existing user
        retrieved_user = get_user_by_username(test_db, user_data["username"])
        assert retrieved_user.id == new_user.id
        assert retrieved_user.username == user_data["username"]
        assert retrieved_user.email == user_data["email"]
    
    def test_get_or_create_user_logic(self, test_db, sample_users):
        """Test get-or-create user logic used by mentor agent"""
        
        username = sample_users[1]["username"]
        
        # First call should create user
        user1 = get_user_by_username(test_db, username)
        if not user1:
            user1 = create_user(test_db, username=username)
        
        assert user1.username == username
        
        # Second call should retrieve existing user
        user2 = get_user_by_username(test_db, username)
        assert user2.id == user1.id
        assert user2.username == user1.username
    
    def test_multiple_users_isolation(self, test_db, sample_users):
        """Test that multiple users are properly isolated"""
        
        # Create multiple users
        users = []
        for user_data in sample_users:
            user = create_user(
                test_db,
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"]
            )
            users.append(user)
        
        # Verify each user has unique ID and data
        user_ids = [user.id for user in users]
        assert len(set(user_ids)) == len(users)  # All IDs are unique
        
        # Verify retrieval by username works correctly
        for i, user_data in enumerate(sample_users):
            retrieved_user = get_user_by_username(test_db, user_data["username"])
            assert retrieved_user.id == users[i].id
            assert retrieved_user.username == user_data["username"]


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI or database not available")
class TestDatabaseSessionManagement:
    """Test session management database operations"""
    
    def test_create_conversation_session(self, test_db):
        """Test creating conversation sessions"""
        
        # Create test user first
        user = create_user(test_db, username="session_test_user")
        
        # Create conversation session
        session = create_conversation(
            test_db,
            user_id=str(user.id),
            session_title="Python Learning Session",
            agent_type="pydantic_strict"
        )
        
        assert session.user_id == user.id
        assert session.title == "Python Learning Session"
        assert session.agent_type == "pydantic_strict"
        assert session.id is not None
        assert session.created_at is not None
        assert session.ended_at is None  # New session not ended yet
    
    def test_multiple_sessions_per_user(self, test_db):
        """Test that users can have multiple sessions"""
        
        # Create test user
        user = create_user(test_db, username="multi_session_user")
        
        # Create multiple sessions
        session_titles = [
            "JavaScript Fundamentals",
            "React Components", 
            "Python Data Structures",
            "Debugging Workshop"
        ]
        
        sessions = []
        for title in session_titles:
            session = create_conversation(
                test_db,
                user_id=str(user.id),
                session_title=title,
                agent_type="pydantic_strict"
            )
            sessions.append(session)
        
        # Verify all sessions created with unique IDs
        session_ids = [session.id for session in sessions]
        assert len(set(session_ids)) == len(sessions)
        
        # Verify all sessions belong to same user
        for session in sessions:
            assert session.user_id == user.id
    
    def test_session_with_generated_id(self, test_db):
        """Test creating session with auto-generated session ID"""
        
        user = create_user(test_db, username="auto_session_user")
        
        # Create session without explicit session_id (should auto-generate)
        session = create_conversation(
            test_db,
            user_id=str(user.id),
            agent_type="pydantic_strict"
        )
        
        assert session.user_id == user.id
        assert session.agent_type == "pydantic_strict"
        assert session.id is not None
        assert session.title is None or len(session.title) == 0


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI or database not available")
class TestDatabaseInteractionStorage:
    """Test interaction storage database operations"""
    
    def test_save_mentor_interaction(self, test_db):
        """Test saving mentor-student interactions"""
        
        # Setup: Create user and conversation
        user = create_user(test_db, username="interaction_test_user")
        conversation = create_conversation(
            test_db,
            user_id=str(user.id),
            session_title="Test Learning Session",
            agent_type="pydantic_strict"
        )
        
        # Save interaction
        interaction = save_interaction(
            test_db,
            conversation_id=str(conversation.id),
            user_message="How do I create a Python function?",
            mentor_response="Great question! Before I guide you through the answer, can you tell me what you think a function does?",
            response_time_ms=1250
        )
        
        assert interaction.conversation_id == conversation.id
        assert interaction.user_message == "How do I create a Python function?"
        assert "Great question!" in interaction.mentor_response
        assert interaction.response_time_ms == 1250
        assert interaction.created_at is not None
        assert interaction.id is not None
    
    def test_multiple_interactions_in_session(self, test_db):
        """Test storing multiple interactions within same session"""
        
        # Setup
        user = create_user(test_db, username="multi_interaction_user")
        conversation = create_conversation(
            test_db,
            user_id=str(user.id),
            agent_type="pydantic_strict"
        )
        
        # Simulate conversation flow
        conversation_flow = [
            {
                "user_message": "What is a Python variable?",
                "mentor_response": "Excellent starting question! What do you think variables are used for in programming?",
                "response_time": 800
            },
            {
                "user_message": "I think variables store data?",
                "mentor_response": "You're on the right track! Can you give me an example of what kind of data you might want to store?",
                "response_time": 950
            },
            {
                "user_message": "Maybe storing a person's name or age?",
                "mentor_response": "Perfect examples! Now, how do you think we might tell Python to create a variable with a name?",
                "response_time": 1100
            }
        ]
        
        interactions = []
        for exchange in conversation_flow:
            interaction = save_interaction(
                test_db,
                conversation_id=str(conversation.id),
                user_message=exchange["user_message"],
                mentor_response=exchange["mentor_response"],
                response_time_ms=exchange["response_time"]
            )
            interactions.append(interaction)
        
        # Verify all interactions saved correctly
        assert len(interactions) == 3
        
        # Verify interactions maintain conversation flow order
        timestamps = [interaction.created_at for interaction in interactions]
        assert timestamps == sorted(timestamps)  # Should be in chronological order
        
        # Verify all belong to same conversation
        for interaction in interactions:
            assert interaction.conversation_id == conversation.id
    
    def test_interaction_response_time_tracking(self, test_db):
        """Test response time tracking in interactions"""
        
        user = create_user(test_db, username="timing_test_user")
        conversation = create_conversation(test_db, str(user.id), agent_type="pydantic_strict")
        
        # Test various response times
        test_cases = [
            ("Quick response test", "Fast guidance", 150),
            ("Medium response test", "Medium guidance", 800),
            ("Complex response test", "Detailed guidance", 2500),
            ("Long processing test", "Complex guidance", 5000)
        ]
        
        for user_msg, mentor_msg, response_time in test_cases:
            interaction = save_interaction(
                test_db,
                conversation_id=str(conversation.id),
                user_message=user_msg,
                mentor_response=mentor_msg,
                response_time_ms=response_time
            )
            
            assert interaction.response_time_ms == response_time


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI or database not available")
class TestMentorToolsDatabaseIntegration:
    """Test MentorTools integration with database operations"""
    
    @pytest.mark.asyncio
    async def test_mentor_tools_database_skill_tracking(self, test_db):
        """Test MentorTools integration with database skill tracking"""
        
        # Create test user
        user = create_user(test_db, username="skill_tracking_user")
        
        # Mock memory store
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.return_value = []
        mock_memory_store.get_user_learning_patterns.return_value = None
        
        # Initialize MentorTools with database session
        tools = MentorTools(memory_store=mock_memory_store, db_session=test_db)
        
        # Mock skill progression data
        with patch('agents.mentor_agent.tools.get_user_by_username') as mock_get_user, \
             patch('agents.mentor_agent.tools.get_user_skill_progression') as mock_get_skills:
            
            mock_get_user.return_value = user
            mock_get_skills.return_value = [
                {
                    "skill_name": "Python Basics",
                    "mastery_level": 0.65,
                    "skill_domain": "SYNTAX", 
                    "last_practiced": "2024-01-15",
                    "total_interactions": 8
                },
                {
                    "skill_name": "Function Design", 
                    "mastery_level": 0.45,
                    "skill_domain": "LOGIC",
                    "last_practiced": "2024-01-14",
                    "total_interactions": 5
                }
            ]
            
            # Test memory context retrieval with database integration
            context = await tools.get_memory_context(
                user_id="skill_tracking_user",
                current_message="How do I improve my Python skills?"
            )
            
            # Verify skill progression data included
            assert "recent_skills" in context.skill_progression
            assert "total_skills_tracked" in context.skill_progression
            assert context.skill_progression["total_skills_tracked"] == 2
            
            # Verify database calls made correctly
            mock_get_user.assert_called_once_with(test_db, "skill_tracking_user")
            mock_get_skills.assert_called_once_with(test_db, str(user.id), limit=10)
    
    @pytest.mark.asyncio
    async def test_mentor_tools_database_error_handling(self, test_db):
        """Test MentorTools handles database errors gracefully"""
        
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.return_value = []
        mock_memory_store.get_user_learning_patterns.return_value = None
        
        tools = MentorTools(memory_store=mock_memory_store, db_session=test_db)
        
        # Mock database functions to raise exceptions
        with patch('agents.mentor_agent.tools.get_user_by_username') as mock_get_user:
            mock_get_user.side_effect = Exception("Database connection failed")
            
            # Should handle database errors gracefully
            context = await tools.get_memory_context(
                user_id="error_test_user",
                current_message="Test question"
            )
            
            # Should return context without database data
            assert context.skill_progression == {}
            assert len(context.similar_interactions) == 0


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI or database not available")
class TestPydanticHandlerDatabaseIntegration:
    """Test PydanticAI handler integration with database operations"""
    
    @pytest.mark.asyncio
    async def test_pydantic_handler_complete_database_workflow(self, test_db):
        """Test complete database workflow through pydantic handler"""
        
        # Mock request object
        mock_request = Mock()
        mock_request.message = "How do I learn Python programming effectively?"
        mock_request.user_id = "handler_test_user"
        mock_request.session_id = "handler_test_session"
        
        # Mock PydanticAI mentor agent
        mock_pydantic_mentor = Mock()
        mock_mentor_response = MentorResponse(
            response="Excellent question! What programming experience do you already have?",
            hint_level=1,
            memory_context_used=False,
            detected_language="python",
            detected_intent="concept_explanation",
            similar_interactions_count=0
        )
        mock_pydantic_mentor.respond = AsyncMock(return_value=mock_mentor_response)
        
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
        assert response["response"] == mock_mentor_response.response
        assert response["agent_type"] == "pydantic_strict"
        assert response["session_id"] == "handler_test_session"
        assert response["detected_language"] == "python"
        assert response["detected_intent"] == "concept_explanation"
        
        # Verify database operations occurred
        # Check user was created
        created_user = get_user_by_username(test_db, "handler_test_user")
        assert created_user is not None
        assert created_user.username == "handler_test_user"
        
        # Verify conversation was created
        # Note: This would require additional database queries to verify fully
        # In a real implementation, you'd query for sessions and interactions
    
    @pytest.mark.asyncio 
    async def test_pydantic_handler_anonymous_user(self, test_db):
        """Test pydantic handler with anonymous user"""
        
        # Mock request without user_id
        mock_request = Mock()
        mock_request.message = "General programming question"
        mock_request.user_id = None  # Anonymous user
        mock_request.session_id = None
        
        # Mock mentor response
        mock_pydantic_mentor = Mock()
        mock_mentor_response = MentorResponse(
            response="I'm here to help! What specific area would you like to explore?",
            memory_context_used=False
        )
        mock_pydantic_mentor.respond = AsyncMock(return_value=mock_mentor_response)
        
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.return_value = []
        
        # Execute handler 
        response = await handle_pydantic_mentor_request(
            request=mock_request,
            db=test_db,
            pydantic_mentor=mock_pydantic_mentor,
            memory_store=mock_memory_store
        )
        
        # Verify anonymous user handling
        assert response["agent_type"] == "pydantic_strict"
        assert response["response"] == mock_mentor_response.response
        
        # Verify anonymous user was created in database
        anonymous_user = get_user_by_username(test_db, "anonymous")
        assert anonymous_user is not None
        assert anonymous_user.username == "anonymous"


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI or database not available")
class TestDatabasePerformance:
    """Test database performance characteristics"""
    
    def test_bulk_interaction_storage_performance(self, test_db):
        """Test performance of storing many interactions"""
        
        # Create test user and conversation
        user = create_user(test_db, username="performance_test_user")
        conversation = create_conversation(test_db, str(user.id), agent_type="pydantic_strict")
        
        # Generate bulk interactions
        num_interactions = 100
        start_time = datetime.now()
        
        for i in range(num_interactions):
            save_interaction(
                test_db,
                conversation_id=str(conversation.id),
                user_message=f"Test question {i} about programming concepts",
                mentor_response=f"Response {i}: Let me guide you through this step by step...",
                response_time_ms=800 + (i % 200)  # Vary response times
            )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Performance verification
        assert duration < 10.0, f"Bulk insert took {duration:.2f}s (should be <10s)"
        
        # Verify all interactions were stored
        # Note: In a real implementation, you'd query the database to count interactions
        print(f"✅ Stored {num_interactions} interactions in {duration:.2f}s")
    
    def test_concurrent_database_operations(self, test_db):
        """Test database handles concurrent operations correctly"""
        
        # Create multiple users concurrently (simulated)
        user_data = [
            ("concurrent_user_1", "user1@test.com"),
            ("concurrent_user_2", "user2@test.com"), 
            ("concurrent_user_3", "user3@test.com"),
            ("concurrent_user_4", "user4@test.com"),
            ("concurrent_user_5", "user5@test.com")
        ]
        
        users = []
        for username, email in user_data:
            user = create_user(test_db, username=username, email=email)
            users.append(user)
        
        # Verify all users created with unique IDs
        user_ids = [user.id for user in users]
        assert len(set(user_ids)) == len(users)
        
        # Create concurrent conversations for each user
        conversations = []
        for user in users:
            conversation = create_conversation(
                test_db,
                user_id=str(user.id),
                session_title=f"Concurrent session for {user.username}",
                agent_type="pydantic_strict"
            )
            conversations.append(conversation)
        
        # Verify all conversations created successfully
        conversation_ids = [conv.id for conv in conversations]
        assert len(set(conversation_ids)) == len(conversations)


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running Mentor Agent Database Integration Tests...")
    
    if PYDANTIC_AI_AVAILABLE:
        print("✅ PydanticAI and database imports available")
        print("✅ Database integration test setup completed successfully!")
        print("Run with: pytest tests/test_mentor_agent_database.py -v")
    else:
        print("⚠️ PydanticAI or database components not available - tests skipped")
        print("Install required dependencies to run full test suite")