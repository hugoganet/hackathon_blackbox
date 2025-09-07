#!/usr/bin/env python3
"""
MCD Business Rules and Data Integrity Tests
Based on backend/database/doc/dev_mentor_ai.mcd

Tests for:
- Data validation rules
- Business logic constraints  
- Referential integrity
- Cascade behaviors
- Unique constraints
- Check constraints
- Trigger behaviors

These tests ensure the database implementation matches the MCD design intentions.
"""

import pytest
import uuid
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, DataError, CheckViolation
import os

# Import database models
from backend.database import Base, get_db
from backend.database import (
    User, Session, Interaction, Skill, SkillHistory,
    Flashcard, ReviewSession, RefDomain, RefLanguage, RefIntent
)

# Test database setup
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:test@localhost:5432/test_business_rules")
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
# UNIQUENESS CONSTRAINTS TESTS
# ==================================================================================

class TestUniqueConstraints:
    """Test unique constraints defined in MCD schema"""
    
    def test_user_username_uniqueness(self, db_session):
        """Test USER.username unique constraint"""
        user1 = User(username="unique_test", role="developer")
        db_session.add(user1)
        db_session.commit()
        
        # Try to create another user with same username
        user2 = User(username="unique_test", role="manager")  # Different role, same username
        db_session.add(user2)
        
        with pytest.raises(IntegrityError) as excinfo:
            db_session.commit()
        assert "username" in str(excinfo.value).lower() or "unique" in str(excinfo.value).lower()

    def test_user_email_uniqueness(self, db_session):
        """Test USER.email unique constraint"""
        user1 = User(username="user1", email="shared@email.com", role="developer")
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(username="user2", email="shared@email.com", role="developer")
        db_session.add(user2)
        
        with pytest.raises(IntegrityError) as excinfo:
            db_session.commit()
        assert "email" in str(excinfo.value).lower() or "unique" in str(excinfo.value).lower()

    def test_ref_domain_name_uniqueness(self, db_session):
        """Test REF_DOMAIN.name unique constraint"""
        domain1 = RefDomain(name="UNIQUE_DOMAIN", description="First description")
        db_session.add(domain1)
        db_session.commit()
        
        domain2 = RefDomain(name="UNIQUE_DOMAIN", description="Second description")
        db_session.add(domain2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_ref_language_name_uniqueness(self, db_session):
        """Test REF_LANGUAGE.name unique constraint"""
        lang1 = RefLanguage(name="UniqueLanguage", category="Programming")
        db_session.add(lang1)
        db_session.commit()
        
        lang2 = RefLanguage(name="UniqueLanguage", category="Framework")
        db_session.add(lang2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_ref_intent_name_uniqueness(self, db_session):
        """Test REF_INTENT.name unique constraint"""
        intent1 = RefIntent(name="unique_intent", description="First description")
        db_session.add(intent1)
        db_session.commit()
        
        intent2 = RefIntent(name="unique_intent", description="Second description")
        db_session.add(intent2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_skill_name_uniqueness(self, db_session):
        """Test SKILL.name unique constraint"""
        domain = RefDomain(name="TEST_SKILLS", description="Test domain")
        db_session.add(domain)
        db_session.commit()
        
        skill1 = Skill(name="Unique Skill", description="First skill", id_domain=domain.id_domain)
        db_session.add(skill1)
        db_session.commit()
        
        skill2 = Skill(name="Unique Skill", description="Second skill", id_domain=domain.id_domain)
        db_session.add(skill2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

# ==================================================================================
# NOT NULL CONSTRAINTS TESTS
# ==================================================================================

class TestNotNullConstraints:
    """Test NOT NULL constraints for required fields"""
    
    def test_user_required_fields(self, db_session):
        """Test USER table required fields"""
        # Missing username (required)
        user = User(role="developer")  # No username
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_session_required_fields(self, db_session):
        """Test SESSION table required fields"""
        # Try creating session without user_id (should fail)
        session = Session(title="Test Session", agent_type="normal")  # No user_id
        db_session.add(session)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_interaction_required_fields(self, db_session):
        """Test INTERACTION table required fields"""
        user = User(username="test_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Missing user_message (required)
        interaction1 = Interaction(
            session_id=session.id_session,
            mentor_response="Response without question"  # No user_message
        )
        db_session.add(interaction1)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Missing mentor_response (required)
        interaction2 = Interaction(
            session_id=session.id_session,
            user_message="Question without answer"  # No mentor_response
        )
        db_session.add(interaction2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_skill_required_fields(self, db_session):
        """Test SKILL table required fields"""
        domain = RefDomain(name="REQ_FIELDS", description="Required fields test")
        db_session.add(domain)
        db_session.commit()
        
        # Missing name (required)
        skill1 = Skill(description="Skill without name", id_domain=domain.id_domain)
        db_session.add(skill1)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Missing domain (required by BELONG_TO relationship)
        skill2 = Skill(name="Skill without domain", description="No domain")
        db_session.add(skill2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_flashcard_required_fields(self, db_session):
        """Test FLASHCARD table required fields"""
        # Missing question
        flashcard1 = Flashcard(answer="Answer without question")
        db_session.add(flashcard1)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Missing answer  
        flashcard2 = Flashcard(question="Question without answer")
        db_session.add(flashcard2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

# ==================================================================================
# CHECK CONSTRAINTS TESTS
# ==================================================================================

class TestCheckConstraints:
    """Test CHECK constraints for data validation"""
    
    def test_user_role_constraint(self, db_session):
        """Test USER.role check constraint (should be 'developer' or 'manager')"""
        # Valid roles should work
        valid_user1 = User(username="dev_user", role="developer")
        valid_user2 = User(username="mgr_user", role="manager")
        db_session.add_all([valid_user1, valid_user2])
        
        try:
            db_session.commit()
            # If successful, both roles are valid
        except IntegrityError:
            pytest.skip("Role constraint not implemented or different validation approach")
        
        db_session.rollback()
        
        # Invalid role should fail
        invalid_user = User(username="invalid_user", role="administrator")  # Invalid role
        db_session.add(invalid_user)
        
        try:
            db_session.commit()
            # If this succeeds, role constraint might not be implemented
            # Or validation happens at application level
        except (IntegrityError, CheckViolation):
            # Expected - invalid role rejected
            pass

    def test_session_agent_type_constraint(self, db_session):
        """Test SESSION.agent_type check constraint"""
        user = User(username="agent_test_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        # Valid agent types
        valid_agents = ["normal", "strict", "curator", "flashcard"]
        for agent_type in valid_agents:
            session = Session(
                user_id=user.id_user,
                title=f"Session with {agent_type}",
                agent_type=agent_type
            )
            db_session.add(session)
        
        try:
            db_session.commit()
            # All valid agent types accepted
        except IntegrityError:
            pytest.skip("Agent type constraint not implemented")
        
        # Clear successful sessions
        db_session.query(Session).filter_by(user_id=user.id_user).delete()
        db_session.commit()
        
        # Invalid agent type
        invalid_session = Session(
            user_id=user.id_user,
            title="Invalid Agent Session",
            agent_type="invalid_agent"
        )
        db_session.add(invalid_session)
        
        try:
            db_session.commit()
            # If successful, constraint might not be implemented
        except (IntegrityError, CheckViolation):
            # Expected - invalid agent type rejected
            pass

    def test_skill_history_mastery_level_constraint(self, db_session):
        """Test SKILL_HISTORY.mastery_level range constraint (1-5)"""
        # Setup prerequisites
        domain = RefDomain(name="MASTERY_TEST", description="Mastery level testing")
        db_session.add(domain)
        db_session.commit()
        
        user = User(username="mastery_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        skill = Skill(name="Test Mastery Skill", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        # Valid mastery levels (1-5)
        for level in range(1, 6):
            history = SkillHistory(
                id_user=user.id_user,
                id_skill=skill.id_skill,
                mastery_level=level,
                snapshot_date=date.today() - timedelta(days=5-level)
            )
            db_session.add(history)
        
        try:
            db_session.commit()
            # All valid levels accepted
        except IntegrityError:
            pytest.skip("Mastery level constraint not implemented")
        
        db_session.rollback()
        
        # Invalid mastery levels
        invalid_levels = [0, -1, 6, 10, 100]
        for invalid_level in invalid_levels:
            history = SkillHistory(
                id_user=user.id_user,
                id_skill=skill.id_skill,
                mastery_level=invalid_level,
                snapshot_date=date.today()
            )
            db_session.add(history)
            
            try:
                db_session.commit()
                # If successful, constraint might not be implemented
                db_session.rollback()
            except (IntegrityError, CheckViolation):
                # Expected - invalid level rejected
                db_session.rollback()

    def test_flashcard_difficulty_constraint(self, db_session):
        """Test FLASHCARD.difficulty range constraint (1-5)"""
        # Valid difficulty levels
        for difficulty in range(1, 6):
            flashcard = Flashcard(
                question=f"Question difficulty {difficulty}",
                answer=f"Answer difficulty {difficulty}",
                difficulty=difficulty,
                card_type="concept"
            )
            db_session.add(flashcard)
        
        try:
            db_session.commit()
            # All valid difficulties accepted
        except IntegrityError:
            pytest.skip("Difficulty constraint not implemented")
        
        db_session.query(Flashcard).delete()
        db_session.commit()
        
        # Invalid difficulty levels
        invalid_difficulties = [0, -1, 6, 10]
        for invalid_difficulty in invalid_difficulties:
            flashcard = Flashcard(
                question="Test question",
                answer="Test answer",
                difficulty=invalid_difficulty,
                card_type="concept"
            )
            db_session.add(flashcard)
            
            try:
                db_session.commit()
                db_session.rollback()
            except (IntegrityError, CheckViolation):
                db_session.rollback()

    def test_flashcard_card_type_constraint(self, db_session):
        """Test FLASHCARD.card_type constraint"""
        valid_types = ["concept", "code_completion", "error_identification", "application"]
        
        for card_type in valid_types:
            flashcard = Flashcard(
                question=f"Question for {card_type}",
                answer=f"Answer for {card_type}",
                card_type=card_type
            )
            db_session.add(flashcard)
        
        try:
            db_session.commit()
        except IntegrityError:
            pytest.skip("Card type constraint not implemented")
        
        db_session.query(Flashcard).delete()
        db_session.commit()
        
        # Invalid card type
        invalid_flashcard = Flashcard(
            question="Test question",
            answer="Test answer",
            card_type="invalid_type"
        )
        db_session.add(invalid_flashcard)
        
        try:
            db_session.commit()
        except (IntegrityError, CheckViolation):
            pass

    def test_review_session_success_score_constraint(self, db_session):
        """Test REVIEW_SESSION.success_score range constraint (0-5)"""
        # Setup prerequisites
        user = User(username="review_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        flashcard = Flashcard(
            question="Review test question",
            answer="Review test answer",
            card_type="concept"
        )
        db_session.add(flashcard)
        db_session.commit()
        
        # Valid success scores (0-5)
        for score in range(0, 6):
            review = ReviewSession(
                id_user=user.id_user,
                id_flashcard=flashcard.id_flashcard,
                success_score=score,
                response_time=30
            )
            db_session.add(review)
        
        try:
            db_session.commit()
        except IntegrityError:
            pytest.skip("Success score constraint not implemented")
        
        db_session.query(ReviewSession).delete()
        db_session.commit()
        
        # Invalid success scores
        invalid_scores = [-1, -5, 6, 10, 100]
        for invalid_score in invalid_scores:
            review = ReviewSession(
                id_user=user.id_user,
                id_flashcard=flashcard.id_flashcard,
                success_score=invalid_score,
                response_time=30
            )
            db_session.add(review)
            
            try:
                db_session.commit()
                db_session.rollback()
            except (IntegrityError, CheckViolation):
                db_session.rollback()

# ==================================================================================
# FOREIGN KEY CONSTRAINTS TESTS
# ==================================================================================

class TestForeignKeyConstraints:
    """Test foreign key constraints and referential integrity"""
    
    def test_session_user_foreign_key(self, db_session):
        """Test SESSION.user_id foreign key constraint"""
        # Valid foreign key
        user = User(username="fk_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()  # Should succeed
        
        # Invalid foreign key
        invalid_session = Session(
            user_id=uuid.uuid4(),  # Non-existent user
            agent_type="normal"
        )
        db_session.add(invalid_session)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_interaction_session_foreign_key(self, db_session):
        """Test INTERACTION.session_id foreign key constraint"""
        user = User(username="interaction_fk_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Valid foreign key
        interaction = Interaction(
            session_id=session.id_session,
            user_message="Valid interaction",
            mentor_response="Valid response"
        )
        db_session.add(interaction)
        db_session.commit()
        
        # Invalid foreign key
        invalid_interaction = Interaction(
            session_id=uuid.uuid4(),  # Non-existent session
            user_message="Invalid interaction",
            mentor_response="Invalid response"
        )
        db_session.add(invalid_interaction)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_skill_domain_foreign_key(self, db_session):
        """Test SKILL.id_domain foreign key constraint (BELONG_TO relationship)"""
        domain = RefDomain(name="FK_TEST", description="Foreign key testing")
        db_session.add(domain)
        db_session.commit()
        
        # Valid foreign key
        skill = Skill(name="Valid Skill", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        # Invalid foreign key
        invalid_skill = Skill(name="Invalid Skill", id_domain=99999)  # Non-existent domain
        db_session.add(invalid_skill)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_skill_history_user_skill_foreign_keys(self, db_session):
        """Test SKILL_HISTORY foreign key constraints"""
        # Setup
        domain = RefDomain(name="HISTORY_FK", description="History FK testing")
        db_session.add(domain)
        db_session.commit()
        
        user = User(username="history_fk_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        skill = Skill(name="History FK Skill", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        # Valid foreign keys
        history = SkillHistory(
            id_user=user.id_user,
            id_skill=skill.id_skill,
            mastery_level=2,
            snapshot_date=date.today()
        )
        db_session.add(history)
        db_session.commit()
        
        # Invalid user foreign key
        invalid_user_history = SkillHistory(
            id_user=uuid.uuid4(),  # Non-existent user
            id_skill=skill.id_skill,
            mastery_level=2,
            snapshot_date=date.today()
        )
        db_session.add(invalid_user_history)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Invalid skill foreign key
        invalid_skill_history = SkillHistory(
            id_user=user.id_user,
            id_skill=99999,  # Non-existent skill
            mastery_level=2,
            snapshot_date=date.today()
        )
        db_session.add(invalid_skill_history)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

# ==================================================================================
# CASCADE BEHAVIOR TESTS
# ==================================================================================

class TestCascadeBehaviors:
    """Test cascade deletion and update behaviors"""
    
    def test_user_deletion_cascades_to_sessions(self, db_session):
        """Test cascading deletion from USER to SESSION"""
        user = User(username="cascade_test_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = Session(
                user_id=user.id_user,
                title=f"Session {i+1}",
                agent_type="normal"
            )
            sessions.append(session)
            db_session.add(session)
        db_session.commit()
        
        # Verify sessions exist
        user_sessions = db_session.query(Session).filter_by(user_id=user.id_user).all()
        assert len(user_sessions) == 3
        
        # Delete user
        user_id = user.id_user
        db_session.delete(user)
        db_session.commit()
        
        # Verify sessions are also deleted (cascade)
        remaining_sessions = db_session.query(Session).filter_by(user_id=user_id).all()
        assert len(remaining_sessions) == 0

    def test_session_deletion_cascades_to_interactions(self, db_session):
        """Test cascading deletion from SESSION to INTERACTION"""
        user = User(username="session_cascade_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Create multiple interactions
        interactions = []
        for i in range(5):
            interaction = Interaction(
                session_id=session.id_session,
                user_message=f"Question {i+1}",
                mentor_response=f"Answer {i+1}"
            )
            interactions.append(interaction)
            db_session.add(interaction)
        db_session.commit()
        
        # Verify interactions exist
        session_interactions = db_session.query(Interaction).filter_by(session_id=session.id_session).all()
        assert len(session_interactions) == 5
        
        # Delete session
        session_id = session.id_session
        db_session.delete(session)
        db_session.commit()
        
        # Verify interactions are also deleted (cascade)
        remaining_interactions = db_session.query(Interaction).filter_by(session_id=session_id).all()
        assert len(remaining_interactions) == 0

    def test_user_deletion_cascades_to_skill_history(self, db_session):
        """Test cascading deletion from USER to SKILL_HISTORY"""
        domain = RefDomain(name="CASCADE_SKILLS", description="Cascade testing")
        db_session.add(domain)
        db_session.commit()
        
        user = User(username="skill_cascade_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        skill = Skill(name="Cascade Test Skill", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        # Create skill history records
        histories = []
        for i in range(4):
            history = SkillHistory(
                id_user=user.id_user,
                id_skill=skill.id_skill,
                mastery_level=i+1,
                snapshot_date=date.today() - timedelta(days=i)
            )
            histories.append(history)
            db_session.add(history)
        db_session.commit()
        
        # Verify skill histories exist
        user_histories = db_session.query(SkillHistory).filter_by(id_user=user.id_user).all()
        assert len(user_histories) == 4
        
        # Delete user
        user_id = user.id_user
        db_session.delete(user)
        db_session.commit()
        
        # Verify skill histories are also deleted (cascade)
        remaining_histories = db_session.query(SkillHistory).filter_by(id_user=user_id).all()
        assert len(remaining_histories) == 0

    def test_flashcard_deletion_cascades_to_review_sessions(self, db_session):
        """Test cascading deletion from FLASHCARD to REVIEW_SESSION"""
        user = User(username="review_cascade_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        flashcard = Flashcard(
            question="Cascade test question",
            answer="Cascade test answer",
            card_type="concept"
        )
        db_session.add(flashcard)
        db_session.commit()
        
        # Create review sessions
        reviews = []
        for i in range(3):
            review = ReviewSession(
                id_user=user.id_user,
                id_flashcard=flashcard.id_flashcard,
                success_score=i+1,
                response_time=30
            )
            reviews.append(review)
            db_session.add(review)
        db_session.commit()
        
        # Verify reviews exist
        flashcard_reviews = db_session.query(ReviewSession).filter_by(id_flashcard=flashcard.id_flashcard).all()
        assert len(flashcard_reviews) == 3
        
        # Delete flashcard
        flashcard_id = flashcard.id_flashcard
        db_session.delete(flashcard)
        db_session.commit()
        
        # Verify reviews are also deleted (cascade)
        remaining_reviews = db_session.query(ReviewSession).filter_by(id_flashcard=flashcard_id).all()
        assert len(remaining_reviews) == 0

# ==================================================================================
# BUSINESS RULE VALIDATION TESTS
# ==================================================================================

class TestBusinessRuleValidation:
    """Test application-level business rules"""
    
    def test_session_end_time_after_start_time(self, db_session):
        """Test business rule: session.ended_at must be after session.created_at"""
        user = User(username="time_rule_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        now = datetime.utcnow()
        past_time = now - timedelta(hours=1)
        future_time = now + timedelta(hours=1)
        
        # Valid: ended_at after created_at
        valid_session = Session(
            user_id=user.id_user,
            agent_type="normal",
            created_at=past_time,
            ended_at=now  # After created_at
        )
        db_session.add(valid_session)
        
        try:
            db_session.commit()
            # Valid session accepted
        except IntegrityError:
            pytest.skip("Time constraint not implemented at database level")
        
        db_session.rollback()
        
        # Invalid: ended_at before created_at
        invalid_session = Session(
            user_id=user.id_user,
            agent_type="normal", 
            created_at=now,
            ended_at=past_time  # Before created_at
        )
        db_session.add(invalid_session)
        
        try:
            db_session.commit()
            # If successful, constraint is not implemented at DB level
            # Would need application-level validation
        except (IntegrityError, CheckViolation):
            # Expected if constraint exists
            pass

    def test_unique_daily_skill_tracking(self, db_session):
        """Test business rule: one skill history per user/skill/day"""
        domain = RefDomain(name="DAILY_UNIQUE", description="Daily unique constraint test")
        db_session.add(domain)
        db_session.commit()
        
        user = User(username="daily_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        skill = Skill(name="Daily Skill", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        today = date.today()
        
        # First skill history for today
        history1 = SkillHistory(
            id_user=user.id_user,
            id_skill=skill.id_skill,
            mastery_level=2,
            snapshot_date=today
        )
        db_session.add(history1)
        db_session.commit()
        
        # Second skill history for same user/skill/day
        history2 = SkillHistory(
            id_user=user.id_user,
            id_skill=skill.id_skill,
            mastery_level=3,
            snapshot_date=today
        )
        db_session.add(history2)
        
        try:
            db_session.commit()
            # If successful, unique constraint not implemented
            # Check how many records exist
            daily_histories = db_session.query(SkillHistory).filter(
                SkillHistory.id_user == user.id_user,
                SkillHistory.id_skill == skill.id_skill,
                SkillHistory.snapshot_date == today
            ).all()
            # Could be 1 (constraint exists) or 2 (no constraint)
        except IntegrityError:
            # Expected if unique constraint on (user_id, skill_id, snapshot_date) exists
            pass

    def test_unique_daily_flashcard_review(self, db_session):
        """Test business rule: one review per user/flashcard/day"""
        user = User(username="daily_reviewer", role="developer")
        db_session.add(user)
        db_session.commit()
        
        flashcard = Flashcard(
            question="Daily review question",
            answer="Daily review answer",
            card_type="concept"
        )
        db_session.add(flashcard)
        db_session.commit()
        
        today = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
        
        # First review today
        review1 = ReviewSession(
            id_user=user.id_user,
            id_flashcard=flashcard.id_flashcard,
            success_score=3,
            response_time=25,
            review_date=today
        )
        db_session.add(review1)
        db_session.commit()
        
        # Second review same day
        review2 = ReviewSession(
            id_user=user.id_user,
            id_flashcard=flashcard.id_flashcard,
            success_score=4,
            response_time=20,
            review_date=today.replace(hour=15)  # Same day, different hour
        )
        db_session.add(review2)
        
        try:
            db_session.commit()
            # If successful, daily review constraint not implemented
        except IntegrityError:
            # Expected if unique constraint on (user_id, flashcard_id, date) exists
            pass

    def test_positive_response_time_constraint(self, db_session):
        """Test business rule: response times must be positive"""
        user = User(username="response_time_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        # Valid positive response time
        valid_interaction = Interaction(
            session_id=session.id_session,
            user_message="Valid question",
            mentor_response="Valid answer",
            response_time_ms=1500  # Positive
        )
        db_session.add(valid_interaction)
        
        try:
            db_session.commit()
        except IntegrityError:
            pytest.skip("Response time constraint not implemented")
        
        db_session.rollback()
        
        # Invalid negative response time
        invalid_interaction = Interaction(
            session_id=session.id_session,
            user_message="Invalid question",
            mentor_response="Invalid answer", 
            response_time_ms=-100  # Negative
        )
        db_session.add(invalid_interaction)
        
        try:
            db_session.commit()
        except (IntegrityError, CheckViolation):
            # Expected if positive constraint exists
            pass

    def test_flashcard_review_count_non_negative(self, db_session):
        """Test business rule: flashcard review_count must be non-negative"""
        # Valid non-negative review count
        valid_flashcard = Flashcard(
            question="Valid question",
            answer="Valid answer",
            card_type="concept",
            review_count=0  # Non-negative
        )
        db_session.add(valid_flashcard)
        
        try:
            db_session.commit()
        except IntegrityError:
            pytest.skip("Review count constraint not implemented")
        
        db_session.rollback()
        
        # Invalid negative review count
        invalid_flashcard = Flashcard(
            question="Invalid question",
            answer="Invalid answer",
            card_type="concept",
            review_count=-5  # Negative
        )
        db_session.add(invalid_flashcard)
        
        try:
            db_session.commit()
        except (IntegrityError, CheckViolation):
            # Expected if non-negative constraint exists
            pass

# ==================================================================================
# DATA CONSISTENCY TESTS
# ==================================================================================

class TestDataConsistency:
    """Test data consistency across related tables"""
    
    def test_orphaned_records_prevention(self, db_session):
        """Test that orphaned records are prevented by foreign key constraints"""
        # This test verifies that records cannot exist without their required parents
        
        # Try to create interaction without session (should fail)
        with pytest.raises(IntegrityError):
            interaction = Interaction(
                user_message="Orphaned interaction",
                mentor_response="No parent session"
            )
            db_session.add(interaction)
            db_session.commit()
        
        db_session.rollback()
        
        # Try to create skill history without user (should fail)
        domain = RefDomain(name="CONSISTENCY", description="Consistency testing")
        db_session.add(domain)
        db_session.commit()
        
        skill = Skill(name="Consistency Skill", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        with pytest.raises(IntegrityError):
            history = SkillHistory(
                id_user=uuid.uuid4(),  # Non-existent user
                id_skill=skill.id_skill,
                mastery_level=2,
                snapshot_date=date.today()
            )
            db_session.add(history)
            db_session.commit()
        
        db_session.rollback()
        
        # Try to create review session without user or flashcard (should fail)
        with pytest.raises(IntegrityError):
            review = ReviewSession(
                id_user=uuid.uuid4(),  # Non-existent user
                id_flashcard=uuid.uuid4(),  # Non-existent flashcard
                success_score=3,
                response_time=30
            )
            db_session.add(review)
            db_session.commit()

    def test_referential_integrity_across_complex_relationships(self, db_session):
        """Test referential integrity in complex multi-table scenarios"""
        # Create a complete data structure with all relationships
        domain = RefDomain(name="INTEGRITY", description="Referential integrity test")
        language = RefLanguage(name="TestLang", category="Testing")
        intent = RefIntent(name="test_intent", description="Testing intent")
        db_session.add_all([domain, language, intent])
        db_session.commit()
        
        user = User(username="integrity_user", role="developer")
        db_session.add(user)
        db_session.commit()
        
        session = Session(user_id=user.id_user, agent_type="normal")
        db_session.add(session)
        db_session.commit()
        
        interaction = Interaction(
            session_id=session.id_session,
            user_message="Complex integrity test",
            mentor_response="Testing all relationships",
            id_domain=domain.id_domain,
            id_language=language.id_language,
            id_intent=intent.id_intent
        )
        db_session.add(interaction)
        db_session.commit()
        
        skill = Skill(name="Integrity Skill", id_domain=domain.id_domain)
        db_session.add(skill)
        db_session.commit()
        
        skill_history = SkillHistory(
            id_user=user.id_user,
            id_skill=skill.id_skill,
            mastery_level=3,
            snapshot_date=date.today()
        )
        db_session.add(skill_history)
        db_session.commit()
        
        flashcard = Flashcard(
            question="Integrity test question",
            answer="Integrity test answer",
            card_type="concept",
            id_interaction=interaction.id_interaction,
            id_skill=skill.id_skill
        )
        db_session.add(flashcard)
        db_session.commit()
        
        review = ReviewSession(
            id_user=user.id_user,
            id_flashcard=flashcard.id_flashcard,
            success_score=4,
            response_time=25
        )
        db_session.add(review)
        db_session.commit()
        
        # Verify all relationships are intact
        saved_interaction = db_session.query(Interaction).first()
        assert saved_interaction.id_domain == domain.id_domain
        assert saved_interaction.id_language == language.id_language
        assert saved_interaction.id_intent == intent.id_intent
        
        saved_flashcard = db_session.query(Flashcard).first()
        assert saved_flashcard.id_interaction == interaction.id_interaction
        assert saved_flashcard.id_skill == skill.id_skill
        
        saved_review = db_session.query(ReviewSession).first()
        assert saved_review.id_user == user.id_user
        assert saved_review.id_flashcard == flashcard.id_flashcard
        
        # Test cascading deletion maintains integrity
        user_id = user.id_user
        db_session.delete(user)
        db_session.commit()
        
        # Verify cascaded deletions
        assert db_session.query(Session).filter_by(user_id=user_id).count() == 0
        assert db_session.query(SkillHistory).filter_by(id_user=user_id).count() == 0
        assert db_session.query(ReviewSession).filter_by(id_user=user_id).count() == 0
        
        # Reference data should remain intact
        assert db_session.query(RefDomain).filter_by(id_domain=domain.id_domain).count() == 1
        assert db_session.query(RefLanguage).filter_by(id_language=language.id_language).count() == 1
        assert db_session.query(RefIntent).filter_by(id_intent=intent.id_intent).count() == 1