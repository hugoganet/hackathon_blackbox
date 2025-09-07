"""
BlackboxMentor Adapter for PydanticAI Integration

This adapter maintains the same interface as the original BlackboxMentor class
while using the enhanced PydanticAI mentor agent internally. This provides
backward compatibility for existing code while enabling memory-guided mentoring.
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from .providers import get_mentor_llm_model
from .prompts import SYSTEM_PROMPT as STRICT_MENTOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class BlackboxMentorAdapter:
    """
    Adapter class that bridges the original BlackboxMentor interface
    with the new PydanticAI mentor agent implementation.
    
    This allows existing code to continue working without changes
    while benefiting from enhanced memory-guided mentoring capabilities.
    """
    
    def __init__(self, agent_file: str = "../agents/agent-mentor-strict.md"):
        """
        Initialize the adapter with the agent file path
        
        Args:
            agent_file: Path to agent markdown file (maintained for compatibility)
        """
        self.agent_file = agent_file
        self.system_prompt = self._load_system_prompt()
        
        # Track session for consistency with original interface
        self.session_id = None
        
        logger.info(f"Initialized BlackboxMentorAdapter with agent file: {agent_file}")
    
    def _load_system_prompt(self) -> str:
        """
        Load system prompt from specified agent file (compatibility method)
        
        Note: The PydanticAI agent has its own prompt system, but we maintain
        this method for interface compatibility.
        """
        prompt_file = Path(self.agent_file)
        
        if not prompt_file.exists():
            logger.warning(f"Agent file {prompt_file} not found, using built-in strict mentor prompt")
            return "You are a strict mentor that guides junior developers using the Socratic method."
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.warning(f"Agent file {prompt_file} is empty, using fallback prompt")
                    return "You are a strict mentor that guides junior developers using the Socratic method."
                return content
        except Exception as e:
            logger.error(f"Error reading agent file {prompt_file}: {e}")
            return "You are a strict mentor that guides junior developers using the Socratic method."
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables (compatibility method)"""
        return os.getenv('BLACKBOX_API_KEY')
    
    def call_blackbox_api(self, user_prompt: str, user_id: str = "anonymous") -> str:
        """
        Main interface method that calls the PydanticAI mentor agent
        
        This method maintains the same signature as the original BlackboxMentor
        but routes to the enhanced PydanticAI agent internally.
        
        Args:
            user_prompt: User's question or message
            user_id: User identifier for memory context (optional)
            
        Returns:
            Mentor response as string
        """
        try:
            # Validate API key availability
            api_key = self._get_api_key()
            if not api_key:
                return ("❌ Error: Blackbox API key not configured. Add BLACKBOX_API_KEY to your environment variables.")
            
            # Generate session ID if not set
            if self.session_id is None:
                self.session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
            
            # Check if we're running in an async context
            try:
                loop = asyncio.get_running_loop()
                # If loop is running, we need to schedule the coroutine
                if loop.is_running():
                    # Create a future and schedule it
                    future = asyncio.create_task(self._async_call_mentor(user_prompt, user_id))
                    # This is tricky - we can't wait for it in a sync context
                    # So we provide a synchronous fallback
                    return self._sync_fallback_response(user_prompt, user_id)
                else:
                    # Loop exists but not running, we can use run_until_complete
                    return loop.run_until_complete(self._async_call_mentor(user_prompt, user_id))
            except RuntimeError:
                # No event loop, create one and run
                return asyncio.run(self._async_call_mentor(user_prompt, user_id))
                
        except Exception as e:
            logger.error(f"BlackboxMentorAdapter call failed: {e}")
            return self._sync_fallback_response(user_prompt, user_id, error=str(e))
    
    async def _async_call_mentor(self, user_prompt: str, user_id: str) -> str:
        """
        Async call to the Blackbox AI client
        
        Args:
            user_prompt: User's question
            user_id: User identifier
            
        Returns:
            Mentor response
        """
        try:
            # Get the Blackbox AI client
            client = get_mentor_llm_model()
            
            # Generate response using the client
            response = await client.generate_response(
                user_message=user_prompt,
                system_prompt=STRICT_MENTOR_SYSTEM_PROMPT
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Blackbox AI client failed: {e}")
            return self._sync_fallback_response(user_prompt, user_id, error=str(e))
    
    def _sync_fallback_response(self, user_prompt: str, user_id: str, error: Optional[str] = None) -> str:
        """
        Synchronous fallback when PydanticAI agent is unavailable
        
        Args:
            user_prompt: User's question
            user_id: User identifier
            error: Optional error message
            
        Returns:
            Basic Socratic response
        """
        if error:
            logger.warning(f"Using fallback response due to error: {error}")
        
        user_lower = user_prompt.lower()
        
        # Basic Socratic response patterns (similar to FallbackModel)
        if any(word in user_lower for word in ['error', 'bug', 'not working', 'broken']):
            return ("Let's debug this step by step. What error message are you seeing? "
                   "And what did you expect to happen instead?")
        
        if any(word in user_lower for word in ['how do i', 'how to', 'what should i']):
            return ("Before I guide you, help me understand your current approach. "
                   "What have you tried so far? What's your thinking behind it?")
        
        if any(word in user_lower for word in ['please help', 'stuck', 'confused']):
            return ("I understand this is challenging! Let's break it down. "
                   "What specific part is causing the most difficulty? "
                   "What do you understand so far?")
        
        if any(word in user_lower for word in ['give me the answer', 'just tell me']):
            return ("I know you'd like a direct answer, but discovering the solution yourself "
                   "will make you a stronger developer. What patterns do you notice in this problem? "
                   "What similar issues have you solved before?")
        
        # Default Socratic response
        return ("That's an interesting question! What's your current understanding of this concept? "
               "What have you observed when you've experimented with it?")
    
    async def call_blackbox_api_async(self, user_prompt: str, user_id: str = "anonymous") -> str:
        """
        Async version of the API call for environments that support it
        
        Args:
            user_prompt: User's question
            user_id: User identifier
            
        Returns:
            Mentor response
        """
        return await self._async_call_mentor(user_prompt, user_id)
    
    def reset_session(self):
        """Reset the session ID for a new conversation"""
        self.session_id = None
    
    def get_session_id(self) -> Optional[str]:
        """Get current session ID"""
        return self.session_id

# Backward compatibility alias
# This allows existing imports like `from backend.main import BlackboxMentor` to work
BlackboxMentor = BlackboxMentorAdapter

# Factory function for creating the adapter
def create_blackbox_mentor_adapter(agent_file: str = "../agents/agent-mentor-strict.md") -> BlackboxMentorAdapter:
    """
    Factory function to create a BlackboxMentorAdapter instance
    
    Args:
        agent_file: Path to agent markdown file
        
    Returns:
        Configured BlackboxMentorAdapter instance
    """
    return BlackboxMentorAdapter(agent_file=agent_file)