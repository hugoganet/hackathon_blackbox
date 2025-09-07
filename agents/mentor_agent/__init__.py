"""
Mentor Agent Package - Memory-Enhanced Socratic Programming Mentor

A Pydantic AI agent that guides junior developers through learning using the Socratic method,
enhanced with memory of past interactions for personalized guidance.
"""

from .agent import mentor_agent, run_mentor_agent, run_mentor_conversation
from .settings import mentor_settings
from .dependencies import MentorDependencies
from .providers import get_mentor_llm_model

__version__ = "1.0.0"
__all__ = [
    "mentor_agent",
    "run_mentor_agent", 
    "run_mentor_conversation",
    "mentor_settings",
    "MentorDependencies",
    "get_mentor_llm_model"
]