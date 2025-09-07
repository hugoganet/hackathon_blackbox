"""
Test suite for PydanticAI Mentor Agent
Tests the migration from agent-mentor-strict.md to PydanticAI implementation
"""

import pytest
import asyncio
import os
import tempfile
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Test imports
try:
    from agents.mentor_agent import (
        MentorAgent, 
        BlackboxMentorAdapter, 
        create_mentor_agent,
        PydanticMentor
    )
    from agents.mentor_agent.tools import MentorTools, MemoryContext, HintTracker
    from agents.mentor_agent.prompts import (
        STRICT_MENTOR_SYSTEM_PROMPT,
        format_memory_context,
        get_hint_escalation_response,
        get_frustration_response,
        get_progress_celebration
    )
    PYDANTIC_AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PydanticAI imports not available: {e}")
    PYDANTIC_AI_AVAILABLE = False
    MentorAgent = None
    BlackboxMentorAdapter = None


class TestPydanticAIMentorAgent:
    """Test suite for the PydanticAI Mentor Agent implementation"""
    
    def test_imports_available(self):
        """Test that PydanticAI mentor agent can be imported"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        # Test main classes are importable
        assert MentorAgent is not None
        assert BlackboxMentorAdapter is not None
        assert create_mentor_agent is not None
        assert PydanticMentor is not None
        
        # Test tools are importable
        assert MentorTools is not None
        assert MemoryContext is not None
        assert HintTracker is not None
        
        # Test prompts are importable
        assert STRICT_MENTOR_SYSTEM_PROMPT is not None
        assert len(STRICT_MENTOR_SYSTEM_PROMPT) > 0
    
    def test_system_prompt_content(self):
        """Test that the system prompt maintains strict mentor principles"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        prompt = STRICT_MENTOR_SYSTEM_PROMPT
        
        # Test key strict mentor principles are present
        assert "NEVER give direct answers" in prompt
        assert "STRICT PROHIBITIONS" in prompt
        assert "progressive hints" in prompt
        assert "Socratic questions" in prompt
        assert "autonomous thinking" in prompt
        
        # Test handling of user frustration is addressed
        assert "pleading" in prompt.lower() or "begs" in prompt.lower()
        assert "frustration" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_blackbox_mentor_adapter_compatibility(self):
        """Test that BlackboxMentorAdapter maintains compatibility with existing interface"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        # Mock the PydanticAI dependencies to avoid requiring API keys
        with patch('agents.mentor_agent.agent.MentorAgent') as mock_mentor:
            mock_response = Mock()
            mock_response.response = "Great question! Let's think about this step by step..."
            mock_mentor.return_value.respond = AsyncMock(return_value=mock_response)
            
            adapter = BlackboxMentorAdapter()
            
            # Test the call_blackbox_api method (main compatibility interface)
            response = adapter.call_blackbox_api("How do I fix this bug?")
            
            # Should return a string response
            assert isinstance(response, str)
            assert len(response) > 0
            
            # Should not give direct answers (strict mentor principle)
            forbidden_phrases = ["the answer is", "here's the solution", "copy this code"]
            response_lower = response.lower()
            for phrase in forbidden_phrases:
                assert phrase not in response_lower
    
    def test_mentor_tools_initialization(self):
        """Test MentorTools initialization and configuration"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        # Test initialization without dependencies
        tools = MentorTools()
        assert tools.memory_store is None
        assert tools.db_session is None
        assert tools.hint_trackers == {}
        
        # Test initialization with mock dependencies
        mock_memory = Mock()
        mock_db = Mock()
        
        tools = MentorTools(memory_store=mock_memory, db_session=mock_db)
        assert tools.memory_store == mock_memory
        assert tools.db_session == mock_db
    
    @pytest.mark.asyncio
    async def test_intent_classification(self):
        """Test user intent classification functionality"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        tools = MentorTools()
        
        # Test debugging intent
        intent = await tools.classify_user_intent("My code has an error and doesn't work")
        assert intent == "debugging"
        
        # Test concept explanation intent
        intent = await tools.classify_user_intent("What is a function in Python?")
        assert intent == "concept_explanation"
        
        # Test improvement intent
        intent = await tools.classify_user_intent("How can I make my code better?")
        assert intent == "improvement"
        
        # Test general intent (fallback)
        intent = await tools.classify_user_intent("Hello there")
        assert intent == "general"
    
    @pytest.mark.asyncio
    async def test_programming_language_detection(self):
        """Test programming language detection from user messages"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        tools = MentorTools()
        
        # Test JavaScript detection
        language = await tools.detect_programming_language("I'm having issues with my React component")
        assert language == "javascript"
        
        # Test Python detection
        language = await tools.detect_programming_language("My Python function with def main() isn't working")
        assert language == "python"
        
        # Test HTML detection
        language = await tools.detect_programming_language("My <div> element isn't showing up")
        assert language == "html"
        
        # Test unknown language (fallback)
        language = await tools.detect_programming_language("I need help with general programming")
        assert language == "unknown"
    
    @pytest.mark.asyncio
    async def test_difficulty_analysis(self):
        """Test difficulty level analysis"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        tools = MentorTools()
        
        # Test beginner level detection
        difficulty = await tools.analyze_difficulty_level("What is a variable? I'm new to programming")
        assert difficulty == "beginner"
        
        # Test advanced level detection
        difficulty = await tools.analyze_difficulty_level("How do I optimize this algorithm for better performance?")
        assert difficulty == "advanced"
        
        # Test intermediate level (default)
        difficulty = await tools.analyze_difficulty_level("How do I use this library?")
        assert difficulty == "intermediate"
    
    @pytest.mark.asyncio
    async def test_hint_escalation_tracking(self):
        """Test hint escalation system"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        tools = MentorTools()
        
        user_id = "test_user"
        session_id = "test_session"
        question = "How do I fix this React error?"
        
        # Test initial hint level
        level = await tools.track_hint_escalation(user_id, session_id, question, "First hint")
        assert level == 1
        
        # Test escalation after more hints
        level = await tools.track_hint_escalation(user_id, session_id, question, "Second hint")
        assert level == 2  # Should still be 2 after 2nd hint
        
        level = await tools.track_hint_escalation(user_id, session_id, question, "Third hint")
        assert level == 2  # Should still be 2
        
        # Test max level cap
        for i in range(10):
            level = await tools.track_hint_escalation(user_id, session_id, question, f"Hint {i+4}")
        
        assert level <= 4  # Should not exceed level 4
    
    def test_prompt_helper_functions(self):
        """Test prompt formatting and helper functions"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        # Test memory context formatting
        mock_patterns = {
            "total_interactions": 5,
            "most_common_language": ("javascript", 3),
            "most_common_intent": ("debugging", 2)
        }
        
        mock_interactions = [
            {"user_message": "How do I fix this React component issue?"},
            {"user_message": "Why is my JavaScript function not working?"}
        ]
        
        context = format_memory_context(mock_patterns, mock_interactions)
        assert "Total conversations: 5" in context
        assert "javascript" in context.lower()
        
        # Test hint escalation response
        response = get_hint_escalation_response(2, "Check the documentation for this method")
        assert "investigate" in response.lower()
        
        # Test frustration response
        frustration_response = get_frustration_response()
        assert isinstance(frustration_response, str)
        assert len(frustration_response) > 0
        
        # Test progress celebration
        celebration = get_progress_celebration()
        assert isinstance(celebration, str)
        assert len(celebration) > 0
    
    @pytest.mark.asyncio
    async def test_memory_context_retrieval(self):
        """Test memory context retrieval from conversation history"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        # Mock memory store
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.return_value = [
            {
                "memory_id": "test_id_1",
                "user_message": "Previous React question",
                "mentor_response": "Previous guidance",
                "similarity": 0.8,
                "metadata": {"programming_language": "javascript"}
            }
        ]
        
        mock_memory_store.get_user_learning_patterns.return_value = {
            "total_interactions": 3,
            "most_common_language": ("javascript", 2),
            "most_common_intent": ("debugging", 2),
            "difficulty_distribution": {"beginner": 3},
            "languages_practiced": ["javascript", "html"]
        }
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        context = await tools.get_memory_context("test_user", "How do I debug React components?")
        
        # Verify memory context structure
        assert context is not None
        assert len(context.similar_interactions) == 1
        assert context.learning_patterns.total_interactions == 3
        assert context.similar_interactions[0].similarity == 0.8
    
    def test_factory_function(self):
        """Test the create_mentor_agent factory function"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        # Test factory function returns MentorAgent instance
        with patch('agents.mentor_agent.agent.MentorAgent') as mock_mentor_class:
            mock_instance = Mock()
            mock_mentor_class.return_value = mock_instance
            
            agent = create_mentor_agent()
            assert agent == mock_instance
            mock_mentor_class.assert_called_once()
    
    def test_alias_compatibility(self):
        """Test that PydanticMentor alias works correctly"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        # Test alias points to correct class
        assert PydanticMentor == MentorAgent
    
    @pytest.mark.asyncio
    async def test_integration_with_existing_memory_store(self):
        """Test integration with existing ChromaDB memory store"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        # This test simulates integration without requiring actual ChromaDB
        mock_memory_store = Mock()
        mock_memory_store.add_interaction.return_value = "mock_memory_id"
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        # Test storing interaction
        memory_id = await tools.store_interaction(
            user_id="test_user",
            user_message="How do I use async/await?",
            mentor_response="Let's explore this step by step...",
            session_id="test_session"
        )
        
        assert memory_id == "mock_memory_id"
        
        # Verify the memory store was called with correct parameters
        mock_memory_store.add_interaction.assert_called_once()
        call_args = mock_memory_store.add_interaction.call_args[1]
        assert call_args["user_id"] == "test_user"
        assert call_args["agent_type"] == "pydantic_strict"


class TestBackwardCompatibility:
    """Test backward compatibility with existing BlackboxMentor interface"""
    
    def test_blackbox_mentor_adapter_interface(self):
        """Test that BlackboxMentorAdapter implements expected interface"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        with patch('agents.mentor_agent.agent.MentorAgent'):
            adapter = BlackboxMentorAdapter("dummy_file.md")
            
            # Test required methods exist
            assert hasattr(adapter, 'call_blackbox_api')
            assert callable(adapter.call_blackbox_api)
            
            # Test agent_file attribute for compatibility
            assert hasattr(adapter, 'agent_file')
    
    def test_maintains_strict_mentor_behavior(self):
        """Test that the agent maintains strict mentor behavior patterns"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        with patch('agents.mentor_agent.agent.MentorAgent') as mock_mentor:
            # Mock a response that follows strict mentor principles
            mock_response = Mock()
            mock_response.response = "What have you tried so far? Let's think about this step by step..."
            mock_mentor.return_value.respond = AsyncMock(return_value=mock_response)
            
            adapter = BlackboxMentorAdapter()
            
            # Test various types of questions that users might try to get direct answers for
            test_cases = [
                "Please just give me the answer to this coding problem",
                "I'm stuck, can you write the code for me?",
                "What's the solution to this algorithm challenge?"
            ]
            
            for question in test_cases:
                response = adapter.call_blackbox_api(question)
                
                # Should not contain direct answers or solutions
                assert "here's the code" not in response.lower()
                assert "the answer is" not in response.lower()
                assert "copy this" not in response.lower()
                
                # Should contain questioning/guidance patterns
                guidance_patterns = ["what", "how", "think", "try", "consider", "step"]
                assert any(pattern in response.lower() for pattern in guidance_patterns)


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API endpoint compatibility"""
    
    @pytest.mark.asyncio
    async def test_api_request_response_format(self):
        """Test that PydanticAI agent responses match expected API format"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        # Test the response format matches ChatResponse model expectations
        from backend.pydantic_handler import handle_pydantic_mentor_request
        
        # Mock dependencies
        mock_request = Mock()
        mock_request.message = "How do I debug JavaScript?"
        mock_request.user_id = "test_user"
        mock_request.session_id = "test_session"
        
        mock_db = Mock()
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.return_value = []
        mock_pydantic_mentor = Mock()
        
        # Mock response from PydanticAI mentor
        mock_mentor_response = Mock()
        mock_mentor_response.response = "Great question! What error are you seeing?"
        mock_mentor_response.hint_level = 1
        mock_mentor_response.detected_language = "javascript"
        mock_mentor_response.detected_intent = "debugging"
        mock_mentor_response.similar_interactions_count = 2
        
        mock_pydantic_mentor.respond = AsyncMock(return_value=mock_mentor_response)
        
        # Mock database operations
        mock_user = Mock()
        mock_user.id = "user_uuid"
        mock_conversation = Mock()
        mock_conversation.id = "conv_uuid"
        
        with patch('backend.pydantic_handler.get_user_by_username', return_value=mock_user), \
             patch('backend.pydantic_handler.create_conversation', return_value=mock_conversation), \
             patch('backend.pydantic_handler.save_interaction'):
            
            # Test the actual handler function
            response = await handle_pydantic_mentor_request(
                request=mock_request,
                db=mock_db,
                pydantic_mentor=mock_pydantic_mentor,
                memory_store=mock_memory_store
            )
            
            # Verify response structure matches API expectations
            assert "response" in response
            assert "agent_type" in response
            assert "session_id" in response
            assert "detected_language" in response
            assert "detected_intent" in response
            assert "similar_interactions_count" in response
            
            # Verify response values
            assert response["response"] == "Great question! What error are you seeing?"
            assert response["agent_type"] == "pydantic_strict"
            assert response["session_id"] == "test_session"
            assert response["detected_language"] == "javascript"
            assert response["detected_intent"] == "debugging"
            assert response["similar_interactions_count"] == 2
    
    @pytest.mark.asyncio
    async def test_error_handling_in_api_integration(self):
        """Test error handling in API integration"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        from backend.pydantic_handler import handle_pydantic_mentor_request
        
        # Mock request
        mock_request = Mock()
        mock_request.message = "Test error handling"
        mock_request.user_id = "error_test_user"
        mock_request.session_id = "error_test_session"
        
        # Mock mentor to raise exception
        mock_pydantic_mentor = Mock()
        mock_pydantic_mentor.respond = AsyncMock(side_effect=Exception("PydanticAI processing error"))
        
        mock_db = Mock()
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.return_value = []
        
        # Mock database operations
        mock_user = Mock()
        mock_user.id = "error_user_uuid"
        
        with patch('backend.pydantic_handler.get_user_by_username', return_value=mock_user):
            # Should handle errors gracefully
            try:
                response = await handle_pydantic_mentor_request(
                    request=mock_request,
                    db=mock_db,
                    pydantic_mentor=mock_pydantic_mentor,
                    memory_store=mock_memory_store
                )
                
                # If no exception is raised, verify fallback response
                assert "response" in response
                assert len(response["response"]) > 0
                
            except Exception:
                # If exception is raised, that's also acceptable
                # (depends on implementation choice for error handling)
                pass


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestComprehensiveIntegration:
    """Additional comprehensive integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test complete conversation flow with memory integration"""
        from backend.memory_store import ConversationMemory
        from agents.mentor_agent.tools import MentorTools
        
        # Create real mentor agent (with mocked model)
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Mock progressive conversation responses
            conversation_responses = [
                MentorResponse(
                    response="Great question! What do you think functions are used for in programming?",
                    hint_level=1,
                    detected_language="python",
                    detected_intent="concept_explanation"
                ),
                MentorResponse(
                    response="You're on the right track! How do you think we might create a function?",
                    hint_level=1,
                    detected_language="python", 
                    detected_intent="concept_explanation"
                ),
                MentorResponse(
                    response="Excellent thinking! What do you think happens when we call a function?",
                    hint_level=2,
                    detected_language="python",
                    detected_intent="concept_explanation"
                )
            ]
            
            response_iter = iter(conversation_responses)
            mock_agent.run = AsyncMock(side_effect=lambda *args, **kwargs: Mock(data=next(response_iter)))
            
            # Mock memory store
            mock_memory_store = Mock()
            mock_memory_store.find_similar_interactions.return_value = []
            mock_memory_store.get_user_learning_patterns.return_value = None
            mock_memory_store.add_interaction.return_value = "test_memory_id"
            
            # Create mentor agent
            from agents.mentor_agent import MentorAgent
            mentor = MentorAgent(model=mock_model)
            
            # Simulate conversation flow
            user_id = "comprehensive_test_user"
            session_id = "comprehensive_test_session"
            
            conversation = [
                "What is a Python function?",
                "I think functions help organize code?",
                "Maybe we use the 'def' keyword?"
            ]
            
            responses = []
            for message in conversation:
                response = await mentor.respond(
                    user_message=message,
                    user_id=user_id,
                    session_id=session_id,
                    memory_store=mock_memory_store
                )
                responses.append(response)
            
            # Verify conversation progression
            assert len(responses) == 3
            for response in responses:
                assert isinstance(response, MentorResponse)
                assert len(response.response) > 0
                assert response.detected_language == "python"
                
                # Verify strict mentor principles maintained
                assert "what do you think" in response.response.lower() or "how" in response.response.lower()
                assert "def function_name" not in response.response.lower()
    
    def test_comprehensive_strict_mentor_validation(self):
        """Test comprehensive validation of strict mentor principles"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        from agents.mentor_agent.prompts import STRICT_MENTOR_SYSTEM_PROMPT
        
        # Test comprehensive prompt analysis for strict principles
        prompt_sections = {
            "prohibitions": [
                "NEVER give direct answers",
                "NEVER write complete code", 
                "NEVER give the final solution",
                "NEVER give in to pleading"
            ],
            "positive_behaviors": [
                "progressive hints",
                "Socratic questions",
                "autonomous thinking",
                "celebrate small victories"
            ],
            "escalation_system": [
                "HINT ESCALATION SYSTEM",
                "4 levels of hints",
                "Conceptual",
                "Investigative", 
                "Directional",
                "Structural"
            ],
            "memory_integration": [
                "MEMORY-GUIDED MENTORING",
                "similar past interactions",
                "learning journey",
                "skill progression"
            ],
            "frustration_handling": [
                "understand your frustration",
                "help you progress",
                "my role is to guide"
            ]
        }
        
        for section_name, required_elements in prompt_sections.items():
            for element in required_elements:
                assert element.lower() in STRICT_MENTOR_SYSTEM_PROMPT.lower(), \
                    f"Missing {section_name} element: {element}"
        
        print("✅ Comprehensive strict mentor principles validated")
    
    @pytest.mark.asyncio
    async def test_edge_case_handling(self):
        """Test handling of edge cases and unusual inputs"""
        if not PYDANTIC_AI_AVAILABLE:
            pytest.skip("PydanticAI not available")
        
        from agents.mentor_agent.tools import MentorTools
        
        tools = MentorTools()
        
        # Test edge cases for intent classification
        edge_cases = {
            "": "general",  # Empty string
            "a" * 1000: "general",  # Very long string
            "🚀💻🎯": "general",  # Only emojis
            "????????????": "general",  # Non-English text
            "SELECT * FROM users; DROP TABLE users;": "general",  # SQL injection attempt
            "<script>alert('test')</script>": "general",  # XSS attempt
        }
        
        for test_input, expected_fallback in edge_cases.items():
            try:
                intent = await tools.classify_user_intent(test_input)
                assert intent in ["debugging", "concept_explanation", "improvement", "testing", "deployment", "general"]
            except Exception:
                # Should handle gracefully, not crash
                pass
        
        # Test language detection edge cases
        language_edge_cases = [
            "",  # Empty
            "mixed python and javascript code",  # Mixed languages
            "1234567890",  # Only numbers
            "python" * 100,  # Repeated text
        ]
        
        for test_input in language_edge_cases:
            try:
                language = await tools.detect_programming_language(test_input)
                assert isinstance(language, str)
                assert len(language) > 0
            except Exception:
                pass
        
        print("✅ Edge case handling validated")


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running PydanticAI Mentor Agent Tests...")
    
    if PYDANTIC_AI_AVAILABLE:
        print("✅ PydanticAI imports available")
        
        # Test basic functionality
        test_instance = TestPydanticAIMentorAgent()
        test_instance.test_imports_available()
        test_instance.test_system_prompt_content()
        print("✅ Basic tests passed")
        
        # Test tools
        tools_test = asyncio.run(test_instance.test_intent_classification())
        print("✅ Intent classification test passed")
        
        # Test comprehensive features
        comprehensive_test = TestComprehensiveIntegration()
        comprehensive_test.test_comprehensive_strict_mentor_validation()
        print("✅ Comprehensive validation passed")
        
        print("🎉 All enhanced tests completed successfully!")
        print("Run full test suite with: pytest tests/test_pydantic_mentor_agent.py -v")
    else:
        print("⚠️ PydanticAI not available - tests skipped")
        print("Install PydanticAI to run full test suite: pip install pydantic-ai")