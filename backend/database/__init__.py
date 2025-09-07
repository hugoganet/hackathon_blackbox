# Database package initialization
# Import all models and database utilities for easy access

from typing import Generator
from sqlalchemy.orm import Session as DBSession
from .models import (
    Base, SessionLocal, engine, create_engine, create_tables,
    User, Conversation, Interaction, MemoryEntry, Skill, SkillHistory, RefDomain,
    RefLanguage, RefIntent, Flashcard, ReviewSession
)

# Alias for MCD schema compatibility
Session = Conversation

def get_db() -> Generator[DBSession, None, None]:
    """
    Dependency function for FastAPI to get database session
    Usage: def endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()