"""
Test utilities for curator agent testing
Provides helper functions for database setup, mock responses, and validation
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import Session
from datetime import datetime, date

# Import database models
from backend.database import User, Conversation, Interaction, get_user_by_username, create_conversation, save_interaction

class MockBlackboxResponse:
    """Mock response from Blackbox AI API"""
    
    def __init__(self, response_text: str):
        self.response_text = response_text
        
    def json(self):
        return {"response": self.response_text}

class CuratorTestHelper:
    """Helper class for curator agent testing"""
    
    @staticmethod
    def create_test_user(db: Session, username: str = None) -> User:
        """Create test user in database"""
        if not username:
            username = f"test_user_{uuid.uuid4().hex[:8]}"
        return get_user_by_username(db, username)
    
    @staticmethod
    def create_test_conversation(
        db: Session, 
        user: User, 
        agent_type: str = "strict",
        session_id: str = None
    ) -> Conversation:
        """Create test conversation in database"""
        if not session_id:
            session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        return create_conversation(db, str(user.id), session_id, agent_type)
    
    @staticmethod
    def create_test_interaction(
        db: Session,
        conversation: Conversation,
        user_message: str,
        mentor_response: str,
        response_time_ms: int = 1500
    ) -> Interaction:
        """Create test interaction in database"""
        return save_interaction(
            db,
            str(conversation.id), 
            user_message,
            mentor_response,
            response_time_ms
        )
    
    @staticmethod
    def validate_curator_response(response: Dict[str, Any]) -> bool:
        """Validate curator response follows expected JSON schema"""
        required_fields = ["skills", "mistakes", "openQuestions", "nextSteps", "confidence"]
        
        # Check all required fields exist
        for field in required_fields:
            if field not in response:
                return False
        
        # Validate field types and constraints
        if not isinstance(response["skills"], list) or len(response["skills"]) > 5:
            return False
        
        if not isinstance(response["mistakes"], list) or len(response["mistakes"]) > 3:
            return False
            
        if not isinstance(response["openQuestions"], list) or len(response["openQuestions"]) > 3:
            return False
            
        if not isinstance(response["nextSteps"], list) or len(response["nextSteps"]) > 3:
            return False
        
        # Validate confidence is float between 0.0 and 1.0
        if not isinstance(response["confidence"], (int, float)) or not 0.0 <= response["confidence"] <= 1.0:
            return False
        
        return True
    
    @staticmethod
    def create_mock_curator_response(scenario: str) -> str:
        """Create mock curator response JSON for testing"""
        mock_responses = {
            "junior_javascript": json.dumps({
                "skills": ["variable_declaration", "let_keyword", "hoisting"],
                "mistakes": ["accessing variable before declaration"],
                "openQuestions": ["difference between let and var"],
                "nextSteps": ["practice variable scoping"],
                "confidence": 0.3
            }),
            "intermediate_react": json.dumps({
                "skills": ["react_hooks", "useState", "performance"],
                "mistakes": ["creating functions in render"],
                "openQuestions": ["when to use useCallback"],
                "nextSteps": ["implement memoization"],
                "confidence": 0.6
            }),
            "senior_architecture": json.dumps({
                "skills": ["microservices", "event_sourcing", "system_design"],
                "mistakes": [],
                "openQuestions": ["complexity vs benefits trade-off"],
                "nextSteps": ["prototype event sourcing"],
                "confidence": 0.8
            }),
            "error_case": json.dumps({
                "skills": [],
                "mistakes": ["non-technical question"],
                "openQuestions": ["what programming topic to learn"],
                "nextSteps": ["ask specific technical question"],
                "confidence": 0.1
            })
        }
        return mock_responses.get(scenario, mock_responses["junior_javascript"])
    
    @staticmethod
    def mock_blackbox_api(response_text: str = None):
        """Create mock for Blackbox AI API calls"""
        if not response_text:
            response_text = CuratorTestHelper.create_mock_curator_response("junior_javascript")
        
        def mock_response_handler(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": response_text
                        }
                    }
                ]
            }
            return mock_response
        
        return patch('requests.post', side_effect=mock_response_handler)

class DatabaseTestHelper:
    """Helper for database operations in tests"""
    
    @staticmethod
    def cleanup_test_data(db: Session, user_ids: List[str]):
        """Clean up test data after tests"""
        for user_id in user_ids:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # Delete associated conversations and interactions
                for conversation in user.conversations:
                    db.delete(conversation)
                db.delete(user)
        db.commit()
    
    @staticmethod
    def get_user_interaction_count(db: Session, user_id: str) -> int:
        """Get total interaction count for a user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        
        total_interactions = 0
        for conversation in user.conversations:
            total_interactions += len(conversation.interactions)
        return total_interactions
    
    @staticmethod
    def get_recent_interactions(db: Session, user_id: str, limit: int = 10) -> List[Interaction]:
        """Get recent interactions for a user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        interactions = []
        for conversation in user.conversations:
            interactions.extend(conversation.interactions)
        
        # Sort by created_at descending and limit
        interactions.sort(key=lambda x: x.created_at, reverse=True)
        return interactions[:limit]

class AssertionHelper:
    """Helper for test assertions"""
    
    @staticmethod
    def assert_curator_response_valid(response: Dict[str, Any]):
        """Assert curator response is valid"""
        assert CuratorTestHelper.validate_curator_response(response), \
            f"Invalid curator response format: {response}"
    
    @staticmethod
    def assert_skills_reasonable(skills: List[str], expected_min: int = 1, expected_max: int = 5):
        """Assert skills list is reasonable"""
        assert isinstance(skills, list), "Skills should be a list"
        assert expected_min <= len(skills) <= expected_max, \
            f"Skills count {len(skills)} should be between {expected_min} and {expected_max}"
        assert all(isinstance(skill, str) and skill.strip() for skill in skills), \
            "All skills should be non-empty strings"
    
    @staticmethod
    def assert_confidence_reasonable(confidence: float, min_val: float = 0.0, max_val: float = 1.0):
        """Assert confidence score is reasonable"""
        assert isinstance(confidence, (int, float)), "Confidence should be numeric"
        assert min_val <= confidence <= max_val, \
            f"Confidence {confidence} should be between {min_val} and {max_val}"
    
    @staticmethod
    def assert_database_state_consistent(db: Session, user_id: str):
        """Assert database is in consistent state after operations"""
        user = db.query(User).filter(User.id == user_id).first()
        assert user is not None, f"User {user_id} should exist"
        assert user.is_active, "User should be active"
        
        # Check conversations exist and are properly linked
        for conversation in user.conversations:
            assert conversation.user_id == user.id, "Conversation should be linked to user"
            assert conversation.session_id, "Conversation should have session_id"
            
            # Check interactions are properly linked
            for interaction in conversation.interactions:
                assert interaction.conversation_id == conversation.id, \
                    "Interaction should be linked to conversation"
                assert interaction.user_message, "Interaction should have user message"
                assert interaction.mentor_response, "Interaction should have mentor response"

class PerformanceTestHelper:
    """Helper for performance testing"""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """Measure function execution time"""
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        return result, execution_time_ms
    
    @staticmethod
    def assert_performance_acceptable(execution_time_ms: float, max_time_ms: float = 2000):
        """Assert performance meets requirements"""
        assert execution_time_ms <= max_time_ms, \
            f"Execution time {execution_time_ms:.2f}ms exceeds maximum {max_time_ms}ms"

# Test data factories
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_skill_progression_data(user_id: str, num_skills: int = 5) -> List[Dict[str, Any]]:
        """Create skill progression test data"""
        skills_data = []
        skill_names = [
            "javascript_variables", "react_hooks", "sql_queries", 
            "async_await", "error_handling", "performance_optimization"
        ]
        
        for i in range(min(num_skills, len(skill_names))):
            skills_data.append({
                "user_id": user_id,
                "skill_name": skill_names[i],
                "mastery_level": min(5, i + 1),  # Progressive skill levels
                "snapshot_date": date.today()
            })
        
        return skills_data
    
    @staticmethod
    def create_multi_session_data(user_id: str, num_sessions: int = 3) -> List[Dict[str, Any]]:
        """Create multi-session conversation data"""
        sessions_data = []
        
        for i in range(num_sessions):
            session_data = {
                "user_id": user_id,
                "session_id": f"session_{i+1}_{uuid.uuid4().hex[:6]}",
                "agent_type": "curator",
                "interactions": [
                    {
                        "user_message": f"Session {i+1}: How do I handle async operations?",
                        "mentor_response": f"Session {i+1}: Let's explore async patterns together..."
                    }
                ]
            }
            sessions_data.append(session_data)
        
        return sessions_data