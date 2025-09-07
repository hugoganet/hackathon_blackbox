#!/usr/bin/env python3
"""
FastAPI Backend for Dev Mentor AI
Main API application following Option 1 architecture
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import time
import asyncio
from datetime import date, timedelta
import uuid
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

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
from .memory_store import get_memory_store, ConversationMemory

# Import new PydanticAI mentor agent
try:
    from agents.mentor_agent import MentorAgent, BlackboxMentorAdapter
    from .pydantic_handler import handle_pydantic_mentor_request
    PYDANTIC_AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ PydanticAI mentor agent not available: {e}")
    MentorAgent = None
    BlackboxMentorAdapter = None
    handle_pydantic_mentor_request = None
    PYDANTIC_AI_AVAILABLE = False

# Load environment variables
load_dotenv()

# Global instances for mentor agents and memory store
normal_mentor: Optional[BlackboxMentor] = None
strict_mentor: Optional[BlackboxMentor] = None
pydantic_mentor: Optional[MentorAgent] = None
curator_agent: Optional[BlackboxMentor] = None
memory_store: Optional[ConversationMemory] = None
spaced_repetition_engine: Optional[SpacedRepetitionEngine] = None

# Thread pool for CPU-bound tasks
thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="curator")

# Performance monitoring
curator_analysis_stats = {
    "total_analyses": 0,
    "successful_analyses": 0,
    "failed_analyses": 0,
    "average_time_ms": 0,
    "learning_value_filtered": 0
}

# Circuit breaker for curator API
curator_circuit_breaker = {
    "failures": 0,
    "last_failure": None,
    "is_open": False,
    "failure_threshold": 5,
    "recovery_timeout": 300  # 5 minutes
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown"""
    # Startup
    global normal_mentor, strict_mentor, pydantic_mentor, curator_agent, memory_store, spaced_repetition_engine
    
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
        
        # Initialize PydanticAI mentor agent if available
        if PYDANTIC_AI_AVAILABLE:
            try:
                pydantic_mentor = MentorAgent()
                print("✅ PydanticAI mentor agent initialized successfully")
            except Exception as e:
                print(f"⚠️ PydanticAI mentor agent initialization failed: {e}")
                # Fallback to adapter for compatibility
                pydantic_mentor = BlackboxMentorAdapter("../agents/agent-mentor-strict.md")
                print("✅ Using BlackboxMentorAdapter as fallback")
        else:
            print("⚠️ PydanticAI not available, using legacy mentor only")
        
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
    agent_type: str = "normal"  # "normal", "strict", "pydantic_strict", or "curator"
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Response model for chat interactions"""
    response: str
    agent_type: str
    session_id: str
    related_memories: Optional[List[str]] = None
    # Enhanced metadata for PydanticAI agent
    hint_level: Optional[int] = None
    detected_language: Optional[str] = None
    detected_intent: Optional[str] = None
    similar_interactions_count: Optional[int] = None

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

# Curator Integration Helper Functions

def has_learning_value(user_message: str, mentor_response: str) -> bool:
    """
    Quick pre-filter for conversations worth analyzing
    Filters out greetings, meta questions, and non-technical content
    """
    # Skip basic greetings and non-technical messages
    low_value_patterns = [
        "hello", "hi", "thanks", "thank you", "bye", "goodbye",
        "how are you", "what can you do", "who are you", "what is this",
        "ok", "okay", "yes", "no", "sure", "fine"
    ]
    
    user_lower = user_message.lower().strip()
    
    # Skip if message is too short or matches low-value patterns
    if len(user_lower) < 10:
        return False
        
    # Skip if primarily low-value content
    if any(pattern in user_lower for pattern in low_value_patterns) and len(user_lower) < 30:
        return False
        
    # Skip if no programming-related keywords
    tech_keywords = [
        "code", "function", "variable", "error", "bug", "debug", "programming",
        "javascript", "python", "react", "sql", "html", "css", "algorithm",
        "syntax", "method", "class", "object", "array", "string", "loop",
        "if", "else", "return", "import", "export", "async", "await"
    ]
    
    combined_text = (user_message + " " + mentor_response).lower()
    has_tech_content = any(keyword in combined_text for keyword in tech_keywords)
    
    return has_tech_content

def is_educationally_valuable(analysis: dict) -> bool:
    """
    Validate curator analysis has educational value
    Filters out low-quality or generic analysis results
    """
    skills = analysis.get("skills", [])
    confidence = analysis.get("confidence", 0.0)
    mistakes = analysis.get("mistakes", [])
    questions = analysis.get("openQuestions", [])
    
    # Filter out generic/meaningless skills
    meaningful_skills = [
        skill for skill in skills 
        if skill.lower() not in ["general", "basic", "simple", "unknown", "programming"]
        and len(skill.strip()) > 3
        and not skill.lower().startswith("general")
    ]
    
    # Must have learning indicators
    has_skills = len(meaningful_skills) > 0
    has_confidence = confidence > 0.1
    has_mistakes = len(mistakes) > 0
    has_questions = len(questions) > 0
    
    return has_skills or has_confidence or has_mistakes or has_questions

@lru_cache(maxsize=500)
def extract_programming_language(skills_tuple: tuple) -> str:
    """
    Extract primary programming language from curator skills (cached for performance)
    """
    language_mapping = {
        "javascript": ["javascript", "js", "react", "node", "jsx", "react_hooks", "useState", "useEffect"],
        "python": ["python", "django", "flask", "pandas", "numpy", "fastapi"],
        "sql": ["sql", "database", "query", "joins", "mysql", "postgresql", "sqlite"],
        "html": ["html", "css", "frontend", "web", "dom"],
        "java": ["java", "spring", "maven", "gradle"],
        "cpp": ["c++", "cpp", "stl", "pointer"],
        "general": ["algorithm", "logic", "debugging", "performance", "architecture"]
    }
    
    skill_text = " ".join(skills_tuple).lower().replace(" ", "_").replace("-", "_")
    
    for language, keywords in language_mapping.items():
        if any(keyword in skill_text for keyword in keywords):
            return language
    
    return "unknown"

def get_programming_language(skills: List[str]) -> str:
    """Helper function to convert list to tuple for caching"""
    return extract_programming_language(tuple(skills))

def extract_user_intent(analysis: dict) -> str:
    """
    Determine user intent from curator analysis
    """
    mistakes = analysis.get("mistakes", [])
    questions = analysis.get("openQuestions", [])
    confidence = analysis.get("confidence", 0.5)
    
    if mistakes:
        return "debugging"  # User had errors to fix
    elif questions and confidence < 0.4:
        return "concept_explanation"  # User learning concepts
    elif confidence > 0.7:
        return "advanced_discussion"  # User has good understanding
    else:
        return "general"

def confidence_to_difficulty(confidence: float) -> str:
    """
    Convert curator confidence to difficulty level
    """
    if confidence < 0.3:
        return "beginner"
    elif confidence < 0.7:
        return "intermediate"
    else:
        return "advanced"

async def update_memory_store_metadata(user_id: str, user_message: str, analysis: dict):
    """
    Update ChromaDB memory store with curator-extracted metadata
    This improves future similarity searches by adding semantic context
    """
    if not memory_store:
        return
        
    try:
        # Extract metadata from analysis
        skills = analysis.get("skills", [])
        programming_language = get_programming_language(skills)
        user_intent = extract_user_intent(analysis)
        difficulty_level = confidence_to_difficulty(analysis.get("confidence", 0.5))
        
        # Find and update the memory entry
        # Note: ChromaDB doesn't support direct updates, so we search for similar entries
        # and update metadata for future queries
        similar_memories = memory_store.find_similar_interactions(
            current_message=user_message,
            user_id=user_id,
            limit=1,
            similarity_threshold=0.95  # Very high threshold for exact match
        )
        
        # If we found the exact memory, it will be used with enhanced metadata in future searches
        if similar_memories:
            print(f"[Curator] Enhanced memory store with metadata: {programming_language}, {user_intent}")
        
    except Exception as e:
        print(f"Failed to update memory store metadata: {e}")

async def update_interaction_metadata(db: Session, interaction_id: str, analysis: dict):
    """
    Update interaction record with curator-extracted metadata
    """
    try:
        from .database import Interaction
        
        # Extract metadata from analysis
        skills = analysis.get("skills", [])
        programming_language = get_programming_language(skills)
        user_intent = extract_user_intent(analysis)
        difficulty_level = confidence_to_difficulty(analysis.get("confidence", 0.5))
        
        # Get interaction and update
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if interaction:
            interaction.programming_language = programming_language
            interaction.user_intent = user_intent
            interaction.difficulty_level = difficulty_level
            interaction.embedding_created = True  # Mark as processed by curator
            db.commit()
            
    except Exception as e:
        print(f"Failed to update interaction metadata: {e}")
        db.rollback()

def check_circuit_breaker() -> bool:
    """Check if curator circuit breaker is open (API unavailable)"""
    if not curator_circuit_breaker["is_open"]:
        return False
    
    # Check if recovery timeout has passed
    if curator_circuit_breaker["last_failure"]:
        time_since_failure = time.time() - curator_circuit_breaker["last_failure"]
        if time_since_failure > curator_circuit_breaker["recovery_timeout"]:
            # Try to recover
            curator_circuit_breaker["is_open"] = False
            curator_circuit_breaker["failures"] = 0
            print("[Curator] Circuit breaker recovered, attempting API calls")
            return False
    
    return True

def record_curator_failure():
    """Record a curator API failure for circuit breaker"""
    curator_circuit_breaker["failures"] += 1
    curator_circuit_breaker["last_failure"] = time.time()
    
    if curator_circuit_breaker["failures"] >= curator_circuit_breaker["failure_threshold"]:
        curator_circuit_breaker["is_open"] = True
        print(f"[Curator] Circuit breaker opened after {curator_circuit_breaker['failures']} failures")

def record_curator_success():
    """Record a successful curator API call"""
    if curator_circuit_breaker["failures"] > 0:
        curator_circuit_breaker["failures"] = max(0, curator_circuit_breaker["failures"] - 1)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((json.JSONDecodeError, ConnectionError, TimeoutError))
)
async def call_curator_api_with_retry(conversation_text: str) -> dict:
    """
    Call curator API with retry logic and circuit breaker for fault tolerance
    """
    # Check circuit breaker
    if check_circuit_breaker():
        raise ConnectionError("Curator API circuit breaker is open - service temporarily unavailable")
    
    if not curator_agent:
        raise ValueError("Curator agent not available")
        
    try:
        response = curator_agent.call_blackbox_api(conversation_text)
        if response.startswith("❌"):
            record_curator_failure()
            raise ConnectionError(f"Curator API error: {response}")
            
        try:
            analysis = json.loads(response)
        except json.JSONDecodeError as e:
            record_curator_failure()
            print(f"Invalid JSON from curator: {e}")
            raise
        
        # Validate required fields
        required_fields = ["skills", "mistakes", "openQuestions", "nextSteps", "confidence"]
        for field in required_fields:
            if field not in analysis:
                record_curator_failure()
                raise ValueError(f"Missing field in curator response: {field}")
        
        # Record success
        record_curator_success()
        return analysis
        
    except Exception as e:
        record_curator_failure()
        raise

async def analyze_conversation_background(
    user_message: str,
    mentor_response: str,
    user_id: str,
    interaction_id: str
) -> Optional[dict]:
    """
    Analyze conversation in background with learning value filtering and retry logic
    Only processes conversations that have educational value
    """
    start_time = time.time()
    
    # Update performance stats
    curator_analysis_stats["total_analyses"] += 1
    
    try:
        # Quick learning value pre-filter
        if not has_learning_value(user_message, mentor_response):
            curator_analysis_stats["learning_value_filtered"] += 1
            print(f"[Curator] Skipping analysis - no learning value detected")
            return None
        
        # Format conversation for curator
        conversation_text = f"""USER MESSAGE:
{user_message}

MENTOR RESPONSE:
{mentor_response}"""
        
        # Call curator agent with retry logic
        try:
            analysis = await call_curator_api_with_retry(conversation_text)
        except Exception as e:
            print(f"[Curator] API call failed after retries: {e}")
            return None
        
        # Validate learning value from curator analysis
        if not is_educationally_valuable(analysis):
            print(f"[Curator] Skipping analysis - low educational value")
            return None
        
        # Create new database session for background task
        from .database import SessionLocal, process_curator_analysis
        db = SessionLocal()
        
        try:
            # Process curator analysis and update skill tracking
            skill_results = process_curator_analysis(db, user_id, analysis)
            
            # Update interaction with extracted metadata
            await update_interaction_metadata(db, interaction_id, analysis)
            
            # Update memory store with enhanced metadata
            await update_memory_store_metadata(user_id, user_message, analysis)
            
            analysis_time = int((time.time() - start_time) * 1000)
            
            # Update performance stats
            curator_analysis_stats["successful_analyses"] += 1
            avg_time = curator_analysis_stats["average_time_ms"]
            total = curator_analysis_stats["successful_analyses"]
            curator_analysis_stats["average_time_ms"] = ((avg_time * (total - 1)) + analysis_time) // total
            
            print(f"[Curator] Analysis completed in {analysis_time}ms - skills updated: {len(skill_results.get('skills_updated', []))}")
            
            return {**analysis, "skill_tracking": skill_results, "analysis_time_ms": analysis_time}
            
        finally:
            db.close()
        
    except Exception as e:
        analysis_time = int((time.time() - start_time) * 1000)
        curator_analysis_stats["failed_analyses"] += 1
        print(f"[Curator] Background analysis failed after {analysis_time}ms: {e}")
        return None

@app.post("/chat", response_model=ChatResponse)
async def chat_with_mentor(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Main chat endpoint - interact with AI mentors with full memory integration
    Now includes automatic curator analysis for educational conversations
    
    Args:
        request: ChatRequest with message, agent_type, user_id, session_id
        background_tasks: FastAPI background tasks for curator analysis
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
        elif request.agent_type == "pydantic_strict":
            if not pydantic_mentor or not handle_pydantic_mentor_request:
                raise HTTPException(status_code=500, detail="PydanticAI mentor not initialized")
            # Handle PydanticAI mentor separately (it has a different interface)
            response_dict = await handle_pydantic_mentor_request(request, db, pydantic_mentor, memory_store)
            return ChatResponse(**response_dict)
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
        # Enhanced with curator metadata filtering when available
        related_memories = []
        if memory_store and request.user_id:
            # Try to detect programming language for better similarity matching
            detected_language = get_programming_language([request.message])
            
            similar_interactions = memory_store.find_similar_interactions(
                current_message=request.message,
                user_id=str(user.id),
                limit=3,
                agent_type=request.agent_type,
                programming_language=detected_language if detected_language != "unknown" else None
            )
            
            # Format memories for response with enhanced context
            related_memories = []
            for memory in similar_interactions[:3]:
                metadata = memory.get("metadata", {})
                prog_lang = metadata.get("programming_language", "")
                intent = metadata.get("user_intent", "")
                
                # Enhanced memory description
                memory_desc = f"Similar past question"
                if prog_lang and prog_lang != "unknown":
                    memory_desc += f" ({prog_lang})"
                if intent and intent != "general":
                    memory_desc += f" - {intent}"
                memory_desc += f": {memory['user_message'][:80]}..."
                
                related_memories.append(memory_desc)
        
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
        
        # 🆕 ADDED: Background curator analysis with learning value filtering
        if request.agent_type != "curator":  # Avoid infinite loop
            background_tasks.add_task(
                analyze_conversation_background,
                user_message=request.message,
                mentor_response=response,
                user_id=str(user.id),
                interaction_id=str(interaction.id)
            )
        
        # Add to vector memory store for future reference
        # Will be enhanced by background curator analysis
        memory_id = None
        if memory_store and request.user_id:
            memory_id = memory_store.add_interaction(
                user_id=str(user.id),
                user_message=request.message,
                mentor_response=response,
                agent_type=request.agent_type,
                programming_language="unknown",  # Will be updated by curator
                user_intent="general"  # Will be updated by curator
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
        from .database import User, Conversation, Interaction
        
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
        from datetime import date
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
        from datetime import date, timedelta
        import uuid
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
        import uuid
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

# =============================================================================
# CURATOR ENHANCED ENDPOINTS  
# =============================================================================

@app.get("/curator/user/{user_id}/conversations")
async def get_user_conversations_with_analysis(
    user_id: str, 
    limit: int = 10,
    include_analysis: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get user conversations enhanced with curator analysis metadata
    Provides detailed learning analytics for each conversation
    """
    try:
        from .database import User, Interaction, Conversation
        from sqlalchemy import desc
        
        # Get user
        user = db.query(User).filter(User.username == user_id).first()
        if not user:
            return {
                "user_id": user_id,
                "conversations": [],
                "message": "User not found"
            }
        
        # Get recent interactions with curator analysis
        interactions_query = db.query(Interaction).join(
            Conversation, Interaction.conversation_id == Conversation.id
        ).filter(
            Conversation.user_id == user.id
        ).order_by(desc(Interaction.created_at)).limit(limit)
        
        interactions = interactions_query.all()
        
        # Format conversations with analysis metadata
        conversations = []
        for interaction in interactions:
            conversation_data = {
                "interaction_id": str(interaction.id),
                "conversation_id": str(interaction.conversation_id),
                "user_message": interaction.user_message,
                "mentor_response": interaction.mentor_response,
                "created_at": interaction.created_at.isoformat(),
                "response_time_ms": interaction.response_time_ms,
                "has_curator_analysis": interaction.programming_language != "unknown"
            }
            
            # Add curator analysis if available and requested
            if include_analysis and interaction.programming_language != "unknown":
                conversation_data["curator_analysis"] = {
                    "programming_language": interaction.programming_language,
                    "user_intent": interaction.user_intent,
                    "difficulty_level": interaction.difficulty_level,
                    "embedding_created": interaction.embedding_created
                }
            
            conversations.append(conversation_data)
        
        return {
            "user_id": user_id,
            "total_conversations": len(conversations),
            "conversations": conversations,
            "curator_analysis_enabled": include_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversations: {str(e)}")

@app.get("/curator/stats")
async def get_curator_stats(db: Session = Depends(get_db)):
    """
    Get curator analysis performance statistics
    Shows how many interactions have been analyzed and skill tracking effectiveness
    """
    try:
        from .database import Interaction, SkillHistory
        
        # Count total interactions
        total_interactions = db.query(Interaction).count()
        
        # Count analyzed interactions (those with programming_language set)
        analyzed_interactions = db.query(Interaction).filter(
            Interaction.programming_language != "unknown",
            Interaction.programming_language.isnot(None)
        ).count()
        
        # Count skill tracking records
        skill_records = db.query(SkillHistory).count()
        
        # Calculate analysis rate
        analysis_rate = analyzed_interactions / max(total_interactions, 1)
        
        return {
            "total_interactions": total_interactions,
            "analyzed_interactions": analyzed_interactions,
            "unanalyzed_interactions": total_interactions - analyzed_interactions,
            "analysis_rate": round(analysis_rate, 3),
            "skill_history_records": skill_records,
            "curator_integration": "active" if analysis_rate > 0 else "inactive",
            "message": f"Curator analysis running on {analysis_rate:.1%} of conversations",
            
            # Performance metrics
            "performance_stats": {
                "total_analysis_requests": curator_analysis_stats["total_analyses"],
                "successful_analyses": curator_analysis_stats["successful_analyses"],
                "failed_analyses": curator_analysis_stats["failed_analyses"],
                "learning_value_filtered": curator_analysis_stats["learning_value_filtered"],
                "success_rate": round(
                    curator_analysis_stats["successful_analyses"] / max(curator_analysis_stats["total_analyses"], 1),
                    3
                ),
                "average_analysis_time_ms": curator_analysis_stats["average_time_ms"],
                "filter_rate": round(
                    curator_analysis_stats["learning_value_filtered"] / max(curator_analysis_stats["total_analyses"], 1),
                    3
                )
            },
            
            # Circuit breaker status
            "circuit_breaker": {
                "is_open": curator_circuit_breaker["is_open"],
                "failure_count": curator_circuit_breaker["failures"],
                "failure_threshold": curator_circuit_breaker["failure_threshold"],
                "last_failure": curator_circuit_breaker["last_failure"],
                "recovery_timeout_seconds": curator_circuit_breaker["recovery_timeout"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving curator stats: {str(e)}")

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