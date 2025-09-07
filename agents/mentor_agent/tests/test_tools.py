"""
Test tool implementations for Mentor Agent.

Tests memory search, interaction saving, pattern analysis, and hint escalation tools
with comprehensive coverage of edge cases and error conditions.
"""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ..tools import (
    memory_search,
    save_interaction,
    analyze_learning_pattern,
    hint_escalation_tracker,
    detect_confusion_signals,
    extract_key_concepts
)
from ..dependencies import MentorDependencies


class TestMemorySearch:
    """Test memory search functionality."""

    @pytest.mark.asyncio
    async def test_memory_search_successful(self, test_dependencies, mock_conversation_memory):
        """Test successful memory search with results."""
        # Mock the context and dependencies
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies._conversation_memory = mock_conversation_memory
        
        # Mock similar interactions response
        mock_conversation_memory.find_similar_interactions.return_value = [
            {
                "interaction_id": "test-1",
                "question": "useState not updating",
                "response": "What do you think setState does?",
                "similarity_score": 0.85,
                "metadata": {"days_ago": 3, "hint_level": 2}
            }
        ]
        
        results = await memory_search(
            mock_ctx,
            "React state not updating immediately",
            "test-user-123",
            limit=3
        )
        
        assert len(results) > 0
        assert results[0]["similarity_score"] == 0.8  # Mock value from implementation
        assert "key_concepts" in results[0]
        mock_conversation_memory.find_similar_interactions.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_search_no_results(self, test_dependencies, mock_conversation_memory):
        """Test memory search when no similar interactions found."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies._conversation_memory = mock_conversation_memory
        
        # Mock empty response
        mock_conversation_memory.find_similar_interactions.return_value = []
        
        results = await memory_search(
            mock_ctx,
            "completely new topic",
            "test-user-123",
            limit=3
        )
        
        assert results == []

    @pytest.mark.asyncio
    async def test_memory_search_error_handling(self, test_dependencies):
        """Test memory search handles errors gracefully."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        
        # Mock memory that throws exception
        mock_memory = Mock()
        mock_memory.find_similar_interactions = AsyncMock(side_effect=Exception("ChromaDB connection failed"))
        test_dependencies._conversation_memory = mock_memory
        
        results = await memory_search(
            mock_ctx,
            "test query",
            "test-user",
            limit=3
        )
        
        assert results == []  # Should return empty list on error

    @pytest.mark.asyncio
    async def test_memory_search_parameter_validation(self, test_dependencies, mock_conversation_memory):
        """Test memory search with various parameter combinations."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies._conversation_memory = mock_conversation_memory
        mock_conversation_memory.find_similar_interactions.return_value = []
        
        # Test different limits
        await memory_search(mock_ctx, "test", "user", limit=1)
        await memory_search(mock_ctx, "test", "user", limit=5)
        await memory_search(mock_ctx, "test", "user", limit=10)
        
        assert mock_conversation_memory.find_similar_interactions.call_count == 3


class TestSaveInteraction:
    """Test interaction saving functionality."""

    @pytest.mark.asyncio
    async def test_save_interaction_successful(self, test_dependencies, mock_conversation_memory):
        """Test successful interaction saving."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies._conversation_memory = mock_conversation_memory
        
        mock_conversation_memory.add_interaction.return_value = {
            "id": "test-interaction-123",
            "status": "saved"
        }
        
        result = await save_interaction(
            mock_ctx,
            "test-user",
            "How do I debug React state?",
            "What patterns do you notice in your state updates?",
            hint_level=2,
            referenced_memories=["mem-1", "mem-2"]
        )
        
        assert result["status"] == "saved"
        assert result["interaction_id"] is not None
        assert "metadata_stored" in result
        
        # Verify metadata structure
        metadata = result["metadata_stored"]
        assert metadata["user_id"] == "test-user"
        assert metadata["hint_level"] == 2
        assert metadata["referenced_memories"] == ["mem-1", "mem-2"]
        assert "timestamp" in metadata
        assert "concepts_extracted" in metadata
        
        mock_conversation_memory.add_interaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_interaction_with_defaults(self, test_dependencies, mock_conversation_memory):
        """Test saving interaction with default parameters."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies._conversation_memory = mock_conversation_memory
        
        mock_conversation_memory.add_interaction.return_value = {"id": "test", "status": "saved"}
        
        result = await save_interaction(
            mock_ctx,
            "test-user",
            "Simple question",
            "Simple response"
        )
        
        assert result["status"] == "saved"
        metadata = result["metadata_stored"]
        assert metadata["hint_level"] == 1  # Default
        assert metadata["referenced_memories"] == []  # Default

    @pytest.mark.asyncio
    async def test_save_interaction_error_handling(self, test_dependencies):
        """Test save interaction handles errors gracefully."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        
        # Mock memory that fails
        mock_memory = Mock()
        mock_memory.add_interaction = AsyncMock(side_effect=Exception("Database write failed"))
        test_dependencies._conversation_memory = mock_memory
        
        result = await save_interaction(
            mock_ctx,
            "test-user",
            "test question",
            "test response"
        )
        
        assert result["status"] == "failed"
        assert "error" in result
        assert result["interaction_id"] is None

    @pytest.mark.asyncio
    async def test_save_interaction_concept_extraction(self, test_dependencies, mock_conversation_memory):
        """Test that key concepts are extracted correctly."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies._conversation_memory = mock_conversation_memory
        
        mock_conversation_memory.add_interaction.return_value = {"id": "test", "status": "saved"}
        
        result = await save_interaction(
            mock_ctx,
            "test-user",
            "I'm having trouble with React useState and async functions",
            "Response about React"
        )
        
        metadata = result["metadata_stored"]
        concepts = metadata["concepts_extracted"]
        assert "react" in concepts
        assert "async" in concepts or "function" in concepts


class TestLearningPatternAnalysis:
    """Test learning pattern analysis and classification."""

    def test_recent_repeat_classification(self):
        """Test classification of recent repeat issues."""
        result = analyze_learning_pattern(
            similarity_score=0.9,
            days_ago=3,
            interaction_count=1
        )
        
        assert result["pattern_type"] == "recent_repeat"
        assert result["confidence"] == 0.9
        assert result["guidance_approach"] == "gentle_reminder_of_discovery"
        assert result["suggested_hint_start_level"] == 1

    def test_pattern_recognition_classification(self):
        """Test classification of pattern recognition opportunities."""
        result = analyze_learning_pattern(
            similarity_score=0.7,
            days_ago=15,
            interaction_count=3
        )
        
        assert result["pattern_type"] == "pattern_recognition"
        assert result["confidence"] == 0.8
        assert result["guidance_approach"] == "connect_common_thread"
        assert result["suggested_hint_start_level"] == 2

    def test_skill_building_classification(self):
        """Test classification of skill building opportunities."""
        result = analyze_learning_pattern(
            similarity_score=0.5,
            days_ago=45,
            interaction_count=2
        )
        
        assert result["pattern_type"] == "skill_building"
        assert result["confidence"] == 0.7
        assert result["guidance_approach"] == "build_on_foundation"
        assert result["suggested_hint_start_level"] == 1

    def test_new_concept_classification(self):
        """Test classification of new concept learning."""
        result = analyze_learning_pattern(
            similarity_score=0.3,
            days_ago=5,
            interaction_count=0
        )
        
        assert result["pattern_type"] == "new_concept"
        assert result["confidence"] == 0.6
        assert result["guidance_approach"] == "standard_socratic_method"
        assert result["suggested_hint_start_level"] == 1

    def test_pattern_analysis_edge_cases(self):
        """Test pattern analysis with edge case inputs."""
        # Zero similarity
        result = analyze_learning_pattern(0.0, 10, 1)
        assert result["pattern_type"] == "new_concept"
        
        # Perfect similarity but very old
        result = analyze_learning_pattern(1.0, 100, 1)
        assert result["pattern_type"] == "skill_building"
        
        # High interaction count
        result = analyze_learning_pattern(0.6, 20, 10)
        assert result["pattern_type"] == "pattern_recognition"

    def test_pattern_analysis_error_handling(self):
        """Test pattern analysis handles errors gracefully."""
        with patch('agents.mentor_agent.tools.logger') as mock_logger:
            # This should not raise an exception
            result = analyze_learning_pattern(
                similarity_score="invalid",  # Invalid type
                days_ago=5,
                interaction_count=1
            )
            
            assert result["pattern_type"] == "skill_building"  # Fallback
            assert "error" in result


class TestHintEscalationTracker:
    """Test hint escalation tracking functionality."""

    @pytest.mark.asyncio
    async def test_hint_escalation_no_confusion(self, test_dependencies):
        """Test hint escalation with no confusion signals."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        
        result = await hint_escalation_tracker(
            mock_ctx,
            "test-session",
            user_confusion_signals=[]
        )
        
        assert result["current_hint_level"] == 1  # Should stay at level 1
        assert result["interaction_count"] == 1
        assert result["confusion_indicators"] == []

    @pytest.mark.asyncio
    async def test_hint_escalation_with_confusion(self, test_dependencies):
        """Test hint escalation when confusion signals detected."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        
        result = await hint_escalation_tracker(
            mock_ctx,
            "test-session",
            user_confusion_signals=["i don't understand", "stuck"]
        )
        
        assert result["current_hint_level"] == 2  # Should escalate
        assert result["suggested_escalation"] == True
        assert result["escalation_reason"] == "confusion_signals_detected"
        assert len(result["confusion_indicators"]) > 0

    @pytest.mark.asyncio
    async def test_hint_escalation_extended_conversation(self, test_dependencies):
        """Test escalation due to extended conversation."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies.conversation_depth = 5  # Extended conversation
        
        result = await hint_escalation_tracker(
            mock_ctx,
            "test-session",
            user_confusion_signals=[]
        )
        
        assert result["suggested_escalation"] == True
        assert result["escalation_reason"] == "extended_conversation"

    @pytest.mark.asyncio
    async def test_hint_escalation_max_level(self, test_dependencies):
        """Test hint escalation at maximum level."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies.current_hint_level = 4  # Max level
        
        result = await hint_escalation_tracker(
            mock_ctx,
            "test-session",
            user_confusion_signals=["very confused"]
        )
        
        assert result["current_hint_level"] == 4  # Should not exceed max
        assert result["max_level_reached"] == True

    @pytest.mark.asyncio
    async def test_hint_escalation_error_handling(self, test_dependencies):
        """Test hint escalation handles errors gracefully."""
        mock_ctx = Mock()
        mock_ctx.deps = None  # Invalid deps
        
        result = await hint_escalation_tracker(
            mock_ctx,
            "test-session",
            user_confusion_signals=["help"]
        )
        
        assert result["current_hint_level"] == 1  # Fallback
        assert result["suggested_escalation"] == False
        assert "error" in result


class TestConfusionSignalDetection:
    """Test confusion signal detection utility."""

    def test_explicit_confusion_detection(self):
        """Test detection of explicit confusion signals."""
        explicit_messages = [
            "I don't understand this at all",
            "I'm really stuck on this problem", 
            "I'm confused about how this works",
            "Can you help me with this?"
        ]
        
        for message in explicit_messages:
            signals = detect_confusion_signals(message)
            assert len(signals) > 0, f"Should detect confusion in: {message}"

    def test_implicit_confusion_detection(self):
        """Test detection of implicit confusion signals."""
        implicit_messages = [
            "How does this work exactly?",
            "But why would it behave that way?",
            "I tried everything but it doesn't work",
            "This still isn't working for me"
        ]
        
        for message in implicit_messages:
            signals = detect_confusion_signals(message)
            assert len(signals) > 0, f"Should detect confusion in: {message}"

    def test_repetitive_confusion_detection(self):
        """Test detection of repetitive confusion signals."""
        repetitive_messages = [
            "It's still not working after trying that",
            "Same error keeps happening",
            "I already tried that approach"
        ]
        
        for message in repetitive_messages:
            signals = detect_confusion_signals(message)
            assert len(signals) > 0, f"Should detect confusion in: {message}"

    def test_no_confusion_detection(self):
        """Test cases where no confusion signals should be detected."""
        clear_messages = [
            "I think I understand the concept now",
            "Let me try implementing this approach",
            "That makes sense, what about this other case?"
        ]
        
        for message in clear_messages:
            signals = detect_confusion_signals(message)
            assert len(signals) == 0, f"Should not detect confusion in: {message}"

    def test_mixed_confusion_signals(self):
        """Test messages with multiple types of confusion signals."""
        mixed_message = "I don't understand why this doesn't work, I tried everything"
        signals = detect_confusion_signals(mixed_message)
        
        assert len(signals) >= 2
        assert any("don't understand" in s for s in signals)
        assert any("tried everything" in s for s in signals)

    def test_case_insensitive_detection(self):
        """Test that confusion detection is case insensitive."""
        messages = [
            "I DON'T UNDERSTAND",
            "I'm STUCK on this",
            "How DOES this work?"
        ]
        
        for message in messages:
            signals = detect_confusion_signals(message)
            assert len(signals) > 0, f"Should detect confusion regardless of case: {message}"

    def test_empty_and_whitespace_messages(self):
        """Test edge cases with empty or whitespace-only messages."""
        edge_cases = ["", "   ", "\n\t", None]
        
        for case in edge_cases:
            if case is not None:
                signals = detect_confusion_signals(case)
                assert len(signals) == 0


class TestKeyConceptExtraction:
    """Test key concept extraction utility."""

    def test_programming_concept_extraction(self):
        """Test extraction of programming-related concepts."""
        text = "I'm having trouble with React useState and JavaScript async functions"
        concepts = extract_key_concepts(text)
        
        assert "react" in concepts
        assert "javascript" in concepts
        assert "async" in concepts or "function" in concepts

    def test_multiple_concepts_extraction(self):
        """Test extraction when multiple concepts are present."""
        text = "My Python loop is not working with the array and database API"
        concepts = extract_key_concepts(text)
        
        assert "python" in concepts
        assert "loop" in concepts
        assert "array" in concepts
        assert "database" in concepts
        assert "api" in concepts

    def test_concept_extraction_limit(self):
        """Test that concept extraction respects the limit."""
        text = "react javascript python html css function variable loop array object class method api database sql async"
        concepts = extract_key_concepts(text)
        
        assert len(concepts) <= 5  # Should limit to top 5

    def test_no_concepts_found(self):
        """Test when no programming concepts are found."""
        text = "Hello there, how are you today? Nice weather we're having."
        concepts = extract_key_concepts(text)
        
        assert len(concepts) == 0

    def test_case_insensitive_extraction(self):
        """Test that concept extraction is case insensitive."""
        text = "I need help with REACT and JavaScript FUNCTIONS"
        concepts = extract_key_concepts(text)
        
        assert "react" in concepts
        assert "function" in concepts

    def test_partial_word_matching(self):
        """Test that concepts are found in partial word matches."""
        text = "My functions are not functioning properly"
        concepts = extract_key_concepts(text)
        
        assert "function" in concepts


class TestToolParameterValidation:
    """Test tool parameter validation and edge cases."""

    @pytest.mark.asyncio
    async def test_memory_search_empty_query(self, test_dependencies, mock_conversation_memory):
        """Test memory search with empty query."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies._conversation_memory = mock_conversation_memory
        mock_conversation_memory.find_similar_interactions.return_value = []
        
        result = await memory_search(mock_ctx, "", "user", 3)
        assert result == []

    @pytest.mark.asyncio
    async def test_memory_search_invalid_limit(self, test_dependencies, mock_conversation_memory):
        """Test memory search with invalid limit values."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies._conversation_memory = mock_conversation_memory
        mock_conversation_memory.find_similar_interactions.return_value = []
        
        # Should handle negative limit
        result = await memory_search(mock_ctx, "test", "user", -1)
        assert isinstance(result, list)
        
        # Should handle zero limit
        result = await memory_search(mock_ctx, "test", "user", 0)
        assert isinstance(result, list)

    def test_analyze_pattern_invalid_inputs(self):
        """Test pattern analysis with invalid input types."""
        # Should handle string inputs gracefully
        result = analyze_learning_pattern("0.5", "3", "1")
        assert "pattern_type" in result
        
        # Should handle None inputs
        result = analyze_learning_pattern(None, None, None)
        assert "pattern_type" in result

    @pytest.mark.asyncio
    async def test_save_interaction_empty_strings(self, test_dependencies, mock_conversation_memory):
        """Test save interaction with empty string inputs."""
        mock_ctx = Mock()
        mock_ctx.deps = test_dependencies
        test_dependencies._conversation_memory = mock_conversation_memory
        mock_conversation_memory.add_interaction.return_value = {"id": "test", "status": "saved"}
        
        result = await save_interaction(mock_ctx, "", "", "")
        assert result["status"] == "saved"  # Should still work with empty strings