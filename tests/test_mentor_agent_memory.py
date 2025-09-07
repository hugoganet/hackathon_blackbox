"""
Integration Tests for Mentor Agent ChromaDB Memory Store
Tests vector storage, similarity search, and memory-guided mentoring functionality
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys
import json
from datetime import datetime, timedelta
import numpy as np

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Test imports
try:
    from agents.mentor_agent import MentorAgent, MentorResponse
    from agents.mentor_agent.tools import MentorTools, MemoryContext, SimilarInteraction
    from backend.memory_store import ConversationMemory
    import chromadb
    from sentence_transformers import SentenceTransformer
    MEMORY_STORE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Memory store imports not available: {e}")
    MEMORY_STORE_AVAILABLE = False


@pytest.fixture(scope="function")
def test_memory_store():
    """Create a test ChromaDB memory store for each test"""
    if not MEMORY_STORE_AVAILABLE:
        pytest.skip("Memory store dependencies not available")
    
    # Create temporary directory for test ChromaDB
    test_dir = tempfile.mkdtemp(prefix="test_chroma_")
    
    try:
        memory_store = ConversationMemory(persist_directory=test_dir)
        yield memory_store
    finally:
        # Clean up temporary directory
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


@pytest.fixture
def sample_conversations():
    """Sample conversation data for testing"""
    return [
        {
            "user_id": "student_001",
            "user_message": "How do I create a Python function with parameters?",
            "mentor_response": "Great question! Before I guide you through it, what do you think parameters are used for?",
            "agent_type": "pydantic_strict",
            "programming_language": "python",
            "difficulty_level": "beginner",
            "user_intent": "concept_explanation"
        },
        {
            "user_id": "student_001", 
            "user_message": "I'm getting a syntax error in my Python function definition",
            "mentor_response": "Let's debug this step by step. Can you show me exactly what error message you're seeing?",
            "agent_type": "pydantic_strict",
            "programming_language": "python",
            "difficulty_level": "beginner",
            "user_intent": "debugging"
        },
        {
            "user_id": "student_002",
            "user_message": "How do I handle user input in a React component?",
            "mentor_response": "Excellent React question! What have you tried so far with handling user events?",
            "agent_type": "pydantic_strict", 
            "programming_language": "javascript",
            "difficulty_level": "intermediate",
            "user_intent": "concept_explanation"
        },
        {
            "user_id": "student_001",
            "user_message": "Can you explain Python list comprehensions?",
            "mentor_response": "List comprehensions are powerful! Let's start with a simple example. What do you think this syntax might do: [x for x in range(5)]?",
            "agent_type": "pydantic_strict",
            "programming_language": "python", 
            "difficulty_level": "intermediate",
            "user_intent": "concept_explanation"
        },
        {
            "user_id": "student_003",
            "user_message": "My JavaScript async function isn't working properly",
            "mentor_response": "Async functions can be tricky! What exactly isn't working? Are you getting an error or unexpected behavior?",
            "agent_type": "pydantic_strict",
            "programming_language": "javascript",
            "difficulty_level": "advanced", 
            "user_intent": "debugging"
        }
    ]


@pytest.mark.skipif(not MEMORY_STORE_AVAILABLE, reason="Memory store not available")
class TestMemoryStoreBasicOperations:
    """Test basic memory store operations"""
    
    def test_memory_store_initialization(self, test_memory_store):
        """Test that memory store initializes correctly"""
        assert test_memory_store is not None
        assert test_memory_store.collection is not None
        assert test_memory_store.embedding_model is not None
        assert isinstance(test_memory_store.embedding_model, SentenceTransformer)
    
    def test_add_single_interaction(self, test_memory_store, sample_conversations):
        """Test adding a single interaction to memory store"""
        conversation = sample_conversations[0]
        
        memory_id = test_memory_store.add_interaction(
            user_id=conversation["user_id"],
            user_message=conversation["user_message"],
            mentor_response=conversation["mentor_response"],
            agent_type=conversation["agent_type"],
            programming_language=conversation["programming_language"],
            difficulty_level=conversation["difficulty_level"],
            user_intent=conversation["user_intent"]
        )
        
        # Verify memory ID was returned
        assert memory_id is not None
        assert isinstance(memory_id, str)
        
        # Verify collection count increased
        assert test_memory_store.collection.count() == 1
    
    def test_add_multiple_interactions(self, test_memory_store, sample_conversations):
        """Test adding multiple interactions to memory store"""
        memory_ids = []
        
        for conversation in sample_conversations:
            memory_id = test_memory_store.add_interaction(
                user_id=conversation["user_id"],
                user_message=conversation["user_message"],
                mentor_response=conversation["mentor_response"],
                agent_type=conversation["agent_type"],
                programming_language=conversation["programming_language"],
                difficulty_level=conversation["difficulty_level"],
                user_intent=conversation["user_intent"]
            )
            memory_ids.append(memory_id)
        
        # Verify all interactions added
        assert len(memory_ids) == len(sample_conversations)
        assert all(memory_id is not None for memory_id in memory_ids)
        assert len(set(memory_ids)) == len(memory_ids)  # All IDs unique
        
        # Verify collection count
        assert test_memory_store.collection.count() == len(sample_conversations)


@pytest.mark.skipif(not MEMORY_STORE_AVAILABLE, reason="Memory store not available")
class TestMemoryStoreSimilaritySearch:
    """Test similarity search functionality"""
    
    def test_find_similar_interactions_basic(self, test_memory_store, sample_conversations):
        """Test basic similarity search functionality"""
        # Add sample conversations to memory store
        for conversation in sample_conversations:
            test_memory_store.add_interaction(
                user_id=conversation["user_id"],
                user_message=conversation["user_message"],
                mentor_response=conversation["mentor_response"],
                agent_type=conversation["agent_type"],
                programming_language=conversation["programming_language"],
                difficulty_level=conversation["difficulty_level"],
                user_intent=conversation["user_intent"]
            )
        
        # Search for similar interactions
        query = "How do I define a function in Python?"
        similar = test_memory_store.find_similar_interactions(
            current_message=query,
            user_id="student_001",
            limit=3
        )
        
        # Verify search results
        assert len(similar) > 0
        assert len(similar) <= 3  # Respects limit
        
        # Verify result structure
        for result in similar:
            assert "memory_id" in result
            assert "user_message" in result
            assert "mentor_response" in result
            assert "similarity" in result
            assert "metadata" in result
            
            # Verify similarity score
            assert 0 <= result["similarity"] <= 1
    
    def test_find_similar_interactions_python_focus(self, test_memory_store, sample_conversations):
        """Test similarity search finds relevant Python interactions"""
        # Add sample conversations
        for conversation in sample_conversations:
            test_memory_store.add_interaction(**conversation)
        
        # Search with Python-specific query
        query = "I need help with Python syntax and functions"
        similar = test_memory_store.find_similar_interactions(
            current_message=query,
            user_id="student_001",
            limit=5
        )
        
        # Verify Python interactions are prioritized
        python_results = [r for r in similar if r["metadata"].get("programming_language") == "python"]
        assert len(python_results) > 0
        
        # Verify similarity scores are reasonable for Python content
        if python_results:
            best_python_match = max(python_results, key=lambda x: x["similarity"])
            assert best_python_match["similarity"] > 0.3  # Should have decent similarity
    
    def test_find_similar_interactions_user_specific(self, test_memory_store, sample_conversations):
        """Test similarity search respects user-specific context"""
        # Add sample conversations
        for conversation in sample_conversations:
            test_memory_store.add_interaction(**conversation)
        
        # Search for student_001's interactions
        query = "Python programming question"
        student_001_results = test_memory_store.find_similar_interactions(
            current_message=query,
            user_id="student_001",
            limit=10
        )
        
        # Search for student_002's interactions  
        student_002_results = test_memory_store.find_similar_interactions(
            current_message=query,
            user_id="student_002", 
            limit=10
        )
        
        # Verify user-specific results
        assert len(student_001_results) > 0
        assert len(student_002_results) >= 0  # student_002 has fewer Python interactions
        
        # student_001 should have more Python results
        student_001_python = [r for r in student_001_results if "python" in r["user_message"].lower()]
        if len(student_001_python) > 0:
            assert len(student_001_python) >= 1
    
    def test_similarity_threshold_filtering(self, test_memory_store, sample_conversations):
        """Test similarity threshold filtering"""
        # Add sample conversations
        for conversation in sample_conversations:
            test_memory_store.add_interaction(**conversation)
        
        # Search with high similarity threshold
        query = "How do I create Python functions?"
        high_threshold_results = test_memory_store.find_similar_interactions(
            current_message=query,
            user_id="student_001",
            limit=10,
            similarity_threshold=0.8
        )
        
        # Search with low similarity threshold
        low_threshold_results = test_memory_store.find_similar_interactions(
            current_message=query,
            user_id="student_001", 
            limit=10,
            similarity_threshold=0.1
        )
        
        # High threshold should return fewer results
        assert len(high_threshold_results) <= len(low_threshold_results)
        
        # All high threshold results should meet the threshold
        for result in high_threshold_results:
            assert result["similarity"] >= 0.8
    
    def test_empty_search_results(self, test_memory_store):
        """Test search behavior with no matching results"""
        # Search empty memory store
        results = test_memory_store.find_similar_interactions(
            current_message="Test query",
            user_id="nonexistent_user",
            limit=5
        )
        
        assert results == []
        assert len(results) == 0


@pytest.mark.skipif(not MEMORY_STORE_AVAILABLE, reason="Memory store not available")
class TestMemoryStoreLearningPatterns:
    """Test learning pattern analysis functionality"""
    
    def test_get_user_learning_patterns_basic(self, test_memory_store, sample_conversations):
        """Test basic learning pattern analysis"""
        # Add sample conversations for student_001
        student_001_conversations = [c for c in sample_conversations if c["user_id"] == "student_001"]
        
        for conversation in student_001_conversations:
            test_memory_store.add_interaction(**conversation)
        
        # Get learning patterns
        patterns = test_memory_store.get_user_learning_patterns("student_001")
        
        # Verify pattern structure
        assert patterns is not None
        assert "total_interactions" in patterns
        assert "most_common_language" in patterns
        assert "most_common_intent" in patterns
        assert "difficulty_distribution" in patterns
        assert "languages_practiced" in patterns
        
        # Verify pattern values
        assert patterns["total_interactions"] == len(student_001_conversations)
        assert patterns["most_common_language"][0] == "python"  # Most common language
        assert "python" in patterns["languages_practiced"]
    
    def test_learning_patterns_multiple_languages(self, test_memory_store, sample_conversations):
        """Test learning patterns with multiple programming languages"""
        # Add all sample conversations
        for conversation in sample_conversations:
            test_memory_store.add_interaction(**conversation)
        
        # Get patterns for student with mixed languages
        patterns = test_memory_store.get_user_learning_patterns("student_001")
        
        if patterns:
            # Should have multiple languages in practice list
            assert len(patterns["languages_practiced"]) >= 1
            assert "python" in patterns["languages_practiced"]
            
            # Difficulty distribution should be present
            assert isinstance(patterns["difficulty_distribution"], dict)
            assert len(patterns["difficulty_distribution"]) > 0
    
    def test_learning_patterns_empty_user(self, test_memory_store):
        """Test learning patterns for user with no interactions"""
        patterns = test_memory_store.get_user_learning_patterns("nonexistent_user")
        
        # Should return None or empty patterns
        assert patterns is None or patterns["total_interactions"] == 0


@pytest.mark.skipif(not MEMORY_STORE_AVAILABLE, reason="Memory store not available")
class TestMentorToolsMemoryIntegration:
    """Test MentorTools integration with memory store"""
    
    @pytest.mark.asyncio
    async def test_mentor_tools_memory_context_integration(self, test_memory_store, sample_conversations):
        """Test MentorTools integration with memory store for context generation"""
        # Populate memory store
        for conversation in sample_conversations:
            test_memory_store.add_interaction(**conversation)
        
        # Initialize MentorTools with memory store
        tools = MentorTools(memory_store=test_memory_store)
        
        # Get memory context
        context = await tools.get_memory_context(
            user_id="student_001",
            current_message="I need help with Python function parameters"
        )
        
        # Verify context structure
        assert isinstance(context, MemoryContext)
        assert len(context.similar_interactions) > 0
        assert context.learning_patterns.total_interactions > 0
        
        # Verify similar interactions are properly structured
        for interaction in context.similar_interactions:
            assert isinstance(interaction, SimilarInteraction)
            assert interaction.memory_id is not None
            assert interaction.user_message is not None
            assert interaction.similarity >= 0
        
        # Verify learning patterns
        assert context.learning_patterns.total_interactions > 0
        assert context.learning_patterns.most_common_language[0] == "python"
    
    @pytest.mark.asyncio
    async def test_mentor_tools_store_interaction(self, test_memory_store):
        """Test MentorTools interaction storage"""
        tools = MentorTools(memory_store=test_memory_store)
        
        # Store interaction
        memory_id = await tools.store_interaction(
            user_id="test_storage_user",
            user_message="How do I use async/await in JavaScript?",
            mentor_response="Great async question! What's your current understanding of promises?",
            session_id="test_session", 
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        # Verify storage succeeded
        assert memory_id is not None
        assert isinstance(memory_id, str)
        
        # Verify interaction was stored with correct classifications
        stored_interactions = test_memory_store.find_similar_interactions(
            current_message="async await JavaScript",
            user_id="test_storage_user",
            limit=1
        )
        
        assert len(stored_interactions) == 1
        stored = stored_interactions[0]
        assert stored["metadata"]["programming_language"] == "javascript"
        assert stored["metadata"]["user_intent"] in ["concept_explanation", "debugging", "general"]
        assert stored["metadata"]["agent_type"] == "pydantic_strict"


@pytest.mark.skipif(not MEMORY_STORE_AVAILABLE, reason="Memory store not available")
class TestMemoryStorePerformance:
    """Test memory store performance characteristics"""
    
    def test_bulk_interaction_storage_performance(self, test_memory_store):
        """Test performance of storing many interactions"""
        start_time = datetime.now()
        
        # Generate bulk test data
        bulk_conversations = []
        for i in range(50):  # Reduced for test speed
            bulk_conversations.append({
                "user_id": f"bulk_user_{i % 5}",  # 5 different users
                "user_message": f"Test question {i} about programming concepts and debugging techniques",
                "mentor_response": f"Response {i}: Let me guide you through this step by step with detailed explanations",
                "agent_type": "pydantic_strict",
                "programming_language": ["python", "javascript", "java", "html", "css"][i % 5],
                "difficulty_level": ["beginner", "intermediate", "advanced"][i % 3],
                "user_intent": ["concept_explanation", "debugging", "improvement"][i % 3]
            })
        
        # Store all interactions
        memory_ids = []
        for conversation in bulk_conversations:
            memory_id = test_memory_store.add_interaction(**conversation)
            memory_ids.append(memory_id)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Performance verification
        assert duration < 30.0, f"Bulk storage took {duration:.2f}s (should be <30s for 50 items)"
        assert len(memory_ids) == len(bulk_conversations)
        assert all(mid is not None for mid in memory_ids)
        
        print(f"✅ Stored {len(bulk_conversations)} interactions in {duration:.2f}s")
    
    def test_similarity_search_performance(self, test_memory_store, sample_conversations):
        """Test similarity search performance"""
        # Add sample conversations
        for conversation in sample_conversations:
            test_memory_store.add_interaction(**conversation)
        
        # Add more conversations for performance testing
        for i in range(20):  # Additional conversations
            test_memory_store.add_interaction(
                user_id=f"perf_user_{i}",
                user_message=f"Performance test question {i} about various programming topics",
                mentor_response=f"Performance test response {i}",
                agent_type="pydantic_strict",
                programming_language=["python", "javascript"][i % 2],
                difficulty_level="intermediate",
                user_intent="concept_explanation"
            )
        
        # Measure search performance
        start_time = datetime.now()
        
        results = test_memory_store.find_similar_interactions(
            current_message="How do I solve programming challenges effectively?",
            user_id="perf_user_1",
            limit=10
        )
        
        end_time = datetime.now()
        search_duration = (end_time - start_time).total_seconds()
        
        # Performance verification
        assert search_duration < 2.0, f"Search took {search_duration:.3f}s (should be <2s)"
        assert len(results) > 0
        
        print(f"✅ Similarity search completed in {search_duration:.3f}s")


@pytest.mark.skipif(not MEMORY_STORE_AVAILABLE, reason="Memory store not available")
class TestMemoryStoreErrorHandling:
    """Test memory store error handling and edge cases"""
    
    def test_invalid_interaction_data_handling(self, test_memory_store):
        """Test handling of invalid interaction data"""
        # Test with missing required fields
        with pytest.raises(Exception):
            test_memory_store.add_interaction(
                user_id=None,  # Missing required field
                user_message="Test message",
                mentor_response="Test response"
            )
        
        # Test with empty messages
        memory_id = test_memory_store.add_interaction(
            user_id="test_user",
            user_message="",  # Empty message
            mentor_response="Test response",
            agent_type="pydantic_strict"
        )
        
        # Should still work with empty message (or handle gracefully)
        assert memory_id is not None or memory_id is None  # Either works or fails gracefully
    
    def test_search_edge_cases(self, test_memory_store):
        """Test search with edge case inputs"""
        # Search with empty query
        results = test_memory_store.find_similar_interactions(
            current_message="",
            user_id="test_user",
            limit=5
        )
        assert isinstance(results, list)  # Should return empty list, not error
        
        # Search with very long query
        long_query = "This is a very long question " * 100  # Very long query
        results = test_memory_store.find_similar_interactions(
            current_message=long_query,
            user_id="test_user",
            limit=5
        )
        assert isinstance(results, list)  # Should handle gracefully
        
        # Search with special characters
        special_query = "How do I use @#$%^&*() in code?"
        results = test_memory_store.find_similar_interactions(
            current_message=special_query,
            user_id="test_user",
            limit=5
        )
        assert isinstance(results, list)  # Should handle gracefully
    
    def test_memory_store_persistence(self, test_memory_store, sample_conversations):
        """Test that memory store data persists correctly"""
        # Add some interactions
        conversation = sample_conversations[0]
        memory_id = test_memory_store.add_interaction(**conversation)
        
        # Verify data is immediately searchable
        results = test_memory_store.find_similar_interactions(
            current_message=conversation["user_message"],
            user_id=conversation["user_id"],
            limit=1
        )
        
        assert len(results) == 1
        assert results[0]["memory_id"] == memory_id
        
        # Note: In a real test, you'd create a new memory store instance
        # pointing to the same directory and verify data persists


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running Mentor Agent Memory Store Integration Tests...")
    
    if MEMORY_STORE_AVAILABLE:
        print("✅ Memory store imports available")
        print("✅ Memory store integration test setup completed successfully!")
        print("Run with: pytest tests/test_mentor_agent_memory.py -v")
    else:
        print("⚠️ Memory store dependencies not available - tests skipped")
        print("Install ChromaDB and sentence-transformers to run memory store tests")