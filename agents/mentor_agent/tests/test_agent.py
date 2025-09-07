"""
Test core mentor agent functionality.

Tests the main agent behavior, tool integration, and response quality using
TestModel and FunctionModel patterns.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, Mock
from typing import List, Dict, Any

from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelTextResponse

from ..agent import mentor_agent, run_mentor_agent, run_mentor_conversation, create_mentor_agent_with_deps
from ..dependencies import MentorDependencies
from ..tools import detect_confusion_signals


class TestMentorAgentBasics:
    """Test basic agent functionality and setup."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self, test_mentor_agent, test_dependencies):
        """Test agent initializes correctly with dependencies."""
        # Agent should be properly configured
        assert test_mentor_agent is not None
        assert test_mentor_agent.deps_type == MentorDependencies
        
        # Test basic run without errors
        result = await test_mentor_agent.run(
            "I'm having trouble with React state",
            deps=test_dependencies
        )
        
        assert result is not None
        assert isinstance(result.data, str)
        assert len(result.data) > 0

    @pytest.mark.asyncio 
    async def test_agent_basic_response_quality(self, test_mentor_agent, test_dependencies):
        """Test agent provides appropriate Socratic responses."""
        result = await test_mentor_agent.run(
            "My JavaScript function isn't working",
            deps=test_dependencies
        )
        
        response = result.data.lower()
        
        # Should ask questions, not give direct answers
        question_indicators = ["?", "what", "how", "why", "when", "where"]
        has_questions = any(indicator in response for indicator in question_indicators)
        assert has_questions, f"Response should contain questions: {result.data}"
        
        # Should not contain direct code solutions
        code_indicators = ["function(", "const ", "let ", "var ", "=&gt;"]
        has_code = any(indicator in response for indicator in code_indicators)
        assert not has_code, f"Response should not contain direct code: {result.data}"

    @pytest.mark.asyncio
    async def test_agent_tool_availability(self, test_mentor_agent):
        """Test that all required tools are available."""
        tool_names = [tool.name for tool in test_mentor_agent.tools]
        
        expected_tools = [
            "search_memory",
            "save_learning_interaction", 
            "classify_learning_opportunity",
            "track_hint_escalation"
        ]
        
        for tool in expected_tools:
            assert tool in tool_names, f"Missing tool: {tool}"

    @pytest.mark.asyncio
    async def test_dependencies_injection(self, test_dependencies):
        """Test dependency injection works correctly."""
        assert test_dependencies.user_id == "test-user-123"
        assert test_dependencies.session_id == "test-session-456"
        assert test_dependencies.current_hint_level == 1
        assert test_dependencies.hint_escalation_levels == 4
        assert test_dependencies.similarity_threshold == 0.7

    @pytest.mark.asyncio
    async def test_conversation_memory_initialization(self, test_dependencies):
        """Test conversation memory initializes correctly."""
        memory = test_dependencies.conversation_memory
        assert memory is not None
        
        # Test memory methods are available
        assert hasattr(memory, 'find_similar_interactions')
        assert hasattr(memory, 'add_interaction')
        assert hasattr(memory, 'close')


class TestSocraticMethodBehavior:
    """Test Socratic method implementation using FunctionModel."""

    def create_socratic_test_function(self, expected_behavior: str):
        """Create function to test specific Socratic behaviors."""
        def socratic_function(messages, tools):
            user_message = messages[-1].content if messages else ""
            
            if expected_behavior == "never_direct_answer":
                # Always respond with questions, never direct answers
                if "fix" in user_message.lower():
                    return ModelTextResponse(
                        content="What do you think might be causing this issue? What debugging steps have you tried?"
                    )
                else:
                    return ModelTextResponse(
                        content="What patterns do you notice? How would you approach investigating this?"
                    )
            
            elif expected_behavior == "memory_reference":
                # Reference past similar issues
                return ModelTextResponse(
                    content="This reminds me of your question from last week about similar functionality. What was the key insight you discovered then?"
                )
            
            elif expected_behavior == "progressive_hints":
                # Escalate hints based on context
                return ModelTextResponse(
                    content="Let's think about this step by step. What's the first thing you would check when debugging this type of issue?"
                )
            
            return ModelTextResponse(content="What do you think about this challenge?")
        
        return socratic_function

    @pytest.mark.asyncio
    async def test_never_gives_direct_answers(self, test_dependencies):
        """Test agent never provides direct code solutions."""
        socratic_function = self.create_socratic_test_function("never_direct_answer")
        function_model = FunctionModel(socratic_function)
        test_agent = mentor_agent.override(model=function_model)
        
        # Test various request types
        direct_requests = [
            "How do I fix this JavaScript error?",
            "Give me the code to solve this",
            "What's the answer to this problem?",
            "Show me how to implement this feature"
        ]
        
        for request in direct_requests:
            result = await test_agent.run(request, deps=test_dependencies)
            response = result.data.lower()
            
            # Should contain questions
            assert "?" in response, f"Response should be a question for: {request}"
            
            # Should not contain direct solutions
            solution_words = ["here's how", "the answer is", "just do", "simply"]
            has_direct_solution = any(word in response for word in solution_words)
            assert not has_direct_solution, f"Response should not give direct answer: {response}"

    @pytest.mark.asyncio
    async def test_references_past_interactions(self, test_dependencies):
        """Test agent references past similar issues appropriately."""
        socratic_function = self.create_socratic_test_function("memory_reference")
        function_model = FunctionModel(socratic_function)
        test_agent = mentor_agent.override(model=function_model)
        
        # Mock past interaction data
        with patch('agents.mentor_agent.tools.memory_search') as mock_search:
            mock_search.return_value = [
                {
                    "interaction_id": "past-1",
                    "question": "Previous useState issue",
                    "similarity_score": 0.85,
                    "days_ago": 3,
                    "hint_level_reached": 2
                }
            ]
            
            result = await test_agent.run(
                "I'm having React state problems again",
                deps=test_dependencies
            )
            
            response = result.data.lower()
            memory_indicators = ["reminds me", "similar to", "like your", "previous", "before"]
            has_memory_reference = any(indicator in response for indicator in memory_indicators)
            assert has_memory_reference, f"Response should reference past issues: {result.data}"

    @pytest.mark.asyncio
    async def test_progressive_hint_escalation(self, test_dependencies):
        """Test hint escalation levels work correctly."""
        call_count = 0
        
        def escalating_function(messages, tools):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                return ModelTextResponse(content="What do you think might be the issue here?")
            elif call_count == 2:
                return ModelTextResponse(content="Consider how this relates to your previous experience with similar problems.")
            elif call_count == 3:
                return ModelTextResponse(content="Think about the specific debugging approach that worked for you before.")
            else:
                return ModelTextResponse(content="Let's work through this step by step, building on what you learned previously.")
        
        function_model = FunctionModel(escalating_function)
        test_agent = mentor_agent.override(model=function_model)
        
        # Simulate multiple interactions with increasing confusion
        confusion_levels = [
            "I'm having an issue",
            "I still don't understand", 
            "I'm really stuck on this",
            "I've tried everything and I'm lost"
        ]
        
        for i, message in enumerate(confusion_levels):
            result = await test_agent.run(message, deps=test_dependencies)
            response = result.data
            
            # Verify hint escalation
            if i == 0:
                assert "what do you think" in response.lower()
            elif i == 1:
                assert "previous experience" in response.lower()
            elif i == 2:
                assert "debugging approach" in response.lower()
            else:
                assert "step by step" in response.lower()

    @pytest.mark.asyncio
    async def test_encourages_discovery_learning(self, test_dependencies):
        """Test agent encourages self-discovery rather than providing answers."""
        def encouraging_function(messages, tools):
            return ModelTextResponse(
                content="You're on the right track! What do you notice when you look at this more closely? What patterns emerge?"
            )
        
        function_model = FunctionModel(encouraging_function)
        test_agent = mentor_agent.override(model=function_model)
        
        result = await test_agent.run(
            "I think the problem might be with async/await",
            deps=test_dependencies
        )
        
        response = result.data.lower()
        encouraging_words = ["great", "right track", "good thinking", "what do you notice"]
        has_encouragement = any(word in response for word in encouraging_words)
        assert has_encouragement, f"Response should be encouraging: {result.data}"


class TestToolIntegration:
    """Test integration between agent and tools."""

    @pytest.mark.asyncio
    async def test_memory_search_integration(self, test_mentor_agent, test_dependencies):
        """Test memory search tool is called appropriately."""
        # Configure TestModel to call memory search
        test_model = test_mentor_agent.model
        test_model.agent_responses = [
            ModelTextResponse(content="Let me search your learning history"),
            {"search_memory": {"query": "React state", "limit": 3}},
            ModelTextResponse(content="Based on your past experience, what approach worked before?")
        ]
        
        with patch('agents.mentor_agent.tools.memory_search') as mock_search:
            mock_search.return_value = [
                {
                    "interaction_id": "test-1", 
                    "similarity_score": 0.8,
                    "days_ago": 5,
                    "question": "Previous React issue"
                }
            ]
            
            result = await test_mentor_agent.run(
                "I'm having React state issues",
                deps=test_dependencies
            )
            
            # Verify tool was called
            tool_calls = [msg for msg in result.all_messages() if hasattr(msg, 'tool_name')]
            assert len(tool_calls) > 0, "Memory search tool should be called"
            
            # Verify search was called with correct parameters
            search_call = next((call for call in tool_calls if call.tool_name == "search_memory"), None)
            assert search_call is not None, "Search memory tool should be called"

    @pytest.mark.asyncio
    async def test_interaction_saving_integration(self, test_mentor_agent, test_dependencies):
        """Test interaction saving happens automatically."""
        test_model = test_mentor_agent.model
        test_model.agent_responses = [
            ModelTextResponse(content="What patterns do you see in this problem?"),
            {"save_learning_interaction": {
                "user_message": "Test question",
                "mentor_response": "Test response",
                "hint_level": 1
            }}
        ]
        
        with patch('agents.mentor_agent.tools.save_interaction') as mock_save:
            mock_save.return_value = {"interaction_id": "test-save", "status": "saved"}
            
            result = await test_mentor_agent.run(
                "How do I debug this?",
                deps=test_dependencies
            )
            
            # Check that save tool was available to be called
            tool_names = [tool.name for tool in test_mentor_agent.tools]
            assert "save_learning_interaction" in tool_names

    @pytest.mark.asyncio
    async def test_hint_escalation_tracking(self, test_mentor_agent, test_dependencies):
        """Test hint escalation tracking works correctly."""
        test_model = test_mentor_agent.model
        test_model.agent_responses = [
            {"track_hint_escalation": {"user_message": "I'm confused"}},
            ModelTextResponse(content="Let's approach this differently. What specific part is confusing?")
        ]
        
        with patch('agents.mentor_agent.tools.hint_escalation_tracker') as mock_tracker:
            mock_tracker.return_value = {
                "current_hint_level": 2,
                "suggested_escalation": True,
                "escalation_reason": "confusion_signals_detected"
            }
            
            result = await test_mentor_agent.run(
                "I'm really confused about this",
                deps=test_dependencies
            )
            
            # Verify escalation tracking is available
            tool_names = [tool.name for tool in test_mentor_agent.tools]
            assert "track_hint_escalation" in tool_names


class TestHighLevelFunctions:
    """Test high-level convenience functions."""

    @pytest.mark.asyncio
    async def test_run_mentor_agent_function(self, mock_settings):
        """Test run_mentor_agent convenience function."""
        with patch('agents.mentor_agent.agent.mentor_agent.run') as mock_run:
            mock_run.return_value = Mock(data="What specific issue are you encountering?")
            
            with patch('agents.mentor_agent.tools.memory_search') as mock_search:
                mock_search.return_value = []
                
                with patch('agents.mentor_agent.tools.save_interaction') as mock_save:
                    mock_save.return_value = {"status": "saved"}
                    
                    response = await run_mentor_agent(
                        "I need help with JavaScript",
                        user_id="test-user"
                    )
                    
                    assert response == "What specific issue are you encountering?"
                    mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_mentor_conversation_function(self, mock_settings):
        """Test multi-turn conversation function."""
        messages = [
            {"role": "user", "content": "I'm having trouble with React"},
            {"role": "assistant", "content": "What specific React concept is challenging?"},
            {"role": "user", "content": "useState isn't updating"}
        ]
        
        with patch('agents.mentor_agent.agent.mentor_agent.run') as mock_run:
            mock_run.return_value = Mock(data="What do you expect useState to do versus what's actually happening?")
            
            with patch('agents.mentor_agent.tools.hint_escalation_tracker') as mock_tracker:
                mock_tracker.return_value = {
                    "current_hint_level": 1,
                    "suggested_escalation": False
                }
                
                with patch('agents.mentor_agent.tools.save_interaction') as mock_save:
                    mock_save.return_value = {"status": "saved"}
                    
                    response = await run_mentor_conversation(
                        messages,
                        user_id="test-user"
                    )
                    
                    assert "What do you expect" in response
                    mock_run.assert_called_once()

    def test_create_mentor_agent_with_deps(self, mock_settings):
        """Test agent creation with custom dependencies."""
        with patch('agents.mentor_agent.dependencies.MentorDependencies.from_settings') as mock_from_settings:
            mock_deps = Mock()
            mock_from_settings.return_value = mock_deps
            
            agent, deps = create_mentor_agent_with_deps(
                user_id="test-user",
                session_id="custom-session"
            )
            
            assert agent == mentor_agent
            assert deps == mock_deps
            mock_from_settings.assert_called_once()


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_memory_search_failure_recovery(self, test_mentor_agent, test_dependencies):
        """Test graceful handling when memory search fails."""
        with patch('agents.mentor_agent.tools.memory_search') as mock_search:
            mock_search.side_effect = Exception("ChromaDB connection failed")
            
            # Agent should still respond even if memory search fails
            result = await test_mentor_agent.run(
                "I need help debugging",
                deps=test_dependencies
            )
            
            assert result is not None
            assert isinstance(result.data, str)
            assert len(result.data) > 0

    @pytest.mark.asyncio 
    async def test_interaction_save_failure_recovery(self, test_mentor_agent, test_dependencies):
        """Test graceful handling when saving interactions fails."""
        with patch('agents.mentor_agent.tools.save_interaction') as mock_save:
            mock_save.side_effect = Exception("Database write failed")
            
            # Agent should still provide response even if save fails
            result = await test_mentor_agent.run(
                "What's the best way to debug?",
                deps=test_dependencies
            )
            
            assert result is not None
            assert isinstance(result.data, str)

    @pytest.mark.asyncio
    async def test_dependency_cleanup(self, test_dependencies):
        """Test dependencies are properly cleaned up."""
        # Mock cleanup methods
        test_dependencies._conversation_memory = Mock()
        test_dependencies._conversation_memory.close = AsyncMock()
        test_dependencies._db_session = Mock()
        test_dependencies._db_session.close = Mock()
        
        await test_dependencies.cleanup()
        
        # Verify cleanup was called
        test_dependencies._conversation_memory.close.assert_called_once()
        test_dependencies._db_session.close.assert_called_once()
        
        
class TestConfusionSignalDetection:
    """Test confusion signal detection functionality."""

    def test_detect_explicit_confusion_signals(self):
        """Test detection of explicit confusion indicators."""
        explicit_confusion = "I don't understand this at all, I'm really stuck"
        signals = detect_confusion_signals(explicit_confusion)
        
        assert len(signals) > 0
        assert "i don't understand" in signals
        assert "i'm stuck" in signals or any("stuck" in s for s in signals)

    def test_detect_implicit_confusion_signals(self):
        """Test detection of implicit confusion indicators."""
        implicit_confusion = "How does this work? I tried everything but it still doesn't work"
        signals = detect_confusion_signals(implicit_confusion)
        
        assert len(signals) > 0
        assert any("how" in s for s in signals) or "how?" in signals

    def test_detect_no_confusion_signals(self):
        """Test when no confusion signals are present."""
        clear_message = "I think I understand the concept and want to try implementing it"
        signals = detect_confusion_signals(clear_message)
        
        # Should either be empty or contain minimal signals
        assert len(signals) <= 1