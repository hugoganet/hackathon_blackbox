"""
PydanticAI Mentor Agent Package

A sophisticated mentor agent implementation using PydanticAI for memory-guided,
progressive hint-based learning support for junior developers.

This package provides:
- Strict Socratic method mentoring (never gives direct answers)
- Memory-guided personalization using ChromaDB vector store
- Progressive hint escalation system (4 levels)
- Learning pattern analysis and skill progression tracking
- Backward compatibility with existing BlackboxMentor interface
"""

from .agent import MentorAgent, BlackboxMentorAdapter, create_mentor_agent, PydanticMentor
from .tools import MentorTools, MemoryContext, HintTracker
from .prompts import (
    STRICT_MENTOR_SYSTEM_PROMPT,
    format_memory_context,
    get_hint_escalation_response,
    get_frustration_response,
    get_progress_celebration
)

__version__ = "1.0.0"

__all__ = [
    # Main agent classes
    "MentorAgent",
    "BlackboxMentorAdapter", 
    "PydanticMentor",
    "create_mentor_agent",
    
    # Tools and utilities
    "MentorTools",
    "MemoryContext",
    "HintTracker",
    
    # Prompt utilities
    "STRICT_MENTOR_SYSTEM_PROMPT",
    "format_memory_context",
    "get_hint_escalation_response",
    "get_frustration_response", 
    "get_progress_celebration",
]

# Package metadata
AGENT_DESCRIPTION = """
Strict Mentor Agent with Memory-Guided Mentoring

This PydanticAI-based agent provides personalized learning support for junior developers
using a strict Socratic methodology. Key features:

- **No Direct Answers**: Maintains pedagogical integrity by never providing complete solutions
- **Memory Integration**: Uses past interactions to personalize guidance and track progress  
- **Progressive Hints**: 4-level hint escalation system for optimal learning difficulty
- **Context Awareness**: Analyzes programming language, intent, and difficulty level
- **Learning Analytics**: Tracks skill progression and identifies knowledge gaps

Perfect for mentoring environments where autonomous learning and problem-solving 
skill development are prioritized over quick answers.
"""

# Configuration defaults
DEFAULT_CONFIG = {
    "similarity_threshold": 0.7,
    "max_memory_results": 3,
    "hint_escalation_levels": 4,
    "context_window_hours": 1,
    "memory_retention_days": 90,
}
