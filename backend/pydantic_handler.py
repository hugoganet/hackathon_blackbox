"""
PydanticAI Mentor Handler
Handler function for PydanticAI mentor agent requests
"""

import time
from typing import Optional
from sqlalchemy.orm import Session

from .database import get_user_by_username, create_conversation, save_interaction


async def handle_pydantic_mentor_request(request, db: Session, pydantic_mentor, memory_store) -> dict:
    """
    Handle requests for the PydanticAI mentor agent
    
    Args:
        request: ChatRequest with user message and metadata
        db: Database session
        pydantic_mentor: PydanticAI mentor agent instance
        memory_store: ConversationMemory instance
    
    Returns:
        ChatResponse dict with enhanced PydanticAI mentor response
    """
    start_time = time.time()
    
    # Get or create user
    username = request.user_id or "anonymous"
    user = get_user_by_username(db, username)
    
    # Generate session ID if not provided
    session_id = request.session_id or f"session_{hash(str(user.id))}"
    
    # Get related memories before responding
    related_memories = []
    if memory_store and request.user_id:
        similar_interactions = memory_store.find_similar_interactions(
            current_message=request.message,
            user_id=str(user.id),
            limit=3,
            agent_type="pydantic_strict"
        )
        
        # Format memories for response
        related_memories = [
            f"Similar past question: {memory['user_message'][:100]}..."
            for memory in similar_interactions[:3]
        ]
    
    # Call PydanticAI mentor agent
    mentor_response = await pydantic_mentor.respond(
        user_message=request.message,
        user_id=str(user.id),
        session_id=session_id,
        memory_store=memory_store,
        db_session=db
    )
    
    # Calculate response time
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Create conversation if needed
    conversation = create_conversation(db, str(user.id), session_id, "pydantic_strict")
    
    # Save interaction to database
    interaction = save_interaction(
        db,
        str(conversation.id),
        request.message,
        mentor_response.response,
        response_time_ms
    )
    
    return {
        "response": mentor_response.response,
        "agent_type": "pydantic_strict",
        "session_id": session_id,
        "related_memories": related_memories,
        "hint_level": mentor_response.hint_level,
        "detected_language": mentor_response.detected_language,
        "detected_intent": mentor_response.detected_intent,
        "similar_interactions_count": mentor_response.similar_interactions_count
    }