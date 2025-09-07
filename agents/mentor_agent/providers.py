"""
Blackbox AI Provider for PydanticAI Integration
Bridges PydanticAI agent with Blackbox AI API for mentor functionality
"""

import os
import logging
from typing import Optional, Dict, Any, List
import asyncio
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class BlackboxAPIClient:
    """
    Simple Blackbox AI client that doesn't inherit from PydanticAI Model
    This provides a simpler integration path while we work out PydanticAI compatibility
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "blackboxai/anthropic/claude-sonnet-4"):
        self.api_key = api_key or os.getenv("BLACKBOX_API_KEY")
        self.model_name = model_name
        self.base_url = "https://api.blackbox.ai/chat/completions"
        
        if not self.api_key:
            logger.warning("BLACKBOX_API_KEY not found, will use fallback responses")
        
        logger.info(f"Initialized BlackboxAPIClient with model: {model_name}")
    
    async def generate_response(self, user_message: str, system_prompt: str = None) -> str:
        """
        Generate response using Blackbox AI API
        
        Args:
            user_message: User's question
            system_prompt: System prompt (optional)
            
        Returns:
            Response from Blackbox AI or fallback response
        """
        try:
            if not self.api_key:
                return self._fallback_response(user_message)
            
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })
            messages.append({
                'role': 'user',
                'content': user_message
            })
            
            # Prepare API request
            payload = {
                'model': self.model_name,
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 1000,
                'stream': False
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            # Make request (using sync requests for simplicity)
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                else:
                    logger.warning("Unexpected Blackbox response format")
                    return self._fallback_response(user_message)
            else:
                logger.error(f"Blackbox API error {response.status_code}: {response.text}")
                return self._fallback_response(user_message)
                
        except Exception as e:
            logger.error(f"Blackbox API request failed: {e}")
            return self._fallback_response(user_message)
    
    def _fallback_response(self, user_message: str) -> str:
        """Provide fallback Socratic response when API is unavailable"""
        user_lower = user_message.lower()
        
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
                   "will make you a stronger developer. What patterns do you notice in this problem?")
        
        # Default Socratic response
        return ("That's an interesting question! What's your current understanding of this concept? "
               "What have you observed when you've experimented with it?")

# Factory functions for model creation

def get_mentor_llm_model(model_choice: Optional[str] = None) -> BlackboxAPIClient:
    """
    Get the primary LLM client for the mentor agent (Blackbox AI)
    
    Returns:
        BlackboxAPIClient configured for mentor interactions
    """
    return BlackboxAPIClient(model_name=model_choice or "blackboxai/anthropic/claude-sonnet-4")

def get_fallback_model() -> Optional[BlackboxAPIClient]:
    """
    Get fallback model for when primary model fails
    
    Returns:
        BlackboxAPIClient for offline operation
    """
    return BlackboxAPIClient()

# Compatibility functions
def create_blackbox_model(
    api_key: Optional[str] = None,
    model_name: str = "blackboxai/anthropic/claude-sonnet-4"
) -> BlackboxAPIClient:
    """
    Create a Blackbox AI client with custom configuration
    
    Args:
        api_key: Blackbox API key (defaults to environment variable)
        model_name: Model name to use
        
    Returns:
        Configured BlackboxAPIClient
    """
    return BlackboxAPIClient(api_key=api_key, model_name=model_name)