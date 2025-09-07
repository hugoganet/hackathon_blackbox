"""
BlackboxAI provider configuration for the mentor agent.
Maintains consistency with existing system setup.
"""

from typing import Optional
from pydantic_ai.models import Model
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from .settings import mentor_settings


def get_mentor_llm_model(model_choice: Optional[str] = None) -> OpenAIModel:
    """
    Get OpenAI model configuration for mentor agent.
    Using OpenAI as fallback since BlackboxAI may not be available in Pydantic AI.
    
    Args:
        model_choice: Optional override for model choice
    
    Returns:
        Configured OpenAI model instance
    """
    # Use GPT-4 as the primary model for quality Socratic mentoring
    model_name = model_choice or "gpt-4"
    
    provider = OpenAIProvider(
        api_key=mentor_settings.llm_api_key
    )
    
    return OpenAIModel(model_name, provider=provider)


def get_fallback_model() -> Optional[OpenAIModel]:
    """
    Get fallback model for reliability.
    Uses GPT-3.5 for basic interactions if needed.
    
    Returns:
        Fallback OpenAI model or None
    """
    if mentor_settings.app_env == "production":
        provider = OpenAIProvider(api_key=mentor_settings.llm_api_key)
        return OpenAIModel("gpt-3.5-turbo", provider=provider)
    return None