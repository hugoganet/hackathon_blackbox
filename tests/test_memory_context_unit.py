"""
Unit Tests for Memory Context Operations
Tests memory retrieval, formatting, and context generation for mentor agent
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
        SimilarInteraction, 
        LearningPatterns
    )
    from agents.mentor_agent.prompts import (
        format_memory_context,
        MEMORY_CONTEXT_TEMPLATE
    )
    PYDANTIC_AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PydanticAI imports not available: {e}")
    PYDANTIC_AI_AVAILABLE = False


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMemoryContextGeneration:
    """Test memory context generation with various data scenarios"""
    
    @pytest.mark.asyncio
    async def test_rich_memory_context_generation(self):
        """Test memory context with full data available"""
        mock_memory_store = Mock()
        mock_db_session = Mock()
        
        # Mock similar interactions
        mock_memory_store.find_similar_interactions.return_value = [
            {
                "memory_id": "mem_001",
                "user_message": "How do I handle React component state?",
                "mentor_response": "Great question! Let's think about state management...",
                "similarity": 0.92,
                "metadata": {
                    "programming_language": "javascript",
                    "user_intent": "concept_explanation",
                    "difficulty_level": "intermediate",
                    "timestamp": "2024-01-15T10:30:00"
                }
            },
            {
                "memory_id": "mem_002", 
                "user_message": "My React hooks aren't working properly",
                "mentor_response": "Let's debug this step by step...",
                "similarity": 0.87,
                "metadata": {
                    "programming_language": "javascript", 
                    "user_intent": "debugging",
                    "difficulty_level": "intermediate",
                    "timestamp": "2024-01-14T14:20:00"
                }
            },
            {
                "memory_id": "mem_003",
                "user_message": "Can you explain React lifecycle methods?",
                "mentor_response": "Let's explore how components work...",
                "similarity": 0.83,
                "metadata": {
                    "programming_language": "javascript",
                    "user_intent": "concept_explanation", 
                    "difficulty_level": "beginner",
                    "timestamp": "2024-01-13T09:15:00"
                }
            }
        ]
        
        # Mock learning patterns
        mock_memory_store.get_user_learning_patterns.return_value = {
            "total_interactions": 15,
            "most_common_language": ("javascript", 12),
            "most_common_intent": ("concept_explanation", 8),
            "difficulty_distribution": {
                "beginner": 5,
                "intermediate": 8, 
                "advanced": 2
            },
            "languages_practiced": ["javascript", "html", "css", "python"]
        }
        
        tools = MentorTools(memory_store=mock_memory_store, db_session=mock_db_session)
        
        context = await tools.get_memory_context(
            user_id="experienced_user",
            current_message="How do I optimize React component rendering?",
            session_id="session_123"
        )
        
        # Verify context structure and content
        assert isinstance(context, MemoryContext)
        assert len(context.similar_interactions) == 3
        
        # Verify similar interactions are properly structured
        first_interaction = context.similar_interactions[0]
        assert first_interaction.memory_id == "mem_001"
        assert first_interaction.similarity == 0.92
        assert "React component state" in first_interaction.user_message
        assert first_interaction.metadata["programming_language"] == "javascript"
        
        # Verify learning patterns
        assert context.learning_patterns.total_interactions == 15
        assert context.learning_patterns.most_common_language == ("javascript", 12)
        assert context.learning_patterns.most_common_intent == ("concept_explanation", 8)
        assert "javascript" in context.learning_patterns.languages_practiced
        
        # Verify recent topics extraction
        assert len(context.recent_topics) > 0
        assert "javascript" in context.recent_topics
    
    @pytest.mark.asyncio
    async def test_sparse_memory_context_generation(self):
        """Test memory context with minimal data"""
        mock_memory_store = Mock()
        
        # Mock minimal similar interactions
        mock_memory_store.find_similar_interactions.return_value = [
            {
                "memory_id": "mem_001",
                "user_message": "Basic Python question",
                "mentor_response": "Let's start simple...",
                "similarity": 0.65,
                "metadata": {
                    "programming_language": "python",
                    "user_intent": "general"
                }
            }
        ]
        
        # Mock minimal learning patterns
        mock_memory_store.get_user_learning_patterns.return_value = {
            "total_interactions": 2,
            "most_common_language": ("python", 2),
            "most_common_intent": ("general", 2),
            "difficulty_distribution": {"beginner": 2},
            "languages_practiced": ["python"]
        }
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        context = await tools.get_memory_context(
            user_id="new_user",
            current_message="What is a Python variable?"
        )
        
        # Verify minimal context is handled properly
        assert isinstance(context, MemoryContext)
        assert len(context.similar_interactions) == 1
        assert context.learning_patterns.total_interactions == 2
        assert context.learning_patterns.most_common_language[0] == "python"
    
    @pytest.mark.asyncio
    async def test_empty_memory_context_generation(self):
        """Test memory context with no previous data"""
        mock_memory_store = Mock()
        
        # Mock empty responses
        mock_memory_store.find_similar_interactions.return_value = []
        mock_memory_store.get_user_learning_patterns.return_value = None
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        context = await tools.get_memory_context(
            user_id="brand_new_user", 
            current_message="I'm completely new to programming"
        )
        
        # Verify default empty context
        assert isinstance(context, MemoryContext)
        assert len(context.similar_interactions) == 0
        assert context.learning_patterns.total_interactions == 0
        assert context.learning_patterns.most_common_language == ("unknown", 0)
        assert context.learning_patterns.most_common_intent == ("general", 0)
        assert context.recent_topics == []
    
    @pytest.mark.asyncio
    async def test_memory_context_with_database_skills(self):
        """Test memory context integration with database skill tracking"""
        mock_memory_store = Mock()
        mock_db_session = Mock()
        
        # Mock memory store responses (minimal)
        mock_memory_store.find_similar_interactions.return_value = []
        mock_memory_store.get_user_learning_patterns.return_value = None
        
        tools = MentorTools(memory_store=mock_memory_store, db_session=mock_db_session)
        
        # Mock database integration
        with patch('agents.mentor_agent.tools.get_user_by_username') as mock_get_user, \
             patch('agents.mentor_agent.tools.get_user_skill_progression') as mock_get_skills:
            
            mock_user = Mock()
            mock_user.id = "user_uuid_123"
            mock_get_user.return_value = mock_user
            
            # Mock skill progression data
            mock_get_skills.return_value = [
                {
                    "skill_name": "JavaScript",
                    "mastery_level": 0.75,
                    "skill_domain": "SYNTAX",
                    "last_practiced": "2024-01-15"
                },
                {
                    "skill_name": "React",
                    "mastery_level": 0.65,
                    "skill_domain": "FRAMEWORKS", 
                    "last_practiced": "2024-01-14"
                },
                {
                    "skill_name": "API Integration",
                    "mastery_level": 0.45,
                    "skill_domain": "ARCHITECTURE",
                    "last_practiced": "2024-01-12"
                }
            ]
            
            context = await tools.get_memory_context(
                user_id="tracked_user",
                current_message="How do I improve my React skills?"
            )
            
            # Verify skill progression is included
            assert "recent_skills" in context.skill_progression
            assert "total_skills_tracked" in context.skill_progression
            assert context.skill_progression["total_skills_tracked"] == 3
            assert len(context.skill_progression["recent_skills"]) == 3
            
            # Verify database calls
            mock_get_user.assert_called_once_with(mock_db_session, "tracked_user")
            mock_get_skills.assert_called_once_with(mock_db_session, "user_uuid_123", limit=10)


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMemoryContextFormatting:
    """Test memory context formatting for use in agent prompts"""
    
    def test_format_memory_context_with_rich_data(self):
        """Test formatting memory context with comprehensive data"""
        memory_patterns = {
            "total_interactions": 25,
            "most_common_language": ("javascript", 18),
            "most_common_intent": ("debugging", 12),
            "languages_practiced": ["javascript", "python", "html", "css"]
        }
        
        similar_interactions = [
            {
                "user_message": "How do I fix this React component that won't update state properly?",
                "similarity": 0.94,
                "metadata": {"programming_language": "javascript"}
            },
            {
                "user_message": "My JavaScript async function is returning undefined instead of data",
                "similarity": 0.87, 
                "metadata": {"programming_language": "javascript"}
            },
            {
                "user_message": "Why isn't my React useEffect hook triggering when props change?",
                "similarity": 0.82,
                "metadata": {"programming_language": "javascript"}
            }
        ]
        
        formatted_context = format_memory_context(memory_patterns, similar_interactions)
        
        # Verify formatting structure
        assert "RELEVANT LEARNING HISTORY" in formatted_context
        assert "Total conversations: 25" in formatted_context
        assert "javascript" in formatted_context
        assert "debugging" in formatted_context
        
        # Verify similar interactions are included
        assert "How do I fix this React component" in formatted_context
        assert "My JavaScript async function" in formatted_context
        assert "Why isn't my React useEffect" in formatted_context
        
        # Verify interaction truncation (100 chars + ...)
        lines = formatted_context.split('\n')
        interaction_lines = [line for line in lines if line.strip().startswith('•') and "React component" in line]
        assert len(interaction_lines) > 0
        for line in interaction_lines:
            if len(line) > 100:
                assert line.endswith("...")
    
    def test_format_memory_context_with_partial_data(self):
        """Test formatting with only patterns or only interactions"""
        # Test with only patterns
        memory_patterns = {
            "total_interactions": 5,
            "most_common_language": ("python", 3),
            "most_common_intent": ("concept_explanation", 4)
        }
        
        formatted_context = format_memory_context(memory_patterns, [])
        
        assert "Total conversations: 5" in formatted_context
        assert "python" in formatted_context
        assert "concept_explanation" in formatted_context
        assert "Similar questions you've explored:" not in formatted_context
        
        # Test with only interactions
        similar_interactions = [
            {"user_message": "What is a Python list?", "metadata": {}},
            {"user_message": "How do I use loops in Python?", "metadata": {}}
        ]
        
        formatted_context = format_memory_context({}, similar_interactions)
        
        assert "What is a Python list" in formatted_context
        assert "How do I use loops" in formatted_context
    
    def test_format_memory_context_empty_data(self):
        """Test formatting with no data returns empty string"""
        # Test various empty scenarios
        assert format_memory_context(None, None) == ""
        assert format_memory_context({}, []) == ""
        assert format_memory_context(None, []) == ""
        assert format_memory_context({}, None) == ""
    
    def test_format_memory_context_template_structure(self):
        """Test that the memory context template is well-structured"""
        # Verify template contains expected sections
        assert "RELEVANT LEARNING HISTORY" in MEMORY_CONTEXT_TEMPLATE
        assert "{memory_patterns}" in MEMORY_CONTEXT_TEMPLATE
        assert "{similar_interactions}" in MEMORY_CONTEXT_TEMPLATE
        assert "Similar questions you've explored:" in MEMORY_CONTEXT_TEMPLATE
        assert "learning progression" in MEMORY_CONTEXT_TEMPLATE.lower()


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMemoryContextFiltering:
    """Test memory context filtering and prioritization"""
    
    @pytest.mark.asyncio
    async def test_similar_interactions_similarity_threshold(self):
        """Test that only interactions above similarity threshold are included"""
        mock_memory_store = Mock()
        
        # Mock interactions with varying similarity scores
        mock_memory_store.find_similar_interactions.return_value = [
            {
                "memory_id": "high_sim",
                "user_message": "Very similar question",
                "mentor_response": "Response",
                "similarity": 0.85,
                "metadata": {"programming_language": "javascript"}
            },
            {
                "memory_id": "medium_sim", 
                "user_message": "Somewhat similar question",
                "mentor_response": "Response",
                "similarity": 0.72,
                "metadata": {"programming_language": "javascript"}
            },
            {
                "memory_id": "low_sim",
                "user_message": "Not very similar question", 
                "mentor_response": "Response",
                "similarity": 0.45,
                "metadata": {"programming_language": "python"}
            }
        ]
        
        mock_memory_store.get_user_learning_patterns.return_value = None
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        context = await tools.get_memory_context(
            user_id="test_user",
            current_message="JavaScript question"
        )
        
        # All interactions should be included (filtering happens in memory store)
        assert len(context.similar_interactions) == 3
        
        # But verify they're sorted by similarity (highest first)
        similarities = [interaction.similarity for interaction in context.similar_interactions]
        assert similarities == sorted(similarities, reverse=True)
    
    @pytest.mark.asyncio
    async def test_recent_topics_extraction(self):
        """Test extraction of recent topics from similar interactions"""
        mock_memory_store = Mock()
        
        # Mock interactions with various programming languages
        mock_memory_store.find_similar_interactions.return_value = [
            {
                "memory_id": "1",
                "user_message": "JavaScript question",
                "mentor_response": "Response",
                "similarity": 0.8,
                "metadata": {"programming_language": "javascript"}
            },
            {
                "memory_id": "2",
                "user_message": "Python question", 
                "mentor_response": "Response",
                "similarity": 0.7,
                "metadata": {"programming_language": "python"}
            },
            {
                "memory_id": "3",
                "user_message": "Another JavaScript question",
                "mentor_response": "Response", 
                "similarity": 0.6,
                "metadata": {"programming_language": "javascript"}
            },
            {
                "memory_id": "4",
                "user_message": "Unknown language question",
                "mentor_response": "Response",
                "similarity": 0.5,
                "metadata": {"programming_language": "unknown"}
            }
        ]
        
        mock_memory_store.get_user_learning_patterns.return_value = None
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        context = await tools.get_memory_context(
            user_id="test_user",
            current_message="Programming question"
        )
        
        # Verify recent topics extraction and deduplication
        assert "javascript" in context.recent_topics
        assert "python" in context.recent_topics
        assert "unknown" not in context.recent_topics  # Should filter out unknown
        assert len(context.recent_topics) <= 5  # Limited to 5 topics
        
        # Should not have duplicates
        assert len(context.recent_topics) == len(set(context.recent_topics))


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")  
class TestMemoryContextErrorHandling:
    """Test error handling in memory context operations"""
    
    @pytest.mark.asyncio
    async def test_memory_store_error_handling(self):
        """Test graceful handling of memory store errors"""
        mock_memory_store = Mock()
        
        # Mock memory store methods to raise exceptions
        mock_memory_store.find_similar_interactions.side_effect = Exception("ChromaDB connection failed")
        mock_memory_store.get_user_learning_patterns.side_effect = Exception("Pattern retrieval failed")
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        # Should not raise exception despite memory store errors
        context = await tools.get_memory_context(
            user_id="test_user",
            current_message="Test question"
        )
        
        # Should return default empty context
        assert isinstance(context, MemoryContext)
        assert len(context.similar_interactions) == 0
        assert context.learning_patterns.total_interactions == 0
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test graceful handling of database errors"""
        mock_memory_store = Mock()
        mock_db_session = Mock()
        
        # Mock successful memory store operations
        mock_memory_store.find_similar_interactions.return_value = []
        mock_memory_store.get_user_learning_patterns.return_value = None
        
        tools = MentorTools(memory_store=mock_memory_store, db_session=mock_db_session)
        
        # Mock database functions to raise exceptions
        with patch('agents.mentor_agent.tools.get_user_by_username') as mock_get_user:
            mock_get_user.side_effect = Exception("Database connection failed")
            
            # Should not raise exception despite database errors
            context = await tools.get_memory_context(
                user_id="test_user",
                current_message="Test question"
            )
            
            # Should return context without skill progression data
            assert isinstance(context, MemoryContext)
            assert context.skill_progression == {}
    
    @pytest.mark.asyncio
    async def test_malformed_data_handling(self):
        """Test handling of malformed memory store data"""
        mock_memory_store = Mock()
        
        # Mock malformed similar interactions data
        mock_memory_store.find_similar_interactions.return_value = [
            {
                # Missing required fields
                "memory_id": "test_id",
                "similarity": 0.8
                # Missing user_message, mentor_response, metadata
            },
            {
                "memory_id": "test_id_2",
                "user_message": "Test question",
                "mentor_response": "Test response", 
                "similarity": "invalid_similarity",  # Should be float
                "metadata": "invalid_metadata"  # Should be dict
            }
        ]
        
        # Mock malformed learning patterns data
        mock_memory_store.get_user_learning_patterns.return_value = {
            "total_interactions": "invalid_number",  # Should be int
            "most_common_language": "invalid_tuple",  # Should be tuple
            "difficulty_distribution": "invalid_dict"  # Should be dict
        }
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        # Should handle malformed data gracefully
        context = await tools.get_memory_context(
            user_id="test_user", 
            current_message="Test question"
        )
        
        # Should return default context due to data validation errors
        assert isinstance(context, MemoryContext)
        # May have partial data depending on validation success


@pytest.mark.skipif(not PYDANTIC_AI_AVAILABLE, reason="PydanticAI not available")
class TestMemoryContextPerformance:
    """Test memory context performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self):
        """Test memory context with large datasets"""
        mock_memory_store = Mock()
        
        # Mock large number of similar interactions
        large_interactions = []
        for i in range(100):
            large_interactions.append({
                "memory_id": f"mem_{i:03d}",
                "user_message": f"Test question {i} about programming concepts and debugging",
                "mentor_response": f"Test response {i} with detailed guidance and hints",
                "similarity": 0.9 - (i * 0.001),  # Decreasing similarity
                "metadata": {
                    "programming_language": ["javascript", "python", "java"][i % 3],
                    "user_intent": ["debugging", "concept_explanation", "improvement"][i % 3],
                    "difficulty_level": ["beginner", "intermediate", "advanced"][i % 3]
                }
            })
        
        mock_memory_store.find_similar_interactions.return_value = large_interactions
        
        # Mock large learning patterns
        mock_memory_store.get_user_learning_patterns.return_value = {
            "total_interactions": 1000,
            "most_common_language": ("javascript", 400),
            "most_common_intent": ("debugging", 350),
            "difficulty_distribution": {
                "beginner": 200,
                "intermediate": 500, 
                "advanced": 300
            },
            "languages_practiced": ["javascript", "python", "java", "html", "css", "sql", "go", "rust"]
        }
        
        tools = MentorTools(memory_store=mock_memory_store)
        
        start_time = asyncio.get_event_loop().time()
        
        context = await tools.get_memory_context(
            user_id="heavy_user",
            current_message="Complex programming question requiring deep analysis"
        )
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        # Verify context is generated correctly with large dataset
        assert isinstance(context, MemoryContext)
        assert len(context.similar_interactions) == 100
        assert context.learning_patterns.total_interactions == 1000
        
        # Verify performance (should be fast despite large dataset)
        assert execution_time < 1.0, f"Memory context generation took {execution_time:.3f}s (should be <1s)"
        
        # Verify recent topics are properly limited
        assert len(context.recent_topics) <= 5


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running Memory Context Unit Tests...")
    
    if PYDANTIC_AI_AVAILABLE:
        print("✅ PydanticAI imports available")
        
        # Test basic functionality
        test_instance = TestMemoryContextGeneration()
        print("✅ Memory context generation tests setup")
        
        format_test = TestMemoryContextFormatting()
        format_test.test_format_memory_context_empty_data()
        print("✅ Memory context formatting tests passed")
        
        print("🎉 Memory context unit tests setup completed successfully!")
        print("Run with: pytest tests/test_memory_context_unit.py -v")
    else:
        print("⚠️ PydanticAI not available - tests skipped")
        print("Install PydanticAI to run full test suite: pip install pydantic-ai")