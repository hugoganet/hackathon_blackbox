"""
Mentor Agent - Memory-Enhanced Socratic Programming Mentor

A Pydantic AI agent that guides junior developers through learning using the Socratic method,
enhanced with memory of past interactions to provide personalized guidance.
"""

import logging
from typing import Optional, List, Dict, Any
from pydantic_ai import Agent, RunContext

from .providers import get_mentor_llm_model, get_fallback_model
from .dependencies import MentorDependencies
from .settings import mentor_settings
from .prompts import SYSTEM_PROMPT, recent_repeat_context, pattern_recognition_context, skill_building_context
from .tools import memory_search, save_interaction, analyze_learning_pattern, hint_escalation_tracker, detect_confusion_signals

logger = logging.getLogger(__name__)

# Initialize the mentor agent with OpenAI
mentor_agent = Agent(
    get_mentor_llm_model(),
    deps_type=MentorDependencies,
    system_prompt=SYSTEM_PROMPT,
    retries=mentor_settings.max_retries
)

# Register dynamic system prompts for different learning contexts
mentor_agent.system_prompt(recent_repeat_context)
mentor_agent.system_prompt(pattern_recognition_context)
mentor_agent.system_prompt(skill_building_context)

# Register fallback model if available
fallback = get_fallback_model()
if fallback:
    mentor_agent.models.append(fallback)
    logger.info("Fallback model configured for mentor agent")


# Tool 1: Memory Search
@mentor_agent.tool
async def search_memory(
    ctx: RunContext[MentorDependencies], 
    query: str, 
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Search for similar past learning interactions to provide memory context.
    
    Args:
        query: Current user question to search for similar past issues
        limit: Maximum number of similar interactions to retrieve
    
    Returns:
        List of similar past interactions with metadata
    """
    return await memory_search(ctx, query, ctx.deps.user_id, limit)


# Tool 2: Save Interaction
@mentor_agent.tool
async def save_learning_interaction(
    ctx: RunContext[MentorDependencies],
    user_message: str,
    mentor_response: str,
    hint_level: Optional[int] = None,
    referenced_memories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Save the current learning interaction for future reference.
    
    Args:
        user_message: The user's question or message
        mentor_response: The mentor's Socratic response
        hint_level: Current hint escalation level (1-4)
        referenced_memories: IDs of past memories referenced in response
    
    Returns:
        Confirmation of interaction saved with metadata
    """
    hint_level = hint_level or ctx.deps.current_hint_level
    return await save_interaction(
        ctx, ctx.deps.user_id, user_message, mentor_response, hint_level, referenced_memories
    )


# Tool 3: Analyze Learning Pattern
@mentor_agent.tool_plain
def classify_learning_opportunity(
    similarity_score: float,
    days_ago: int,
    interaction_count: int = 1
) -> Dict[str, Any]:
    """
    Classify the type of learning opportunity based on past interactions.
    
    Args:
        similarity_score: How similar current question is to past questions (0-1)
        days_ago: Days since the most similar past interaction
        interaction_count: Number of similar past interactions
    
    Returns:
        Learning pattern classification and suggested approach
    """
    return analyze_learning_pattern(similarity_score, days_ago, interaction_count)


# Tool 4: Hint Escalation Tracker
@mentor_agent.tool
async def track_hint_escalation(
    ctx: RunContext[MentorDependencies],
    user_message: str
) -> Dict[str, Any]:
    """
    Track conversation depth and determine appropriate hint escalation level.
    
    Args:
        user_message: Latest message from user to analyze for confusion signals
    
    Returns:
        Hint level recommendation and escalation status
    """
    confusion_signals = detect_confusion_signals(user_message)
    return await hint_escalation_tracker(ctx, ctx.deps.session_id, confusion_signals)


# Convenience functions for using the mentor agent

async def run_mentor_agent(
    prompt: str,
    user_id: str,
    session_id: Optional[str] = None,
    **dependency_overrides
) -> str:
    """
    Run the mentor agent with automatic dependency injection.
    
    Args:
        prompt: User's programming question
        user_id: User identifier for memory retrieval
        session_id: Optional session identifier for hint tracking
        **dependency_overrides: Override default dependencies
    
    Returns:
        Mentor's Socratic response as string
    """
    deps = MentorDependencies.from_settings(
        mentor_settings,
        user_id=user_id,
        session_id=session_id,
        **dependency_overrides
    )
    
    try:
        # Search for similar past interactions first
        similar_interactions = await memory_search(None, prompt, user_id, 3)
        
        # Analyze learning pattern if we found similar interactions
        if similar_interactions:
            most_similar = similar_interactions[0]
            pattern_analysis = analyze_learning_pattern(
                most_similar['similarity_score'],
                most_similar['days_ago'],
                len(similar_interactions)
            )
            # Add pattern analysis to deps for dynamic prompts
            deps.learning_classification = pattern_analysis['pattern_type']
        
        # Run the agent
        result = await mentor_agent.run(prompt, deps=deps)
        
        # Save the interaction for future reference
        await save_interaction(None, user_id, prompt, result.data, deps.current_hint_level)
        
        return result.data
    except Exception as e:
        logger.error(f"Mentor agent execution failed: {e}")
        return "I apologize, but I'm having trouble accessing my memory systems right now. Let's work through your question step by step. What specific programming challenge are you facing?"
    finally:
        await deps.cleanup()


async def run_mentor_conversation(
    messages: List[Dict[str, str]],
    user_id: str,
    session_id: Optional[str] = None
) -> str:
    """
    Run a multi-turn conversation with the mentor agent.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        user_id: User identifier for memory context
        session_id: Session identifier for hint tracking
    
    Returns:
        Mentor's response to the latest message
    """
    if not messages:
        return "Hello! I'm your programming mentor. What would you like to work on today?"
    
    # Get the latest user message
    latest_message = messages[-1]['content']
    
    # Create dependencies with session context
    deps = MentorDependencies.from_settings(
        mentor_settings,
        user_id=user_id,
        session_id=session_id
    )
    
    try:
        # Track hint escalation based on conversation history
        escalation_data = await hint_escalation_tracker(
            type('MockCtx', (), {'deps': deps})(),
            session_id or "default",
            detect_confusion_signals(latest_message)
        )
        
        # Update deps with escalation data
        deps.current_hint_level = escalation_data['current_hint_level']
        
        # Run the agent with full conversation context
        result = await mentor_agent.run(latest_message, deps=deps)
        
        # Save the interaction
        await save_interaction(
            type('MockCtx', (), {'deps': deps})(),
            user_id,
            latest_message,
            result.data,
            deps.current_hint_level
        )
        
        return result.data
        
    except Exception as e:
        logger.error(f"Mentor conversation failed: {e}")
        return "I'm having some technical difficulties, but let's continue. Can you tell me more about what you're trying to accomplish?"
    finally:
        await deps.cleanup()


def create_mentor_agent_with_deps(user_id: str, **dependency_overrides):
    """
    Create mentor agent instance with custom dependencies.
    
    Args:
        user_id: User identifier for memory context
        **dependency_overrides: Custom dependency values
    
    Returns:
        Tuple of (agent, dependencies)
    """
    deps = MentorDependencies.from_settings(
        mentor_settings, 
        user_id=user_id, 
        **dependency_overrides
    )
    return mentor_agent, deps


# Main execution function for testing
if __name__ == "__main__":
    import asyncio
    
    async def test_mentor():
        """Test the mentor agent with a sample question."""
        response = await run_mentor_agent(
            "I'm having trouble with React state not updating immediately",
            user_id="test-user-123"
        )
        print(f"Mentor Response: {response}")
    
    asyncio.run(test_mentor())