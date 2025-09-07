"""
Integration tests for Mentor Agent.

Tests full conversation flows, multi-turn interactions, and end-to-end
functionality with realistic scenarios.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelTextResponse

from ..agent import mentor_agent, run_mentor_agent, run_mentor_conversation
from ..dependencies import MentorDependencies
from ..tools import analyze_learning_pattern


class TestFullConversationFlows:
    """Test complete conversation scenarios from start to finish."""

    @pytest.mark.asyncio
    async def test_new_user_first_question_flow(self, test_dependencies):
        """Test complete flow for a new user's first question."""
        conversation_flow = []
        
        def new_user_function(messages, tools):
            conversation_flow.append(len(messages))
            
            # First interaction - no memory found
            if len(messages) == 1:
                return ModelTextResponse(
                    content="I notice this is a new challenge for you. What specific behavior are you seeing that's unexpected?"
                )
            # Follow-up questions based on user response
            elif len(messages) == 2:
                return ModelTextResponse(
                    content="That's a good observation. What do you think might be causing this behavior? What have you tried so far?"
                )
            else:
                return ModelTextResponse(
                    content="You're thinking about this well. What would be your next debugging step based on what you've discovered?"
                )
        
        function_model = FunctionModel(new_user_function)
        test_agent = mentor_agent.override(model=function_model)
        
        with patch('agents.mentor_agent.tools.memory_search') as mock_search:
            mock_search.return_value = []  # No past interactions
            
            with patch('agents.mentor_agent.tools.save_interaction') as mock_save:
                mock_save.return_value = {"interaction_id": "test", "status": "saved"}
                
                # Simulate multi-turn conversation
                user_messages = [
                    "My JavaScript function isn't working correctly",
                    "It's returning undefined instead of the expected value",
                    "I think it might be a scope issue"
                ]
                
                for message in user_messages:
                    result = await test_agent.run(message, deps=test_dependencies)
                    response = result.data.lower()
                    
                    # Should always ask questions, never give direct answers
                    assert "?" in response
                    # Should be encouraging and guidance-focused
                    assert any(word in response for word in ["what", "how", "think", "observe"])

    @pytest.mark.asyncio
    async def test_recent_repeat_issue_flow(self, test_dependencies):
        """Test flow when user repeats a recent issue."""
        def recent_repeat_function(messages, tools):
            if len(messages) == 1:
                return ModelTextResponse(
                    content="This looks very similar to your question from Tuesday about useState. What did you discover then about React's state batching?"
                )
            elif len(messages) == 2:
                return ModelTextResponse(
                    content="Exactly! So knowing that React batches state updates, what do you think might be happening in your current situation?"
                )
            else:
                return ModelTextResponse(
                    content="Perfect connection! Now that you've recognized the pattern, how would you modify your approach?"
                )
        
        function_model = FunctionModel(recent_repeat_function)
        test_agent = mentor_agent.override(model=function_model)
        
        with patch('agents.mentor_agent.tools.memory_search') as mock_search:
            mock_search.return_value = [
                {
                    "interaction_id": "tuesday-issue",
                    "question": "useState not updating immediately",
                    "similarity_score": 0.9,
                    "days_ago": 2,
                    "hint_level_reached": 3,
                    "resolution_approach": "discovered state batching"
                }
            ]
            
            conversation = [
                "My useState is not updating the UI immediately again",
                "Oh right, React batches state updates for performance",
                "So I should use useEffect or functional updates"
            ]
            
            for i, message in enumerate(conversation):
                result = await test_agent.run(message, deps=test_dependencies)
                response = result.data.lower()
                
                if i == 0:
                    # Should reference the recent similar issue
                    assert "similar" in response or "tuesday" in response
                    assert "discovered" in response or "batching" in response
                elif i == 1:
                    # Should confirm their understanding and build on it
                    assert "exactly" in response or "right" in response
                    assert "current situation" in response or "happening" in response
                else:
                    # Should encourage application of the pattern
                    assert "perfect" in response or "recognized" in response

    @pytest.mark.asyncio
    async def test_hint_escalation_conversation_flow(self, test_dependencies):
        """Test complete hint escalation from level 1 to 4."""
        escalation_level = 0
        
        def escalation_function(messages, tools):
            nonlocal escalation_level
            escalation_level += 1
            
            if escalation_level == 1:
                # Level 1 - Basic questioning
                return ModelTextResponse(
                    content="What do you think might be causing this issue? Have you encountered anything similar before?"
                )
            elif escalation_level == 2:
                # Level 2 - Pattern connection
                return ModelTextResponse(
                    content="I notice you've had debugging challenges before. What's the common thread in how you've approached these issues?"
                )
            elif escalation_level == 3:
                # Level 3 - Specific guidance
                return ModelTextResponse(
                    content="Remember when you successfully debugged a similar issue by checking the browser console? What did that approach teach you?"
                )
            else:
                # Level 4 - Step-by-step with history
                return ModelTextResponse(
                    content="Let's use your proven debugging method. First step - what should we examine to understand the current state?"
                )
        
        function_model = FunctionModel(escalation_function)
        test_agent = mentor_agent.override(model=function_model)
        
        with patch('agents.mentor_agent.tools.hint_escalation_tracker') as mock_tracker:
            mock_tracker.side_effect = [
                {"current_hint_level": 1, "suggested_escalation": False},
                {"current_hint_level": 2, "suggested_escalation": True, "escalation_reason": "confusion_signals_detected"},
                {"current_hint_level": 3, "suggested_escalation": True, "escalation_reason": "extended_conversation"},
                {"current_hint_level": 4, "suggested_escalation": True, "escalation_reason": "max_guidance_needed"}
            ]
            
            confusion_progression = [
                "I have a bug in my code",
                "I don't really understand what's happening",
                "I'm getting really stuck on this problem",
                "I've tried everything and I'm completely lost"
            ]
            
            for i, message in enumerate(confusion_progression):
                result = await test_agent.run(message, deps=test_dependencies)
                response = result.data.lower()
                
                # Verify escalation progression
                if i == 0:
                    assert "what do you think" in response
                elif i == 1:
                    assert "common thread" in response
                elif i == 2:
                    assert "remember when" in response
                else:
                    assert "first step" in response and "examine" in response

    @pytest.mark.asyncio
    async def test_pattern_recognition_flow(self, test_dependencies):
        """Test flow when user shows recurring learning patterns."""
        def pattern_function(messages, tools):
            if len(messages) == 1:
                return ModelTextResponse(
                    content="I notice you've asked about async operations several times. What pattern do you see across these different issues?"
                )
            else:
                return ModelTextResponse(
                    content="Great insight! How can you apply that understanding to identify what might be happening here?"
                )
        
        function_model = FunctionModel(pattern_function)
        test_agent = mentor_agent.override(model=function_model)
        
        with patch('agents.mentor_agent.tools.memory_search') as mock_search:
            mock_search.return_value = [
                {
                    "interaction_id": "async-1",
                    "question": "Promise not resolving",
                    "similarity_score": 0.7,
                    "days_ago": 15,
                    "key_concepts": ["promise", "async"]
                },
                {
                    "interaction_id": "async-2", 
                    "question": "Async/await not working",
                    "similarity_score": 0.65,
                    "days_ago": 22,
                    "key_concepts": ["async", "await"]
                }
            ]
            
            result = await test_agent.run(
                "My fetch request is returning a Promise instead of data",
                deps=test_dependencies
            )
            
            response = result.data.lower()
            assert "notice" in response and "async" in response and "pattern" in response


class TestMultiTurnInteractionHandling:
    """Test multi-turn conversation management."""

    @pytest.mark.asyncio
    async def test_conversation_context_maintenance(self, mock_settings):
        """Test that conversation context is maintained across turns."""
        messages_history = [
            {"role": "user", "content": "I'm learning React hooks"},
            {"role": "assistant", "content": "What specific aspect of hooks interests you?"},
            {"role": "user", "content": "useState seems confusing"},
            {"role": "assistant", "content": "What behavior are you seeing that's unexpected?"},
            {"role": "user", "content": "The state doesn't update immediately"}
        ]
        
        with patch('agents.mentor_agent.agent.mentor_agent.run') as mock_run:
            mock_run.return_value = Mock(data="What do you think happens when you call setState multiple times quickly?")
            
            with patch('agents.mentor_agent.tools.hint_escalation_tracker') as mock_tracker:
                mock_tracker.return_value = {
                    "current_hint_level": 2,
                    "suggested_escalation": True
                }
                
                with patch('agents.mentor_agent.tools.save_interaction') as mock_save:
                    mock_save.return_value = {"status": "saved"}
                    
                    response = await run_mentor_conversation(
                        messages_history,
                        user_id="test-user",
                        session_id="conversation-123"
                    )
                    
                    # Should process the latest message in context
                    assert "setState" in response
                    mock_run.assert_called_once()
                    # Should track escalation across the conversation
                    mock_tracker.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_state_tracking(self, test_dependencies):
        """Test that session state is tracked across interactions."""
        session_states = []
        
        def session_tracking_function(messages, tools):
            session_states.append(len(messages))
            return ModelTextResponse(
                content=f"This is interaction {len(messages)} in our session. What would you like to explore?"
            )
        
        function_model = FunctionModel(session_tracking_function)
        test_agent = mentor_agent.override(model=function_model)
        
        # Simulate multiple interactions in same session
        test_dependencies.session_id = "persistent-session"
        
        interactions = [
            "I want to learn JavaScript",
            "Can you help with functions?", 
            "What about arrow functions?",
            "How do closures work?"
        ]
        
        for i, interaction in enumerate(interactions):
            result = await test_agent.run(interaction, deps=test_dependencies)
            response = result.data
            assert f"interaction {i+1}" in response.lower()
        
        # Verify all interactions were tracked
        assert len(session_states) == 4
        assert session_states == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_memory_building_across_session(self, test_dependencies):
        """Test that each interaction builds the memory for future reference."""
        saved_interactions = []
        
        def memory_building_function(messages, tools):
            return ModelTextResponse(
                content="What patterns do you notice? How does this connect to what we discussed before?"
            )
        
        function_model = FunctionModel(memory_building_function)
        test_agent = mentor_agent.override(model=function_model)
        
        with patch('agents.mentor_agent.tools.save_interaction') as mock_save:
            def capture_save(ctx, user_id, message, response, hint_level=1, referenced_memories=None):
                saved_interactions.append({
                    "user_message": message,
                    "mentor_response": response,
                    "hint_level": hint_level
                })
                return {"interaction_id": f"save-{len(saved_interactions)}", "status": "saved"}
            
            mock_save.side_effect = capture_save
            
            learning_progression = [
                "I'm new to React",
                "How do components work?",
                "What about state management?",
                "Can you explain props vs state?"
            ]
            
            for message in learning_progression:
                await test_agent.run(message, deps=test_dependencies)
            
            # Verify each interaction was saved for memory building
            assert len(saved_interactions) == len(learning_progression)
            for i, saved in enumerate(saved_interactions):
                assert saved["user_message"] == learning_progression[i]


class TestRealisticLearningScenarios:
    """Test realistic programming learning scenarios."""

    @pytest.mark.asyncio
    async def test_react_debugging_scenario(self, test_dependencies):
        """Test a realistic React debugging learning scenario."""
        scenario_responses = [
            "What specific behavior are you seeing with your React component? When does this issue occur?",
            "Good observation about the timing. What do you know about how React handles state updates? What might cause a delay?",
            "Exactly! React batches state updates. Based on this understanding, what debugging approach would you take?",
            "Perfect! You're connecting the concepts well. How would you verify that batching is indeed what's happening?"
        ]
        
        response_index = 0
        def react_scenario_function(messages, tools):
            nonlocal response_index
            if response_index < len(scenario_responses):
                response = scenario_responses[response_index]
                response_index += 1
                return ModelTextResponse(content=response)
            return ModelTextResponse(content="You're developing strong debugging skills!")
        
        function_model = FunctionModel(react_scenario_function)
        test_agent = mentor_agent.override(model=function_model)
        
        with patch('agents.mentor_agent.tools.memory_search') as mock_search:
            mock_search.return_value = [
                {
                    "interaction_id": "react-state-1",
                    "question": "React state not updating",
                    "similarity_score": 0.8,
                    "days_ago": 10
                }
            ]
            
            learning_journey = [
                "My React component state isn't updating when I click the button",
                "The state seems to update after a delay, not immediately",
                "I remember you mentioned React batches updates for performance",
                "I could add console.logs to see the update timing"
            ]
            
            responses = []
            for message in learning_journey:
                result = await test_agent.run(message, deps=test_dependencies)
                responses.append(result.data)
            
            # Verify the learning progression
            assert "specific behavior" in responses[0].lower()
            assert "batches state updates" in responses[1].lower() or "delay" in responses[1].lower()
            assert "exactly" in responses[2].lower() and "connecting" in responses[2].lower()
            assert "verify" in responses[3].lower() or "debugging skills" in responses[3].lower()

    @pytest.mark.asyncio
    async def test_javascript_concepts_learning_scenario(self, test_dependencies):
        """Test learning JavaScript concepts with progressive understanding."""
        def js_concepts_function(messages, tools):
            message_content = messages[-1].content.lower()
            
            if "closure" in message_content:
                return ModelTextResponse(
                    content="Closures are a fascinating concept! What do you think happens to variables when a function finishes executing?"
                )
            elif "scope" in message_content:
                return ModelTextResponse(
                    content="Great question about scope! How do you think JavaScript decides which variables a function can access?"
                )
            elif "hoisting" in message_content:
                return ModelTextResponse(
                    content="Hoisting can be tricky! What do you predict happens when you use a variable before you declare it?"
                )
            else:
                return ModelTextResponse(
                    content="What specific JavaScript concept would you like to explore? What's puzzling you?"
                )
        
        function_model = FunctionModel(js_concepts_function)
        test_agent = mentor_agent.override(model=function_model)
        
        concept_progression = [
            "I want to understand JavaScript better",
            "What is closure in JavaScript?",
            "How does variable scope work?", 
            "Can you explain hoisting behavior?"
        ]
        
        for message in concept_progression:
            result = await test_agent.run(message, deps=test_dependencies)
            response = result.data.lower()
            
            # Should always be asking questions to guide discovery
            assert "?" in response
            # Should be encouraging exploration
            assert any(word in response for word in ["think", "predict", "what", "how", "explore"])

    @pytest.mark.asyncio
    async def test_debugging_methodology_scenario(self, test_dependencies):
        """Test learning systematic debugging methodology."""
        debugging_steps = [
            "What's the first thing you do when you encounter a bug? Where do you start looking?",
            "Excellent approach! After checking the console, what patterns do you look for in the error messages?",
            "Great systematic thinking! Once you identify the error location, how do you narrow down the root cause?",
            "Perfect debugging methodology! You're developing the systematic approach that expert developers use."
        ]
        
        step_index = 0
        def debugging_function(messages, tools):
            nonlocal step_index
            if step_index < len(debugging_steps):
                response = debugging_steps[step_index]
                step_index += 1
                return ModelTextResponse(content=response)
            return ModelTextResponse(content="You're becoming a systematic debugger!")
        
        function_model = FunctionModel(debugging_function)
        test_agent = mentor_agent.override(model=function_model)
        
        with patch('agents.mentor_agent.tools.memory_search') as mock_search:
            mock_search.return_value = [
                {
                    "interaction_id": "debug-1", 
                    "question": "How to debug JavaScript errors",
                    "similarity_score": 0.75,
                    "days_ago": 7
                }
            ]
            
            debugging_conversation = [
                "I keep getting bugs but don't know how to debug effectively",
                "I usually check the browser console first for error messages",
                "I look for line numbers and try to understand the error description",
                "I use console.log to trace the execution flow and variable values"
            ]
            
            for message in debugging_conversation:
                result = await test_agent.run(message, deps=test_dependencies)
                # Each response should build on the previous learning
                assert result.data is not None
                assert len(result.data) > 0


class TestErrorRecoveryAndFallbacks:
    """Test error handling in integration scenarios."""

    @pytest.mark.asyncio
    async def test_memory_failure_graceful_degradation(self, test_dependencies):
        """Test graceful handling when memory systems fail."""
        def fallback_function(messages, tools):
            return ModelTextResponse(
                content="Let's work through this step by step. What specific challenge are you facing right now?"
            )
        
        function_model = FunctionModel(fallback_function) 
        test_agent = mentor_agent.override(model=function_model)
        
        with patch('agents.mentor_agent.tools.memory_search') as mock_search:
            mock_search.side_effect = Exception("ChromaDB connection failed")
            
            # Should still provide helpful response despite memory failure
            result = await test_agent.run(
                "I need help with React state management",
                deps=test_dependencies
            )
            
            response = result.data.lower()
            assert "step by step" in response
            assert "?" in response  # Still Socratic
            # Should not expose technical errors to user
            assert "chromadb" not in response

    @pytest.mark.asyncio
    async def test_save_failure_conversation_continues(self, test_dependencies):
        """Test conversation continues even when saving interactions fails."""
        def continuing_function(messages, tools):
            return ModelTextResponse(
                content="That's an interesting question. What patterns do you notice in this problem?"
            )
        
        function_model = FunctionModel(continuing_function)
        test_agent = mentor_agent.override(model=function_model)
        
        with patch('agents.mentor_agent.tools.save_interaction') as mock_save:
            mock_save.side_effect = Exception("Database write failed")
            
            # Conversation should continue despite save failure
            result = await test_agent.run(
                "How do I implement authentication?", 
                deps=test_dependencies
            )
            
            assert result.data is not None
            assert "patterns" in result.data.lower()
            assert "?" in result.data

    @pytest.mark.asyncio
    async def test_dependency_initialization_failure_recovery(self):
        """Test recovery when dependency initialization fails."""
        with patch('agents.mentor_agent.dependencies.MentorDependencies.from_settings') as mock_deps:
            mock_deps.side_effect = Exception("Database connection failed")
            
            # High-level function should handle dependency failures gracefully
            with patch('agents.mentor_agent.agent.logger') as mock_logger:
                response = await run_mentor_agent(
                    "I need programming help",
                    user_id="test-user"
                )
                
                # Should return helpful fallback response
                assert "memory systems" in response or "step by step" in response
                mock_logger.error.assert_called()


class TestPerformanceScenarios:
    """Test performance characteristics in integration scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_conversations_handling(self, test_dependencies):
        """Test handling multiple concurrent conversation sessions."""
        def concurrent_function(messages, tools):
            return ModelTextResponse(
                content="I'm ready to help with your programming challenge. What specific issue would you like to explore?"
            )
        
        function_model = FunctionModel(concurrent_function)
        test_agent = mentor_agent.override(model=function_model)
        
        # Simulate multiple users asking questions simultaneously
        concurrent_requests = [
            ("user-1", "Help with React hooks"),
            ("user-2", "JavaScript closure question"),
            ("user-3", "Python debugging issue"),
            ("user-1", "Follow-up on React hooks"),  # Same user, different session
        ]
        
        tasks = []
        for user_id, message in concurrent_requests:
            # Create separate dependencies for each session
            session_deps = MentorDependencies.from_settings(
                test_dependencies,
                user_id=user_id,
                session_id=f"session-{user_id}-{len(tasks)}"
            )
            task = test_agent.run(message, deps=session_deps)
            tasks.append(task)
        
        # Run all conversations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All conversations should complete successfully
        assert len(results) == 4
        for result in results:
            assert not isinstance(result, Exception)
            assert result.data is not None

    @pytest.mark.asyncio 
    async def test_long_conversation_memory_efficiency(self, test_dependencies):
        """Test memory efficiency in long conversations."""
        interaction_count = 0
        
        def memory_efficient_function(messages, tools):
            nonlocal interaction_count
            interaction_count += 1
            return ModelTextResponse(
                content=f"Continuing our learning journey (interaction {interaction_count}). What would you like to explore next?"
            )
        
        function_model = FunctionModel(memory_efficient_function)
        test_agent = mentor_agent.override(model=function_model)
        
        # Simulate a long learning conversation (20 interactions)
        for i in range(20):
            message = f"Question {i+1}: Help me understand concept {i+1}"
            result = await test_agent.run(message, deps=test_dependencies)
            
            # Should continue to respond appropriately even in long conversations
            assert f"interaction {i+1}" in result.data
            
        # Verify all interactions were handled
        assert interaction_count == 20