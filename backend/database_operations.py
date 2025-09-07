"""
Database operations for Dev Mentor AI
Includes all CRUD operations for users, conversations, skills, and flashcards
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_
from typing import List, Optional, Dict, Any, Generator
from datetime import date, datetime, timedelta
import uuid
import json

# Import all models from the main database module
from .database import (
    SessionLocal, Base, create_engine, engine,
    User, Conversation, Interaction, MemoryEntry, Skill, SkillHistory, RefDomain,
    Flashcard, ReviewSession
)

# Re-export essential functions for backward compatibility
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
    # PostgreSQL: convert string to UUID object
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
    
    conversation = Conversation(
        id=uuid.uuid4(),
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
    # PostgreSQL: convert string to UUID object
    if isinstance(conversation_id, str):
        conversation_id = uuid.UUID(conversation_id)
    
    interaction = Interaction(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        user_message=user_message,
        mentor_response=mentor_response,
        response_time_ms=response_time_ms
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction

# =============================================================================
# SKILL TRACKING OPERATIONS
# =============================================================================

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
    
    # PostgreSQL: convert string to UUID object
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
        skill_history = SkillHistory(
            id_history=uuid.uuid4(),
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
    # PostgreSQL: convert string to UUID object
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

# =============================================================================
# FLASHCARD CRUD OPERATIONS
# =============================================================================

def create_flashcard(
    db: Session,
    user_id: str,
    question: str,
    answer: str,
    difficulty: int = 1,
    card_type: str = "concept",
    skill_id: Optional[int] = None,
    interaction_id: Optional[str] = None,
    next_review_date: Optional[date] = None
) -> Flashcard:
    """
    Create a new flashcard
    """
    flashcard = Flashcard(
        id=uuid.uuid4(),
        question=question,
        answer=answer,
        difficulty=difficulty,
        card_type=card_type,
        skill_id=skill_id,
        interaction_id=uuid.UUID(interaction_id) if interaction_id else None,
        next_review_date=next_review_date or date.today()
    )
    
    db.add(flashcard)
    db.commit()
    db.refresh(flashcard)
    return flashcard

def get_flashcard_by_id(db: Session, flashcard_id: str) -> Optional[Flashcard]:
    """
    Get flashcard by ID
    """
    flashcard_uuid = uuid.UUID(flashcard_id) if isinstance(flashcard_id, str) else flashcard_id
    return db.query(Flashcard).filter(Flashcard.id == flashcard_uuid).first()

def get_due_flashcards(db: Session, user_id: str, limit: int = 20) -> List[Flashcard]:
    """
    Get flashcards due for review by user
    """
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    today = date.today()
    
    # Get flashcards due for review through interactions and conversations
    due_flashcards = db.query(Flashcard).join(
        Interaction, Flashcard.interaction_id == Interaction.id, isouter=True
    ).join(
        Conversation, Interaction.conversation_id == Conversation.id, isouter=True
    ).filter(
        and_(
            Flashcard.next_review_date <= today,
            or_(
                Conversation.user_id == user_uuid,
                Flashcard.interaction_id == None  # Cards not linked to interactions
            )
        )
    ).order_by(Flashcard.next_review_date).limit(limit).all()
    
    return due_flashcards

def update_flashcard_schedule(
    db: Session,
    flashcard_id: str,
    next_review_date: date,
    difficulty: float,
    review_count: int
) -> Flashcard:
    """
    Update flashcard scheduling parameters
    """
    flashcard_uuid = uuid.UUID(flashcard_id) if isinstance(flashcard_id, str) else flashcard_id
    flashcard = db.query(Flashcard).filter(Flashcard.id == flashcard_uuid).first()
    
    if flashcard:
        flashcard.next_review_date = next_review_date
        flashcard.difficulty = int(difficulty)  # Convert ease factor to difficulty
        flashcard.review_count = review_count
        db.commit()
        db.refresh(flashcard)
    
    return flashcard

def create_review_session(
    db: Session,
    user_id: str,
    flashcard_id: str,
    success_score: int,
    response_time: Optional[int] = None
) -> ReviewSession:
    """
    Create a new review session record
    """
    review_session = ReviewSession(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
        flashcard_id=uuid.UUID(flashcard_id) if isinstance(flashcard_id, str) else flashcard_id,
        success_score=success_score,
        response_time=response_time
    )
    
    db.add(review_session)
    db.commit()
    db.refresh(review_session)
    return review_session

def get_user_review_history(db: Session, user_id: str, limit: int = 50) -> List[ReviewSession]:
    """
    Get user's review history
    """
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    
    return db.query(ReviewSession).filter(
        ReviewSession.user_id == user_uuid
    ).order_by(desc(ReviewSession.review_date)).limit(limit).all()

def get_user_flashcard_stats(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive flashcard statistics for a user
    """
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    today = date.today()
    
    # Total flashcards for user (through conversations/interactions)
    total_flashcards = db.query(Flashcard).join(
        Interaction, Flashcard.interaction_id == Interaction.id, isouter=True
    ).join(
        Conversation, Interaction.conversation_id == Conversation.id, isouter=True
    ).filter(
        or_(
            Conversation.user_id == user_uuid,
            Flashcard.interaction_id == None
        )
    ).count()
    
    # Due flashcards
    due_flashcards = db.query(Flashcard).join(
        Interaction, Flashcard.interaction_id == Interaction.id, isouter=True
    ).join(
        Conversation, Interaction.conversation_id == Conversation.id, isouter=True
    ).filter(
        and_(
            Flashcard.next_review_date <= today,
            or_(
                Conversation.user_id == user_uuid,
                Flashcard.interaction_id == None
            )
        )
    ).count()
    
    # Recent reviews (last 7 days)
    week_ago = today - timedelta(days=7)
    recent_reviews = db.query(ReviewSession).filter(
        and_(
            ReviewSession.user_id == user_uuid,
            ReviewSession.review_date >= week_ago
        )
    ).count()
    
    # Average score and success rate
    avg_score_result = db.query(func.avg(ReviewSession.success_score)).filter(
        ReviewSession.user_id == user_uuid
    ).scalar()
    avg_score = float(avg_score_result) if avg_score_result else 0.0
    
    # Success rate (scores >= 3)
    total_reviews = db.query(ReviewSession).filter(ReviewSession.user_id == user_uuid).count()
    successful_reviews = db.query(ReviewSession).filter(
        and_(
            ReviewSession.user_id == user_uuid,
            ReviewSession.success_score >= 3
        )
    ).count()
    
    success_rate = (successful_reviews / total_reviews) if total_reviews > 0 else 0.0
    
    # Calculate streak (consecutive days with reviews)
    streak_days = 0
    check_date = today
    while True:
        day_reviews = db.query(ReviewSession).filter(
            and_(
                ReviewSession.user_id == user_uuid,
                func.date(ReviewSession.review_date) == check_date
            )
        ).count()
        
        if day_reviews > 0:
            streak_days += 1
            check_date -= timedelta(days=1)
        else:
            break
        
        # Prevent infinite loop
        if streak_days > 365:
            break
    
    return {
        "total_flashcards": total_flashcards,
        "due_flashcards": due_flashcards,
        "recent_reviews": recent_reviews,
        "average_score": round(avg_score, 2),
        "success_rate": round(success_rate, 2),
        "streak_days": streak_days
    }

def get_flashcards_by_skill(db: Session, skill_id: int, limit: int = 50) -> List[Flashcard]:
    """
    Get flashcards for a specific skill
    """
    return db.query(Flashcard).filter(
        Flashcard.skill_id == skill_id
    ).limit(limit).all()

def batch_create_flashcards(db: Session, flashcards_data: List[Dict[str, Any]]) -> List[Flashcard]:
    """
    Create multiple flashcards in batch
    """
    flashcards = []
    
    for card_data in flashcards_data:
        flashcard = Flashcard(
            id=uuid.uuid4(),
            question=card_data["question"],
            answer=card_data["answer"],
            difficulty=card_data.get("difficulty", 1),
            card_type=card_data.get("card_type", "concept"),
            skill_id=card_data.get("skill_id"),
            interaction_id=card_data.get("interaction_id"),
            next_review_date=card_data.get("next_review_date", date.today())
        )
        flashcards.append(flashcard)
        db.add(flashcard)
    
    db.commit()
    
    for flashcard in flashcards:
        db.refresh(flashcard)
    
    return flashcards

def delete_flashcard(db: Session, flashcard_id: str, user_id: str) -> bool:
    """
    Delete flashcard with ownership verification
    """
    flashcard_uuid = uuid.UUID(flashcard_id) if isinstance(flashcard_id, str) else flashcard_id
    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    
    # Verify ownership through conversation relationship
    flashcard = db.query(Flashcard).join(
        Interaction, Flashcard.interaction_id == Interaction.id, isouter=True
    ).join(
        Conversation, Interaction.conversation_id == Conversation.id, isouter=True
    ).filter(
        and_(
            Flashcard.id == flashcard_uuid,
            or_(
                Conversation.user_id == user_uuid,
                Flashcard.interaction_id == None  # Allow deletion of orphaned cards
            )
        )
    ).first()
    
    if flashcard:
        # Delete associated review sessions first
        db.query(ReviewSession).filter(ReviewSession.flashcard_id == flashcard_uuid).delete()
        db.delete(flashcard)
        db.commit()
        return True
    
    return False

# Development helper
if __name__ == "__main__":
    print("Database operations module loaded successfully!")
    print("Available operations:")
    print("- User management: get_user_by_username")
    print("- Conversations: create_conversation, save_interaction")  
    print("- Skills: process_curator_analysis, get_user_skill_progression")
    print("- Flashcards: create_flashcard, get_due_flashcards, update_flashcard_schedule")
    print("- Reviews: create_review_session, get_user_flashcard_stats")
