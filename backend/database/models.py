"""
Database models and configuration for Dev Mentor AI
Uses PostgreSQL with SQLAlchemy for Railway deployment
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, UniqueConstraint, Index, CheckConstraint, func
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
import uuid
import os

# Database configuration - PostgreSQL only
# Railway automatically provides DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/dev_mentor_ai")

# Ensure we're using PostgreSQL
if not DATABASE_URL.startswith(("postgresql://", "postgres://")):
    raise ValueError("DATABASE_URL must be a PostgreSQL connection string")

# SQLAlchemy setup - PostgreSQL only
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# PostgreSQL UUID type
UUIDType = UUID(as_uuid=True)

class User(Base):
    """
    User model - represents junior developers using the platform
    """
    __tablename__ = "users"
    
    id_user = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default='developer')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    sessions = relationship("Session", back_populates="user")
    skill_history = relationship("SkillHistory", back_populates="user")

class Session(Base):
    """
    Session model - represents a chat session between user and mentor
    """
    __tablename__ = "sessions"
    
    id_session = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    id_user = Column(UUIDType, ForeignKey("users.id_user"), nullable=False)
    title = Column(String(255), nullable=True)  # Optional session title
    agent_type = Column(String(20), nullable=False, default='normal')  # "normal", "strict", "curator", "flashcard"
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    interactions = relationship("Interaction", back_populates="session")

class Interaction(Base):
    """
    Interaction model - individual message exchanges within a session
    This data will be used to create embeddings for the vector store
    """
    __tablename__ = "interactions"
    
    id_interaction = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    id_session = Column(UUIDType, ForeignKey("sessions.id_session"), nullable=False)
    
    # Message content
    user_message = Column(Text, nullable=False)
    mentor_response = Column(Text, nullable=False)
    
    # Vector store integration
    vector_id = Column(String(255), nullable=True)  # Reference to ChromaDB embedding
    
    # Context for vector store - proper foreign key relationships
    id_intent = Column(Integer, ForeignKey("ref_intents.id_intent"), nullable=True)
    id_language = Column(Integer, ForeignKey("ref_languages.id_language"), nullable=True) 
    id_domain = Column(Integer, ForeignKey("ref_domains.id_domain"), nullable=True)
    
    # Metadata
    response_time_ms = Column(Integer, nullable=True)  # API response time for monitoring
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="interactions")
    intent = relationship("RefIntent", back_populates="interactions")
    language = relationship("RefLanguage", back_populates="interactions")
    domain = relationship("RefDomain")
    
    # Table constraints - indexes for performance
    __table_args__ = (
        Index('ix_interaction_intent_id', 'id_intent'),
        Index('ix_interaction_language_id', 'id_language'),
        Index('ix_interaction_domain_id', 'id_domain'),
    )

class MemoryEntry(Base):
    """
    Memory Entry model - tracks patterns and insights about user learning
    Used alongside vector store for personalized mentoring
    """
    __tablename__ = "memory_entries"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    id_user = Column(UUIDType, ForeignKey("users.id_user"), nullable=False)
    
    # Learning insights
    concept = Column(String(100), nullable=False)  # e.g., "react_hooks", "async_await"
    mastery_level = Column(Integer, default=1)  # 1-5 scale of understanding
    common_mistakes = Column(Text, nullable=True)  # JSON array of common errors
    learning_style = Column(String(50), nullable=True)  # e.g., "visual", "hands_on"
    
    # Tracking
    first_encountered = Column(DateTime, default=datetime.utcnow)
    last_practiced = Column(DateTime, default=datetime.utcnow)
    practice_count = Column(Integer, default=1)
    
    # Vector store reference
    vector_id = Column(String(255), nullable=True)  # Reference to Chroma embedding

class RefDomain(Base):
    """
    Reference table for learning domains
    """
    __tablename__ = "ref_domains"
    
    id_domain = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to skills
    skills = relationship("Skill", back_populates="domain")

class RefLanguage(Base):
    """
    Reference table for programming languages
    Used to classify interactions and maintain consistent vocabulary
    """
    __tablename__ = "ref_languages"
    
    id_language = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    category = Column(String(30), nullable=True)  # e.g., "Frontend", "Backend", "Framework"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to interactions
    interactions = relationship("Interaction", back_populates="language")

class RefIntent(Base):
    """
    Reference table for interaction intent types
    Classifies the purpose/type of user interactions
    """
    __tablename__ = "ref_intents"
    
    id_intent = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to interactions
    interactions = relationship("Interaction", back_populates="intent")

class Skill(Base):
    """
    Skills table - represents learning competencies to be mastered
    """
    __tablename__ = "skills"
    
    id_skill = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    id_domain = Column(Integer, ForeignKey("ref_domains.id_domain"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    domain = relationship("RefDomain", back_populates="skills")
    skill_history = relationship("SkillHistory", back_populates="skill")

class SkillHistory(Base):
    """
    Skill History table - tracks daily snapshots of user skill progression
    Used by spaced repetition algorithm to optimize learning
    """
    __tablename__ = "skill_history"
    
    id_history = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    id_user = Column(UUIDType, ForeignKey("users.id_user"), nullable=False)
    id_skill = Column(Integer, ForeignKey("skills.id_skill"), nullable=False)
    mastery_level = Column(Integer, nullable=False, default=1)
    snapshot_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="skill_history")
    skill = relationship("Skill", back_populates="skill_history")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('id_user', 'id_skill', 'snapshot_date', name='skill_history_unique_daily'),
    )

class Flashcard(Base):
    """
    Flashcard model - spaced repetition learning cards generated from interactions
    """
    __tablename__ = "flashcards"
    
    id_flashcard = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    difficulty = Column(Integer, nullable=False, default=1)  # 1-5 scale
    card_type = Column(String(50), nullable=False, default='concept')
    created_at = Column(DateTime, default=datetime.utcnow)
    next_review_date = Column(Date, nullable=False, default=date.today)
    review_count = Column(Integer, nullable=False, default=0)
    
    # Foreign keys
    id_interaction = Column(UUIDType, ForeignKey("interactions.id_interaction"), nullable=True)
    id_skill = Column(Integer, ForeignKey("skills.id_skill"), nullable=True)
    
    # Relationships
    interaction = relationship("Interaction", backref="flashcards")
    skill = relationship("Skill", backref="flashcards")

class ReviewSession(Base):
    """
    Review Session model - tracks flashcard review performance for spaced repetition
    """
    __tablename__ = "review_sessions"
    
    id_review = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    id_user = Column(UUIDType, ForeignKey("users.id_user"), nullable=False)
    id_flashcard = Column(UUIDType, ForeignKey("flashcards.id_flashcard"), nullable=False)
    success_score = Column(Integer, nullable=False)  # 0-5 scale
    response_time = Column(Integer, nullable=True)  # seconds
    review_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="review_sessions")
    flashcard = relationship("Flashcard", backref="review_sessions")

def create_tables():
    """
    Create all database tables
    This will be called during startup or migration
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

# Development helper
if __name__ == "__main__":
    print("Creating database tables...")
    create_tables()
    print("Done!")