"""
Integration Tests for Mentor Agent Workflow
Tests the complete workflow from user input through agent processing to response generation
"""

import pytest
import asyncio
import os
import tempfile
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys
from datetime import datetime

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Test imports
try:
    from agents.mentor_agent import (
        MentorAgent, 
        BlackboxMentorAdapter,
        MentorResponse,
        MentorAgentDeps
    )
    from agents.mentor_agent.tools import MentorTools, MemoryContext, LearningPatterns
    from backend.memory_store import ConversationMemory
    from backend.database import User, Session, Interaction
    PYDANTIC_AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PydanticAI imports not available: {e}")
    PYDANTIC_AI_AVAILABLE = False


@pytest.fixture
def mock_memory_store():
    """Fixture providing a mock memory store"""
    memory_store = Mock(spec=ConversationMemory)
    memory_store.find_similar_interactions.return_value = []
    memory_store.get_user_learning_patterns.return_value = None
    memory_store.add_interaction.return_value = "mock_memory_id"
    return memory_store


@pytest.fixture 
def mock_db_session():
    """Fixture providing a mock database session"""
    db_session = Mock()
    return db_session


@pytest.fixture
def sample_user_data():
    """Fixture providing sample user data for testing"""
    return {
        "user_id": "test_user_123",
        "session_id": "session_456", 
        "user_messages": [
            "What is a Python function?",
            "How do I create a list in Python?",
            "My code has a syntax error, can you help?",
            "I'm getting a NameError in my Python script"
        ]
    }


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMentorAgentWorkflowIntegration:
    """Test complete mentor agent workflow integration"""
    
    @pytest.mark.asyncio
    async def test_complete_conversation_workflow(self, mock_memory_store, mock_db_session, sample_user_data):
        """Test complete workflow from user question to mentor response with memory integration"""
        
        # Mock PydanticAI model and agent
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            # Setup mock PydanticAI agent
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Mock agent response
            mock_result = Mock()
            mock_result.data = MentorResponse(
                response="Great question! Before I guide you toward the answer, can you tell me what you think a function does? What's your current understanding?",
                hint_level=1,
                memory_context_used=False,
                detected_language="python",
                detected_intent="concept_explanation",
                similar_interactions_count=0
            )
            mock_agent.run = AsyncMock(return_value=mock_result)
            
            # Setup memory store with some historical data  
            mock_memory_store.find_similar_interactions.return_value = [
                {
                    "memory_id": "prev_001",
                    "user_message": "What are Python variables?",
                    "mentor_response": "Let's think about variables step by step...",
                    "similarity": 0.75,
                    "metadata": {"programming_language": "python", "user_intent": "concept_explanation"}
                }
            ]
            
            mock_memory_store.get_user_learning_patterns.return_value = {
                "total_interactions": 3,
                "most_common_language": ("python", 3),
                "most_common_intent": ("concept_explanation", 2),
                "difficulty_distribution": {"beginner": 3},
                "languages_practiced": ["python"]
            }
            
            # Initialize mentor agent
            mentor = MentorAgent(model=mock_model)
            
            # Execute complete workflow
            response = await mentor.respond(
                user_message=sample_user_data["user_messages"][0],  # "What is a Python function?"
                user_id=sample_user_data["user_id"],
                session_id=sample_user_data["session_id"],
                memory_store=mock_memory_store,
                db_session=mock_db_session
            )
            
            # Verify response structure and content
            assert isinstance(response, MentorResponse)
            assert response.response.startswith("Great question!")
            assert "what you think a function does" in response.response
            assert response.detected_language == "python"
            assert response.detected_intent == "concept_explanation"
            assert response.similar_interactions_count == 1
            
            # Verify memory store interactions
            mock_memory_store.find_similar_interactions.assert_called()
            mock_memory_store.get_user_learning_patterns.assert_called_with(sample_user_data["user_id"])
            
            # Verify strict mentor principles (no direct answers)
            forbidden_phrases = ["a function is", "functions are", "def keyword creates", "here's how to define"]
            for phrase in forbidden_phrases:
                assert phrase.lower() not in response.response.lower()
    
    @pytest.mark.asyncio
    async def test_progressive_hint_escalation_workflow(self, mock_memory_store, mock_db_session):
        """Test hint escalation over multiple interactions in same session"""
        
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Create mentor agent
            mentor = MentorAgent(model=mock_model)
            
            user_id = "struggling_user"
            session_id = "learning_session"
            question = "How do I fix this Python syntax error?"
            
            # Simulate multiple interactions with same question (hint escalation)
            responses = []
            
            for hint_level in range(1, 5):  # Test levels 1-4
                # Mock escalating responses
                mock_result = Mock()
                mock_result.data = MentorResponse(
                    response=f"Level {hint_level} hint: Let me guide you step by step...",
                    hint_level=hint_level,
                    memory_context_used=True,
                    detected_language="python", 
                    detected_intent="debugging",
                    similar_interactions_count=2
                )
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                response = await mentor.respond(
                    user_message=question,
                    user_id=user_id,
                    session_id=session_id,
                    memory_store=mock_memory_store,
                    db_session=mock_db_session
                )
                
                responses.append(response)
                
                # Verify hint level progression
                assert response.hint_level == hint_level
                assert response.hint_level <= 4  # Never exceeds maximum
            
            # Verify all responses maintain strict mentor principles
            for response in responses:
                assert "step by step" in response.response.lower() or "guide you" in response.response.lower()
                assert "here's the complete solution" not in response.response.lower()
    
    @pytest.mark.asyncio
    async def test_multi_language_conversation_workflow(self, mock_memory_store, mock_db_session):
        """Test workflow across multiple programming languages"""
        
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            mentor = MentorAgent(model=mock_model)
            
            user_id = "polyglot_user"
            session_id = "multi_lang_session"
            
            # Questions in different programming languages
            language_questions = [
                ("How do I create an array in JavaScript?", "javascript"),
                ("What's the difference between lists and tuples in Python?", "python"),
                ("How do I declare a class in Java?", "java"),
                ("Can you explain HTML div elements?", "html")
            ]
            
            for question, expected_language in language_questions:
                # Mock response for each language
                mock_result = Mock()
                mock_result.data = MentorResponse(
                    response=f"Great {expected_language} question! Let's explore this concept...",
                    detected_language=expected_language,
                    detected_intent="concept_explanation",
                    memory_context_used=False,
                    similar_interactions_count=0
                )
                mock_agent.run = AsyncMock(return_value=mock_result)
                
                response = await mentor.respond(
                    user_message=question,
                    user_id=user_id,
                    session_id=session_id, 
                    memory_store=mock_memory_store,
                    db_session=mock_db_session
                )
                
                # Verify language detection
                assert response.detected_language == expected_language
                assert expected_language in response.response.lower()
                
                # Verify consistent strict mentor behavior across languages
                assert "let's explore" in response.response.lower() or "great question" in response.response.lower()
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, mock_memory_store, mock_db_session):
        """Test error handling throughout the workflow"""
        
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Mock PydanticAI agent to raise exception
            mock_agent.run = AsyncMock(side_effect=Exception("PydanticAI processing error"))
            
            mentor = MentorAgent(model=mock_model)
            
            # Should gracefully handle PydanticAI errors
            response = await mentor.respond(
                user_message="How do I handle exceptions in Python?",
                user_id="error_test_user",
                session_id="error_test_session",
                memory_store=mock_memory_store,
                db_session=mock_db_session
            )
            
            # Verify fallback response
            assert isinstance(response, MentorResponse)
            assert "I apologize, but I'm having trouble processing" in response.response
            assert response.memory_context_used == False
            assert response.detected_language == "unknown"
            assert response.detected_intent == "general"
            
            # Verify fallback still maintains mentor principles
            assert "what specific part" in response.response
            assert "what have you already tried" in response.response
    
    @pytest.mark.asyncio
    async def test_memory_integration_workflow(self, mock_db_session):
        """Test workflow with rich memory integration"""
        
        # Create more comprehensive mock memory store
        mock_memory_store = Mock(spec=ConversationMemory)
        
        # Mock rich historical data
        mock_memory_store.find_similar_interactions.return_value = [
            {
                "memory_id": "hist_001",
                "user_message": "I'm confused about Python dictionaries",
                "mentor_response": "Let's break down dictionaries step by step...",
                "similarity": 0.88,
                "metadata": {
                    "programming_language": "python",
                    "user_intent": "concept_explanation",
                    "difficulty_level": "beginner",
                    "timestamp": "2024-01-10T10:00:00"
                }
            },
            {
                "memory_id": "hist_002", 
                "user_message": "How do I iterate over a Python dictionary?",
                "mentor_response": "Great question! What methods do you think might work?",
                "similarity": 0.83,
                "metadata": {
                    "programming_language": "python",
                    "user_intent": "debugging", 
                    "difficulty_level": "intermediate",
                    "timestamp": "2024-01-12T14:30:00"
                }
            }
        ]
        
        mock_memory_store.get_user_learning_patterns.return_value = {
            "total_interactions": 12,
            "most_common_language": ("python", 10),
            "most_common_intent": ("concept_explanation", 7),
            "difficulty_distribution": {
                "beginner": 8,
                "intermediate": 4
            },
            "languages_practiced": ["python", "javascript"]
        }
        
        mock_memory_store.add_interaction.return_value = "new_memory_id_789"
        
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Mock response that references memory
            mock_result = Mock()
            mock_result.data = MentorResponse(
                response="I notice you've been exploring Python data structures. Building on what we discussed about dictionaries, what do you think sets are used for?",
                memory_context_used=True,
                detected_language="python",
                detected_intent="concept_explanation", 
                similar_interactions_count=2
            )
            mock_agent.run = AsyncMock(return_value=mock_result)
            
            mentor = MentorAgent(model=mock_model)
            
            response = await mentor.respond(
                user_message="What are Python sets and how do they work?",
                user_id="experienced_learner",
                session_id="python_learning_session",
                memory_store=mock_memory_store,
                db_session=mock_db_session
            )
            
            # Verify memory-guided response
            assert response.memory_context_used == True
            assert response.similar_interactions_count == 2
            assert "building on what we discussed" in response.response.lower()
            
            # Verify memory storage of new interaction
            mock_memory_store.add_interaction.assert_called_once()
            
            # Verify memory search was performed
            mock_memory_store.find_similar_interactions.assert_called()
            mock_memory_store.get_user_learning_patterns.assert_called()


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestBlackboxMentorAdapterIntegration:
    """Test backward compatibility adapter integration"""
    
    def test_adapter_interface_compatibility(self, mock_memory_store):
        """Test BlackboxMentorAdapter maintains interface compatibility"""
        
        with patch('agents.mentor_agent.agent.MentorAgent') as mock_mentor_class:
            # Mock mentor response
            mock_mentor_response = MentorResponse(
                response="That's a thoughtful question! What's your current understanding of this concept?",
                detected_language="python",
                detected_intent="concept_explanation"
            )
            mock_mentor_instance = Mock()
            mock_mentor_instance.respond = AsyncMock(return_value=mock_mentor_response)
            mock_mentor_class.return_value = mock_mentor_instance
            
            adapter = BlackboxMentorAdapter("legacy_agent_file.md")
            
            # Test legacy interface method
            response = adapter.call_blackbox_api(
                user_prompt="How do I learn Python programming?",
                user_id="legacy_user"
            )
            
            # Verify response format matches legacy expectations
            assert isinstance(response, str)
            assert len(response) > 0
            assert "thoughtful question" in response
            
            # Verify strict mentor principles maintained
            assert "what's your current understanding" in response.lower()
            assert "here's the complete answer" not in response.lower()
    
    def test_adapter_sync_async_handling(self):
        """Test adapter handles sync/async execution properly"""
        
        with patch('agents.mentor_agent.agent.MentorAgent') as mock_mentor_class:
            mock_mentor_instance = Mock()
            mock_mentor_class.return_value = mock_mentor_instance
            
            adapter = BlackboxMentorAdapter()
            
            # Test various sync execution scenarios
            test_questions = [
                "Please just give me the answer to this problem",
                "My code is broken and not working",
                "Can you help me understand this concept?"
            ]
            
            for question in test_questions:
                response = adapter.call_blackbox_api(question, "sync_test_user")
                
                # Verify fallback responses maintain mentor principles
                assert isinstance(response, str)
                assert len(response) > 0
                
                # Should not give direct answers even in fallback mode
                forbidden_fallback_phrases = ["here's the answer", "the solution is", "copy this code"]
                for phrase in forbidden_fallback_phrases:
                    assert phrase.lower() not in response.lower()


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestConcurrentWorkflowIntegration:
    """Test mentor agent workflow under concurrent usage"""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_sessions(self, mock_memory_store, mock_db_session):
        """Test mentor agent handles concurrent user sessions correctly"""
        
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            mentor = MentorAgent(model=mock_model)
            
            # Create concurrent sessions for different users
            users_and_questions = [
                ("user_001", "session_001", "How do I use Python loops?"),
                ("user_002", "session_002", "What's wrong with my JavaScript function?"),
                ("user_003", "session_003", "Can you explain HTML elements?"),
                ("user_004", "session_004", "I need help with CSS styling"),
                ("user_005", "session_005", "How do I debug Java errors?")
            ]
            
            # Setup mock responses for each user
            def mock_agent_run(*args, **kwargs):
                # Create different responses based on the user message
                user_message = args[0] if args else ""
                
                if "python" in user_message.lower():
                    return Mock(data=MentorResponse(
                        response="Great Python question! What kind of loop are you thinking about?",
                        detected_language="python",
                        detected_intent="concept_explanation"
                    ))
                elif "javascript" in user_message.lower():
                    return Mock(data=MentorResponse(
                        response="Let's debug this JavaScript step by step...",
                        detected_language="javascript", 
                        detected_intent="debugging"
                    ))
                elif "html" in user_message.lower():
                    return Mock(data=MentorResponse(
                        response="HTML elements are fundamental! What specific element are you working with?",
                        detected_language="html",
                        detected_intent="concept_explanation"
                    ))
                elif "css" in user_message.lower():
                    return Mock(data=MentorResponse(
                        response="CSS styling can be tricky! What effect are you trying to achieve?",
                        detected_language="css",
                        detected_intent="improvement"
                    ))
                else:
                    return Mock(data=MentorResponse(
                        response="Let's work through this together!",
                        detected_language="java",
                        detected_intent="debugging"
                    ))
            
            mock_agent.run = AsyncMock(side_effect=mock_agent_run)
            
            # Execute concurrent requests
            tasks = []
            for user_id, session_id, question in users_and_questions:
                task = mentor.respond(
                    user_message=question,
                    user_id=user_id,
                    session_id=session_id,
                    memory_store=mock_memory_store,
                    db_session=mock_db_session
                )
                tasks.append(task)
            
            # Wait for all concurrent requests to complete
            responses = await asyncio.gather(*tasks)
            
            # Verify all requests completed successfully
            assert len(responses) == 5
            
            for i, response in enumerate(responses):
                user_id, session_id, question = users_and_questions[i]
                
                # Verify response quality
                assert isinstance(response, MentorResponse)
                assert len(response.response) > 0
                
                # Verify language detection worked correctly
                if "python" in question.lower():
                    assert response.detected_language == "python"
                elif "javascript" in question.lower(): 
                    assert response.detected_language == "javascript"
                elif "html" in question.lower():
                    assert response.detected_language == "html"
                elif "css" in question.lower():
                    assert response.detected_language == "css"
                else:
                    assert response.detected_language == "java"
            
            # Verify memory store was called for each user
            assert mock_memory_store.find_similar_interactions.call_count == 5
            assert mock_memory_store.get_user_learning_patterns.call_count == 5
    
    @pytest.mark.asyncio
    async def test_session_isolation(self, mock_memory_store, mock_db_session):
        """Test that different sessions maintain proper isolation"""
        
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Mock different responses for different sessions
            session_responses = {
                "beginner_session": MentorResponse(
                    response="Let's start with the basics...",
                    detected_language="python",
                    hint_level=1
                ),
                "advanced_session": MentorResponse(
                    response="That's a complex topic, let's break it down...",
                    detected_language="python", 
                    hint_level=3
                )
            }
            
            def mock_session_response(*args, **kwargs):
                deps = kwargs.get('deps')
                if deps and deps.session_id in session_responses:
                    return Mock(data=session_responses[deps.session_id])
                return Mock(data=MentorResponse(response="Default response"))
            
            mock_agent.run = AsyncMock(side_effect=mock_session_response)
            
            mentor = MentorAgent(model=mock_model)
            
            # Test same user in different sessions
            user_id = "multi_session_user"
            
            beginner_response = await mentor.respond(
                user_message="What is a Python variable?",
                user_id=user_id,
                session_id="beginner_session",
                memory_store=mock_memory_store,
                db_session=mock_db_session
            )
            
            advanced_response = await mentor.respond(
                user_message="How do I optimize this algorithm?",
                user_id=user_id,
                session_id="advanced_session", 
                memory_store=mock_memory_store,
                db_session=mock_db_session
            )
            
            # Verify sessions maintain different contexts
            assert "start with the basics" in beginner_response.response
            assert "complex topic" in advanced_response.response
            assert beginner_response.hint_level != advanced_response.hint_level


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running Mentor Agent Integration Tests...")
    
    if PYDANTIC_AI_AVAILABLE:
        print("✅ PydanticAI imports available")
        print("✅ Integration test setup completed successfully!")
        print("Run with: pytest tests/test_mentor_agent_integration.py -v")
    else:
        print("⚠️ PydanticAI not available - tests skipped") 
        print("Install PydanticAI to run full test suite: pip install pydantic-ai")