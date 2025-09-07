"""
Test configuration for Mentor Agent.

Provides shared fixtures and utilities for comprehensive testing using
Pydantic AI's TestModel and FunctionModel patterns.
"""

import pytest
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelTextResponse

from ..agent import mentor_agent, run_mentor_agent
from ..dependencies import MentorDependencies, LearningMemory
from ..settings import MentorSettings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_model():
    """Create TestModel for basic agent testing."""
    return TestModel()


@pytest.fixture
def test_mentor_agent(test_model):
    """Create mentor agent with TestModel for fast testing."""
    return mentor_agent.override(model=test_model)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=MentorSettings)
    settings.llm_api_key = "test-api-key"
    settings.database_url = "postgresql://test:test@localhost:5432/test_db"
    settings.chroma_path = "./test_chroma_memory"
    settings.max_memory_results = 3
    settings.similarity_threshold = 0.7
    settings.recent_repeat_days = 7
    settings.pattern_recognition_days = 30
    settings.hint_escalation_levels = 4
    settings.debug = True
    settings.max_retries = 3
    settings.timeout_seconds = 30
    return settings


@pytest.fixture
def test_dependencies(mock_settings):
    """Create test dependencies with mocked services."""
    return MentorDependencies.from_settings(
        mock_settings,
        user_id="test-user-123",
        session_id="test-session-456"
    )


@pytest.fixture
def mock_conversation_memory():
    """Mock ConversationMemory with test data."""
    memory = Mock()
    memory.find_similar_interactions = AsyncMock(return_value=[])
    memory.add_interaction = AsyncMock(return_value={"id": "test-interaction", "status": "saved"})
    memory.close = AsyncMock()
    return memory


@pytest.fixture
def sample_past_interactions():
    """Sample past interaction data for testing."""
    return [
        {
            "interaction_id": "past-1",
            "question": "Why isn't my useState updating immediately?",
            "mentor_response": "What do you think happens when you call setState?",
            "similarity_score": 0.85,
            "days_ago": 3,
            "hint_level_reached": 2,
            "key_concepts": ["react", "state", "async"],
            "resolution_approach": "discovered through questioning"
        },
        {
            "interaction_id": "past-2", 
            "question": "My array map function isn't working",
            "mentor_response": "How does map differ from forEach?",
            "similarity_score": 0.65,
            "days_ago": 14,
            "hint_level_reached": 3,
            "key_concepts": ["array", "map", "function"],
            "resolution_approach": "step-by-step discovery"
        },
        {
            "interaction_id": "past-3",
            "question": "Promise not resolving correctly",
            "mentor_response": "What happens in the promise chain?",
            "similarity_score": 0.45,
            "days_ago": 30,
            "hint_level_reached": 1,
            "key_concepts": ["promise", "async", "javascript"],
            "resolution_approach": "guided exploration"
        }
    ]


@pytest.fixture
def socratic_response_function():
    """Create function that generates Socratic responses."""
    def generate_socratic_response(messages, tools):
        """Generate appropriate Socratic response based on input."""
        user_message = messages[-1].content if messages else ""
        
        # Never give direct answers - always respond with questions
        if "useState" in user_message:
            return ModelTextResponse(
                content="What do you think happens when React batches state updates? How might this relate to your previous experience with asynchronous operations?"
            )
        elif "error" in user_message.lower():
            return ModelTextResponse(
                content="What information does the error message provide? What have you tried to debug this so far?"
            )
        elif "confused" in user_message.lower() or "stuck" in user_message.lower():
            return ModelTextResponse(
                content="Let's break this down step by step. What's the first thing you notice about this problem? Does this remind you of anything you've encountered before?"
            )
        else:
            return ModelTextResponse(
                content="That's an interesting challenge. What's your first instinct about what might be causing this behavior?"
            )
    
    return generate_socratic_response


@pytest.fixture
def memory_search_function():
    """Create function that simulates memory search behavior."""
    def search_memory(messages, tools):
        """Simulate memory search tool call."""
        return {
            "search_memory": {
                "query": "test query",
                "limit": 3
            }
        }
    return search_memory


@pytest.fixture
def hint_escalation_function():
    """Create function that simulates hint escalation."""
    call_count = 0
    
    def escalate_hints(messages, tools):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            # Level 1 - Basic probing
            return ModelTextResponse(
                content="What patterns do you notice here? How does this relate to similar issues you've faced before?"
            )
        elif call_count == 2:
            # Level 2 - Pattern recognition
            return ModelTextResponse(
                content="Remember your question from last week about similar functionality? What was the key insight you discovered then?"
            )
        elif call_count == 3:
            # Level 3 - Specific guidance
            return ModelTextResponse(
                content="In your previous debugging session, you found that checking the console helped identify the root cause. What does the console tell you now?"
            )
        else:
            # Level 4 - Step-by-step with memory
            return ModelTextResponse(
                content="Let's use the same approach that worked for your previous issue. First step - what should we examine to understand the current state?"
            )
    
    return escalate_hints


@pytest.fixture
def learning_patterns():
    """Sample learning pattern classifications."""
    return {
        "recent_repeat": {
            "pattern_type": "recent_repeat",
            "confidence": 0.9,
            "guidance_approach": "gentle_reminder_of_discovery",
            "suggested_hint_start_level": 1
        },
        "pattern_recognition": {
            "pattern_type": "pattern_recognition", 
            "confidence": 0.8,
            "guidance_approach": "connect_common_thread",
            "suggested_hint_start_level": 2
        },
        "skill_building": {
            "pattern_type": "skill_building",
            "confidence": 0.7,
            "guidance_approach": "build_on_foundation",
            "suggested_hint_start_level": 1
        },
        "new_concept": {
            "pattern_type": "new_concept",
            "confidence": 0.6,
            "guidance_approach": "standard_socratic_method",
            "suggested_hint_start_level": 1
        }
    }


@pytest.fixture
def confusion_signals():
    """Sample confusion signal detection data."""
    return {
        "high_confusion": ["i don't understand", "i'm stuck", "help"],
        "medium_confusion": ["how?", "but why", "doesn't work"],
        "low_confusion": ["what if", "could it be", "maybe"],
        "no_confusion": ["i think", "let me try", "what about"]
    }


class MockChromaClient:
    """Mock ChromaDB client for testing."""
    
    def __init__(self):
        self.collections = {}
    
    def create_collection(self, name: str):
        collection = Mock()
        collection.query = Mock(return_value={"documents": [], "metadatas": [], "distances": []})
        collection.add = Mock()
        self.collections[name] = collection
        return collection
    
    def get_collection(self, name: str):
        return self.collections.get(name, self.create_collection(name))


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client."""
    return MockChromaClient()


# Helper functions for test data generation

def create_test_interaction(
    question: str = "Test question",
    similarity: float = 0.8,
    days_ago: int = 5,
    hint_level: int = 1,
    concepts: List[str] = None
) -> Dict[str, Any]:
    """Create a test interaction object."""
    return {
        "interaction_id": f"test-{hash(question) % 10000}",
        "question": question,
        "mentor_response": "What do you think about this approach?",
        "similarity_score": similarity,
        "days_ago": days_ago,
        "hint_level_reached": hint_level,
        "key_concepts": concepts or ["test", "programming"],
        "resolution_approach": "socratic_questioning"
    }


def create_test_memory_result(
    user_id: str = "test-user",
    interactions: List[Dict] = None
) -> List[Dict[str, Any]]:
    """Create test memory search results."""
    if interactions is None:
        interactions = [
            create_test_interaction("Previous React question", 0.85, 3),
            create_test_interaction("Array manipulation issue", 0.65, 14),
        ]
    return interactions


# Performance testing utilities

@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing."""
    return {
        "memory_search_max_time": 2.0,  # seconds
        "interaction_save_max_time": 1.0,  # seconds
        "agent_response_max_time": 5.0,  # seconds
        "hint_escalation_max_time": 0.5,  # seconds
    }


# Security testing utilities

@pytest.fixture
def malicious_inputs():
    """Malicious input samples for security testing."""
    return [
        "'; DROP TABLE users; --",  # SQL injection
        "<script>alert('xss')</script>",  # XSS
        "../../etc/passwd",  # Path traversal
        "{{7*7}}",  # Template injection
        "eval(process.env)",  # Code injection
    ]


@pytest.fixture 
def edge_case_inputs():
    """Edge case inputs for robustness testing."""
    return [
        "",  # Empty string
        " " * 1000,  # Very long whitespace
        "a" * 10000,  # Very long text
        "🚀👨‍💻💻🔥",  # Unicode/emoji only
        "\n\r\t\0",  # Control characters
        None,  # None value (if handled)
    ]