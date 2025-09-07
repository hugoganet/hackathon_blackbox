"""
Unit Tests for MentorAgent Core Functionality
Tests the core PydanticAI agent behavior, initialization, and core methods
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
        create_mentor_agent,
        PydanticMentor,
        MentorAgentDeps,
        MentorResponse
    )
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


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMentorAgentInitialization:
    """Test MentorAgent initialization and configuration"""
    
    def test_mentor_agent_initialization_without_model(self):
        """Test MentorAgent can be initialized without providing a model"""
        with patch('agents.mentor_agent.agent.OpenAIModel') as mock_openai:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                mock_model = Mock()
                mock_openai.return_value = mock_model
                
                agent = MentorAgent()
                
                assert agent is not None
                mock_openai.assert_called_once_with('gpt-4', api_key='test_key')
    
    def test_mentor_agent_initialization_with_blackbox_key(self):
        """Test MentorAgent falls back to BLACKBOX_API_KEY"""
        with patch('agents.mentor_agent.agent.OpenAIModel') as mock_openai:
            with patch.dict(os.environ, {'BLACKBOX_API_KEY': 'blackbox_key'}, clear=True):
                mock_model = Mock()
                mock_openai.return_value = mock_model
                
                agent = MentorAgent()
                
                assert agent is not None
                mock_openai.assert_called_once_with('gpt-4', api_key='blackbox_key')
    
    def test_mentor_agent_initialization_no_api_key(self):
        """Test MentorAgent raises error when no API key is provided"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY or BLACKBOX_API_KEY must be set"):
                MentorAgent()
    
    def test_mentor_agent_initialization_with_custom_model(self):
        """Test MentorAgent can be initialized with a custom model"""
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            agent = MentorAgent(model=mock_model)
            
            assert agent is not None
            mock_agent_class.assert_called_once()
            call_args = mock_agent_class.call_args[1]
            assert call_args['model'] == mock_model
            assert call_args['result_type'] == MentorResponse
            assert call_args['deps_type'] == MentorAgentDeps


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMentorAgentSystemPrompt:
    """Test system prompt content and validation"""
    
    def test_system_prompt_contains_strict_principles(self):
        """Test that system prompt contains key strict mentor principles"""
        prompt = STRICT_MENTOR_SYSTEM_PROMPT
        
        # Core strict mentor principles
        assert "NEVER give direct answers" in prompt
        assert "STRICT PROHIBITIONS" in prompt
        assert "progressive hints" in prompt
        assert "Socratic questions" in prompt
        assert "autonomous thinking" in prompt
        
        # Prohibited behaviors
        assert "NEVER write complete code" in prompt
        assert "NEVER give the final solution" in prompt
        assert "NEVER give in to pleading" in prompt
        
        # Positive behaviors
        assert "guide through hints" in prompt.lower()
        assert "break down problems" in prompt.lower()
        assert "celebrate small victories" in prompt.lower()
    
    def test_system_prompt_handles_user_frustration(self):
        """Test system prompt addresses handling user frustration"""
        prompt = STRICT_MENTOR_SYSTEM_PROMPT
        
        assert "pleading" in prompt.lower() or "begs" in prompt.lower()
        assert "frustration" in prompt.lower()
        assert "understand your frustration" in prompt.lower()
        assert "help you progress" in prompt.lower()
    
    def test_system_prompt_includes_memory_guidance(self):
        """Test system prompt includes memory-guided mentoring instructions"""
        prompt = STRICT_MENTOR_SYSTEM_PROMPT
        
        assert "MEMORY-GUIDED MENTORING" in prompt
        assert "similar past interactions" in prompt.lower()
        assert "learning journey" in prompt.lower()
        assert "build on concepts" in prompt.lower()
    
    def test_system_prompt_includes_hint_escalation(self):
        """Test system prompt includes hint escalation system"""
        prompt = STRICT_MENTOR_SYSTEM_PROMPT
        
        assert "HINT ESCALATION SYSTEM" in prompt
        assert "4 levels of hints" in prompt.lower()
        assert "Conceptual" in prompt
        assert "Investigative" in prompt
        assert "Directional" in prompt
        assert "Structural" in prompt


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMentorAgentTools:
    """Test MentorAgent tool registration and execution"""
    
    @patch('agents.mentor_agent.agent.Agent')
    def test_tool_registration(self, mock_agent_class):
        """Test that tools are properly registered with the PydanticAI agent"""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            agent = MentorAgent()
            
            # Verify agent.tool was called for each tool
            assert mock_agent.tool.call_count == 5  # 5 tools registered
            
            # Get the tool functions that were registered
            tool_calls = mock_agent.tool.call_args_list
            tool_names = []
            
            for call in tool_calls:
                # The decorated function is the first argument
                func = call[0][0]
                tool_names.append(func.__name__)
            
            expected_tools = [
                'get_memory_context',
                'track_hint_progression', 
                'analyze_user_context',
                'provide_encouragement',
                'handle_frustration'
            ]
            
            for tool_name in expected_tools:
                assert tool_name in tool_names


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMentorAgentResponse:
    """Test MentorAgent response generation and formatting"""
    
    @pytest.mark.asyncio
    async def test_successful_response_generation(self):
        """Test successful response generation with all metadata"""
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            # Mock the PydanticAI agent
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Mock the response from PydanticAI
            mock_result = Mock()
            mock_result.data = Mock()
            mock_result.data.response = "Great question! What have you tried so far?"
            mock_agent.run = AsyncMock(return_value=mock_result)
            
            # Mock MentorTools
            with patch('agents.mentor_agent.agent.MentorTools') as mock_tools_class:
                mock_tools = Mock()
                mock_tools_class.return_value = mock_tools
                
                # Mock tool methods
                mock_tools.detect_programming_language = AsyncMock(return_value="python")
                mock_tools.classify_user_intent = AsyncMock(return_value="debugging")
                
                mock_memory_context = Mock()
                mock_memory_context.similar_interactions = [Mock(), Mock()]  # 2 similar interactions
                mock_tools.get_memory_context = AsyncMock(return_value=mock_memory_context)
                mock_tools.store_interaction = AsyncMock(return_value="memory_id_123")
                
                # Mock memory store
                mock_memory_store = Mock()
                
                agent = MentorAgent(model=mock_model)
                
                response = await agent.respond(
                    user_message="My Python code has a bug",
                    user_id="test_user",
                    session_id="test_session",
                    memory_store=mock_memory_store,
                    db_session=None
                )
                
                # Verify response structure
                assert isinstance(response, MentorResponse)
                assert response.response == "Great question! What have you tried so far?"
                assert response.detected_language == "python"
                assert response.detected_intent == "debugging"
                assert response.similar_interactions_count == 2
                assert response.memory_context_used == True
    
    @pytest.mark.asyncio
    async def test_error_fallback_response(self):
        """Test fallback response when PydanticAI fails"""
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            # Mock the PydanticAI agent to raise an exception
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_agent.run = AsyncMock(side_effect=Exception("API Error"))
            
            agent = MentorAgent(model=mock_model)
            
            response = await agent.respond(
                user_message="Help me with this error",
                user_id="test_user"
            )
            
            # Verify fallback response
            assert isinstance(response, MentorResponse)
            assert "I apologize, but I'm having trouble processing" in response.response
            assert "what specific part" in response.response
            assert response.memory_context_used == False
            assert response.detected_language == "unknown"
            assert response.detected_intent == "general"
            assert response.similar_interactions_count == 0


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestBlackboxMentorAdapter:
    """Test backward compatibility adapter"""
    
    def test_adapter_initialization(self):
        """Test BlackboxMentorAdapter initialization"""
        with patch('agents.mentor_agent.agent.MentorAgent') as mock_mentor:
            mock_mentor.return_value = Mock()
            
            adapter = BlackboxMentorAdapter("test_file.md")
            
            assert adapter.agent_file == "test_file.md"
            assert adapter.mentor_agent is not None
            mock_mentor.assert_called_once()
    
    def test_call_blackbox_api_method(self):
        """Test call_blackbox_api method maintains interface compatibility"""
        with patch('agents.mentor_agent.agent.MentorAgent') as mock_mentor:
            # Mock the mentor agent response
            mock_response = Mock()
            mock_response.response = "Let's think about this step by step..."
            mock_mentor_instance = Mock()
            mock_mentor_instance.respond = AsyncMock(return_value=mock_response)
            mock_mentor.return_value = mock_mentor_instance
            
            adapter = BlackboxMentorAdapter()
            
            # Mock event loop for asyncio handling
            with patch('asyncio.get_event_loop') as mock_get_loop, \
                 patch('asyncio.new_event_loop') as mock_new_loop, \
                 patch('asyncio.set_event_loop'):
                
                mock_loop = Mock()
                mock_loop.is_running.return_value = False
                mock_loop.run_until_complete.return_value = mock_response
                mock_get_loop.return_value = mock_loop
                
                result = adapter.call_blackbox_api("How do I fix this bug?", "test_user")
                
                assert isinstance(result, str)
                assert result == "Let's think about this step by step..."
    
    def test_sync_fallback_method(self):
        """Test synchronous fallback when async execution fails"""
        with patch('agents.mentor_agent.agent.MentorAgent'):
            adapter = BlackboxMentorAdapter()
            
            # Test different types of questions
            result1 = adapter._sync_fallback("Please give me the answer")
            assert "I understand you'd like a direct answer" in result1
            
            result2 = adapter._sync_fallback("My code has an error")
            assert "Let's debug this step by step" in result2
            
            result3 = adapter._sync_fallback("General question")
            assert "That's a great question" in result3


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestPromptHelperFunctions:
    """Test prompt formatting and helper functions"""
    
    def test_format_memory_context_with_data(self):
        """Test memory context formatting with actual data"""
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
        assert "javascript" in context
        assert "debugging" in context
        assert "How do I fix this React component" in context
    
    def test_format_memory_context_empty_data(self):
        """Test memory context formatting with empty data"""
        context = format_memory_context({}, [])
        assert context == ""
        
        context = format_memory_context(None, None)
        assert context == ""
    
    def test_hint_escalation_responses(self):
        """Test hint escalation response generation"""
        hint = "Check the documentation for this method"
        
        response1 = get_hint_escalation_response(1, hint)
        assert "high-level approach" in response1.lower()
        assert hint in response1
        
        response2 = get_hint_escalation_response(2, hint)
        assert "investigate" in response2.lower()
        assert hint in response2
        
        response3 = get_hint_escalation_response(3, hint)
        assert "right area" in response3.lower()
        assert hint in response3
        
        response4 = get_hint_escalation_response(4, hint)
        assert "structural guidance" in response4.lower()
        assert hint in response4
    
    def test_frustration_response_generation(self):
        """Test frustration response generation"""
        response = get_frustration_response()
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Should contain supportive language
        supportive_keywords = ["understand", "challenging", "frustration", "step", "small"]
        assert any(keyword in response.lower() for keyword in supportive_keywords)
    
    def test_progress_celebration_generation(self):
        """Test progress celebration generation"""
        response = get_progress_celebration()
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Should contain encouraging language
        encouraging_keywords = ["excellent", "great", "perfect", "thinking", "next"]
        assert any(keyword in response.lower() for keyword in encouraging_keywords)


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestFactoryFunction:
    """Test factory function and aliases"""
    
    def test_create_mentor_agent_factory(self):
        """Test create_mentor_agent factory function"""
        with patch('agents.mentor_agent.agent.MentorAgent') as mock_mentor:
            mock_instance = Mock()
            mock_mentor.return_value = mock_instance
            
            agent = create_mentor_agent()
            
            assert agent == mock_instance
            mock_mentor.assert_called_once_with(model=None)
    
    def test_create_mentor_agent_with_model(self):
        """Test create_mentor_agent with custom model"""
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.MentorAgent') as mock_mentor:
            mock_instance = Mock()
            mock_mentor.return_value = mock_instance
            
            agent = create_mentor_agent(model=mock_model)
            
            assert agent == mock_instance
            mock_mentor.assert_called_once_with(model=mock_model)
    
    def test_pydantic_mentor_alias(self):
        """Test PydanticMentor alias points to MentorAgent"""
        assert PydanticMentor == MentorAgent


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMentorAgentModels:
    """Test Pydantic models used by MentorAgent"""
    
    def test_mentor_agent_deps_model(self):
        """Test MentorAgentDeps model validation"""
        deps = MentorAgentDeps(
            user_id="test_user",
            memory_store=Mock(),
            db_session=Mock(),
            session_id="test_session"
        )
        
        assert deps.user_id == "test_user"
        assert deps.session_id == "test_session"
        assert deps.memory_store is not None
        assert deps.db_session is not None
    
    def test_mentor_response_model(self):
        """Test MentorResponse model validation"""
        response = MentorResponse(
            response="Great question! Let's explore this...",
            hint_level=2,
            memory_context_used=True,
            detected_language="python",
            detected_intent="debugging",
            similar_interactions_count=3
        )
        
        assert response.response == "Great question! Let's explore this..."
        assert response.hint_level == 2
        assert response.memory_context_used == True
        assert response.detected_language == "python"
        assert response.detected_intent == "debugging"
        assert response.similar_interactions_count == 3
    
    def test_mentor_response_model_defaults(self):
        """Test MentorResponse model with default values"""
        response = MentorResponse(response="Test response")
        
        assert response.response == "Test response"
        assert response.hint_level is None
        assert response.memory_context_used == False
        assert response.detected_language is None
        assert response.detected_intent is None
        assert response.similar_interactions_count == 0


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running MentorAgent Unit Tests...")
    
    if PYDANTIC_AI_AVAILABLE:
        print("✅ PydanticAI imports available")
        
        # Test basic functionality
        test_instance = TestMentorAgentInitialization()
        print("✅ Initialization tests setup")
        
        prompt_test = TestMentorAgentSystemPrompt()
        prompt_test.test_system_prompt_contains_strict_principles()
        print("✅ System prompt tests passed")
        
        print("🎉 Unit tests setup completed successfully!")
        print("Run with: pytest tests/test_mentor_agent_unit.py -v")
    else:
        print("⚠️ PydanticAI not available - tests skipped")
        print("Install PydanticAI to run full test suite: pip install pydantic-ai")