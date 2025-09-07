"""
PydanticAI Mentor Agent
Main agent implementation with memory-guided mentoring capabilities
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model
import os
import asyncio
from datetime import datetime

from .prompts import (
    STRICT_MENTOR_SYSTEM_PROMPT, 
    format_memory_context,
    get_hint_escalation_response,
    get_frustration_response,
    get_progress_celebration
)
from .tools import MentorTools, MemoryContext

class MentorAgentDeps(BaseModel):
    """Dependencies for the Mentor Agent"""
    memory_store: Optional[Any] = None
    db_session: Optional[Any] = None
    user_id: str
    session_id: Optional[str] = None

class MentorResponse(BaseModel):
    """Structured response from the mentor agent"""
    response: str
    hint_level: Optional[int] = None
    memory_context_used: bool = False
    detected_language: Optional[str] = None
    detected_intent: Optional[str] = None
    similar_interactions_count: int = 0

class MentorAgent:
    """
    PydanticAI-based Strict Mentor Agent
    
    Provides memory-guided mentoring with progressive hints while maintaining
    strict pedagogical principles of never giving direct answers.
    """
    
    def __init__(self, model: Optional[Model] = None):
        """
        Initialize the Mentor Agent
        
        Args:
            model: PydanticAI model instance (defaults to OpenAI if not provided)
        """
        # Use OpenAI as default model if none provided
        if model is None:
            from pydantic_ai.models.openai import OpenAIModel
            api_key = os.getenv('OPENAI_API_KEY') or os.getenv('BLACKBOX_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY or BLACKBOX_API_KEY must be set")
            model = OpenAIModel('gpt-4', api_key=api_key)
        
        # Initialize the PydanticAI agent
        self.agent = Agent(
            model=model,
            result_type=MentorResponse,
            system_prompt=STRICT_MENTOR_SYSTEM_PROMPT,
            deps_type=MentorAgentDeps
        )
        
        # Register tools
        self._register_tools()
        
        print("✅ PydanticAI Mentor Agent initialized")
    
    def _register_tools(self):
        """Register tools with the PydanticAI agent"""
        
        @self.agent.tool
        async def get_memory_context(ctx: RunContext[MentorAgentDeps], user_message: str) -> str:
            """
            Retrieve memory context for personalized mentoring
            
            Args:
                user_message: Current user question
                
            Returns:
                Formatted memory context string
            """
            tools = MentorTools(ctx.deps.memory_store, ctx.deps.db_session)
            
            memory_context = await tools.get_memory_context(
                user_id=ctx.deps.user_id,
                current_message=user_message,
                session_id=ctx.deps.session_id
            )
            
            # Format memory context for the agent
            if memory_context.similar_interactions or memory_context.learning_patterns.total_interactions > 0:
                patterns_dict = {
                    "total_interactions": memory_context.learning_patterns.total_interactions,
                    "most_common_language": memory_context.learning_patterns.most_common_language,
                    "most_common_intent": memory_context.learning_patterns.most_common_intent,
                    "languages_practiced": memory_context.learning_patterns.languages_practiced
                }
                
                similar_interactions = [
                    {
                        "user_message": interaction.user_message,
                        "similarity": interaction.similarity,
                        "metadata": interaction.metadata
                    }
                    for interaction in memory_context.similar_interactions
                ]
                
                return format_memory_context(patterns_dict, similar_interactions)
            
            return "No previous learning history available for this user."
        
        @self.agent.tool
        async def track_hint_progression(ctx: RunContext[MentorAgentDeps], question: str, hint: str) -> str:
            """
            Track hint escalation and provide appropriate level of guidance
            
            Args:
                question: Current question being asked
                hint: Hint being provided
                
            Returns:
                Formatted hint response with appropriate escalation
            """
            tools = MentorTools(ctx.deps.memory_store, ctx.deps.db_session)
            
            hint_level = await tools.track_hint_escalation(
                user_id=ctx.deps.user_id,
                session_id=ctx.deps.session_id or "default",
                question=question,
                hint=hint
            )
            
            return get_hint_escalation_response(hint_level, hint)
        
        @self.agent.tool
        async def analyze_user_context(ctx: RunContext[MentorAgentDeps], user_message: str) -> str:
            """
            Analyze user intent and programming language from their message
            
            Args:
                user_message: User's question or message
                
            Returns:
                Context analysis for better response customization
            """
            tools = MentorTools(ctx.deps.memory_store, ctx.deps.db_session)
            
            intent = await tools.classify_user_intent(user_message)
            language = await tools.detect_programming_language(user_message)
            difficulty = await tools.analyze_difficulty_level(user_message)
            
            return f"Context Analysis - Intent: {intent}, Language: {language}, Difficulty: {difficulty}"
        
        @self.agent.tool
        async def provide_encouragement(ctx: RunContext[MentorAgentDeps]) -> str:
            """
            Provide encouraging response for user progress
            
            Returns:
                Encouraging message template
            """
            return get_progress_celebration()
        
        @self.agent.tool
        async def handle_frustration(ctx: RunContext[MentorAgentDeps]) -> str:
            """
            Handle user frustration with supportive guidance
            
            Returns:
                Supportive response template
            """
            return get_frustration_response()
    
    async def respond(
        self, 
        user_message: str, 
        user_id: str,
        session_id: Optional[str] = None,
        memory_store: Optional[Any] = None,
        db_session: Optional[Any] = None
    ) -> MentorResponse:
        """
        Generate mentor response to user message
        
        Args:
            user_message: User's question or message
            user_id: User identifier
            session_id: Session identifier
            memory_store: ConversationMemory instance
            db_session: Database session
            
        Returns:
            MentorResponse with guidance and metadata
        """
        deps = MentorAgentDeps(
            memory_store=memory_store,
            db_session=db_session,
            user_id=user_id,
            session_id=session_id
        )
        
        try:
            # Run the PydanticAI agent
            result = await self.agent.run(user_message, deps=deps)
            
            # Extract metadata from tools if available
            tools = MentorTools(memory_store, db_session)
            detected_language = await tools.detect_programming_language(user_message)
            detected_intent = await tools.classify_user_intent(user_message)
            
            # Get memory context to count similar interactions
            memory_context = await tools.get_memory_context(user_id, user_message, session_id)
            
            # Store this interaction for future reference
            if memory_store:
                await tools.store_interaction(
                    user_id=user_id,
                    user_message=user_message,
                    mentor_response=result.data.response,
                    session_id=session_id,
                    metadata={
                        "detected_language": detected_language,
                        "detected_intent": detected_intent,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            return MentorResponse(
                response=result.data.response,
                memory_context_used=len(memory_context.similar_interactions) > 0,
                detected_language=detected_language,
                detected_intent=detected_intent,
                similar_interactions_count=len(memory_context.similar_interactions)
            )
            
        except Exception as e:
            # Fallback response if PydanticAI fails
            return MentorResponse(
                response=f"I apologize, but I'm having trouble processing your question right now. "
                        f"However, I can still help! Let's start with this: what specific part of "
                        f"your problem would you like to focus on first? What have you already tried?",
                memory_context_used=False,
                detected_language="unknown",
                detected_intent="general",
                similar_interactions_count=0
            )
    
    async def respond_sync(
        self,
        user_message: str,
        user_id: str, 
        session_id: Optional[str] = None,
        memory_store: Optional[Any] = None,
        db_session: Optional[Any] = None
    ) -> MentorResponse:
        """
        Synchronous wrapper for respond method
        
        This allows integration with existing synchronous code
        """
        return await self.respond(user_message, user_id, session_id, memory_store, db_session)

class BlackboxMentorAdapter:
    """
    Adapter to maintain compatibility with existing BlackboxMentor interface
    
    This allows gradual migration from the old system to PydanticAI
    """
    
    def __init__(self, agent_file: Optional[str] = None):
        """Initialize the adapter with PydanticAI mentor"""
        self.mentor_agent = MentorAgent()
        self.agent_file = agent_file  # Kept for compatibility
    
    def call_blackbox_api(self, user_prompt: str, user_id: str = "anonymous") -> str:
        """
        Compatibility method that mimics the original BlackboxMentor interface
        
        Args:
            user_prompt: User's question
            user_id: User identifier (defaults to anonymous)
            
        Returns:
            Mentor response as string
        """
        try:
            # Run async method in sync context
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # If loop is already running, use sync method
                import asyncio
                result = asyncio.create_task(self.mentor_agent.respond(user_prompt, user_id))
                # This is a workaround for environments where async isn't easily available
                return self._sync_fallback(user_prompt)
            else:
                result = loop.run_until_complete(
                    self.mentor_agent.respond(user_prompt, user_id)
                )
                return result.response
                
        except Exception as e:
            # Fallback to basic mentor behavior
            return self._sync_fallback(user_prompt)
    
    def _sync_fallback(self, user_prompt: str) -> str:
        """Synchronous fallback if async execution fails"""
        # Basic Socratic response patterns
        if any(word in user_prompt.lower() for word in ["please give me", "just tell me", "what's the answer"]):
            return ("I understand you'd like a direct answer, but my role is to help you discover "
                   "the solution yourself. What have you tried so far? What's your current understanding "
                   "of this problem?")
        
        if any(word in user_prompt.lower() for word in ["error", "not working", "bug"]):
            return ("Let's debug this step by step! First, can you tell me exactly what error "
                   "message you're seeing? And what did you expect to happen instead?")
        
        return ("That's a great question! Before I guide you toward the answer, help me understand "
               "your current approach. What have you tried so far, and what's your thinking behind it?")

# Factory function for easy instantiation
def create_mentor_agent(model: Optional[Model] = None) -> MentorAgent:
    """
    Factory function to create a MentorAgent instance
    
    Args:
        model: Optional PydanticAI model, defaults to OpenAI GPT-4
        
    Returns:
        Configured MentorAgent instance
    """
    return MentorAgent(model=model)

# Backward compatibility alias
PydanticMentor = MentorAgent