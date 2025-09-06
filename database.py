"""
Database models and configuration for Dev Mentor AI
Uses PostgreSQL with SQLAlchemy for Railway deployment
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import os
from typing import Generator

# Database configuration
# Railway automatically provides DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev_mentor.db")  # Fallback to SQLite for local dev

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    # PostgreSQL specific settings (ignored by SQLite)
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes  
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models

class User(Base):
    """
    User model - represents junior developers using the platform
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship to conversations
    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    """
    Conversation model - represents a chat session between user and mentor
    """
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=False, index=True)
    agent_type = Column(String(20), nullable=False)  # "normal" or "strict"
    title = Column(String(255), nullable=True)  # Optional conversation title
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    interactions = relationship("Interaction", back_populates="conversation")

class Interaction(Base):
    """
    Interaction model - individual message exchanges within a conversation
    This data will be used to create embeddings for the vector store
    """
    __tablename__ = "interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    
    # Message content
    user_message = Column(Text, nullable=False)
    mentor_response = Column(Text, nullable=False)
    
    # Context for vector store
    user_intent = Column(String(100), nullable=True)  # Classified intent (e.g., "debugging", "concept_explanation")
    programming_language = Column(String(50), nullable=True)  # e.g., "javascript", "python"
    difficulty_level = Column(String(20), nullable=True)  # e.g., "beginner", "intermediate"
    
    # Metadata
    response_time_ms = Column(Integer, nullable=True)  # API response time for monitoring
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Vector store integration
    embedding_created = Column(Boolean, default=False)  # Track if embedding was created
    
    # Relationship
    conversation = relationship("Conversation", back_populates="interactions")

class MemoryEntry(Base):
    """
    Memory Entry model - tracks patterns and insights about user learning
    Used alongside vector store for personalized mentoring
    """
    __tablename__ = "memory_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
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

# Database utility functions

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session
    Usage: def endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all database tables
    This will be called during startup or migration
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def get_user_by_username(db: Session, username: str) -> User:
    """
    Get user by username, create if doesn't exist
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def create_conversation(db: Session, user_id: str, session_id: str, agent_type: str) -> Conversation:
    """
    Create new conversation record
    """
    conversation = Conversation(
        user_id=user_id,
        session_id=session_id,
        agent_type=agent_type
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

def save_interaction(
    db: Session, 
    conversation_id: str, 
    user_message: str, 
    mentor_response: str,
    response_time_ms: int = None
) -> Interaction:
    """
    Save interaction to database for memory and analytics
    """
    interaction = Interaction(
        conversation_id=conversation_id,
        user_message=user_message,
        mentor_response=mentor_response,
        response_time_ms=response_time_ms
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction

# Development helper
if __name__ == "__main__":
    print("Creating database tables...")
    create_tables()
    print("Done!")