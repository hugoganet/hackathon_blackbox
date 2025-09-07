#!/usr/bin/env python3
"""
Comprehensive Reference Tables Tests
Tests for RefLanguage, RefIntent tables and their CRUD operations

This test file validates:
- Foreign key constraint validation
- Case-insensitive language lookup testing
- RefLanguage and RefIntent CRUD operations
- Duplicate prevention and uniqueness constraints
- Performance tests for indexed queries
- Validation constraints for categories
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import os

# Import database models and operations
from backend.database import (
    Base, RefLanguage, RefIntent, Interaction, User, Conversation
)
from backend.database_operations import (
    create_or_get_language, create_or_get_intent,
    get_all_languages, get_all_intents, populate_reference_data
)

# Test database setup
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:test@localhost:5432/test_reference")
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def setup_test_db():
    """Setup test database schema"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_test_db):
    """Create test database session"""
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing relationships"""
    user = User(username="test_user")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_conversation(db_session, sample_user):
    """Create a sample conversation for testing relationships"""
    conversation = Conversation(
        user_id=sample_user.id,
        session_id="test_session",
        agent_type="strict"
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation

# ==================================================================================
# REF_LANGUAGE TABLE TESTS
# ==================================================================================

class TestRefLanguageTable:
    """Tests for RefLanguage table and operations"""
    
    def test_ref_language_creation(self, db_session):
        """Test RefLanguage creation with all fields"""
        language = RefLanguage(
            name="Python",
            category="programming", 
            is_active=True
        )
        db_session.add(language)
        db_session.commit()
        
        # Verify creation
        saved_language = db_session.query(RefLanguage).filter_by(name="Python").first()
        assert saved_language is not None
        assert saved_language.name == "Python"
        assert saved_language.category == "programming"
        assert saved_language.is_active == True
        assert saved_language.id_language is not None
        assert isinstance(saved_language.created_at, datetime)

    def test_ref_language_name_unique_constraint(self, db_session):
        """Test name field uniqueness constraint"""
        # Create first language
        language1 = RefLanguage(name="JavaScript", category="programming")
        db_session.add(language1)
        db_session.commit()
        
        # Try to create duplicate name
        language2 = RefLanguage(name="JavaScript", category="scripting") 
        db_session.add(language2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_ref_language_required_fields(self, db_session):
        """Test required fields validation"""
        # Missing name (should fail)
        language = RefLanguage(category="programming")
        db_session.add(language)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_ref_language_category_constraint(self, db_session):
        """Test category validation constraint"""
        # Valid category should work
        valid_language = RefLanguage(name="TypeScript", category="programming")
        db_session.add(valid_language)
        db_session.commit()
        
        # Invalid category should fail
        db_session.rollback()
        invalid_language = RefLanguage(name="InvalidLang", category="invalid_category")
        db_session.add(invalid_language)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_valid_categories(self, db_session):
        """Test all valid language categories"""
        valid_categories = ["programming", "markup", "styling", "query", "scripting"]
        
        for i, category in enumerate(valid_categories):
            language = RefLanguage(name=f"TestLang{i}", category=category)
            db_session.add(language)
        
        db_session.commit()
        
        # Verify all were created
        created_languages = db_session.query(RefLanguage).filter(
            RefLanguage.name.like("TestLang%")
        ).all()
        assert len(created_languages) == 5

# ==================================================================================
# REF_INTENT TABLE TESTS  
# ==================================================================================

class TestRefIntentTable:
    """Tests for RefIntent table and operations"""
    
    def test_ref_intent_creation(self, db_session):
        """Test RefIntent creation with all fields"""
        intent = RefIntent(
            name="debugging",
            description="User is seeking help with fixing bugs or errors"
        )
        db_session.add(intent)
        db_session.commit()
        
        # Verify creation
        saved_intent = db_session.query(RefIntent).filter_by(name="debugging").first()
        assert saved_intent is not None
        assert saved_intent.name == "debugging"
        assert "debugging" in saved_intent.description.lower()
        assert saved_intent.id_intent is not None
        assert isinstance(saved_intent.created_at, datetime)

    def test_ref_intent_name_unique_constraint(self, db_session):
        """Test name field uniqueness constraint"""
        # Create first intent
        intent1 = RefIntent(name="code_review", description="First description")
        db_session.add(intent1)
        db_session.commit()
        
        # Try to create duplicate name
        intent2 = RefIntent(name="code_review", description="Different description")
        db_session.add(intent2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_ref_intent_required_fields(self, db_session):
        """Test required fields validation"""
        # Missing name (should fail)
        intent = RefIntent(description="Missing name intent")
        db_session.add(intent)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_ref_intent_optional_description(self, db_session):
        """Test that description is optional"""
        intent = RefIntent(name="test_intent")  # No description
        db_session.add(intent)
        db_session.commit()
        
        saved_intent = db_session.query(RefIntent).filter_by(name="test_intent").first()
        assert saved_intent is not None
        assert saved_intent.description is None

# ==================================================================================
# CRUD OPERATIONS TESTS
# ==================================================================================

class TestCRUDOperations:
    """Tests for CRUD operations on reference tables"""
    
    def test_create_or_get_language_new(self, db_session):
        """Test creating a new language"""
        language = create_or_get_language(db_session, "Rust", "programming")
        
        assert language.name == "Rust"
        assert language.category == "programming"
        assert language.id_language is not None
        
        # Verify it was saved
        saved = db_session.query(RefLanguage).filter_by(name="Rust").first()
        assert saved.id_language == language.id_language

    def test_create_or_get_language_existing(self, db_session):
        """Test getting an existing language"""
        # Create first time
        language1 = create_or_get_language(db_session, "Go", "programming")
        
        # Get second time (should return same)
        language2 = create_or_get_language(db_session, "Go", "programming")
        
        assert language1.id_language == language2.id_language
        assert language1.name == language2.name

    def test_create_or_get_language_case_insensitive(self, db_session):
        """Test case-insensitive language lookup"""
        # Create with standard case
        language1 = create_or_get_language(db_session, "JavaScript", "programming")
        
        # Try different cases - should return the same language
        language2 = create_or_get_language(db_session, "javascript", "programming")
        language3 = create_or_get_language(db_session, "JAVASCRIPT", "programming")
        language4 = create_or_get_language(db_session, "JaVaScRiPt", "programming")
        
        assert language1.id_language == language2.id_language
        assert language1.id_language == language3.id_language
        assert language1.id_language == language4.id_language
        assert language1.name == "Javascript"  # Should be normalized to title case

    def test_create_or_get_intent_new(self, db_session):
        """Test creating a new intent"""
        intent = create_or_get_intent(db_session, "performance_optimization", 
                                     "User wants to improve code performance")
        
        assert intent.name == "performance_optimization"
        assert "performance" in intent.description.lower()
        assert intent.id_intent is not None

    def test_create_or_get_intent_existing(self, db_session):
        """Test getting an existing intent"""
        # Create first time
        intent1 = create_or_get_intent(db_session, "best_practices", "Best practices guidance")
        
        # Get second time
        intent2 = create_or_get_intent(db_session, "best_practices", "Different description")
        
        assert intent1.id_intent == intent2.id_intent
        assert intent1.description == intent2.description  # Should keep original description

    def test_get_all_languages(self, db_session):
        """Test getting all active languages"""
        # Create some languages
        create_or_get_language(db_session, "Python", "programming")
        create_or_get_language(db_session, "CSS", "styling")
        
        # Create inactive language
        inactive_lang = RefLanguage(name="Obsolete", category="programming", is_active=False)
        db_session.add(inactive_lang)
        db_session.commit()
        
        languages = get_all_languages(db_session)
        
        # Should only return active languages, ordered by name
        assert len(languages) >= 2
        language_names = [lang.name for lang in languages]
        assert "Python" in language_names
        assert "CSS" in language_names
        assert "Obsolete" not in language_names
        assert language_names == sorted(language_names)  # Should be ordered

    def test_get_all_intents(self, db_session):
        """Test getting all intents"""
        # Create some intents
        create_or_get_intent(db_session, "debugging", "Debug help")
        create_or_get_intent(db_session, "architecture", "Architecture advice")
        
        intents = get_all_intents(db_session)
        
        assert len(intents) >= 2
        intent_names = [intent.name for intent in intents]
        assert "debugging" in intent_names
        assert "architecture" in intent_names
        assert intent_names == sorted(intent_names)  # Should be ordered

    def test_populate_reference_data(self, db_session):
        """Test populating initial reference data"""
        # Check initial count
        initial_languages = len(get_all_languages(db_session))
        initial_intents = len(get_all_intents(db_session))
        
        # Populate reference data
        populate_reference_data(db_session)
        
        # Check that data was added
        final_languages = len(get_all_languages(db_session))
        final_intents = len(get_all_intents(db_session))
        
        assert final_languages > initial_languages
        assert final_intents > initial_intents
        
        # Check specific languages were created
        languages = get_all_languages(db_session)
        language_names = [lang.name for lang in languages]
        expected_languages = ["Python", "Javascript", "Typescript", "Java", "Html", "Css", "Sql"]
        for expected in expected_languages:
            assert expected in language_names
        
        # Check specific intents were created
        intents = get_all_intents(db_session)
        intent_names = [intent.name for intent in intents]
        expected_intents = ["debugging", "concept_explanation", "code_review", "best_practices"]
        for expected in expected_intents:
            assert expected in intent_names

# ==================================================================================
# FOREIGN KEY RELATIONSHIPS TESTS
# ==================================================================================

class TestForeignKeyRelationships:
    """Tests for foreign key relationships with Interaction table"""
    
    def test_interaction_with_language_relationship(self, db_session, sample_conversation):
        """Test Interaction -> RefLanguage foreign key relationship"""
        # Create language
        language = create_or_get_language(db_session, "Python", "programming")
        
        # Create interaction with language reference
        interaction = Interaction(
            conversation_id=sample_conversation.id,
            user_message="How do I use Python lists?",
            mentor_response="Let's explore Python lists together...",
            language_id=language.id_language
        )
        db_session.add(interaction)
        db_session.commit()
        
        # Test relationship works
        assert interaction.language is not None
        assert interaction.language.name == "Python"
        assert language.interactions[0].id == interaction.id

    def test_interaction_with_intent_relationship(self, db_session, sample_conversation):
        """Test Interaction -> RefIntent foreign key relationship"""
        # Create intent
        intent = create_or_get_intent(db_session, "concept_explanation", "Explaining concepts")
        
        # Create interaction with intent reference
        interaction = Interaction(
            conversation_id=sample_conversation.id,
            user_message="What is object-oriented programming?",
            mentor_response="Let's explore OOP concepts...",
            intent_id=intent.id_intent
        )
        db_session.add(interaction)
        db_session.commit()
        
        # Test relationship works
        assert interaction.intent is not None
        assert interaction.intent.name == "concept_explanation"
        assert intent.interactions[0].id == interaction.id

    def test_interaction_foreign_key_constraints(self, db_session, sample_conversation):
        """Test foreign key constraints prevent orphaned references"""
        # Try to create interaction with non-existent language_id
        interaction1 = Interaction(
            conversation_id=sample_conversation.id,
            user_message="Test message",
            mentor_response="Test response",
            language_id=999  # Non-existent language
        )
        db_session.add(interaction1)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Try to create interaction with non-existent intent_id  
        interaction2 = Interaction(
            conversation_id=sample_conversation.id,
            user_message="Test message", 
            mentor_response="Test response",
            intent_id=999  # Non-existent intent
        )
        db_session.add(interaction2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

# ==================================================================================
# PERFORMANCE TESTS FOR INDEXES
# ==================================================================================

class TestIndexPerformance:
    """Performance tests for database indexes on foreign keys"""
    
    def test_language_id_index_performance(self, db_session, sample_conversation):
        """Test that language_id index improves query performance"""
        # Create test data
        language = create_or_get_language(db_session, "TestLanguage", "programming")
        
        # Create multiple interactions with the same language
        interactions = []
        for i in range(100):
            interaction = Interaction(
                conversation_id=sample_conversation.id,
                user_message=f"Test message {i}",
                mentor_response=f"Test response {i}",
                language_id=language.id_language
            )
            interactions.append(interaction)
        
        db_session.add_all(interactions)
        db_session.commit()
        
        # Query by language_id (should use index)
        import time
        start_time = time.time()
        
        results = db_session.query(Interaction).filter(
            Interaction.language_id == language.id_language
        ).all()
        
        query_time = time.time() - start_time
        
        # Verify results and performance
        assert len(results) == 100
        assert query_time < 0.1  # Should be fast with index

    def test_intent_id_index_performance(self, db_session, sample_conversation):
        """Test that intent_id index improves query performance"""
        # Create test data
        intent = create_or_get_intent(db_session, "test_intent", "Test intent description")
        
        # Create multiple interactions with the same intent
        interactions = []
        for i in range(100):
            interaction = Interaction(
                conversation_id=sample_conversation.id,
                user_message=f"Test message {i}",
                mentor_response=f"Test response {i}",
                intent_id=intent.id_intent
            )
            interactions.append(interaction)
        
        db_session.add_all(interactions)
        db_session.commit()
        
        # Query by intent_id (should use index)
        import time
        start_time = time.time()
        
        results = db_session.query(Interaction).filter(
            Interaction.intent_id == intent.id_intent
        ).all()
        
        query_time = time.time() - start_time
        
        # Verify results and performance
        assert len(results) == 100
        assert query_time < 0.1  # Should be fast with index

    def test_complex_join_query_performance(self, db_session, sample_conversation):
        """Test performance of complex queries joining with reference tables"""
        # Create test data
        language = create_or_get_language(db_session, "JoinTestLang", "programming")
        intent = create_or_get_intent(db_session, "join_test_intent", "Join test intent")
        
        # Create interactions
        for i in range(50):
            interaction = Interaction(
                conversation_id=sample_conversation.id,
                user_message=f"Test message {i}",
                mentor_response=f"Test response {i}",
                language_id=language.id_language,
                intent_id=intent.id_intent
            )
            db_session.add(interaction)
        
        db_session.commit()
        
        # Complex join query
        import time
        start_time = time.time()
        
        results = db_session.query(Interaction)\
            .join(RefLanguage, Interaction.language_id == RefLanguage.id_language)\
            .join(RefIntent, Interaction.intent_id == RefIntent.id_intent)\
            .filter(RefLanguage.category == "programming")\
            .filter(RefIntent.name.like("%test%"))\
            .all()
        
        query_time = time.time() - start_time
        
        # Verify results and performance
        assert len(results) == 50
        assert query_time < 0.2  # Should be reasonably fast with indexes

if __name__ == "__main__":
    pytest.main([__file__, "-v"])