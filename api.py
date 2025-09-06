#!/usr/bin/env python3
"""
FastAPI Backend for Dev Mentor AI
Main API application following Option 1 architecture
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
import time
from sqlalchemy.orm import Session

# Import our components
from main import BlackboxMentor, load_env_file
from database import get_db, create_tables, get_user_by_username, create_conversation, save_interaction
from memory_store import get_memory_store, ConversationMemory

# Load environment variables
load_dotenv()

# Create FastAPI app instance
app = FastAPI(
    title="Dev Mentor AI API",
    description="AI mentoring system for junior developers with memory capabilities",
    version="1.0.0"
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
    agent_type: str = "normal"  # "normal" or "strict" 
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

# Global mentor instances (initialized once for performance)
normal_mentor: Optional[BlackboxMentor] = None
strict_mentor: Optional[BlackboxMentor] = None
memory_store: Optional[ConversationMemory] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    global normal_mentor, strict_mentor, memory_store
    
    # Load environment variables
    load_env_file()
    
    try:
        # Initialize database tables
        create_tables()
        print("✅ Database tables initialized")
        
        # Initialize both mentor agents
        normal_mentor = BlackboxMentor("agent-mentor.md")
        strict_mentor = BlackboxMentor("agent-mentor-strict.md")
        print("✅ Mentor agents initialized successfully")
        
        # Initialize vector store (Chroma)
        memory_store = get_memory_store()
        print("✅ Memory store initialized")
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        raise e

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
        from database import User, Conversation, Interaction
        
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
                "agents_loaded": bool(normal_mentor and strict_mentor)
            }
        }
        
    except Exception as e:
        return {
            "database": {"status": f"error: {e}"},
            "memory_store": {"status": "unknown"},
            "api": {"status": "running", "agents_loaded": False}
        }

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