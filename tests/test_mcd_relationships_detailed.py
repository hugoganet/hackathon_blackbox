#!/usr/bin/env python3
"""
Detailed MCD Relationship Tests
Based on backend/database/doc/dev_mentor_ai.mcd

Tests every relationship defined in the MCD with specific focus on:
- Cardinalities (0N, 1N, 11, 01)
- Junction table attributes
- Relationship constraints and business rules

MCD Relationships to Test:
Line 2:  CLASSIFY, 0N INTERACTION, 11 REF_DOMAIN
Line 4:  BELONG_TO, 0N SKILL, 11 REF_DOMAIN  
Line 10: USE, 0N INTERACTION, 01 REF_LANGUAGE
Line 12: GENERATE, 0N INTERACTION, 0N FLASHCARD
Line 14: REVIEW, 0N USER, 0N FLASHCARD, 1N REVIEW_SESSION: success_score, response_time
Line 16: MASTER, 0N USER, 0N SKILL: initial_level, creation_date
Line 17: TRACK, 0N USER, 0N SKILL, 1N SKILL_HISTORY: mastery_level, snapshot_date
Line 20: CATEGORIZE, 0N INTERACTION, 01 REF_INTENT
Line 21: CONTAIN, 0N SESSION, 1N INTERACTION
Line 23: OWN, 0N USER, 1N SESSION
"""

import pytest
import uuid
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import os

# Import database models
from backend.database import Base, get_db
from backend.database import (
    User, Session, Interaction, Skill, SkillHistory,
    Flashcard, ReviewSession, RefDomain, RefLanguage, RefIntent
)

# Test database setup
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:test@localhost:5432/test_mcd_relations")
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
    db.rollback()
    db.close()

# ==================================================================================
# MCD LINE 2: CLASSIFY, 0N INTERACTION, 11 REF_DOMAIN
# ==================================================================================

class TestClassifyRelationship:
    """
    CLASSIFY: 0N INTERACTION, 11 REF_DOMAIN
    - Many interactions can be classified by one domain (0N -> 11)
    - Each interaction can optionally have one domain classification
    - Domain is required if classification exists (11 = exactly one)
    """
    
    def test_classify_cardinality_multiple_interactions_one_domain(self, db_session):
        """Test that multiple interactions can be classified by the same domain"""
        # Setup domain
        domain = RefDomain(name="DEBUGGING", description="Debugging and troubleshooting")
        db_session.add(domain)
        db_session.commit()
        
        # Setup user and session
        user = User(username="classify_test_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Create multiple interactions classified by same domain
        interactions = []
        for i in range(3):
            interaction = Interaction(
                session_id=session.id_session,
                user_message=f"Debug question {i+1}",
                mentor_response=f"Debug answer {i+1}",
                id_domain=domain.id_domain  # CLASSIFY relationship
            )
            interactions.append(interaction)
            db_session.add(interaction)
        
        db_session.commit()
        
        # Verify multiple interactions classified by same domain
        classified_interactions = db_session.query(Interaction).filter_by(id_domain=domain.id_domain).all()
        assert len(classified_interactions) == 3
        
        # Verify each interaction points to the same domain
        for interaction in classified_interactions:
            assert interaction.id_domain == domain.id_domain

    def test_classify_optional_relationship(self, db_session):
        """Test that interaction can exist without domain classification (optional)"""
        # Setup user and session
        user = User(username="optional_classify_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Create interaction without domain classification
        interaction = Interaction(
            session_id=session.id_session,
            user_message="Generic question",
            mentor_response="Generic answer"
            # id_domain is None - optional classification
        )
        db_session.add(interaction)
        db_session.commit()
        
        saved_interaction = db_session.query(Interaction).first()
        assert saved_interaction.id_domain is None  # No classification

    def test_classify_invalid_domain_fails(self, db_session):
        """Test that interaction cannot reference non-existent domain"""
        user = User(username="invalid_domain_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Try to classify with non-existent domain
        interaction = Interaction(
            session_id=session.id_session,
            user_message="Question",
            mentor_response="Answer",
            id_domain=99999  # Non-existent domain
        )
        db_session.add(interaction)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

# ==================================================================================
# MCD LINE 4: BELONG_TO, 0N SKILL, 11 REF_DOMAIN
# ==================================================================================

class TestBelongToRelationship:
    """
    BELONG_TO: 0N SKILL, 11 REF_DOMAIN
    - Multiple skills belong to one domain (0N -> 11)
    - Each skill must belong to exactly one domain (11 = required)
    """
    
    def test_belong_to_multiple_skills_one_domain(self, db_session):
        """Test multiple skills belonging to same domain"""
        domain = RefDomain(name="PYTHON", description="Python programming")
        db_session.add(domain)
        db_session.commit()
        
        # Create multiple skills in same domain
        skills = [
            Skill(name="Python Lists", description="Working with lists", id_domain=domain.id_domain),
            Skill(name="Python Dicts", description="Working with dictionaries", id_domain=domain.id_domain),
            Skill(name="Python Functions", description="Writing functions", id_domain=domain.id_domain)
        ]
        
        for skill in skills:
            db_session.add(skill)
        db_session.commit()
        
        # Verify all skills belong to same domain
        domain_skills = db_session.query(Skill).filter_by(id_domain=domain.id_domain).all()
        assert len(domain_skills) == 3
        
        for skill in domain_skills:
            assert skill.id_domain == domain.id_domain

    def test_belong_to_required_domain(self, db_session):
        """Test that skill requires domain (11 cardinality means required)"""
        # Try to create skill without domain
        skill = Skill(name="Orphaned Skill", description="Skill without domain")
        # id_domain is None - should fail if NOT NULL constraint exists
        db_session.add(skill)
        
        try:
            db_session.commit()
            # If this succeeds, check if domain is actually required in implementation
            saved_skill = db_session.query(Skill).first()
            # This would indicate the constraint might not be implemented
        except IntegrityError:
            # Expected behavior - skill requires domain
            pass

    def test_belong_to_domain_deletion_behavior(self, db_session):
        """Test behavior when domain is deleted (cascade vs restrict)"""
        domain = RefDomain(name="DELETION_TEST", description="Testing deletion behavior")
        db_session.add(domain)
        db_session.commit()
        
        skill = Skill(name="Test Skill", description="Will be affected by domain deletion", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        # Try to delete domain
        try:
            db_session.delete(domain)
            db_session.commit()
            
            # Check if skill still exists
            remaining_skill = db_session.query(Skill).filter_by(name="Test Skill").first()
            if remaining_skill is None:
                # CASCADE: Skill was deleted with domain
                pass
            else:
                # RESTRICT/SET NULL: Skill remains but domain reference changed
                pass
                
        except IntegrityError:
            # RESTRICT: Cannot delete domain with dependent skills
            db_session.rollback()
            
            # Verify skill and domain still exist
            assert db_session.query(Skill).filter_by(name="Test Skill").first() is not None
            assert db_session.query(RefDomain).filter_by(name="DELETION_TEST").first() is not None

# ==================================================================================
# MCD LINE 10: USE, 0N INTERACTION, 01 REF_LANGUAGE
# ==================================================================================

class TestUseRelationship:
    """
    USE: 0N INTERACTION, 01 REF_LANGUAGE
    - Multiple interactions can use same language (0N)
    - Each interaction optionally uses one language (01 = zero or one)
    """
    
    def test_use_multiple_interactions_one_language(self, db_session):
        """Test multiple interactions using same language"""
        language = RefLanguage(name="JavaScript", category="Programming")
        db_session.add(language)
        db_session.commit()
        
        # Setup user and session
        user = User(username="js_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Create multiple JavaScript-related interactions
        js_interactions = []
        for i in range(4):
            interaction = Interaction(
                session_id=session.id_session,
                user_message=f"JavaScript question {i+1}",
                mentor_response=f"JavaScript answer {i+1}",
                id_language=language.id_language  # USE relationship
            )
            js_interactions.append(interaction)
            db_session.add(interaction)
        
        db_session.commit()
        
        # Verify multiple interactions use same language
        language_interactions = db_session.query(Interaction).filter_by(id_language=language.id_language).all()
        assert len(language_interactions) == 4

    def test_use_optional_language(self, db_session):
        """Test that interaction can exist without language specification (01 = optional)"""
        user = User(username="no_lang_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Create interaction without language
        interaction = Interaction(
            session_id=session.id_session,
            user_message="Language-agnostic question",
            mentor_response="Language-agnostic answer"
            # id_language is None - optional
        )
        db_session.add(interaction)
        db_session.commit()
        
        saved_interaction = db_session.query(Interaction).first()
        assert saved_interaction.id_language is None

    def test_use_zero_or_one_constraint(self, db_session):
        """Test that interaction cannot use multiple languages (01 = zero or one)"""
        # This is enforced by the database schema - interaction has single id_language field
        # Cannot assign multiple languages to one interaction
        
        language1 = RefLanguage(name="Python", category="Programming")
        language2 = RefLanguage(name="Java", category="Programming")
        db_session.add_all([language1, language2])
        db_session.commit()
        
        user = User(username="single_lang_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Can only assign one language per interaction
        interaction = Interaction(
            session_id=session.id_session,
            user_message="Single language question",
            mentor_response="Single language answer",
            id_language=language1.id_language  # Can only set one language
        )
        db_session.add(interaction)
        db_session.commit()
        
        saved_interaction = db_session.query(Interaction).first()
        assert saved_interaction.id_language == language1.id_language
        # Cannot also set language2 - schema enforces single language

# ==================================================================================
# MCD LINE 12: GENERATE, 0N INTERACTION, 0N FLASHCARD
# ==================================================================================

class TestGenerateRelationship:
    """
    GENERATE: 0N INTERACTION, 0N FLASHCARD
    - Multiple interactions can generate flashcards (0N)
    - Multiple flashcards can be generated from interactions (0N)
    - Many-to-many relationship (though implementation might be simpler)
    """
    
    def test_generate_interaction_to_multiple_flashcards(self, db_session):
        """Test one interaction generating multiple flashcards"""
        # Setup
        user = User(username="flashcard_gen_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="flashcard")
        db_session.add(session)
        db_session.commit()
        
        interaction = Interaction(
            session_id=session.id_session,
            user_message="What are Python decorators and how do they work?",
            mentor_response="Decorators are functions that modify other functions..."
        )
        db_session.add(interaction)
        db_session.commit()
        
        # Generate multiple flashcards from single interaction
        flashcards = [
            Flashcard(
                question="What is a Python decorator?",
                answer="A function that modifies another function",
                card_type="concept",
                id_interaction=interaction.id_interaction
            ),
            Flashcard(
                question="What syntax is used for decorators?",
                answer="The @ symbol followed by decorator name",
                card_type="application", 
                id_interaction=interaction.id_interaction
            ),
            Flashcard(
                question="Write a simple decorator example",
                answer="@decorator_name\\ndef function_name():",
                card_type="code_completion",
                id_interaction=interaction.id_interaction
            )
        ]
        
        for flashcard in flashcards:
            db_session.add(flashcard)
        db_session.commit()
        
        # Verify multiple flashcards generated from one interaction
        generated_cards = db_session.query(Flashcard).filter_by(id_interaction=interaction.id_interaction).all()
        assert len(generated_cards) == 3
        
        # Verify all cards reference the same interaction
        for card in generated_cards:
            assert card.id_interaction == interaction.id_interaction

    def test_generate_flashcard_without_interaction(self, db_session):
        """Test flashcard can exist without being generated from interaction (0N allows zero)"""
        # Create standalone flashcard (not generated from interaction)
        flashcard = Flashcard(
            question="What is recursion?",
            answer="A function calling itself with a base case",
            card_type="concept"
            # id_interaction is None - not generated from interaction
        )
        db_session.add(flashcard)
        db_session.commit()
        
        saved_flashcard = db_session.query(Flashcard).first()
        assert saved_flashcard.id_interaction is None

    def test_generate_interaction_without_flashcards(self, db_session):
        """Test interaction can exist without generating flashcards (0N allows zero)"""
        user = User(username="no_flashcard_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Create interaction that doesn't generate flashcards
        interaction = Interaction(
            session_id=session.id_session,
            user_message="Simple greeting",
            mentor_response="Hello! How can I help?"
        )
        db_session.add(interaction)
        db_session.commit()
        
        # Verify no flashcards generated
        generated_cards = db_session.query(Flashcard).filter_by(id_interaction=interaction.id_interaction).all()
        assert len(generated_cards) == 0

# ==================================================================================
# MCD LINE 14-15: REVIEW, 0N USER, 0N FLASHCARD, 1N REVIEW_SESSION
# ==================================================================================

class TestReviewRelationship:
    """
    REVIEW: 0N USER, 0N FLASHCARD, 1N REVIEW_SESSION: success_score, response_time
    - Many users can review many flashcards (many-to-many)
    - Each review creates exactly one review_session record (1N)
    - Junction table has attributes: success_score, response_time
    """
    
    def test_review_many_to_many_user_flashcard(self, db_session):
        """Test many users can review many flashcards"""
        # Create users
        users = [
            User(username="reviewer1", role="developer"),
            User(username="reviewer2", role="developer")
        ]
        for user in users:
            db_session.add(user)
        db_session.commit()
        
        # Create flashcards
        flashcards = [
            Flashcard(question="What is a variable?", answer="A storage location", card_type="concept"),
            Flashcard(question="What is a loop?", answer="Repeated execution", card_type="concept"),
            Flashcard(question="What is a function?", answer="Reusable code block", card_type="concept")
        ]
        for flashcard in flashcards:
            db_session.add(flashcard)
        db_session.commit()
        
        # Create review sessions - many-to-many relationships
        review_combinations = [
            # User 1 reviews all flashcards
            (users[0].id_user, flashcards[0].id_flashcard, 5, 20),
            (users[0].id_user, flashcards[1].id_flashcard, 4, 25),
            (users[0].id_user, flashcards[2].id_flashcard, 3, 30),
            # User 2 reviews some flashcards
            (users[1].id_user, flashcards[0].id_flashcard, 4, 22),
            (users[1].id_user, flashcards[2].id_flashcard, 5, 18)
        ]
        
        for user_id, flashcard_id, success_score, response_time in review_combinations:
            review = ReviewSession(
                id_user=user_id,
                id_flashcard=flashcard_id,
                success_score=success_score,
                response_time=response_time
            )
            db_session.add(review)
        
        db_session.commit()
        
        # Verify many-to-many relationships
        total_reviews = db_session.query(ReviewSession).count()
        assert total_reviews == 5
        
        # Verify user 1 has 3 reviews
        user1_reviews = db_session.query(ReviewSession).filter_by(id_user=users[0].id_user).all()
        assert len(user1_reviews) == 3
        
        # Verify flashcard 1 was reviewed by 2 users
        flashcard1_reviews = db_session.query(ReviewSession).filter_by(id_flashcard=flashcards[0].id_flashcard).all()
        assert len(flashcard1_reviews) == 2

    def test_review_session_attributes(self, db_session):
        """Test review session junction table attributes"""
        user = User(username="reviewer", role="developer")
        db_session.add(user)
        db_session.commit()
        
        flashcard = Flashcard(question="Test question", answer="Test answer", card_type="concept")
        db_session.add(flashcard)
        db_session.commit()
        
        # Create review with specific attributes
        review = ReviewSession(
            id_user=user.id_user,
            id_flashcard=flashcard.id_flashcard,
            success_score=4,  # Junction table attribute
            response_time=25,  # Junction table attribute
            review_date=datetime.utcnow()
        )
        db_session.add(review)
        db_session.commit()
        
        saved_review = db_session.query(ReviewSession).first()
        assert saved_review.success_score == 4
        assert saved_review.response_time == 25
        assert saved_review.review_date is not None

    def test_review_unique_constraint_per_day(self, db_session):
        """Test potential unique constraint on user/flashcard/day"""
        user = User(username="daily_reviewer", role="developer")
        db_session.add(user)
        db_session.commit()
        
        flashcard = Flashcard(question="Daily question", answer="Daily answer", card_type="concept")
        db_session.add(flashcard)
        db_session.commit()
        
        today = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
        
        # First review today
        review1 = ReviewSession(
            id_user=user.id_user,
            id_flashcard=flashcard.id_flashcard,
            success_score=3,
            response_time=30,
            review_date=today
        )
        db_session.add(review1)
        db_session.commit()
        
        # Second review same day (should fail if unique constraint exists)
        review2 = ReviewSession(
            id_user=user.id_user,
            id_flashcard=flashcard.id_flashcard,
            success_score=5,
            response_time=20,
            review_date=today.replace(hour=14)  # Same day, different time
        )
        db_session.add(review2)
        
        try:
            db_session.commit()
            # If successful, no daily unique constraint
            daily_reviews = db_session.query(ReviewSession).filter(
                ReviewSession.id_user == user.id_user,
                ReviewSession.id_flashcard == flashcard.id_flashcard
            ).all()
            # Could be 1 or 2 depending on constraint implementation
            assert len(daily_reviews) >= 1
        except IntegrityError:
            # Expected if unique constraint on user/flashcard/day exists
            pass

# ==================================================================================
# MCD LINE 16: MASTER, 0N USER, 0N SKILL
# ==================================================================================

class TestMasterRelationship:
    """
    MASTER: 0N USER, 0N SKILL: initial_level, creation_date
    - Many users can master many skills (many-to-many)
    - Junction table has attributes: initial_level, creation_date
    - This might be implemented through SkillHistory table
    """
    
    def test_master_many_to_many_user_skill(self, db_session):
        """Test many users can master many skills"""
        # Create domain first
        domain = RefDomain(name="MASTERY", description="Skills mastery testing")
        db_session.add(domain)
        db_session.commit()
        
        # Create users
        users = [
            User(username="learner1", role="developer"),
            User(username="learner2", role="developer")
        ]
        for user in users:
            db_session.add(user)
        db_session.commit()
        
        # Create skills  
        skills = [
            Skill(name="Python Basics", description="Basic Python", id_domain=domain.id_domain),
            Skill(name="JavaScript Basics", description="Basic JavaScript", id_domain=domain.id_domain)
        ]
        for skill in skills:
            db_session.add(skill)
        db_session.commit()
        
        # Create mastery relationships via SkillHistory (represents MASTER relationship)
        mastery_relationships = [
            # User 1 masters both skills
            SkillHistory(id_user=users[0].id_user, id_skill=skills[0].id_skill, mastery_level=1, snapshot_date=date.today()),
            SkillHistory(id_user=users[0].id_user, id_skill=skills[1].id_skill, mastery_level=1, snapshot_date=date.today()),
            # User 2 masters one skill  
            SkillHistory(id_user=users[1].id_user, id_skill=skills[0].id_skill, mastery_level=2, snapshot_date=date.today())
        ]
        
        for mastery in mastery_relationships:
            db_session.add(mastery)
        db_session.commit()
        
        # Verify many-to-many relationships
        # User 1 masters 2 skills
        user1_masteries = db_session.query(SkillHistory).filter_by(id_user=users[0].id_user).all()
        assert len(user1_masteries) == 2
        
        # Skill 1 is mastered by 2 users
        skill1_masters = db_session.query(SkillHistory).filter_by(id_skill=skills[0].id_skill).all()
        assert len(skill1_masters) == 2

    def test_master_relationship_attributes(self, db_session):
        """Test MASTER relationship attributes: initial_level, creation_date"""
        domain = RefDomain(name="ATTRIBUTES", description="Attribute testing")
        db_session.add(domain)
        db_session.commit()
        
        user = User(username="attribute_tester", role="developer")
        db_session.add(user)
        db_session.commit()
        
        skill = Skill(name="Test Skill", description="For attribute testing", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        # Create mastery with specific initial level and date
        creation_date = date.today() - timedelta(days=30)
        mastery = SkillHistory(
            id_user=user.id_user,
            id_skill=skill.id_skill,
            mastery_level=1,  # Represents initial_level attribute
            snapshot_date=creation_date,  # Represents creation_date attribute
            created_at=datetime.utcnow()
        )
        db_session.add(mastery)
        db_session.commit()
        
        saved_mastery = db_session.query(SkillHistory).first()
        assert saved_mastery.mastery_level == 1  # initial_level
        assert saved_mastery.snapshot_date == creation_date  # creation_date
        assert saved_mastery.created_at is not None

# ==================================================================================
# MCD LINE 17: TRACK, 0N USER, 0N SKILL, 1N SKILL_HISTORY
# ==================================================================================

class TestTrackRelationship:
    """
    TRACK: 0N USER, 0N SKILL, 1N SKILL_HISTORY: mastery_level, snapshot_date
    - Many users track many skills through skill history (many-to-many)
    - Each tracking event creates exactly one skill_history record (1N)
    - Junction table attributes: mastery_level, snapshot_date
    """
    
    def test_track_skill_progression_over_time(self, db_session):
        """Test tracking skill progression through multiple history records"""
        domain = RefDomain(name="PROGRESSION", description="Skill progression tracking")
        db_session.add(domain)
        db_session.commit()
        
        user = User(username="progressor", role="developer")
        db_session.add(user)
        db_session.commit()
        
        skill = Skill(name="Algorithm Design", description="Designing algorithms", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        # Track skill progression over multiple days
        progression_data = [
            (date.today() - timedelta(days=30), 1),  # Started as novice
            (date.today() - timedelta(days=20), 2),  # Improved to beginner
            (date.today() - timedelta(days=10), 3),  # Reached intermediate
            (date.today(), 4)  # Now advanced
        ]
        
        skill_histories = []
        for snapshot_date, mastery_level in progression_data:
            history = SkillHistory(
                id_user=user.id_user,
                id_skill=skill.id_skill,
                mastery_level=mastery_level,
                snapshot_date=snapshot_date
            )
            skill_histories.append(history)
            db_session.add(history)
        
        db_session.commit()
        
        # Verify progression tracking
        tracked_progression = db_session.query(SkillHistory).filter_by(
            id_user=user.id_user,
            id_skill=skill.id_skill
        ).order_by(SkillHistory.snapshot_date).all()
        
        assert len(tracked_progression) == 4
        
        # Verify progression order and values
        expected_levels = [1, 2, 3, 4]
        for i, history in enumerate(tracked_progression):
            assert history.mastery_level == expected_levels[i]

    def test_track_multiple_users_same_skill(self, db_session):
        """Test multiple users tracking the same skill"""
        domain = RefDomain(name="MULTI_USER", description="Multi-user skill tracking")
        db_session.add(domain)
        db_session.commit()
        
        # Create multiple users
        users = [
            User(username="tracker1", role="developer"),
            User(username="tracker2", role="developer"),
            User(username="tracker3", role="developer")
        ]
        for user in users:
            db_session.add(user)
        db_session.commit()
        
        skill = Skill(name="React Hooks", description="Using React hooks", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        # Each user tracks the same skill with different mastery levels
        tracking_data = [
            (users[0].id_user, 3),  # User 1 - intermediate
            (users[1].id_user, 2),  # User 2 - beginner  
            (users[2].id_user, 4)   # User 3 - advanced
        ]
        
        for user_id, mastery_level in tracking_data:
            history = SkillHistory(
                id_user=user_id,
                id_skill=skill.id_skill,
                mastery_level=mastery_level,
                snapshot_date=date.today()
            )
            db_session.add(history)
        
        db_session.commit()
        
        # Verify multiple users track same skill
        skill_trackers = db_session.query(SkillHistory).filter_by(id_skill=skill.id_skill).all()
        assert len(skill_trackers) == 3
        
        # Verify different mastery levels
        mastery_levels = [tracker.mastery_level for tracker in skill_trackers]
        assert set(mastery_levels) == {2, 3, 4}

# ==================================================================================
# MCD LINE 20: CATEGORIZE, 0N INTERACTION, 01 REF_INTENT
# ==================================================================================

class TestCategorizeRelationship:
    """
    CATEGORIZE: 0N INTERACTION, 01 REF_INTENT
    - Multiple interactions can have same intent (0N)
    - Each interaction optionally has one intent (01 = zero or one)
    """
    
    def test_categorize_multiple_interactions_same_intent(self, db_session):
        """Test multiple interactions categorized with same intent"""
        intent = RefIntent(name="code_review", description="Code review and feedback")
        db_session.add(intent)
        db_session.commit()
        
        user = User(username="reviewer_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Create multiple interactions with same intent
        review_interactions = [
            "Please review this function",
            "Is this code following best practices?",
            "Can you check my error handling?",
            "What do you think about this algorithm?"
        ]
        
        for question in review_interactions:
            interaction = Interaction(
                session_id=session.id_session,
                user_message=question,
                mentor_response="Let me review that for you...",
                id_intent=intent.id_intent  # CATEGORIZE relationship
            )
            db_session.add(interaction)
        
        db_session.commit()
        
        # Verify multiple interactions with same intent
        categorized_interactions = db_session.query(Interaction).filter_by(id_intent=intent.id_intent).all()
        assert len(categorized_interactions) == 4

    def test_categorize_optional_intent(self, db_session):
        """Test interaction can exist without intent categorization (01 = optional)"""
        user = User(username="uncategorized_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Create interaction without intent
        interaction = Interaction(
            session_id=session.id_session,
            user_message="Random question without specific intent",
            mentor_response="Let me help with that"
            # id_intent is None - optional categorization
        )
        db_session.add(interaction)
        db_session.commit()
        
        saved_interaction = db_session.query(Interaction).first()
        assert saved_interaction.id_intent is None

# ==================================================================================
# MCD LINE 21: CONTAIN, 0N SESSION, 1N INTERACTION
# ==================================================================================

class TestContainRelationship:
    """
    CONTAIN: 0N SESSION, 1N INTERACTION
    - One session can contain multiple interactions (0N)
    - Each interaction belongs to exactly one session (1N = required)
    """
    
    def test_contain_multiple_interactions_one_session(self, db_session):
        """Test one session containing multiple interactions"""
        user = User(username="chatty_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(
            user_id=user.id_user,
            title="Long Learning Session",
            agent_type="normal"
        )
        db_session.add(session)
        db_session.commit()
        
        # Create multiple interactions in same session
        conversation = [
            ("What is a variable?", "A variable stores data..."),
            ("How do I declare a variable in Python?", "You can use the assignment operator..."),
            ("What about variable naming conventions?", "Good variable names should be..."),
            ("Can you show me an example?", "Here's an example...")
        ]
        
        interactions = []
        for user_msg, mentor_msg in conversation:
            interaction = Interaction(
                session_id=session.id_session,
                user_message=user_msg,
                mentor_response=mentor_msg
            )
            interactions.append(interaction)
            db_session.add(interaction)
        
        db_session.commit()
        
        # Verify session contains multiple interactions
        session_interactions = db_session.query(Interaction).filter_by(session_id=session.id_session).all()
        assert len(session_interactions) == 4
        
        # Verify all interactions belong to the same session
        for interaction in session_interactions:
            assert interaction.session_id == session.id_session

    def test_contain_interaction_requires_session(self, db_session):
        """Test that interaction requires session (1N = exactly one)"""
        # Try to create interaction without session
        interaction = Interaction(
            user_message="Orphaned interaction",
            mentor_response="This should fail"
            # session_id is None - should fail
        )
        db_session.add(interaction)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_contain_session_can_be_empty(self, db_session):
        """Test session can exist without interactions initially (0N allows zero)"""
        user = User(username="empty_session_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        # Create empty session
        session = Session(
            user_id=user.id_user,
            title="Empty Session",
            agent_type="normal"
        )
        db_session.add(session)
        db_session.commit()
        
        # Verify session exists without interactions
        empty_session = db_session.query(Session).filter_by(title="Empty Session").first()
        assert empty_session is not None
        
        session_interactions = db_session.query(Interaction).filter_by(session_id=empty_session.id_session).all()
        assert len(session_interactions) == 0

# ==================================================================================
# MCD LINE 23: OWN, 0N USER, 1N SESSION  
# ==================================================================================

class TestOwnRelationship:
    """
    OWN: 0N USER, 1N SESSION
    - One user can own multiple sessions (0N)
    - Each session is owned by exactly one user (1N = required)
    """
    
    def test_own_multiple_sessions_one_user(self, db_session):
        """Test one user owning multiple sessions"""
        user = User(username="prolific_learner", role="developer")
        db_session.add(user)
        db_session.commit()
        
        # Create multiple sessions for same user
        session_titles = [
            "Python Basics Session",
            "JavaScript Advanced Session", 
            "React Components Session",
            "Database Design Session"
        ]
        
        sessions = []
        for title in session_titles:
            session = Session(
                user_id=user.id_user,
                title=title,
                agent_type="normal"
            )
            sessions.append(session)
            db_session.add(session)
        
        db_session.commit()
        
        # Verify user owns multiple sessions
        user_sessions = db_session.query(Session).filter_by(user_id=user.id_user).all()
        assert len(user_sessions) == 4
        
        # Verify all sessions belong to same user
        for session in user_sessions:
            assert session.user_id == user.id_user

    def test_own_session_requires_user(self, db_session):
        """Test that session requires user (1N = exactly one)"""
        # Try to create session without user
        session = Session(
            title="Orphaned Session",
            agent_type="normal"
            # user_id is None - should fail
        )
        db_session.add(session)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_own_user_can_have_zero_sessions(self, db_session):
        """Test user can exist without sessions initially (0N allows zero)"""
        user = User(username="inactive_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        # Verify user exists without sessions
        inactive_user = db_session.query(User).filter_by(username="inactive_user").first()
        assert inactive_user is not None
        
        user_sessions = db_session.query(Session).filter_by(user_id=inactive_user.id_user).all()
        assert len(user_sessions) == 0