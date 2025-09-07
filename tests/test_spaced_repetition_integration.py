"""
Integration tests for Spaced Repetition API endpoints
Tests the complete workflow from API to database
"""

import pytest
import json
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

# Import our application components
from backend.api import app
from backend.database_operations import Base, get_db
from backend.database.models import Flashcard, ReviewSession, User, Conversation, Interaction, Skill


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_spaced_repetition.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    """Create test database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create test user and related data
    test_user = User(
        username="testuser",
        full_name="Test User",
        email="test@example.com"
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # Create test skill
    test_skill = Skill(
        name="Python Basics",
        description="Basic Python programming concepts"
    )
    db.add(test_skill)
    db.commit()
    db.refresh(test_skill)
    
    # Create test conversation and interaction
    test_conversation = Conversation(
        user_id=test_user.id,
        session_id="test-session-123"
    )
    db.add(test_conversation)
    db.commit()
    db.refresh(test_conversation)
    
    test_interaction = Interaction(
        conversation_id=test_conversation.id,
        user_message="How do I use async/await?",
        mentor_response="Let's explore async/await step by step...",
        agent_type="strict"
    )
    db.add(test_interaction)
    db.commit()
    db.refresh(test_interaction)
    
    yield {
        "db": db,
        "user": test_user,
        "skill": test_skill,
        "conversation": test_conversation,
        "interaction": test_interaction
    }
    
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestFlashcardCreationAPI:
    """Test flashcard creation endpoints"""
    
    def test_create_flashcard_success(self, client, test_db):
        """Test successful flashcard creation"""
        test_data = test_db
        
        flashcard_data = {
            "question": "What is async/await in Python?",
            "answer": "async/await is a syntax for writing asynchronous code...",
            "difficulty": 2,
            "card_type": "concept",
            "skill_id": test_data["skill"].id,
            "interaction_id": str(test_data["interaction"].id),
            "confidence_score": 0.7
        }
        
        response = client.post("/flashcards/create", json=flashcard_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["question"] == flashcard_data["question"]
        assert data["answer"] == flashcard_data["answer"]
        assert data["difficulty"] == flashcard_data["difficulty"]
        assert data["card_type"] == flashcard_data["card_type"]
        assert "next_review_date" in data
        assert data["review_count"] == 0
    
    def test_create_flashcard_minimal_data(self, client, test_db):
        """Test flashcard creation with minimal data"""
        flashcard_data = {
            "question": "What is a Python list?",
            "answer": "A Python list is an ordered collection of items..."
        }
        
        response = client.post("/flashcards/create", json=flashcard_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["difficulty"] == 1  # Default value
        assert data["card_type"] == "concept"  # Default value
        assert data["review_count"] == 0
    
    def test_batch_create_flashcards(self, client, test_db):
        """Test batch flashcard creation"""
        test_data = test_db
        
        batch_data = {
            "user_id": str(test_data["user"].id),
            "flashcards": [
                {
                    "question": "What is a Python dictionary?",
                    "answer": "A dictionary is a collection of key-value pairs...",
                    "confidence_score": 0.8
                },
                {
                    "question": "How do you handle exceptions?",
                    "answer": "Use try-except blocks to handle exceptions...",
                    "confidence_score": 0.6,
                    "difficulty": 3
                }
            ]
        }
        
        response = client.post("/flashcards/batch", json=batch_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert all("id" in card for card in data)
        assert all("next_review_date" in card for card in data)


class TestFlashcardReviewAPI:
    """Test flashcard review endpoints"""
    
    @pytest.fixture
    def sample_flashcard(self, test_db):
        """Create a sample flashcard for testing"""
        test_data = test_db
        db = test_data["db"]
        
        flashcard = Flashcard(
            question="What is a Python function?",
            answer="A function is a block of reusable code...",
            difficulty=2,
            card_type="concept",
            next_review_date=date.today() - timedelta(days=1),  # Due for review
            review_count=1,
            skill_id=test_data["skill"].id,
            interaction_id=test_data["interaction"].id
        )
        
        db.add(flashcard)
        db.commit()
        db.refresh(flashcard)
        
        return flashcard
    
    def test_get_due_flashcards(self, client, test_db, sample_flashcard):
        """Test getting due flashcards for review"""
        test_data = test_db
        user_id = str(test_data["user"].id)
        
        response = client.get(f"/flashcards/review/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "flashcards" in data
        assert "total_due" in data
        assert "user_stats" in data
        
        assert len(data["flashcards"]) >= 1
        assert data["total_due"] >= 1
        
        # Check flashcard data structure
        flashcard = data["flashcards"][0]
        assert "id" in flashcard
        assert "question" in flashcard
        assert "answer" in flashcard
        assert "next_review_date" in flashcard
    
    def test_submit_successful_review(self, client, test_db, sample_flashcard):
        """Test submitting a successful review"""
        test_data = test_db
        
        review_data = {
            "flashcard_id": str(sample_flashcard.id),
            "user_id": str(test_data["user"].id),
            "success_score": 4,
            "response_time": 30
        }
        
        response = client.post("/flashcards/review", json=review_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "next_review_date" in data
        assert "interval_days" in data
        assert "difficulty_factor" in data
        assert "card_state" in data
        assert "message" in data
        
        # Successful review should increase interval
        assert data["interval_days"] > 1
        
        # Next review should be in the future
        next_review = date.fromisoformat(data["next_review_date"])
        assert next_review > date.today()
    
    def test_submit_failed_review(self, client, test_db, sample_flashcard):
        """Test submitting a failed review"""
        test_data = test_db
        
        review_data = {
            "flashcard_id": str(sample_flashcard.id),
            "user_id": str(test_data["user"].id),
            "success_score": 1,  # Failed review
            "response_time": 120
        }
        
        response = client.post("/flashcards/review", json=review_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        
        # Failed review should reset to short interval
        assert data["interval_days"] == 1
        assert data["card_state"] == "learning"
        
        # Next review should be tomorrow
        next_review = date.fromisoformat(data["next_review_date"])
        assert next_review == date.today() + timedelta(days=1)
    
    def test_review_nonexistent_flashcard(self, client, test_db):
        """Test reviewing a flashcard that doesn't exist"""
        test_data = test_db
        
        review_data = {
            "flashcard_id": "00000000-0000-0000-0000-000000000000",
            "user_id": str(test_data["user"].id),
            "success_score": 4
        }
        
        response = client.post("/flashcards/review", json=review_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestFlashcardStatsAPI:
    """Test flashcard statistics endpoints"""
    
    @pytest.fixture
    def flashcards_with_reviews(self, test_db):
        """Create flashcards with review history"""
        test_data = test_db
        db = test_data["db"]
        
        # Create flashcards
        flashcards = []
        for i in range(3):
            flashcard = Flashcard(
                question=f"Test question {i}",
                answer=f"Test answer {i}",
                difficulty=2,
                card_type="concept",
                next_review_date=date.today() + timedelta(days=i),
                review_count=i,
                skill_id=test_data["skill"].id,
                interaction_id=test_data["interaction"].id
            )
            db.add(flashcard)
            flashcards.append(flashcard)
        
        db.commit()
        
        # Create review sessions
        for i, flashcard in enumerate(flashcards):
            review = ReviewSession(
                user_id=test_data["user"].id,
                flashcard_id=flashcard.id,
                success_score=3 + i,  # Scores 3, 4, 5
                response_time=30 + i * 10
            )
            db.add(review)
        
        db.commit()
        
        return flashcards
    
    def test_get_flashcard_stats(self, client, test_db, flashcards_with_reviews):
        """Test getting user flashcard statistics"""
        test_data = test_db
        user_id = str(test_data["user"].id)
        
        response = client.get(f"/flashcards/stats/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_flashcards" in data
        assert "due_flashcards" in data
        assert "recent_reviews" in data
        assert "average_score" in data
        assert "success_rate" in data
        assert "streak_days" in data
        
        assert data["total_flashcards"] >= 3
        assert isinstance(data["average_score"], (int, float))
        assert 0.0 <= data["success_rate"] <= 1.0
    
    def test_get_review_schedule(self, client, test_db, flashcards_with_reviews):
        """Test getting review schedule"""
        test_data = test_db
        user_id = str(test_data["user"].id)
        
        response = client.get(f"/flashcards/schedule/{user_id}?days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_id" in data
        assert "schedule" in data
        assert "total_upcoming" in data
        
        # Should have 7 days in schedule
        assert len(data["schedule"]) == 7
        
        # Each day should have required fields
        for date_key, day_data in data["schedule"].items():
            assert "date" in day_data
            assert "cards_due" in day_data
            assert "is_today" in day_data
            assert isinstance(day_data["cards_due"], int)


class TestFlashcardDeletionAPI:
    """Test flashcard deletion endpoint"""
    
    def test_delete_flashcard_success(self, client, test_db):
        """Test successful flashcard deletion"""
        test_data = test_db
        db = test_data["db"]
        
        # Create a flashcard
        flashcard = Flashcard(
            question="Test question for deletion",
            answer="Test answer",
            skill_id=test_data["skill"].id,
            interaction_id=test_data["interaction"].id
        )
        db.add(flashcard)
        db.commit()
        db.refresh(flashcard)
        
        flashcard_id = str(flashcard.id)
        user_id = str(test_data["user"].id)
        
        response = client.delete(
            f"/flashcards/{flashcard_id}?user_id={user_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "deleted successfully" in data["message"]
    
    def test_delete_nonexistent_flashcard(self, client, test_db):
        """Test deleting a flashcard that doesn't exist"""
        test_data = test_db
        
        flashcard_id = "00000000-0000-0000-0000-000000000000"
        user_id = str(test_data["user"].id)
        
        response = client.delete(
            f"/flashcards/{flashcard_id}?user_id={user_id}"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAPIErrorHandling:
    """Test API error handling and edge cases"""
    
    def test_invalid_json_data(self, client):
        """Test handling of invalid JSON data"""
        response = client.post("/flashcards/create", data="invalid json")
        
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        incomplete_data = {
            "question": "Test question"
            # Missing answer field
        }
        
        response = client.post("/flashcards/create", json=incomplete_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_success_score(self, client, test_db):
        """Test handling of invalid success scores"""
        test_data = test_db
        
        review_data = {
            "flashcard_id": "00000000-0000-0000-0000-000000000000",
            "user_id": str(test_data["user"].id),
            "success_score": 10  # Invalid score (should be 0-5)
        }
        
        response = client.post("/flashcards/review", json=review_data)
        
        # Should handle gracefully (algorithm clamps values)
        assert response.status_code in [404, 422, 500]  # Various possible responses
    
    def test_negative_success_score(self, client, test_db):
        """Test handling of negative success scores"""
        test_data = test_db
        
        review_data = {
            "flashcard_id": "00000000-0000-0000-0000-000000000000",
            "user_id": str(test_data["user"].id),
            "success_score": -1  # Negative score
        }
        
        response = client.post("/flashcards/review", json=review_data)
        
        # Should handle gracefully
        assert response.status_code in [404, 422, 500]


class TestReviewWorkflow:
    """Test complete review workflow"""
    
    def test_complete_review_cycle(self, client, test_db):
        """Test a complete review cycle: create -> review -> schedule"""
        test_data = test_db
        user_id = str(test_data["user"].id)
        
        # Step 1: Create flashcard
        flashcard_data = {
            "question": "What is Python?",
            "answer": "Python is a programming language...",
            "confidence_score": 0.5
        }
        
        create_response = client.post("/flashcards/create", json=flashcard_data)
        assert create_response.status_code == 200
        flashcard = create_response.json()
        flashcard_id = flashcard["id"]
        
        # Step 2: Review the flashcard
        review_data = {
            "flashcard_id": flashcard_id,
            "user_id": user_id,
            "success_score": 4,
            "response_time": 45
        }
        
        review_response = client.post("/flashcards/review", json=review_data)
        assert review_response.status_code == 200
        review_result = review_response.json()
        
        # Step 3: Check updated statistics
        stats_response = client.get(f"/flashcards/stats/{user_id}")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        assert stats["total_flashcards"] >= 1
        assert stats["recent_reviews"] >= 1
        
        # Step 4: Check schedule
        schedule_response = client.get(f"/flashcards/schedule/{user_id}")
        assert schedule_response.status_code == 200
        schedule = schedule_response.json()
        
        assert "schedule" in schedule
        assert schedule["total_upcoming"] >= 0


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])