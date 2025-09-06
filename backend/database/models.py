"""
SQLAlchemy Models for Dev Mentor AI
Complete schema with all relationships
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, UniqueConstraint, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

# ========================================
# REFERENCE TABLES
# ========================================

class RefDomain(Base):
    """Learning domains reference table"""
    __tablename__ = "ref_domains"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    skills = relationship("Skill", back_populates="domain")
    interactions = relationship("Interaction", back_populates="domain")


class RefLanguage(Base):
    """Programming languages reference table"""
    __tablename__ = "ref_languages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    category = Column(String(30))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    interactions = relationship("Interaction", back_populates="language")


class RefIntent(Base):
    """Intent types reference table"""
    __tablename__ = "ref_intents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    interactions = relationship("Interaction", back_populates="intent")


# ========================================
# CORE TABLES
# ========================================

class User(Base):
    """Platform users (developers and managers)"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    password_hash = Column(String(255))
    role = Column(String(20), nullable=False, default='developer')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(role.in_(['developer', 'manager']), name='users_role_check'),
        CheckConstraint('length(username) >= 3', name='users_username_length'),
    )
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    skill_history = relationship("SkillHistory", back_populates="user", cascade="all, delete-orphan")
    review_sessions = relationship("ReviewSession", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """Conversation sessions between users and AI agents"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255))
    agent_type = Column(String(20), nullable=False, default='normal')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(agent_type.in_(['normal', 'strict', 'curator', 'flashcard']), name='sessions_agent_type_check'),
        CheckConstraint('ended_at IS NULL OR ended_at >= created_at', name='sessions_end_after_start'),
    )
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    interactions = relationship("Interaction", back_populates="session", cascade="all, delete-orphan")


class Skill(Base):
    """Learning competencies to be mastered"""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    domain_id = Column(Integer, ForeignKey("ref_domains.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length(name) >= 2', name='skills_name_length'),
    )
    
    # Relationships
    domain = relationship("RefDomain", back_populates="skills")
    skill_history = relationship("SkillHistory", back_populates="skill")
    flashcards = relationship("Flashcard", back_populates="skill")


class Interaction(Base):
    """Individual message exchanges within sessions"""
    __tablename__ = "interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    user_message = Column(Text, nullable=False)
    mentor_response = Column(Text, nullable=False)
    vector_id = Column(String(255))  # Reference to ChromaDB
    response_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Foreign keys to reference tables
    domain_id = Column(Integer, ForeignKey("ref_domains.id"))
    language_id = Column(Integer, ForeignKey("ref_languages.id"))
    intent_id = Column(Integer, ForeignKey("ref_intents.id"))
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length(user_message) > 0', name='interactions_message_length'),
        CheckConstraint('length(mentor_response) > 0', name='interactions_response_length'),
        CheckConstraint('response_time_ms IS NULL OR response_time_ms >= 0', name='interactions_response_time_positive'),
    )
    
    # Relationships
    session = relationship("Session", back_populates="interactions")
    domain = relationship("RefDomain", back_populates="interactions")
    language = relationship("RefLanguage", back_populates="interactions")
    intent = relationship("RefIntent", back_populates="interactions")
    flashcards = relationship("Flashcard", back_populates="interaction")


class SkillHistory(Base):
    """Daily snapshots of user skill progression"""
    __tablename__ = "skill_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    mastery_level = Column(Integer, nullable=False, default=1)
    snapshot_date = Column(Date, nullable=False, default=datetime.today)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('mastery_level BETWEEN 1 AND 5', name='skill_history_mastery_range'),
        UniqueConstraint('user_id', 'skill_id', 'snapshot_date', name='skill_history_unique_daily'),
    )
    
    # Relationships
    user = relationship("User", back_populates="skill_history")
    skill = relationship("Skill", back_populates="skill_history")


class Flashcard(Base):
    """Spaced repetition learning cards"""
    __tablename__ = "flashcards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    difficulty = Column(Integer, nullable=False, default=1)
    card_type = Column(String(50), nullable=False, default='concept')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    next_review_date = Column(Date, nullable=False, default=datetime.today)
    review_count = Column(Integer, nullable=False, default=0)
    
    # Foreign keys
    interaction_id = Column(UUID(as_uuid=True), ForeignKey("interactions.id", ondelete="SET NULL"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    
    # Constraints
    __table_args__ = (
        CheckConstraint('difficulty BETWEEN 1 AND 5', name='flashcards_difficulty_range'),
        CheckConstraint(card_type.in_(['concept', 'code_completion', 'error_identification', 'application']), 
                       name='flashcards_card_type_check'),
        CheckConstraint('review_count >= 0', name='flashcards_review_count_positive'),
    )
    
    # Relationships
    interaction = relationship("Interaction", back_populates="flashcards")
    skill = relationship("Skill", back_populates="flashcards")
    review_sessions = relationship("ReviewSession", back_populates="flashcard", cascade="all, delete-orphan")


class ReviewSession(Base):
    """History of flashcard review performance"""
    __tablename__ = "review_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    flashcard_id = Column(UUID(as_uuid=True), ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False)
    success_score = Column(Integer, nullable=False)
    response_time = Column(Integer)  # in seconds
    review_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('success_score BETWEEN 0 AND 5', name='review_sessions_score_range'),
        CheckConstraint('response_time IS NULL OR response_time > 0', name='review_sessions_response_time_positive'),
    )
    
    # Relationships
    user = relationship("User", back_populates="review_sessions")
    flashcard = relationship("Flashcard", back_populates="review_sessions")