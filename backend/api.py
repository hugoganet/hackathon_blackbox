#!/usr/bin/env python3
"""
FastAPI Backend for Dev Mentor AI
Main API application following Option 1 architecture
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import time
from sqlalchemy.orm import Session

# Import our components
from .main import BlackboxMentor, load_env_file
from .database_operations import (
    get_db, create_tables, get_user_by_username, create_conversation, save_interaction,
    process_curator_analysis, get_user_skill_progression, populate_initial_data,
    create_flashcard, get_due_flashcards, get_flashcard_by_id, update_flashcard_schedule,
    create_review_session, get_user_review_history, get_user_flashcard_stats,
    get_flashcards_by_skill, batch_create_flashcards, delete_flashcard
)
from .spaced_repetition import SpacedRepetitionEngine, ReviewResult
from datetime import date, timedelta
import uuid
from .memory_store import get_memory_store, ConversationMemory

# Load environment variables
load_dotenv()

# Global instances for mentor agents and memory store
normal_mentor: Optional[BlackboxMentor] = None
strict_mentor: Optional[BlackboxMentor] = None
curator_agent: Optional[BlackboxMentor] = None
memory_store: Optional[ConversationMemory] = None
spaced_repetition_engine: Optional[SpacedRepetitionEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown"""
    # Startup
    global normal_mentor, strict_mentor, curator_agent, memory_store, spaced_repetition_engine
    
    # Load environment variables
    load_env_file()
    
    try:
        # Initialize database tables
        create_tables()
        print("✅ Database tables initialized")
        
        # Populate initial skill data
        from .database_operations import SessionLocal
        db = SessionLocal()
        try:
            populate_initial_data(db)
        finally:
            db.close()
        
        # Initialize all mentor agents
        normal_mentor = BlackboxMentor("../agents/agent-mentor-strict.md")  # Use strict agent for now since no normal agent exists
        strict_mentor = BlackboxMentor("../agents/agent-mentor-strict.md")
        curator_agent = BlackboxMentor("../agents/curator-agent.md")
        print("✅ All mentor agents initialized successfully")
        
        # Initialize vector store (Chroma)
        memory_store = get_memory_store()
        print("✅ Memory store initialized")
        
        # Initialize spaced repetition engine
        spaced_repetition_engine = SpacedRepetitionEngine()
        print("✅ Spaced repetition engine initialized")
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        raise e
    
    yield
    
    # Shutdown - cleanup if needed
    print("👋 Shutting down application...")

# Create FastAPI app instance with lifespan
app = FastAPI(
    title="Dev Mentor AI API",
    description="AI mentoring system for junior developers with memory capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for React frontend (Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local React development
        "https://*.vercel.app",   # Vercel deployment
        "https://dev-mentor-ai.vercel.app"  # Your production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models (Pydantic for API validation)
class ChatRequest(BaseModel):
    """Request model for chat interactions"""
    message: str
    agent_type: str = "normal"  # "normal", "strict", or "curator"
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Response model for chat interactions"""
    response: str
    agent_type: str
    session_id: str
    related_memories: Optional[List[str]] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str

class CuratorAnalysisRequest(BaseModel):
    """Request model for curator conversation analysis"""
    user_message: str
    mentor_response: str
    user_id: str
    session_id: Optional[str] = None

class CuratorAnalysisResponse(BaseModel):
    """Response model for curator analysis"""
    skills: List[str]
    mistakes: List[str]
    openQuestions: List[str]
    nextSteps: List[str]
    confidence: float
    analysis_time_ms: int
    skill_tracking: Dict[str, Any] = None


# Flashcard API Models
class FlashcardCreateRequest(BaseModel):
    """Request model for creating flashcards"""
    question: str
    answer: str
    difficulty: int = 1  # 1-5 scale
    card_type: str = "concept"
    skill_id: Optional[int] = None
    interaction_id: Optional[str] = None
    confidence_score: float = 0.5  # From curator analysis


class FlashcardResponse(BaseModel):
    """Response model for flashcard data"""
    id: str
    question: str
    answer: str
    difficulty: int
    card_type: str
    next_review_date: str  # ISO date string
    review_count: int
    created_at: str
    skill_id: Optional[int] = None


class ReviewRequest(BaseModel):
    """Request model for recording review results"""
    flashcard_id: str
    user_id: str
    success_score: int  # 0-5 scale
    response_time: Optional[int] = None  # seconds


class ReviewResponse(BaseModel):
    """Response model for review submission"""
    success: bool
    next_review_date: str  # ISO date string
    interval_days: int
    difficulty_factor: float
    card_state: str
    message: str


class DueCardsResponse(BaseModel):
    """Response model for due cards"""
    flashcards: List[FlashcardResponse]
    total_due: int
    user_stats: Dict[str, Any]


class FlashcardStatsResponse(BaseModel):
    """Response model for user flashcard statistics"""
    total_flashcards: int
    due_flashcards: int
    recent_reviews: int
    average_score: float
    success_rate: float
    streak_days: int


class BatchCreateRequest(BaseModel):
    """Request model for batch flashcard creation"""
    flashcards: List[FlashcardCreateRequest]
    user_id: str

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        message="Dev Mentor AI API is running"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy", 
        message="All systems operational"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_with_mentor(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint - interact with AI mentors with full memory integration
    
    Args:
        request: ChatRequest with message, agent_type, user_id, session_id
        db: Database session (injected by FastAPI)
        
    Returns:
        ChatResponse with mentor's response and related memories
    """
    start_time = time.time()
    
    try:
        # Select appropriate mentor based on request
        if request.agent_type == "strict":
            mentor = strict_mentor
            if not mentor:
                raise HTTPException(status_code=500, detail="Strict mentor not initialized")
        elif request.agent_type == "curator":
            mentor = curator_agent
            if not mentor:
                raise HTTPException(status_code=500, detail="Curator agent not initialized")
        else:
            mentor = normal_mentor
            if not mentor:
                raise HTTPException(status_code=500, detail="Normal mentor not initialized")
        
        # Get or create user
        username = request.user_id or "anonymous"
        user = get_user_by_username(db, username)
        
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{hash(str(user.id))}"
        
        # Search for related memories before responding
        related_memories = []
        if memory_store and request.user_id:
            similar_interactions = memory_store.find_similar_interactions(
                current_message=request.message,
                user_id=str(user.id),
                limit=3,
                agent_type=request.agent_type
            )
            
            # Format memories for response
            related_memories = [
                f"Similar past question: {memory['user_message'][:100]}..."
                for memory in similar_interactions[:3]
            ]
        
        # Call the Blackbox API through our mentor
        response = mentor.call_blackbox_api(request.message)
        
        # Check for API errors
        if response.startswith("❌"):
            raise HTTPException(status_code=500, detail=f"Mentor API error: {response}")
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Create conversation if needed
        conversation = create_conversation(db, str(user.id), session_id, request.agent_type)
        
        # Save interaction to database
        interaction = save_interaction(
            db, 
            str(conversation.id), 
            request.message, 
            response,
            response_time_ms
        )
        
        # Add to vector memory store for future reference
        if memory_store and request.user_id:
            memory_store.add_interaction(
                user_id=str(user.id),
                user_message=request.message,
                mentor_response=response,
                agent_type=request.agent_type,
                # TODO: Add automatic classification of programming language and intent
                programming_language="unknown",
                user_intent="general"
            )
        
        return ChatResponse(
            response=response,
            agent_type=request.agent_type,
            session_id=session_id,
            related_memories=related_memories
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/agents")
async def list_agents():
    """List available mentor agents"""
    return {
        "agents": [
            {
                "id": "normal",
                "name": "Mentor Agent",
                "description": "Provides complete answers and detailed guidance"
            },
            {
                "id": "strict", 
                "name": "Strict Mentor Agent",
                "description": "Guides through hints only, refuses to give direct answers"
            },
            {
                "id": "curator",
                "name": "Curator Agent",
                "description": "Analyzes conversations and extracts learning analytics"
            }
        ]
    }

@app.get("/user/{user_id}/memories")
async def get_user_memories(user_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Get recent memories/interactions for a user
    Useful for showing conversation history in the frontend
    """
    try:
        if memory_store:
            patterns = memory_store.get_user_learning_patterns(user_id)
            return {
                "user_id": user_id,
                "learning_patterns": patterns,
                "memory_store_status": "active"
            }
        else:
            return {
                "user_id": user_id,
                "learning_patterns": {"message": "Memory store not initialized"},
                "memory_store_status": "inactive"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving memories: {str(e)}")

@app.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """
    Get system statistics for monitoring
    Useful for Railway deployment monitoring
    """
    try:
        # Database stats
        from .database.models import User, Conversation, Interaction
        
        user_count = db.query(User).count()
        conversation_count = db.query(Conversation).count() 
        interaction_count = db.query(Interaction).count()
        
        # Memory store stats
        memory_stats = memory_store.get_stats() if memory_store else {"status": "not initialized"}
        
        return {
            "database": {
                "users": user_count,
                "conversations": conversation_count,
                "interactions": interaction_count,
                "status": "connected"
            },
            "memory_store": memory_stats,
            "api": {
                "status": "running",
                "agents_loaded": bool(normal_mentor and strict_mentor and curator_agent)
            }
        }
        
    except Exception as e:
        return {
            "database": {"status": f"error: {e}"},
            "memory_store": {"status": "unknown"},
            "api": {"status": "running", "agents_loaded": False}
        }

@app.post("/curator/analyze", response_model=CuratorAnalysisResponse)
async def analyze_conversation(request: CuratorAnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyze a conversation using the curator agent to extract learning analytics
    
    Args:
        request: CuratorAnalysisRequest with conversation data
        db: Database session
        
    Returns:
        CuratorAnalysisResponse with structured learning analytics
    """
    start_time = time.time()
    
    try:
        if not curator_agent:
            raise HTTPException(status_code=500, detail="Curator agent not initialized")
        
        # Format conversation for curator analysis
        conversation_text = f"""
USER MESSAGE:
{request.user_message}

MENTOR RESPONSE:
{request.mentor_response}
"""
        
        # Call curator agent
        response = curator_agent.call_blackbox_api(conversation_text)
        
        # Check for API errors
        if response.startswith("❌"):
            raise HTTPException(status_code=500, detail=f"Curator API error: {response}")
        
        # Parse JSON response
        try:
            analysis = json.loads(response)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Invalid JSON from curator: {e}")
        
        # Validate response structure
        required_fields = ["skills", "mistakes", "openQuestions", "nextSteps", "confidence"]
        for field in required_fields:
            if field not in analysis:
                raise HTTPException(status_code=500, detail=f"Missing field in curator response: {field}")
        
        # Calculate analysis time
        analysis_time_ms = int((time.time() - start_time) * 1000)
        
        # Process curator analysis and update skill tracking
        skill_tracking_results = None
        try:
            # Get or create user to ensure they exist
            user = get_user_by_username(db, request.user_id)
            
            # Process the curator analysis and update skill history
            skill_tracking_results = process_curator_analysis(db, str(user.id), analysis)
        except Exception as e:
            print(f"Warning: Could not update skill tracking: {e}")
            # Continue without skill tracking if there's an error
        
        return CuratorAnalysisResponse(
            skills=analysis["skills"],
            mistakes=analysis["mistakes"],
            openQuestions=analysis["openQuestions"],
            nextSteps=analysis["nextSteps"],
            confidence=float(analysis["confidence"]),
            analysis_time_ms=analysis_time_ms,
            skill_tracking=skill_tracking_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/curator/user/{user_id}/skills")
async def get_user_skills(user_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """
    Get user skill progression data from skill_history table
    
    Args:
        user_id: Username or user identifier
        limit: Maximum number of skill history entries to return
        db: Database session
        
    Returns:
        User skill progression with mastery levels and dates
    """
    try:
        # Get user to verify existence and get UUID
        user = get_user_by_username(db, user_id)
        
        # Get skill progression history
        skill_progression = get_user_skill_progression(db, str(user.id), limit)
        
        # Calculate summary statistics
        skills_summary = {}
        domains_summary = {}
        
        for entry in skill_progression:
            skill_name = entry["skill_name"]
            domain = entry["domain"]
            mastery_level = entry["mastery_level"]
            
            # Track highest mastery level for each skill
            if skill_name not in skills_summary or skills_summary[skill_name]["mastery_level"] < mastery_level:
                skills_summary[skill_name] = {
                    "mastery_level": mastery_level,
                    "domain": domain,
                    "last_updated": entry["snapshot_date"]
                }
            
            # Track domain progress
            if domain not in domains_summary:
                domains_summary[domain] = {"skills_count": 0, "avg_mastery": 0, "total_mastery": 0}
            domains_summary[domain]["skills_count"] += 1
            domains_summary[domain]["total_mastery"] += mastery_level
            domains_summary[domain]["avg_mastery"] = domains_summary[domain]["total_mastery"] / domains_summary[domain]["skills_count"]
        
        return {
            "user_id": user_id,
            "user_uuid": str(user.id),
            "total_skills_tracked": len(skills_summary),
            "skill_progression": skill_progression,
            "skills_summary": skills_summary,
            "domains_summary": domains_summary,
            "message": "Skill tracking active - data sourced from skill_history table"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving skills: {str(e)}")


# =============================================================================
# FLASHCARD AND SPACED REPETITION API ENDPOINTS
# =============================================================================

@app.post("/flashcards/create", response_model=FlashcardResponse)
async def create_flashcard_endpoint(request: FlashcardCreateRequest, db: Session = Depends(get_db)):
    """Create a new flashcard with spaced repetition scheduling"""
    try:
        # Use spaced repetition engine to calculate initial parameters
        initial_params = spaced_repetition_engine.get_initial_parameters(
            confidence_score=request.confidence_score
        )
        
        # Create flashcard in database
        flashcard = create_flashcard(
            db=db,
            user_id="", # Will be derived from interaction_id if provided
            question=request.question,
            answer=request.answer,
            difficulty=request.difficulty,
            card_type=request.card_type,
            skill_id=request.skill_id,
            interaction_id=request.interaction_id,
            next_review_date=initial_params.next_review_date
        )
        
        return FlashcardResponse(
            id=str(flashcard.id),
            question=flashcard.question,
            answer=flashcard.answer,
            difficulty=flashcard.difficulty,
            card_type=flashcard.card_type,
            next_review_date=flashcard.next_review_date.isoformat(),
            review_count=flashcard.review_count,
            created_at=flashcard.created_at.isoformat(),
            skill_id=flashcard.skill_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating flashcard: {str(e)}")


@app.get("/flashcards/review/{user_id}", response_model=DueCardsResponse)
async def get_due_flashcards_endpoint(user_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """Get flashcards due for review"""
    try:
        due_flashcards = get_due_flashcards(db, user_id, limit)
        user_stats = get_user_flashcard_stats(db, user_id)
        
        flashcard_responses = [
            FlashcardResponse(
                id=str(card.id),
                question=card.question,
                answer=card.answer,
                difficulty=card.difficulty,
                card_type=card.card_type,
                next_review_date=card.next_review_date.isoformat(),
                review_count=card.review_count,
                created_at=card.created_at.isoformat(),
                skill_id=card.skill_id
            ) for card in due_flashcards
        ]
        
        return DueCardsResponse(
            flashcards=flashcard_responses,
            total_due=len(flashcard_responses),
            user_stats=user_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving due flashcards: {str(e)}")


@app.post("/flashcards/review", response_model=ReviewResponse)
async def submit_review_endpoint(request: ReviewRequest, db: Session = Depends(get_db)):
    """Submit a flashcard review and update spaced repetition schedule"""
    try:
        # Get current flashcard data
        flashcard = get_flashcard_by_id(db, request.flashcard_id)
        if not flashcard:
            raise HTTPException(status_code=404, detail="Flashcard not found")
        
        # Create review session record
        review_session = create_review_session(
            db=db,
            user_id=request.user_id,
            flashcard_id=request.flashcard_id,
            success_score=request.success_score,
            response_time=request.response_time
        )
        
        # Calculate new spaced repetition parameters
        new_params = spaced_repetition_engine.calculate_next_review(
            current_interval=(flashcard.next_review_date - date.today()).days,
            difficulty_factor=float(flashcard.difficulty),  # Convert to ease factor approximation
            success_score=request.success_score,
            review_count=flashcard.review_count
        )
        
        # Update flashcard schedule
        updated_flashcard = update_flashcard_schedule(
            db=db,
            flashcard_id=request.flashcard_id,
            next_review_date=new_params.next_review_date,
            difficulty=new_params.difficulty_factor,
            review_count=new_params.review_count
        )
        
        return ReviewResponse(
            success=True,
            next_review_date=new_params.next_review_date.isoformat(),
            interval_days=new_params.interval_days,
            difficulty_factor=new_params.difficulty_factor,
            card_state=new_params.card_state.value,
            message=f"Review recorded successfully. Next review in {new_params.interval_days} days."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing review: {str(e)}")


@app.get("/flashcards/stats/{user_id}", response_model=FlashcardStatsResponse) 
async def get_flashcard_stats_endpoint(user_id: str, db: Session = Depends(get_db)):
    """Get comprehensive flashcard statistics for a user"""
    try:
        stats = get_user_flashcard_stats(db, user_id)
        
        return FlashcardStatsResponse(
            total_flashcards=stats["total_flashcards"],
            due_flashcards=stats["due_flashcards"],
            recent_reviews=stats["recent_reviews"],
            average_score=stats["average_score"],
            success_rate=stats["success_rate"],
            streak_days=stats["streak_days"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@app.get("/flashcards/schedule/{user_id}")
async def get_review_schedule_endpoint(user_id: str, days: int = 7, db: Session = Depends(get_db)):
    """Get review schedule for upcoming days"""
    try:
        today = date.today()
        schedule = {}
        
        for i in range(days):
            check_date = today + timedelta(days=i)
            day_flashcards = db.query(Flashcard)\
                .join(Interaction, Flashcard.interaction_id == Interaction.id, isouter=True)\
                .join(Conversation, Interaction.conversation_id == Conversation.id, isouter=True)\
                .filter(
                    Flashcard.next_review_date == check_date,
                    Conversation.user_id == uuid.UUID(user_id) if user_id else True
                ).count()
            
            schedule[check_date.isoformat()] = {
                "date": check_date.isoformat(),
                "cards_due": day_flashcards,
                "is_today": i == 0
            }
        
        return {
            "user_id": user_id,
            "schedule": schedule,
            "total_upcoming": sum(day["cards_due"] for day in schedule.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving schedule: {str(e)}")


@app.post("/flashcards/batch", response_model=List[FlashcardResponse])
async def batch_create_flashcards_endpoint(request: BatchCreateRequest, db: Session = Depends(get_db)):
    """Create multiple flashcards in batch"""
    try:
        flashcards_data = []
        
        for card_request in request.flashcards:
            # Calculate initial parameters for each card
            initial_params = spaced_repetition_engine.get_initial_parameters(
                confidence_score=card_request.confidence_score
            )
            
            card_data = {
                "question": card_request.question,
                "answer": card_request.answer,
                "difficulty": card_request.difficulty,
                "card_type": card_request.card_type,
                "next_review_date": initial_params.next_review_date,
                "skill_id": card_request.skill_id,
                "interaction_id": uuid.UUID(card_request.interaction_id) if card_request.interaction_id else None
            }
            flashcards_data.append(card_data)
        
        # Create flashcards in batch
        created_flashcards = batch_create_flashcards(db, flashcards_data)
        
        return [
            FlashcardResponse(
                id=str(card.id),
                question=card.question,
                answer=card.answer,
                difficulty=card.difficulty,
                card_type=card.card_type,
                next_review_date=card.next_review_date.isoformat(),
                review_count=card.review_count,
                created_at=card.created_at.isoformat(),
                skill_id=card.skill_id
            ) for card in created_flashcards
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating flashcards: {str(e)}")


@app.delete("/flashcards/{flashcard_id}")
async def delete_flashcard_endpoint(flashcard_id: str, user_id: str, db: Session = Depends(get_db)):
    """Delete a flashcard (with ownership verification)"""
    try:
        success = delete_flashcard(db, flashcard_id, user_id)
        
        if success:
            return {"success": True, "message": "Flashcard deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Flashcard not found or access denied")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting flashcard: {str(e)}")


# Development server runner
if __name__ == "__main__":
    import uvicorn
    
    # This runs the development server
    # In production, Railway will use: uvicorn api:app --host 0.0.0.0 --port $PORT
    uvicorn.run(
        "api:app",
        host="0.0.0.0", 
        port=8000,
        reload=True  # Auto-reload on code changes (dev only)
    )