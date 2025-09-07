"""
Mentor Agent Tools - Memory search, interaction saving, pattern analysis, and hint escalation.
"""

import json
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic_ai import RunContext
from .dependencies import MentorDependencies, LearningMemory

logger = logging.getLogger(__name__)


def extract_key_concepts(text: str) -> List[str]:
    """Extract key programming concepts from text."""
    # Simple keyword extraction - could be enhanced with NLP
    programming_keywords = [
        'react', 'javascript', 'python', 'html', 'css', 'function', 'variable',
        'loop', 'array', 'object', 'class', 'method', 'api', 'database', 'sql',
        'async', 'await', 'promise', 'state', 'props', 'component', 'error',
        'debug', 'test', 'algorithm', 'data structure'
    ]
    
    text_lower = text.lower()
    found_concepts = [keyword for keyword in programming_keywords if keyword in text_lower]
    return found_concepts[:5]  # Return top 5 concepts


def detect_confusion_signals(text: str) -> List[str]:
    """Detect signals that user is confused or stuck."""
    confusion_signals = {
        "explicit": ["i don't understand", "i'm stuck", "i'm confused", "help", "what?"],
        "implicit": ["how?", "but why", "i tried everything", "doesn't work"],
        "repetitive": ["still not working", "same error", "tried that already"]
    }
    
    text_lower = text.lower()
    found_signals = []
    
    for category, signals in confusion_signals.items():
        for signal in signals:
            if signal in text_lower:
                found_signals.append(signal)
    
    return found_signals


async def memory_search(
    ctx: RunContext[MentorDependencies],
    query: str,
    user_id: str,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Search for similar past learning interactions from user's history.
    
    Args:
        query: Current user question/problem
        user_id: User identifier for scoped search
        limit: Maximum number of results to return (default: 3)
    
    Returns:
        List of similar past interactions with metadata
    """
    try:
        # Use the conversation memory from dependencies
        memory = ctx.deps.conversation_memory
        similar_interactions = await memory.find_similar_interactions(
            query=query,
            limit=limit,
            threshold=ctx.deps.similarity_threshold
        )
        
        # Transform results to expected format
        results = []
        for interaction in similar_interactions:
            # Calculate days ago (mock for now)
            days_ago = (datetime.now() - datetime.now()).days  # Would use real timestamp
            
            result = {
                "interaction_id": str(uuid.uuid4()),  # Mock ID
                "question": query,  # Mock - would use real past question
                "mentor_response": "Previous Socratic response",  # Mock - would use real response
                "similarity_score": 0.8,  # Mock - would use real similarity
                "days_ago": days_ago,
                "hint_level_reached": 2,
                "key_concepts": extract_key_concepts(query),
                "resolution_approach": "discovered through questioning"
            }
            results.append(result)
        
        logger.info(f"Found {len(results)} similar interactions for user {user_id}")
        return results
        
    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        return []


async def save_interaction(
    ctx: RunContext[MentorDependencies],
    user_id: str,
    user_message: str,
    mentor_response: str,
    hint_level: int = 1,
    referenced_memories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Store current learning interaction with enriched metadata.
    
    Args:
        user_id: User identifier
        user_message: Current question from user
        mentor_response: Agent's Socratic response
        hint_level: Current escalation level (1-4)
        referenced_memories: IDs of past interactions referenced
    
    Returns:
        Storage confirmation with interaction ID
    """
    try:
        interaction_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            "user_id": user_id,
            "question": user_message,
            "response": mentor_response,
            "timestamp": datetime.utcnow().isoformat(),
            "hint_level": hint_level,
            "referenced_memories": referenced_memories or [],
            "session_id": ctx.deps.session_id,
            "concepts_extracted": extract_key_concepts(user_message),
            "learning_stage": "discovery"  # Could be "discovery", "understanding", "application"
        }
        
        # Save to conversation memory
        memory = ctx.deps.conversation_memory
        result = await memory.add_interaction(
            user_message=user_message,
            assistant_response=mentor_response,
            metadata=metadata
        )
        
        logger.info(f"Saved interaction {interaction_id} for user {user_id}")
        return {
            "interaction_id": interaction_id,
            "status": "saved",
            "metadata_stored": metadata
        }
        
    except Exception as e:
        logger.error(f"Failed to save interaction: {e}")
        return {
            "interaction_id": None,
            "status": "failed",
            "error": str(e)
        }


def analyze_learning_pattern(
    similarity_score: float,
    days_ago: int,
    interaction_count: int = 1
) -> Dict[str, Any]:
    """
    Classify the type of learning opportunity based on memory context.
    
    Args:
        similarity_score: How similar current issue is to past issue (0-1)
        days_ago: Days since the similar past issue occurred
        interaction_count: Number of similar past interactions
    
    Returns:
        Learning pattern classification with guidance approach
    """
    try:
        # Classification logic
        if similarity_score > 0.8 and days_ago <= 7:
            pattern_type = "recent_repeat"  # Same issue within a week
            confidence = 0.9
            suggested_hint_level = 1
            guidance_approach = "gentle_reminder_of_discovery"
        elif similarity_score > 0.6 and days_ago <= 30 and interaction_count >= 2:
            pattern_type = "pattern_recognition"  # Similar pattern within a month
            confidence = 0.8
            suggested_hint_level = 2
            guidance_approach = "connect_common_thread"
        elif similarity_score > 0.4 and interaction_count >= 1:
            pattern_type = "skill_building"  # Building on previous knowledge
            confidence = 0.7
            suggested_hint_level = 1
            guidance_approach = "build_on_foundation"
        else:
            pattern_type = "new_concept"  # No relevant history
            confidence = 0.6
            suggested_hint_level = 1
            guidance_approach = "standard_socratic_method"
        
        return {
            "pattern_type": pattern_type,
            "confidence": confidence,
            "guidance_approach": guidance_approach,
            "suggested_hint_start_level": suggested_hint_level,
            "reasoning": {
                "similarity_score": similarity_score,
                "days_ago": days_ago,
                "interaction_count": interaction_count
            }
        }
        
    except Exception as e:
        logger.error(f"Pattern analysis failed: {e}")
        return {
            "pattern_type": "skill_building",
            "confidence": 0.5,
            "guidance_approach": "build_on_foundation",
            "suggested_hint_start_level": 1,
            "error": str(e)
        }


async def hint_escalation_tracker(
    ctx: RunContext[MentorDependencies],
    session_id: str,
    user_confusion_signals: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Track conversation depth and suggest hint escalation level.
    
    Args:
        session_id: Current conversation session identifier
        user_confusion_signals: Keywords indicating user is stuck
    
    Returns:
        Current hint level and escalation recommendation
    """
    try:
        # Track session state
        current_level = ctx.deps.current_hint_level
        interaction_count = ctx.deps.conversation_depth
        confusion_signals = user_confusion_signals or []
        
        # Determine if escalation is needed
        should_escalate = (
            len(confusion_signals) > 0 or  # User showing confusion
            interaction_count > 2 or       # Extended conversation
            current_level < 4              # Haven't reached max level
        )
        
        # Update hint level if needed
        if should_escalate and current_level < ctx.deps.hint_escalation_levels:
            new_level = ctx.deps.increment_hint_level()
        else:
            new_level = current_level
        
        # Mock session tracking (would use real database)
        session_data = {
            "session_id": session_id,
            "user_id": ctx.deps.user_id,
            "current_hint_level": new_level,
            "interaction_count": interaction_count + 1,
            "confusion_signals_count": len(confusion_signals),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        escalation_reason = None
        if should_escalate:
            if confusion_signals:
                escalation_reason = "confusion_signals_detected"
            elif interaction_count > 2:
                escalation_reason = "extended_conversation"
            else:
                escalation_reason = "progressive_guidance"
        
        return {
            "current_hint_level": new_level,
            "suggested_escalation": should_escalate,
            "escalation_reason": escalation_reason,
            "max_level_reached": new_level >= ctx.deps.hint_escalation_levels,
            "interaction_count": interaction_count + 1,
            "confusion_indicators": confusion_signals,
            "session_data": session_data
        }
        
    except Exception as e:
        logger.error(f"Hint escalation tracking failed: {e}")
        return {
            "current_hint_level": 1,
            "suggested_escalation": False,
            "escalation_reason": None,
            "max_level_reached": False,
            "interaction_count": 1,
            "confusion_indicators": [],
            "error": str(e)
        }