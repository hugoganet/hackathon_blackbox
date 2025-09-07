"""
Database models and configuration for Dev Mentor AI
Uses PostgreSQL with SQLAlchemy for Railway deployment
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
import uuid
import os
from typing import Generator, List, Optional

# Database configuration - PostgreSQL only
# Railway automatically provides DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required. This application requires PostgreSQL.")

if not DATABASE_URL.startswith("postgresql"):
    raise ValueError("Only PostgreSQL databases are supported. Please provide a PostgreSQL DATABASE_URL.")

# PostgreSQL-only SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models

# PostgreSQL UUID column type
UUIDType = UUID(as_uuid=True)

class User(Base):
    """
    User model - represents junior developers using the platform
    """
    __tablename__ = "users"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    skill_history = relationship("SkillHistory", back_populates="user")

class Conversation(Base):
    """
    Conversation model - represents a chat session between user and mentor
    """
    __tablename__ = "conversations"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=False)
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
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUIDType, ForeignKey("conversations.id"), nullable=False)
    
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
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=False)
    
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
    id_user = Column(UUIDType, ForeignKey("users.id"), nullable=False)
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
    # Handle UUID for PostgreSQL
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
    conversation_id = uuid.uuid4()
    
    conversation = Conversation(
        id=conversation_id,
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
    # Handle UUID for PostgreSQL
    if isinstance(conversation_id, str):
        conversation_id = uuid.UUID(conversation_id)
    interaction_id = uuid.uuid4()
    
    interaction = Interaction(
        id=interaction_id,
        conversation_id=conversation_id,
        user_message=user_message,
        mentor_response=mentor_response,
        response_time_ms=response_time_ms
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction

# Skill tracking and mapping functions

def create_or_update_skill(db: Session, skill_name: str, description: str = None, domain_name: str = "SYNTAX") -> Skill:
    """
    Create or update a skill in the database
    """
    # First try to get existing skill
    skill = db.query(Skill).filter(Skill.name == skill_name).first()
    if skill:
        return skill
    
    # Get or create domain
    domain = db.query(RefDomain).filter(RefDomain.name == domain_name).first()
    if not domain:
        domain = RefDomain(name=domain_name, description=f"Auto-created domain: {domain_name}")
        db.add(domain)
        db.flush()  # Get the ID without committing
    
    # Create new skill
    skill = Skill(
        name=skill_name,
        description=description or f"Auto-created skill: {skill_name}",
        id_domain=domain.id_domain
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill

def update_skill_history(db: Session, user_id: str, skill_name: str, confidence: float, domain_name: str = "SYNTAX") -> SkillHistory:
    """
    Update skill history for a user based on curator analysis
    """
    # Convert confidence (0.0-1.0) to mastery level (1-5)
    mastery_level = max(1, min(5, int(confidence * 4) + 1))
    
    # Get or create skill
    skill = create_or_update_skill(db, skill_name, domain_name=domain_name)
    
    # Get user UUID for PostgreSQL
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    
    # Check for existing skill history today
    today = date.today()
    existing_history = db.query(SkillHistory).filter(
        SkillHistory.id_user == user_uuid,
        SkillHistory.id_skill == skill.id_skill,
        SkillHistory.snapshot_date == today
    ).first()
    
    if existing_history:
        # Update existing entry with higher mastery level
        if mastery_level > existing_history.mastery_level:
            existing_history.mastery_level = mastery_level
            db.commit()
            db.refresh(existing_history)
        return existing_history
    else:
        # Create new skill history entry
        history_id = uuid.uuid4()
        
        skill_history = SkillHistory(
            id_history=history_id,
            id_user=user_uuid,
            id_skill=skill.id_skill,
            mastery_level=mastery_level,
            snapshot_date=today
        )
        db.add(skill_history)
        db.commit()
        db.refresh(skill_history)
        return skill_history

def get_user_skill_progression(db: Session, user_id: str, limit: int = 20) -> List[dict]:
    """
    Get user's skill progression history
    """
    # Handle UUID for PostgreSQL
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    
    # Query skill history with skill names
    skill_histories = db.query(SkillHistory, Skill.name, RefDomain.name.label("domain_name")).join(
        Skill, SkillHistory.id_skill == Skill.id_skill
    ).join(
        RefDomain, Skill.id_domain == RefDomain.id_domain
    ).filter(
        SkillHistory.id_user == user_uuid
    ).order_by(
        SkillHistory.snapshot_date.desc()
    ).limit(limit).all()
    
    return [
        {
            "skill_name": skill_name,
            "domain": domain_name,
            "mastery_level": skill_history.mastery_level,
            "snapshot_date": skill_history.snapshot_date.isoformat(),
            "created_at": skill_history.created_at.isoformat()
        }
        for skill_history, skill_name, domain_name in skill_histories
    ]

def process_curator_analysis(db: Session, user_id: str, curator_analysis: dict) -> dict:
    """
    Process curator analysis results and update skill tracking
    """
    results = {
        "skills_updated": [],
        "new_skills_created": [],
        "skill_histories_created": 0
    }
    
    # Map curator skills to database skills with domain classification
    skill_domain_mapping = {
        # JavaScript/Programming Fundamentals
        "variable_declaration": "SYNTAX",
        "let_keyword": "SYNTAX", 
        "hoisting": "SYNTAX",
        "temporal_dead_zone": "SYNTAX",
        "function_syntax": "SYNTAX",
        "conditional_logic": "LOGIC",
        "loop_structures": "LOGIC",
        
        # React/Frontend
        "react_hooks": "FRAMEWORKS",
        "useState": "FRAMEWORKS",
        "useEffect": "FRAMEWORKS",
        "state_updates": "FRAMEWORKS",
        "react_rendering": "FRAMEWORKS",
        "component_design": "ARCHITECTURE",
        
        # Database
        "sql_queries": "DATABASES",
        "joins": "DATABASES", 
        "aggregate_functions": "DATABASES",
        "database_relationships": "DATABASES",
        
        # Error Handling & Debugging
        "error_handling": "DEBUGGING",
        "async_await": "SYNTAX",
        "debugging": "DEBUGGING",
        
        # Performance & Architecture
        "performance": "PERFORMANCE",
        "system_design": "ARCHITECTURE",
        "microservices": "ARCHITECTURE",
        "event_sourcing": "ARCHITECTURE",
    }
    
    # Process each skill from curator analysis
    for skill_name in curator_analysis.get("skills", []):
        # Normalize skill name
        normalized_skill = skill_name.lower().replace(" ", "_").replace("-", "_")
        domain = skill_domain_mapping.get(normalized_skill, "SYNTAX")
        
        try:
            # Update skill history
            skill_history = update_skill_history(
                db, 
                user_id, 
                skill_name, 
                curator_analysis.get("confidence", 0.5), 
                domain
            )
            
            results["skills_updated"].append({
                "skill_name": skill_name,
                "domain": domain,
                "mastery_level": skill_history.mastery_level
            })
            results["skill_histories_created"] += 1
            
        except Exception as e:
            print(f"Error processing skill {skill_name}: {e}")
            continue
    
    return results

def populate_initial_data(db: Session):
    """
    Populate initial reference data and skills
    """
    # Create domains if they don't exist
    domains = [
        ("ALGORITHMIC", "Data structures, complexity, optimization", 1),
        ("SYNTAX", "Language syntax mastery", 2),
        ("LOGIC", "Programming logic, control structures", 3),
        ("ARCHITECTURE", "Design patterns, code organization", 4),
        ("DEBUGGING", "Error resolution, testing, troubleshooting", 5),
        ("FRAMEWORKS", "React, Angular, Spring, etc.", 6),
        ("DATABASES", "SQL, NoSQL, data modeling", 7),
        ("DEVOPS", "Deployment, CI/CD, containerization", 8),
        ("SECURITY", "Application security, authentication", 9),
        ("PERFORMANCE", "Optimization, monitoring, scaling", 10),
    ]
    
    for name, description, display_order in domains:
        existing_domain = db.query(RefDomain).filter(RefDomain.name == name).first()
        if not existing_domain:
            domain = RefDomain(
                name=name,
                description=description,
                display_order=display_order
            )
            db.add(domain)
    
    db.commit()
    print("✅ Initial domain data populated")

# Development helper
if __name__ == "__main__":
    print("Creating database tables...")
    create_tables()
    
    # Populate initial data
    db = SessionLocal()
    try:
        populate_initial_data(db)
    finally:
        db.close()
    
    print("Done!")