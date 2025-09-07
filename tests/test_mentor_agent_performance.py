"""
Performance Tests for Mentor Agent Load Testing
Tests system performance under load including response times, concurrent users, and scalability
"""

import pytest
import asyncio
import time
import statistics
import concurrent.futures
import threading
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys
from datetime import datetime
import json
import os
import tempfile
import shutil
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Test imports
try:
    from backend.api import app, get_db
    from backend.database import Base, User, Session as DBSession, create_user
    from backend.memory_store import ConversationMemory
    from agents.mentor_agent import MentorAgent, MentorResponse
    from agents.mentor_agent.tools import MentorTools
    PERFORMANCE_TEST_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Performance test imports not available: {e}")
    PERFORMANCE_TEST_AVAILABLE = False


# Performance test configuration
PERFORMANCE_THRESHOLDS = {
    "single_response_time": 2.0,  # seconds
    "concurrent_response_time": 5.0,  # seconds under load
    "memory_search_time": 0.1,  # seconds for similarity search
    "database_operation_time": 0.05,  # seconds for basic DB ops
    "bulk_processing_time": 30.0,  # seconds for 100 operations
}

TEST_DATABASE_URL = "sqlite:///test_performance_mentor_agent.db"


@pytest.fixture(scope="function")
def perf_test_db():
    """Create test database optimized for performance testing"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        try:
            os.remove("test_performance_mentor_agent.db")
        except FileNotFoundError:
            pass


@pytest.fixture(scope="function")
def perf_memory_store():
    """Create test memory store for performance testing"""
    test_dir = tempfile.mkdtemp(prefix="test_perf_chroma_")
    
    try:
        if PERFORMANCE_TEST_AVAILABLE:
            memory_store = ConversationMemory(persist_directory=test_dir)
            yield memory_store
        else:
            yield None
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


@pytest.fixture
def performance_client(perf_test_db):
    """Create test client for performance testing"""
    if not PERFORMANCE_TEST_AVAILABLE:
        pytest.skip("Performance test dependencies not available")
    
    def override_get_db():
        try:
            yield perf_test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


def time_operation(operation, *args, **kwargs):
    """Utility to time operations and return (result, duration)"""
    start_time = time.time()
    result = operation(*args, **kwargs)
    duration = time.time() - start_time
    return result, duration


async def time_async_operation(operation, *args, **kwargs):
    """Utility to time async operations and return (result, duration)"""
    start_time = time.time()
    result = await operation(*args, **kwargs)
    duration = time.time() - start_time
    return result, duration


@pytest.mark.skipif(not PERFORMANCE_TEST_AVAILABLE, reason="Performance test dependencies not available")
class TestSingleRequestPerformance:
    """Test performance of individual operations"""
    
    @patch('backend.api.pydantic_mentor')
    def test_single_chat_request_performance(self, mock_pydantic_mentor, performance_client):
        """Test single chat request response time"""
        
        # Mock fast mentor response
        mock_response = MentorResponse(
            response="Great question! What's your current understanding of this concept?",
            hint_level=1,
            memory_context_used=False,
            detected_language="python",
            detected_intent="concept_explanation",
            similar_interactions_count=0
        )
        mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
        
        chat_request = {
            "message": "How do I create a Python function?",
            "agent_type": "pydantic_strict",
            "user_id": "perf_test_user"
        }
        
        # Time the request
        response, duration = time_operation(
            performance_client.post, "/chat", json=chat_request
        )
        
        # Verify response succeeded
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        
        # Verify performance threshold
        assert duration < PERFORMANCE_THRESHOLDS["single_response_time"], \
            f"Single request took {duration:.3f}s (threshold: {PERFORMANCE_THRESHOLDS['single_response_time']}s)"
        
        print(f"✅ Single chat request: {duration:.3f}s")
    
    @pytest.mark.asyncio
    async def test_mentor_agent_response_performance(self):
        """Test direct MentorAgent response performance"""
        
        mock_model = Mock()
        
        with patch('agents.mentor_agent.agent.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Mock fast PydanticAI response
            mock_result = Mock()
            mock_result.data = MentorResponse(
                response="Excellent question! What have you tried so far?",
                hint_level=1
            )
            mock_agent.run = AsyncMock(return_value=mock_result)
            
            mentor = MentorAgent(model=mock_model)
            
            # Time the mentor response
            response, duration = await time_async_operation(
                mentor.respond,
                user_message="Test performance question",
                user_id="perf_user"
            )
            
            # Verify response
            assert isinstance(response, MentorResponse)
            assert len(response.response) > 0
            
            # Verify performance
            assert duration < PERFORMANCE_THRESHOLDS["single_response_time"], \
                f"Mentor response took {duration:.3f}s"
            
            print(f"✅ Direct mentor response: {duration:.3f}s")
    
    @pytest.mark.asyncio  
    async def test_memory_search_performance(self, perf_memory_store):
        """Test memory store similarity search performance"""
        
        # Add sample interactions for performance testing
        sample_conversations = [
            {
                "user_id": f"perf_user_{i}",
                "user_message": f"Performance test question {i} about Python programming and software development",
                "mentor_response": f"Performance test response {i} with detailed guidance",
                "agent_type": "pydantic_strict",
                "programming_language": ["python", "javascript"][i % 2],
                "difficulty_level": ["beginner", "intermediate", "advanced"][i % 3],
                "user_intent": ["concept_explanation", "debugging"][i % 2]
            }
            for i in range(50)  # Moderate dataset for performance testing
        ]
        
        # Add all interactions
        for conversation in sample_conversations:
            perf_memory_store.add_interaction(**conversation)
        
        # Test similarity search performance
        query = "How do I solve programming challenges with Python functions and data structures?"
        
        search_result, duration = time_operation(
            perf_memory_store.find_similar_interactions,
            current_message=query,
            user_id="perf_user_1", 
            limit=5
        )
        
        # Verify search results
        assert isinstance(search_result, list)
        assert len(search_result) <= 5
        
        # Verify performance threshold
        assert duration < PERFORMANCE_THRESHOLDS["memory_search_time"], \
            f"Memory search took {duration:.3f}s (threshold: {PERFORMANCE_THRESHOLDS['memory_search_time']}s)"
        
        print(f"✅ Memory similarity search: {duration:.3f}s")
    
    @pytest.mark.asyncio
    async def test_mentor_tools_performance(self, perf_memory_store):
        """Test MentorTools operations performance"""
        
        tools = MentorTools(memory_store=perf_memory_store)
        
        # Test intent classification performance
        classify_result, classify_duration = await time_async_operation(
            tools.classify_user_intent,
            "My JavaScript async function is not working properly and I need debugging help"
        )
        
        assert classify_result in ["debugging", "concept_explanation", "improvement", "general"]
        assert classify_duration < 0.01, f"Intent classification took {classify_duration:.3f}s"
        
        # Test language detection performance
        detect_result, detect_duration = await time_async_operation(
            tools.detect_programming_language,
            "I'm having trouble with React components and useState hooks in my JavaScript application"
        )
        
        assert detect_result == "javascript"
        assert detect_duration < 0.01, f"Language detection took {detect_duration:.3f}s"
        
        # Test difficulty analysis performance
        difficulty_result, difficulty_duration = await time_async_operation(
            tools.analyze_difficulty_level,
            "How do I optimize algorithm performance for large datasets using advanced data structures?"
        )
        
        assert difficulty_result in ["beginner", "intermediate", "advanced"]
        assert difficulty_duration < 0.01, f"Difficulty analysis took {difficulty_duration:.3f}s"
        
        print(f"✅ MentorTools operations: classify={classify_duration:.4f}s, detect={detect_duration:.4f}s, difficulty={difficulty_duration:.4f}s")


@pytest.mark.skipif(not PERFORMANCE_TEST_AVAILABLE, reason="Performance test dependencies not available")
class TestConcurrentUserPerformance:
    """Test performance under concurrent load"""
    
    @patch('backend.api.pydantic_mentor')
    def test_concurrent_chat_requests(self, mock_pydantic_mentor, performance_client):
        """Test performance with concurrent users"""
        
        # Mock mentor response with slight delay to simulate realistic processing
        async def mock_respond(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return MentorResponse(
                response="Great question! Let me guide you through this step by step.",
                hint_level=1,
                memory_context_used=False,
                detected_language="python",
                detected_intent="concept_explanation"
            )
        
        mock_pydantic_mentor.respond = mock_respond
        
        # Create concurrent requests
        num_concurrent_requests = 10
        concurrent_requests = [
            {
                "message": f"Concurrent test question {i} about programming concepts",
                "agent_type": "pydantic_strict",
                "user_id": f"concurrent_user_{i}",
                "session_id": f"concurrent_session_{i}"
            }
            for i in range(num_concurrent_requests)
        ]
        
        def make_request(request_data):
            start_time = time.time()
            response = performance_client.post("/chat", json=request_data)
            duration = time.time() - start_time
            return response, duration
        
        # Execute concurrent requests
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
            future_to_request = {
                executor.submit(make_request, request): request 
                for request in concurrent_requests
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_request):
                response, duration = future.result()
                results.append((response, duration))
        
        total_time = time.time() - start_time
        
        # Verify all requests succeeded
        assert len(results) == num_concurrent_requests
        for response, duration in results:
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert len(data["response"]) > 0
        
        # Calculate performance metrics
        response_times = [duration for _, duration in results]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # Verify performance thresholds
        assert avg_response_time < PERFORMANCE_THRESHOLDS["concurrent_response_time"], \
            f"Average response time {avg_response_time:.3f}s exceeds threshold"
        
        assert max_response_time < PERFORMANCE_THRESHOLDS["concurrent_response_time"] * 1.5, \
            f"Max response time {max_response_time:.3f}s too high"
        
        print(f"✅ Concurrent requests ({num_concurrent_requests} users):")
        print(f"   Total time: {total_time:.3f}s")
        print(f"   Avg response: {avg_response_time:.3f}s")
        print(f"   Min/Max: {min_response_time:.3f}s / {max_response_time:.3f}s")
    
    def test_memory_store_concurrent_access(self, perf_memory_store):
        """Test memory store performance under concurrent access"""
        
        # Add base data
        for i in range(20):
            perf_memory_store.add_interaction(
                user_id=f"concurrent_user_{i % 5}",
                user_message=f"Concurrent test question {i}",
                mentor_response=f"Concurrent test response {i}",
                agent_type="pydantic_strict",
                programming_language="python",
                difficulty_level="intermediate",
                user_intent="concept_explanation"
            )
        
        # Define concurrent operations
        def search_operation(query_id):
            start_time = time.time()
            results = perf_memory_store.find_similar_interactions(
                current_message=f"Concurrent query {query_id}",
                user_id=f"concurrent_user_{query_id % 5}",
                limit=3
            )
            duration = time.time() - start_time
            return len(results), duration
        
        def add_operation(interaction_id):
            start_time = time.time()
            memory_id = perf_memory_store.add_interaction(
                user_id=f"concurrent_new_user_{interaction_id}",
                user_message=f"New concurrent question {interaction_id}",
                mentor_response=f"New concurrent response {interaction_id}",
                agent_type="pydantic_strict",
                programming_language="javascript",
                difficulty_level="beginner", 
                user_intent="debugging"
            )
            duration = time.time() - start_time
            return memory_id is not None, duration
        
        # Execute concurrent operations
        num_operations = 15
        operations = []
        
        # Mix search and add operations
        for i in range(num_operations):
            if i % 3 == 0:
                operations.append(("add", add_operation, i))
            else:
                operations.append(("search", search_operation, i))
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_op = {
                executor.submit(op_func, op_id): (op_type, op_id)
                for op_type, op_func, op_id in operations
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_op):
                op_type, op_id = future_to_op[future]
                success, duration = future.result()
                results.append((op_type, success, duration))
        
        total_time = time.time() - start_time
        
        # Verify all operations succeeded
        assert len(results) == num_operations
        for op_type, success, duration in results:
            assert success, f"Operation {op_type} failed"
            assert duration < 1.0, f"Operation {op_type} took {duration:.3f}s (too slow)"
        
        # Calculate metrics by operation type
        search_times = [duration for op_type, _, duration in results if op_type == "search"]
        add_times = [duration for op_type, _, duration in results if op_type == "add"]
        
        if search_times:
            avg_search_time = statistics.mean(search_times)
            print(f"✅ Concurrent memory operations:")
            print(f"   Total time: {total_time:.3f}s")
            print(f"   Avg search: {avg_search_time:.3f}s")
        
        if add_times:
            avg_add_time = statistics.mean(add_times)
            print(f"   Avg add: {avg_add_time:.3f}s")


@pytest.mark.skipif(not PERFORMANCE_TEST_AVAILABLE, reason="Performance test dependencies not available")
class TestScalabilityPerformance:
    """Test system scalability with large datasets and operations"""
    
    def test_large_memory_dataset_performance(self, perf_memory_store):
        """Test performance with large memory dataset"""
        
        # Add large dataset
        large_dataset_size = 100
        print(f"Adding {large_dataset_size} interactions to memory store...")
        
        start_time = time.time()
        
        for i in range(large_dataset_size):
            perf_memory_store.add_interaction(
                user_id=f"scale_user_{i % 10}",  # 10 different users
                user_message=f"Scalability test question {i} about programming, algorithms, data structures, and software development best practices",
                mentor_response=f"Scalability test response {i} with comprehensive guidance and educational content for learning programming concepts",
                agent_type="pydantic_strict",
                programming_language=["python", "javascript", "java", "html", "css"][i % 5],
                difficulty_level=["beginner", "intermediate", "advanced"][i % 3],
                user_intent=["concept_explanation", "debugging", "improvement"][i % 3]
            )
        
        bulk_add_time = time.time() - start_time
        
        # Verify bulk add performance
        assert bulk_add_time < PERFORMANCE_THRESHOLDS["bulk_processing_time"], \
            f"Bulk add took {bulk_add_time:.3f}s (threshold: {PERFORMANCE_THRESHOLDS['bulk_processing_time']}s)"
        
        print(f"✅ Added {large_dataset_size} interactions in {bulk_add_time:.3f}s")
        
        # Test search performance with large dataset
        search_queries = [
            "How do I optimize Python algorithms for better performance?",
            "My JavaScript application has memory leaks and performance issues",
            "What are the best practices for data structure selection?", 
            "I need help debugging complex software architecture problems",
            "Can you explain advanced programming concepts and design patterns?"
        ]
        
        search_times = []
        for query in search_queries:
            start_time = time.time()
            results = perf_memory_store.find_similar_interactions(
                current_message=query,
                user_id="scale_user_1",
                limit=10
            )
            search_time = time.time() - start_time
            search_times.append(search_time)
            
            # Verify search quality
            assert len(results) <= 10
            assert all(result["similarity"] >= 0 for result in results)
        
        avg_search_time = statistics.mean(search_times)
        max_search_time = max(search_times)
        
        # Verify search performance scales well
        assert avg_search_time < PERFORMANCE_THRESHOLDS["memory_search_time"] * 2, \
            f"Large dataset search avg {avg_search_time:.3f}s too slow"
        
        assert max_search_time < PERFORMANCE_THRESHOLDS["memory_search_time"] * 3, \
            f"Large dataset search max {max_search_time:.3f}s too slow"
        
        print(f"✅ Search performance with {large_dataset_size} interactions:")
        print(f"   Avg search: {avg_search_time:.3f}s")
        print(f"   Max search: {max_search_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_mentor_tools_scaling_performance(self, perf_memory_store):
        """Test MentorTools performance with large context"""
        
        # Add comprehensive user history
        user_id = "scaling_test_user"
        
        # Add 50 historical interactions
        for i in range(50):
            perf_memory_store.add_interaction(
                user_id=user_id,
                user_message=f"Historical question {i} covering various programming topics and learning scenarios",
                mentor_response=f"Historical response {i} with detailed guidance and educational support",
                agent_type="pydantic_strict",
                programming_language=["python", "javascript", "java"][i % 3],
                difficulty_level=["beginner", "intermediate", "advanced"][i % 3],
                user_intent=["concept_explanation", "debugging", "improvement"][i % 3]
            )
        
        tools = MentorTools(memory_store=perf_memory_store)
        
        # Test memory context retrieval with large history
        start_time = time.time()
        
        context = await tools.get_memory_context(
            user_id=user_id,
            current_message="I need comprehensive help with advanced programming concepts and software architecture"
        )
        
        context_retrieval_time = time.time() - start_time
        
        # Verify context quality
        assert len(context.similar_interactions) > 0
        assert context.learning_patterns.total_interactions > 0
        assert len(context.recent_topics) > 0
        
        # Verify performance with large context
        assert context_retrieval_time < 1.0, \
            f"Context retrieval with large history took {context_retrieval_time:.3f}s"
        
        print(f"✅ Memory context with large history: {context_retrieval_time:.3f}s")
        
        # Test storing interaction with rich context
        start_time = time.time()
        
        memory_id = await tools.store_interaction(
            user_id=user_id,
            user_message="Complex new question about advanced programming topics",
            mentor_response="Comprehensive mentor response with detailed guidance",
            session_id="scaling_test_session",
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        store_time = time.time() - start_time
        
        # Verify storage succeeded and performance
        assert memory_id is not None
        assert store_time < 0.5, f"Interaction storage took {store_time:.3f}s"
        
        print(f"✅ Interaction storage with context: {store_time:.3f}s")


@pytest.mark.skipif(not PERFORMANCE_TEST_AVAILABLE, reason="Performance test dependencies not available")
class TestPerformanceRegression:
    """Test for performance regression detection"""
    
    def test_baseline_performance_metrics(self, performance_client, perf_memory_store):
        """Establish baseline performance metrics for regression testing"""
        
        # This test documents expected performance characteristics
        # and can be used to detect regressions in future changes
        
        performance_results = {}
        
        # Test 1: Simple chat request
        with patch('backend.api.pydantic_mentor') as mock_mentor:
            mock_mentor.respond = AsyncMock(return_value=MentorResponse(
                response="Test response for baseline measurement",
                hint_level=1
            ))
            
            chat_request = {
                "message": "Baseline performance test question",
                "agent_type": "pydantic_strict",
                "user_id": "baseline_user"
            }
            
            response, duration = time_operation(
                performance_client.post, "/chat", json=chat_request
            )
            
            performance_results["simple_chat_request"] = {
                "duration": duration,
                "success": response.status_code == 200
            }
        
        # Test 2: Memory search with moderate dataset
        # Add 30 interactions
        for i in range(30):
            perf_memory_store.add_interaction(
                user_id=f"baseline_user_{i % 3}",
                user_message=f"Baseline test question {i}",
                mentor_response=f"Baseline test response {i}",
                agent_type="pydantic_strict",
                programming_language="python",
                difficulty_level="intermediate",
                user_intent="concept_explanation"
            )
        
        # Search performance
        search_result, search_duration = time_operation(
            perf_memory_store.find_similar_interactions,
            current_message="Baseline search query for performance testing",
            user_id="baseline_user_1",
            limit=5
        )
        
        performance_results["memory_search"] = {
            "duration": search_duration,
            "results_count": len(search_result),
            "success": len(search_result) > 0
        }
        
        # Test 3: Learning patterns analysis
        patterns_result, patterns_duration = time_operation(
            perf_memory_store.get_user_learning_patterns,
            "baseline_user_1"
        )
        
        performance_results["learning_patterns"] = {
            "duration": patterns_duration,
            "success": patterns_result is not None
        }
        
        # Log baseline metrics for future comparison
        print("\n📊 BASELINE PERFORMANCE METRICS:")
        for test_name, metrics in performance_results.items():
            print(f"   {test_name}: {metrics['duration']:.4f}s (success: {metrics['success']})")
        
        # Assert all operations succeeded
        for test_name, metrics in performance_results.items():
            assert metrics["success"], f"Baseline test {test_name} failed"
        
        # Assert reasonable baseline performance
        assert performance_results["simple_chat_request"]["duration"] < 1.0
        assert performance_results["memory_search"]["duration"] < 0.2
        assert performance_results["learning_patterns"]["duration"] < 0.1
        
        # Return results for potential regression comparison
        return performance_results
    
    def test_performance_under_stress(self, performance_client):
        """Test system behavior under stress conditions"""
        
        # Rapid consecutive requests from same user
        with patch('backend.api.pydantic_mentor') as mock_mentor:
            mock_mentor.respond = AsyncMock(return_value=MentorResponse(
                response="Stress test response",
                hint_level=1
            ))
            
            stress_requests = [
                {
                    "message": f"Rapid stress test question {i}",
                    "agent_type": "pydantic_strict",
                    "user_id": "stress_test_user",
                    "session_id": "stress_test_session"
                }
                for i in range(20)
            ]
            
            # Send requests rapidly
            start_time = time.time()
            responses = []
            
            for request in stress_requests:
                response = performance_client.post("/chat", json=request)
                responses.append(response)
            
            total_stress_time = time.time() - start_time
            
            # Verify system stability under stress
            success_count = sum(1 for r in responses if r.status_code == 200)
            success_rate = success_count / len(stress_requests)
            
            assert success_rate >= 0.9, f"Success rate {success_rate:.2f} too low under stress"
            assert total_stress_time < 30.0, f"Stress test took {total_stress_time:.3f}s (too slow)"
            
            print(f"✅ Stress test: {len(stress_requests)} requests in {total_stress_time:.3f}s")
            print(f"   Success rate: {success_rate:.2%}")
            print(f"   Avg per request: {total_stress_time/len(stress_requests):.3f}s")


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running Mentor Agent Performance Tests...")
    
    if PERFORMANCE_TEST_AVAILABLE:
        print("✅ Performance test dependencies available")
        print("🔧 Performance thresholds:")
        for metric, threshold in PERFORMANCE_THRESHOLDS.items():
            print(f"   {metric}: {threshold}s")
        print("✅ Performance test setup completed successfully!")
        print("Run with: pytest tests/test_mentor_agent_performance.py -v")
    else:
        print("⚠️ Performance test dependencies not available - tests skipped")
        print("Install all required dependencies to run performance tests")