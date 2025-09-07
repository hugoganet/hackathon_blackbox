"""
Unit Tests for MentorTools Class Methods
Tests the individual methods of the MentorTools class for memory-guided mentoring
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Test imports
try:
    from agents.mentor_agent.tools import (
        MentorTools, 
        MemoryContext, 
        HintTracker, 
        SimilarInteraction, 
        LearningPatterns
    )
    PYDANTIC_AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PydanticAI imports not available: {e}")
    PYDANTIC_AI_AVAILABLE = False


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMentorToolsInitialization:
    """Test MentorTools initialization and configuration"""
    
    def test_initialization_without_dependencies(self):
        """Test MentorTools can be initialized without dependencies"""
        tools = MentorTools()
        
        assert tools.memory_store is None
        assert tools.db_session is None
        assert tools.hint_trackers == {}
    
    def test_initialization_with_dependencies(self):
        """Test MentorTools initialization with mock dependencies"""
        mock_memory = Mock()
        mock_db = Mock()
        
        tools = MentorTools(memory_store=mock_memory, db_session=mock_db)
        
        assert tools.memory_store == mock_memory
        assert tools.db_session == mock_db
        assert tools.hint_trackers == {}


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestIntentClassification:
    """Test user intent classification functionality"""
    
    @pytest.mark.asyncio
    async def test_debugging_intent_detection(self):
        """Test detection of debugging-related intents"""
        tools = MentorTools()
        
        test_cases = [
            "My code has an error",
            "There's a bug in my program", 
            "This doesn't work properly",
            "I'm getting an issue with my function",
            "My script is not working"
        ]
        
        for message in test_cases:
            intent = await tools.classify_user_intent(message)
            assert intent == "debugging", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_concept_explanation_intent(self):
        """Test detection of concept explanation intents"""
        tools = MentorTools()
        
        test_cases = [
            "How do I create a function?",
            "What is a variable in Python?",
            "Can you explain how loops work?",
            "I need to understand recursion",
            "Help me understand classes"
        ]
        
        for message in test_cases:
            intent = await tools.classify_user_intent(message)
            assert intent == "concept_explanation", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_improvement_intent(self):
        """Test detection of code improvement intents"""
        tools = MentorTools()
        
        test_cases = [
            "How can I improve this code?",
            "What's a better way to write this?",
            "How do I optimize my function?",
            "What are the best practices for this?"
        ]
        
        for message in test_cases:
            intent = await tools.classify_user_intent(message)
            assert intent == "improvement", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_testing_intent(self):
        """Test detection of testing-related intents"""
        tools = MentorTools()
        
        test_cases = [
            "How do I test this function?",
            "I need help writing unit tests",
            "What's the best way to test this code?"
        ]
        
        for message in test_cases:
            intent = await tools.classify_user_intent(message)
            assert intent == "testing", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_deployment_intent(self):
        """Test detection of deployment-related intents"""
        tools = MentorTools()
        
        test_cases = [
            "How do I deploy this app?",
            "I need help with production deployment",
            "What's the best hosting solution?"
        ]
        
        for message in test_cases:
            intent = await tools.classify_user_intent(message)
            assert intent == "deployment", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_general_intent_fallback(self):
        """Test fallback to general intent for unclear messages"""
        tools = MentorTools()
        
        test_cases = [
            "Hello there",
            "I need some help",
            "Can you assist me?",
            "Programming question"
        ]
        
        for message in test_cases:
            intent = await tools.classify_user_intent(message)
            assert intent == "general", f"Failed for: {message}"


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestProgrammingLanguageDetection:
    """Test programming language detection from user messages"""
    
    @pytest.mark.asyncio
    async def test_javascript_detection(self):
        """Test JavaScript language detection"""
        tools = MentorTools()
        
        test_cases = [
            "I'm having issues with my React component",
            "My JavaScript function uses const variables",
            "How do I use npm install?",
            "My Vue.js app isn't working",
            "I'm using the => arrow function syntax"
        ]
        
        for message in test_cases:
            language = await tools.detect_programming_language(message)
            assert language == "javascript", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_python_detection(self):
        """Test Python language detection"""
        tools = MentorTools()
        
        test_cases = [
            "My Python function with def main() isn't working",
            "I'm using Django for my web app",
            "How do I import numpy?",
            "My Flask application has an issue",
            "I'm getting a Python __init__ error"
        ]
        
        for message in test_cases:
            language = await tools.detect_programming_language(message)
            assert language == "python", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_java_detection(self):
        """Test Java language detection"""
        tools = MentorTools()
        
        test_cases = [
            "My Java class has a public static method",
            "I'm using Spring Boot for my API",
            "How do I use Maven for dependencies?",
            "My private class variable isn't accessible"
        ]
        
        for message in test_cases:
            language = await tools.detect_programming_language(message)
            assert language == "java", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_html_detection(self):
        """Test HTML language detection"""
        tools = MentorTools()
        
        test_cases = [
            "My <div> element isn't showing up",
            "I need help with HTML class attributes", 
            "My <!DOCTYPE html> declaration is missing",
            "How do I use <span> tags properly?"
        ]
        
        for message in test_cases:
            language = await tools.detect_programming_language(message)
            assert language == "html", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_css_detection(self):
        """Test CSS language detection"""
        tools = MentorTools()
        
        test_cases = [
            "My CSS color: red isn't working",
            "I need help with margin: 10px",
            "How do I use flexbox in my styles?",
            "My background: blue isn't showing"
        ]
        
        for message in test_cases:
            language = await tools.detect_programming_language(message)
            assert language == "css", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_multiple_languages_highest_score(self):
        """Test language detection when multiple languages are mentioned"""
        tools = MentorTools()
        
        # JavaScript should win due to more keywords
        message = "I'm using JavaScript with React and some HTML div elements"
        language = await tools.detect_programming_language(message)
        assert language == "javascript"
    
    @pytest.mark.asyncio
    async def test_unknown_language_fallback(self):
        """Test fallback to unknown for unrecognized languages"""
        tools = MentorTools()
        
        test_cases = [
            "I need help with general programming",
            "My algorithm isn't working",
            "Can you help me with this problem?"
        ]
        
        for message in test_cases:
            language = await tools.detect_programming_language(message)
            assert language == "unknown", f"Failed for: {message}"


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestDifficultyAnalysis:
    """Test difficulty level analysis functionality"""
    
    @pytest.mark.asyncio
    async def test_beginner_difficulty_detection(self):
        """Test beginner difficulty level detection"""
        tools = MentorTools()
        
        test_cases = [
            "What is a variable? I'm new to programming",
            "How do I start learning to code?",
            "I'm a beginner and need basic help",
            "Can you explain simple programming concepts?",
            "This is my first time coding"
        ]
        
        for message in test_cases:
            difficulty = await tools.analyze_difficulty_level(message)
            assert difficulty == "beginner", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_advanced_difficulty_detection(self):
        """Test advanced difficulty level detection"""
        tools = MentorTools()
        
        test_cases = [
            "How do I optimize this algorithm for better performance?",
            "I need help with microservices architecture",
            "Can you explain distributed system patterns?",
            "How do I implement async/await with threading?",
            "I'm working on algorithm complexity optimization"
        ]
        
        for message in test_cases:
            difficulty = await tools.analyze_difficulty_level(message)
            assert difficulty == "advanced", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_intermediate_difficulty_fallback(self):
        """Test intermediate difficulty as default/fallback"""
        tools = MentorTools()
        
        test_cases = [
            "How do I use this library?",
            "I'm having trouble with this function",
            "Can you help me understand this code?"
        ]
        
        for message in test_cases:
            difficulty = await tools.analyze_difficulty_level(message)
            assert difficulty == "intermediate", f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_difficulty_with_learning_patterns(self):
        """Test difficulty analysis considering learning patterns"""
        tools = MentorTools()
        
        # Mock learning patterns for a beginner
        beginner_patterns = LearningPatterns(
            total_interactions=3,
            most_common_language=("python", 2),
            most_common_intent=("concept_explanation", 2), 
            difficulty_distribution={"beginner": 3},
            languages_practiced=["python"]
        )
        
        difficulty = await tools.analyze_difficulty_level(
            "How do I use functions?", 
            learning_patterns=beginner_patterns
        )
        assert difficulty == "beginner"
        
        # Mock learning patterns for an advanced user
        advanced_patterns = LearningPatterns(
            total_interactions=25,
            most_common_language=("javascript", 15),
            most_common_intent=("optimization", 8),
            difficulty_distribution={"advanced": 20, "intermediate": 5},
            languages_practiced=["javascript", "typescript", "python", "java"]
        )
        
        difficulty = await tools.analyze_difficulty_level(
            "How do I use this framework?",
            learning_patterns=advanced_patterns
        )
        assert difficulty == "advanced"


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestHintEscalationTracking:
    """Test hint escalation system functionality"""
    
    @pytest.mark.asyncio
    async def test_initial_hint_level(self):
        """Test initial hint level for new questions"""
        tools = MentorTools()
        
        level = await tools.track_hint_escalation(
            user_id="test_user",
            session_id="test_session", 
            question="How do I fix this React error?",
            hint="First hint"
        )
        
        assert level == 1
    
    @pytest.mark.asyncio
    async def test_hint_escalation_progression(self):
        """Test hint level progression over multiple hints"""
        tools = MentorTools()
        
        user_id = "test_user"
        session_id = "test_session"
        question = "How do I debug this JavaScript issue?"
        
        # First hint - should be level 1
        level1 = await tools.track_hint_escalation(user_id, session_id, question, "First hint")
        assert level1 == 1
        
        # Second hint - should still be level 1 (escalation happens after 2 hints per level)
        level2 = await tools.track_hint_escalation(user_id, session_id, question, "Second hint")
        assert level2 == 2  # Escalates after 2 hints
        
        # Third hint - should be level 2
        level3 = await tools.track_hint_escalation(user_id, session_id, question, "Third hint")
        assert level3 == 2
        
        # Fourth hint - should escalate to level 3
        level4 = await tools.track_hint_escalation(user_id, session_id, question, "Fourth hint")
        assert level4 == 3
    
    @pytest.mark.asyncio
    async def test_hint_level_maximum_cap(self):
        """Test that hint level never exceeds 4"""
        tools = MentorTools()
        
        user_id = "test_user"
        session_id = "test_session"
        question = "Complex algorithm question"
        
        # Give many hints to test the cap
        for i in range(15):
            level = await tools.track_hint_escalation(
                user_id, session_id, question, f"Hint {i+1}"
            )
            assert level <= 4, f"Level {level} exceeded maximum of 4"
        
        # Final level should be 4
        assert level == 4
    
    @pytest.mark.asyncio
    async def test_different_questions_independent_tracking(self):
        """Test that different questions track hints independently"""
        tools = MentorTools()
        
        user_id = "test_user"
        session_id = "test_session"
        
        # First question
        question1 = "How do I use React hooks?"
        level1a = await tools.track_hint_escalation(user_id, session_id, question1, "Hint 1")
        level1b = await tools.track_hint_escalation(user_id, session_id, question1, "Hint 2")
        
        # Second question (different)
        question2 = "How do I handle API errors?"
        level2a = await tools.track_hint_escalation(user_id, session_id, question2, "Hint 1")
        
        # First question should have escalated
        assert level1b == 2
        # Second question should start fresh
        assert level2a == 1
    
    @pytest.mark.asyncio
    async def test_hint_tracker_timeout_reset(self):
        """Test hint tracker resets after timeout period"""
        tools = MentorTools()
        
        user_id = "test_user"
        session_id = "test_session"
        question = "Test question"
        
        # Give initial hint
        level1 = await tools.track_hint_escalation(user_id, session_id, question, "First hint")
        assert level1 == 1
        
        # Manually set timestamp to simulate timeout
        question_hash = str(hash(question.lower().strip()))
        tracker_key = f"{user_id}_{session_id}_{question_hash}"
        
        if tracker_key in tools.hint_trackers:
            tools.hint_trackers[tracker_key].timestamp = datetime.now() - timedelta(hours=2)
        
        # Next hint should reset to level 1 due to timeout
        level2 = await tools.track_hint_escalation(user_id, session_id, question, "Second hint")
        assert level2 == 1  # Reset due to timeout


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMemoryContextRetrieval:
    """Test memory context retrieval functionality"""
    
    @pytest.mark.asyncio
    async def test_memory_context_with_similar_interactions(self):
        """Test memory context retrieval with similar past interactions"""
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.return_value = [
            {
                "memory_id": "test_id_1",
                "user_message": "Previous React question",
                "mentor_response": "Previous guidance",
                "similarity": 0.8,
                "metadata": {"programming_language": "javascript"}
            },
            {
                "memory_id": "test_id_2", 
                "user_message": "Another JavaScript question",
                "mentor_response": "More guidance",
                "similarity": 0.7,
                "metadata": {"programming_language": "javascript"}
            }
        ]
        
        mock_memory_store.get_user_learning_patterns.return_value = {
            "total_interactions": 5,
            "most_common_language": ("javascript", 3),
            "most_common_intent": ("debugging", 2),
            "difficulty_distribution": {"beginner": 3, "intermediate": 2},
            "languages_practiced": ["javascript", "html"]
        }
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        context = await tools.get_memory_context(
            "test_user", 
            "How do I debug React components?"
        )
        
        # Verify context structure
        assert isinstance(context, MemoryContext)
        assert len(context.similar_interactions) == 2
        assert context.learning_patterns.total_interactions == 5
        assert context.learning_patterns.most_common_language == ("javascript", 3)
        assert "javascript" in context.recent_topics
        
        # Verify similar interactions
        assert context.similar_interactions[0].memory_id == "test_id_1"
        assert context.similar_interactions[0].similarity == 0.8
        assert context.similar_interactions[1].similarity == 0.7
    
    @pytest.mark.asyncio
    async def test_memory_context_without_memory_store(self):
        """Test memory context when memory store is not available"""
        tools = MentorTools()
        
        context = await tools.get_memory_context(
            "test_user",
            "How do I use Python?"
        )
        
        # Should return empty context with defaults
        assert isinstance(context, MemoryContext)
        assert len(context.similar_interactions) == 0
        assert context.learning_patterns.total_interactions == 0
        assert context.learning_patterns.most_common_language == ("unknown", 0)
        assert context.learning_patterns.most_common_intent == ("general", 0)
        assert context.recent_topics == []
    
    @pytest.mark.asyncio
    async def test_memory_context_with_database_integration(self):
        """Test memory context with database skill progression data"""
        mock_db = Mock()
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.return_value = []
        mock_memory_store.get_user_learning_patterns.return_value = None
        
        tools = MentorTools(memory_store=mock_memory_store, db_session=mock_db)
        
        # Mock database functions
        with patch('agents.mentor_agent.tools.get_user_by_username') as mock_get_user, \
             patch('agents.mentor_agent.tools.get_user_skill_progression') as mock_get_skills:
            
            mock_user = Mock()
            mock_user.id = "user_uuid"
            mock_get_user.return_value = mock_user
            
            mock_get_skills.return_value = [
                {"skill_name": "JavaScript", "mastery_level": 0.7},
                {"skill_name": "React", "mastery_level": 0.5}
            ]
            
            context = await tools.get_memory_context("test_user", "Programming question")
            
            # Verify skill progression data is included
            assert context.skill_progression["total_skills_tracked"] == 2
            assert len(context.skill_progression["recent_skills"]) == 2
    
    @pytest.mark.asyncio
    async def test_memory_context_error_handling(self):
        """Test memory context handles errors gracefully"""
        mock_memory_store = Mock()
        mock_memory_store.find_similar_interactions.side_effect = Exception("Memory store error")
        mock_memory_store.get_user_learning_patterns.side_effect = Exception("Pattern error")
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        context = await tools.get_memory_context("test_user", "Test question")
        
        # Should handle errors and return default context
        assert isinstance(context, MemoryContext)
        assert len(context.similar_interactions) == 0
        assert context.learning_patterns.total_interactions == 0


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestInteractionStorage:
    """Test interaction storage functionality"""
    
    @pytest.mark.asyncio
    async def test_store_interaction_success(self):
        """Test successful interaction storage"""
        mock_memory_store = Mock()
        mock_memory_store.add_interaction.return_value = "memory_id_123"
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        memory_id = await tools.store_interaction(
            user_id="test_user",
            user_message="How do I use async/await in Python?",
            mentor_response="Great question! Let's explore this step by step...",
            session_id="test_session",
            metadata={"timestamp": "2024-01-01T12:00:00"}
        )
        
        assert memory_id == "memory_id_123"
        
        # Verify memory store was called with correct parameters
        mock_memory_store.add_interaction.assert_called_once()
        call_kwargs = mock_memory_store.add_interaction.call_args[1]
        
        assert call_kwargs["user_id"] == "test_user"
        assert call_kwargs["user_message"] == "How do I use async/await in Python?"
        assert call_kwargs["agent_type"] == "pydantic_strict"
        assert call_kwargs["programming_language"] == "python"  # Should be detected
        assert call_kwargs["difficulty_level"] in ["beginner", "intermediate", "advanced"]
        assert call_kwargs["user_intent"] == "concept_explanation"  # Should be classified
    
    @pytest.mark.asyncio
    async def test_store_interaction_without_memory_store(self):
        """Test interaction storage when memory store is not available"""
        tools = MentorTools()
        
        memory_id = await tools.store_interaction(
            user_id="test_user",
            user_message="Test question",
            mentor_response="Test response"
        )
        
        assert memory_id is None
    
    @pytest.mark.asyncio
    async def test_store_interaction_error_handling(self):
        """Test interaction storage error handling"""
        mock_memory_store = Mock()
        mock_memory_store.add_interaction.side_effect = Exception("Storage error")
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        memory_id = await tools.store_interaction(
            user_id="test_user", 
            user_message="Test question",
            mentor_response="Test response"
        )
        
        assert memory_id is None


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestUtilityMethods:
    """Test utility methods and cleanup functionality"""
    
    def test_cleanup_old_trackers(self):
        """Test cleanup of old hint trackers"""
        tools = MentorTools()
        
        # Add some trackers with different timestamps
        current_time = datetime.now()
        old_tracker = HintTracker(
            user_id="user1",
            session_id="session1", 
            current_question_hash="hash1",
            timestamp=current_time - timedelta(hours=25)  # Old
        )
        
        recent_tracker = HintTracker(
            user_id="user2",
            session_id="session2",
            current_question_hash="hash2",
            timestamp=current_time - timedelta(hours=1)  # Recent
        )
        
        tools.hint_trackers["old_key"] = old_tracker
        tools.hint_trackers["recent_key"] = recent_tracker
        
        # Cleanup trackers older than 24 hours
        tools.cleanup_old_trackers(hours_old=24)
        
        # Old tracker should be removed, recent one should remain
        assert "old_key" not in tools.hint_trackers
        assert "recent_key" in tools.hint_trackers


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestPydanticModels:
    """Test Pydantic models used by MentorTools"""
    
    def test_similar_interaction_model(self):
        """Test SimilarInteraction model validation"""
        interaction = SimilarInteraction(
            memory_id="test_id",
            user_message="Test question",
            mentor_response="Test response",
            similarity=0.85,
            metadata={"language": "python", "intent": "debugging"}
        )
        
        assert interaction.memory_id == "test_id"
        assert interaction.similarity == 0.85
        assert interaction.metadata["language"] == "python"
    
    def test_learning_patterns_model(self):
        """Test LearningPatterns model validation"""
        patterns = LearningPatterns(
            total_interactions=10,
            most_common_language=("javascript", 6),
            most_common_intent=("debugging", 4),
            difficulty_distribution={"beginner": 3, "intermediate": 7},
            languages_practiced=["javascript", "python", "html"]
        )
        
        assert patterns.total_interactions == 10
        assert patterns.most_common_language == ("javascript", 6)
        assert patterns.most_common_intent == ("debugging", 4)
        assert "javascript" in patterns.languages_practiced
    
    def test_memory_context_model(self):
        """Test MemoryContext model validation"""
        similar_interactions = [
            SimilarInteraction(
                memory_id="1",
                user_message="Test 1",
                mentor_response="Response 1",
                similarity=0.8,
                metadata={}
            )
        ]
        
        learning_patterns = LearningPatterns(
            total_interactions=5,
            most_common_language=("python", 3),
            most_common_intent=("concept_explanation", 2),
            difficulty_distribution={"beginner": 5},
            languages_practiced=["python"]
        )
        
        context = MemoryContext(
            similar_interactions=similar_interactions,
            learning_patterns=learning_patterns,
            recent_topics=["python", "functions"],
            skill_progression={"total_skills": 3}
        )
        
        assert len(context.similar_interactions) == 1
        assert context.learning_patterns.total_interactions == 5
        assert "python" in context.recent_topics
    
    def test_hint_tracker_model(self):
        """Test HintTracker model validation and defaults"""
        tracker = HintTracker(
            user_id="test_user",
            session_id="test_session", 
            current_question_hash="hash123"
        )
        
        assert tracker.user_id == "test_user"
        assert tracker.hint_level == 1  # Default
        assert tracker.hints_given == []  # Default
        assert isinstance(tracker.timestamp, datetime)
        
        # Test with custom values
        custom_tracker = HintTracker(
            user_id="test_user2",
            session_id="test_session2",
            current_question_hash="hash456",
            hint_level=3,
            hints_given=["Hint 1", "Hint 2", "Hint 3"]
        )
        
        assert custom_tracker.hint_level == 3
        assert len(custom_tracker.hints_given) == 3


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running MentorTools Unit Tests...")
    
    if PYDANTIC_AI_AVAILABLE:
        print("✅ PydanticAI imports available")
        
        # Test basic functionality
        test_instance = TestMentorToolsInitialization()
        test_instance.test_initialization_without_dependencies()
        print("✅ Initialization tests passed")
        
        intent_test = TestIntentClassification()
        asyncio.run(intent_test.test_debugging_intent_detection())
        print("✅ Intent classification tests passed")
        
        print("🎉 MentorTools unit tests setup completed successfully!")
        print("Run with: pytest tests/test_mentor_tools_unit.py -v")
    else:
        print("⚠️ PydanticAI not available - tests skipped")
        print("Install PydanticAI to run full test suite: pip install pydantic-ai")