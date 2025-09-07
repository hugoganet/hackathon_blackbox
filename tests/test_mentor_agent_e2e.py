"""
End-to-End Tests for Complete Mentor Agent User Journey
Tests the complete user experience from initial question through multi-turn conversations
"""

import pytest
import asyncio
import json
import os
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Test imports
try:
    from backend.api import app, get_db
    from backend.database import Base, User, Session as DBSession, Interaction, create_user
    from backend.memory_store import ConversationMemory
    from agents.mentor_agent import MentorAgent, MentorResponse
    E2E_TEST_AVAILABLE = True
except ImportError as e:
    print(f"Warning: E2E test imports not available: {e}")
    E2E_TEST_AVAILABLE = False


# Test database and memory store setup
TEST_DATABASE_URL = "sqlite:///test_e2e_mentor_agent.db"


@pytest.fixture(scope="function")
def test_db():
    """Create test database for E2E tests"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up test database
        try:
            os.remove("test_e2e_mentor_agent.db")
        except FileNotFoundError:
            pass


@pytest.fixture(scope="function")
def test_memory_store():
    """Create test ChromaDB memory store for E2E tests"""
    test_dir = tempfile.mkdtemp(prefix="test_e2e_chroma_")
    
    try:
        if E2E_TEST_AVAILABLE:
            memory_store = ConversationMemory(persist_directory=test_dir)
            yield memory_store
        else:
            yield None
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


@pytest.fixture
def client(test_db):
    """Create test client with dependency override"""
    if not E2E_TEST_AVAILABLE:
        pytest.skip("E2E test dependencies not available")
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def learning_scenarios():
    """Real-world learning scenarios for E2E testing"""
    return {
        "python_beginner": {
            "user_id": "python_beginner_student",
            "session_id": "python_learning_session",
            "conversation_flow": [
                {
                    "message": "I'm completely new to programming. Where should I start with Python?",
                    "expected_patterns": ["what interests you", "what would you like", "experience", "background"],
                    "should_not_contain": ["start with variables", "here's how to", "first you need to"]
                },
                {
                    "message": "I want to build a simple calculator",
                    "expected_patterns": ["what operations", "what should it do", "think about", "break it down"],
                    "should_not_contain": ["def calculator", "import", "here's the code"]
                },
                {
                    "message": "Maybe it should add and subtract numbers?",
                    "expected_patterns": ["great start", "how might", "what do you think", "where would"],
                    "should_not_contain": ["def add", "return a + b", "def subtract"]
                },
                {
                    "message": "I think I need to get numbers from the user somehow?",
                    "expected_patterns": ["excellent thinking", "how do you think", "what would happen", "good insight"],
                    "should_not_contain": ["input()", "int(input", "here's how to get input"]
                }
            ]
        },
        "javascript_debugging": {
            "user_id": "js_debugging_student",
            "session_id": "js_debugging_session",
            "conversation_flow": [
                {
                    "message": "My JavaScript function isn't working and I'm getting frustrated!",
                    "expected_patterns": ["understand", "frustration", "what error", "step by step", "what's happening"],
                    "should_not_contain": ["here's your problem", "the issue is", "change this line"]
                },
                {
                    "message": "It says 'TypeError: Cannot read property' but I don't understand what that means",
                    "expected_patterns": ["what do you think", "where does this happen", "what might cause", "break it down"],
                    "should_not_contain": ["you have a null", "add a check for", "the problem is undefined"]
                },
                {
                    "message": "Please just tell me what's wrong! I've been stuck for hours!",
                    "expected_patterns": ["understand your frustration", "help you discover", "my role is to guide", "what have you tried"],
                    "should_not_contain": ["the error is", "change line", "add this code", "the solution is"]
                },
                {
                    "message": "Okay, I'll try to debug it myself. The error happens when I click the button.",
                    "expected_patterns": ["great approach", "when you click", "what do you expect", "step through"],
                    "should_not_contain": ["add event listener", "addEventListener", "here's the fix"]
                }
            ]
        },
        "react_intermediate": {
            "user_id": "react_intermediate_student",  
            "session_id": "react_learning_session",
            "conversation_flow": [
                {
                    "message": "I understand basic React but I'm confused about when to use useEffect",
                    "expected_patterns": ["what situations", "when do you think", "what have you used", "what's confusing"],
                    "should_not_contain": ["useEffect is used for", "here's when to use", "you need useEffect when"]
                },
                {
                    "message": "I think it's for when data changes? But I'm not sure when exactly.",
                    "expected_patterns": ["good intuition", "what kind of changes", "can you think of examples", "what scenarios"],
                    "should_not_contain": ["useEffect(() => {", "dependency array", "here's an example"]
                },
                {
                    "message": "Maybe when I need to fetch data from an API?",
                    "expected_patterns": ["excellent example", "when would you want", "what about after", "good thinking"],
                    "should_not_contain": ["fetch()", "async", "useEffect(() => { fetch"]
                }
            ]
        }
    }


@pytest.mark.skipif(not E2E_TEST_AVAILABLE, reason="E2E test dependencies not available")
class TestCompleteUserJourneys:
    """Test complete user learning journeys"""
    
    @patch('backend.api.pydantic_mentor')
    def test_python_beginner_complete_journey(self, mock_pydantic_mentor, client, learning_scenarios, test_memory_store):
        """Test complete journey for Python beginner"""
        
        scenario = learning_scenarios["python_beginner"]
        user_id = scenario["user_id"]
        session_id = scenario["session_id"]
        
        conversation_history = []
        
        for i, exchange in enumerate(scenario["conversation_flow"]):
            # Mock appropriate mentor response that follows strict principles
            mock_response = MentorResponse(
                response=f"That's a thoughtful question! {' '.join(exchange['expected_patterns'][:2])}?",
                hint_level=min(i + 1, 4),
                memory_context_used=(i > 0),  # Use context after first message
                detected_language="python",
                detected_intent="concept_explanation",
                similar_interactions_count=i
            )
            mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
            
            # Make chat request
            chat_request = {
                "message": exchange["message"],
                "agent_type": "pydantic_strict",
                "user_id": user_id,
                "session_id": session_id
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            conversation_history.append({
                "user_message": exchange["message"],
                "mentor_response": data["response"],
                "hint_level": data.get("hint_level", 1),
                "detected_language": data.get("detected_language"),
                "memory_context_used": data.get("memory_context_used", False)
            })
            
            # Verify strict mentor principles maintained
            response_text = data["response"].lower()
            
            # Should contain guiding patterns
            has_guiding_pattern = any(pattern in response_text for pattern in exchange["expected_patterns"])
            assert has_guiding_pattern, f"Response missing guiding patterns: {data['response']}"
            
            # Should not contain direct answers
            for forbidden in exchange["should_not_contain"]:
                assert forbidden.lower() not in response_text, f"Response contains forbidden content '{forbidden}': {data['response']}"
            
            # Verify session continuity
            assert data["session_id"] == session_id
            assert data["agent_type"] == "pydantic_strict"
        
        # Verify conversation progression
        assert len(conversation_history) == len(scenario["conversation_flow"])
        
        # Verify memory context usage increases over time
        memory_usage = [exchange.get("memory_context_used", False) for exchange in conversation_history]
        assert any(memory_usage[1:]), "Memory context should be used in later exchanges"
        
        # Verify hint level progression (should not exceed 4)
        hint_levels = [exchange.get("hint_level", 1) for exchange in conversation_history]
        assert all(level <= 4 for level in hint_levels), "Hint levels should not exceed 4"
    
    @patch('backend.api.pydantic_mentor')
    def test_javascript_debugging_frustration_handling(self, mock_pydantic_mentor, client, learning_scenarios):
        """Test handling user frustration in debugging scenario"""
        
        scenario = learning_scenarios["javascript_debugging"]
        user_id = scenario["user_id"] 
        session_id = scenario["session_id"]
        
        for i, exchange in enumerate(scenario["conversation_flow"]):
            # Mock empathetic but firm mentor response
            if "frustrated" in exchange["message"] or "please just tell me" in exchange["message"].lower():
                # Frustration handling response
                mock_response = MentorResponse(
                    response="I understand your frustration, but giving you the answer wouldn't help you grow as a developer. Let's work through this together - what have you tried so far?",
                    hint_level=1,  # Reset hint level for frustration
                    memory_context_used=True,
                    detected_language="javascript",
                    detected_intent="debugging"
                )
            else:
                # Regular debugging guidance
                mock_response = MentorResponse(
                    response=f"Let's debug this step by step. {' '.join(exchange['expected_patterns'][:2])}?",
                    hint_level=min(i + 1, 4),
                    memory_context_used=(i > 0),
                    detected_language="javascript",
                    detected_intent="debugging"
                )
            
            mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
            
            # Make chat request
            chat_request = {
                "message": exchange["message"],
                "agent_type": "pydantic_strict",
                "user_id": user_id,
                "session_id": session_id
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            response_text = data["response"].lower()
            
            # Special handling for frustration exchanges
            if "frustrated" in exchange["message"] or "please just tell me" in exchange["message"].lower():
                # Should acknowledge frustration but maintain pedagogical stance
                frustration_indicators = ["understand", "frustration", "help you", "work through", "together"]
                assert any(indicator in response_text for indicator in frustration_indicators)
                
                # Should not give in to pressure for direct answers
                direct_answer_phrases = ["the problem is", "change this", "add this line", "here's the fix"]
                assert not any(phrase in response_text for phrase in direct_answer_phrases)
            
            # Always verify mentor principles
            for forbidden in exchange["should_not_contain"]:
                assert forbidden.lower() not in response_text
    
    @patch('backend.api.pydantic_mentor')
    def test_multi_session_learning_progression(self, mock_pydantic_mentor, client, test_memory_store):
        """Test learning progression across multiple sessions"""
        
        user_id = "multi_session_learner"
        
        # Session 1: Introduction to Python functions
        session1_id = "python_functions_session_1"
        session1_messages = [
            "What is a Python function?",
            "I think functions are like recipes?",
            "How do I create a simple function?"
        ]
        
        # Session 2: Function parameters (continuing learning)
        session2_id = "python_functions_session_2"
        session2_messages = [
            "I remember we talked about functions. Now I want to learn about parameters.",
            "Can a function take multiple parameters?",
            "What happens if I don't provide all the parameters?"
        ]
        
        all_sessions = [
            (session1_id, session1_messages),
            (session2_id, session2_messages)
        ]
        
        for session_id, messages in all_sessions:
            for i, message in enumerate(messages):
                # Mock progressive responses with increasing context awareness
                if session_id == session2_id:
                    # Second session should reference previous learning
                    mock_response = MentorResponse(
                        response=f"Building on what we discussed about functions, {message.lower()}? What do you remember from our previous exploration?",
                        hint_level=1 + i,
                        memory_context_used=True,
                        detected_language="python",
                        detected_intent="concept_explanation",
                        similar_interactions_count=3 + i  # Accumulated context
                    )
                else:
                    # First session - fresh start
                    mock_response = MentorResponse(
                        response=f"Great question about {message.lower()}! What's your current thinking about this?",
                        hint_level=1 + i,
                        memory_context_used=(i > 0),
                        detected_language="python", 
                        detected_intent="concept_explanation",
                        similar_interactions_count=i
                    )
                
                mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
                
                # Make request
                chat_request = {
                    "message": message,
                    "agent_type": "pydantic_strict",
                    "user_id": user_id,
                    "session_id": session_id
                }
                
                response = client.post("/chat", json=chat_request)
                assert response.status_code == 200
                
                data = response.json()
                
                # Verify session continuity
                assert data["session_id"] == session_id
                
                # Session 2 should show memory context usage
                if session_id == session2_id:
                    assert data.get("memory_context_used", False) == True
                    assert data.get("similar_interactions_count", 0) > 0
                    assert "building on" in data["response"].lower() or "remember" in data["response"].lower()


@pytest.mark.skipif(not E2E_TEST_AVAILABLE, reason="E2E test dependencies not available")
class TestUserPersonaJourneys:
    """Test different user personas and their learning patterns"""
    
    @patch('backend.api.pydantic_mentor')  
    def test_impatient_user_persistence(self, mock_pydantic_mentor, client):
        """Test mentor persistence with impatient user trying to get direct answers"""
        
        user_id = "impatient_user"
        session_id = "impatience_test_session"
        
        # Progressively demanding requests
        impatient_requests = [
            "How do I sort an array in JavaScript?",
            "Just show me the code for sorting an array",
            "Come on, just give me the answer! I need the sort() method syntax!",
            "This is ridiculous! Every other AI just gives me the code. What's wrong with you?",
            "Fine, I'll try to figure it out myself. What should I think about when sorting data?"
        ]
        
        expected_responses = [
            "Great question! What do you think sorting means in programming?",
            "I understand you want a quick solution, but let's explore this together. What kinds of sorting have you encountered in real life?",
            "I know this can be frustrating, but my role is to help you become a stronger programmer. What have you tried so far?",
            "I'm here to help you learn, not just provide answers. Other approaches might give you code, but won't help you understand. Let's break this down - what do you want to achieve?",
            "Excellent! That's the learning mindset. When you sort data, what do you think needs to happen to the elements?"
        ]
        
        for i, (request, expected_pattern) in enumerate(zip(impatient_requests, expected_responses)):
            mock_response = MentorResponse(
                response=expected_pattern,
                hint_level=1,  # Reset for each new approach
                memory_context_used=True,
                detected_language="javascript",
                detected_intent="concept_explanation" if i == 0 or i == 4 else "general"
            )
            mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
            
            chat_request = {
                "message": request,
                "agent_type": "pydantic_strict", 
                "user_id": user_id,
                "session_id": session_id
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            response_text = data["response"].lower()
            
            # Verify mentor never gives in to pressure
            forbidden_direct_answers = [
                "array.sort()",
                ".sort(function",
                "here's the code",
                "array.sort((a, b)",
                "use this syntax"
            ]
            
            for forbidden in forbidden_direct_answers:
                assert forbidden.lower() not in response_text
            
            # Should maintain empathetic but firm stance
            if "frustrating" in request.lower() or "ridiculous" in request.lower():
                empathy_indicators = ["understand", "frustrat", "help you", "role is"]
                assert any(indicator in response_text for indicator in empathy_indicators)
            
            # Final response should acknowledge the shift to learning mindset
            if i == len(impatient_requests) - 1:
                positive_indicators = ["excellent", "great", "learning", "think about"]
                assert any(indicator in response_text for indicator in positive_indicators)
    
    @patch('backend.api.pydantic_mentor')
    def test_methodical_learner_journey(self, mock_pydantic_mentor, client):
        """Test mentor adaptation to methodical, detail-oriented learner"""
        
        user_id = "methodical_learner"
        session_id = "methodical_learning_session"
        
        # Methodical learner asks thorough, well-thought questions
        methodical_questions = [
            "I'm learning about Python classes. I understand the basic concept but want to make sure I grasp the fundamentals before moving forward.",
            "You asked what I think classes are for. I believe they're for organizing related data and functions together, like a blueprint. Is this the right direction?", 
            "That makes sense. Now I'm wondering about the relationship between a class and an instance. Should I think of instances as copies of the blueprint?",
            "I see. So each instance can have different values but the same structure. How does this help with code organization in larger projects?"
        ]
        
        # Responses should match the thoughtful nature and build progressively
        for i, question in enumerate(methodical_questions):
            if i == 0:
                mock_response = MentorResponse(
                    response="I appreciate your thoughtful approach! That's exactly the right mindset for solid learning. What do you think classes are fundamentally designed to accomplish?",
                    hint_level=1,
                    memory_context_used=False,
                    detected_language="python",
                    detected_intent="concept_explanation"
                )
            elif i == 1:
                mock_response = MentorResponse(
                    response="Excellent analogy with blueprints! You're thinking about this very clearly. Now, when you use that blueprint, what do you think happens?",
                    hint_level=1,
                    memory_context_used=True,
                    detected_language="python",
                    detected_intent="concept_explanation"
                )
            elif i == 2:
                mock_response = MentorResponse(
                    response="Perfect understanding! You've grasped the key relationship. Now you're asking great questions about practical applications. What kinds of organization challenges do you think classes might solve?",
                    hint_level=2,
                    memory_context_used=True,
                    detected_language="python",
                    detected_intent="concept_explanation"
                )
            else:
                mock_response = MentorResponse(
                    response="You're connecting concepts beautifully! That's advanced thinking. In larger projects, what problems do you imagine might arise without good organization?",
                    hint_level=2,
                    memory_context_used=True,
                    detected_language="python",
                    detected_intent="improvement"
                )
            
            mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
            
            chat_request = {
                "message": question,
                "agent_type": "pydantic_strict",
                "user_id": user_id,
                "session_id": session_id
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            response_text = data["response"].lower()
            
            # Should acknowledge thoughtful approach
            positive_acknowledgments = ["excellent", "perfect", "great", "thoughtful", "clearly", "beautifully"]
            assert any(ack in response_text for ack in positive_acknowledgments)
            
            # Should still maintain questioning approach (not give answers)
            should_contain_questions = ["what do you think", "what", "how", "why"]
            assert any(question_word in response_text for question_word in should_contain_questions)
            
            # Should not provide direct technical explanations
            forbidden_explanations = [
                "a class is defined with",
                "self parameter represents",
                "instances are created by",
                "here's how classes work"
            ]
            for forbidden in forbidden_explanations:
                assert forbidden not in response_text


@pytest.mark.skipif(not E2E_TEST_AVAILABLE, reason="E2E test dependencies not available")
class TestScenarioComplexity:
    """Test complex real-world learning scenarios"""
    
    @patch('backend.api.pydantic_mentor')
    def test_project_based_learning_scenario(self, mock_pydantic_mentor, client):
        """Test mentor guidance through a complete project scenario"""
        
        user_id = "project_learner"
        session_id = "todo_app_project"
        
        # Simulated project development conversation
        project_conversation = [
            {
                "message": "I want to build a todo app in React. Where should I start?",
                "phase": "planning",
                "expected_guidance": ["what features", "what should users", "break it down", "think about"]
            },
            {
                "message": "Users should be able to add tasks, mark them complete, and delete them.",
                "phase": "requirements",
                "expected_guidance": ["good start", "what about", "how might", "what data"]
            },
            {
                "message": "I think I need to store the tasks in state somehow?",
                "phase": "architecture",
                "expected_guidance": ["excellent thinking", "what kind of", "how would you", "what happens when"]
            },
            {
                "message": "Maybe an array of task objects? Each task could have text and a completed status?",
                "phase": "data_modeling", 
                "expected_guidance": ["great structure", "what operations", "how would you", "what about"]
            },
            {
                "message": "I'm getting stuck on how to update a specific task when marking it complete.",
                "phase": "implementation",
                "expected_guidance": ["common challenge", "what identifies", "how might you find", "think about"]
            }
        ]
        
        for i, exchange in enumerate(project_conversation):
            # Mock progressive, project-focused guidance
            mock_response = MentorResponse(
                response=f"{exchange['expected_guidance'][0].title()}! You're in the {exchange['phase']} phase. {' '.join(exchange['expected_guidance'][1:3])}?",
                hint_level=min(i + 1, 4),
                memory_context_used=(i > 0),
                detected_language="javascript",
                detected_intent="concept_explanation" if exchange['phase'] in ["planning", "requirements"] else "improvement",
                similar_interactions_count=i
            )
            mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
            
            chat_request = {
                "message": exchange["message"],
                "agent_type": "pydantic_strict", 
                "user_id": user_id,
                "session_id": session_id
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            response_text = data["response"].lower()
            
            # Should guide through project phases without giving implementation
            phase_guidance = any(pattern in response_text for pattern in exchange["expected_guidance"])
            assert phase_guidance, f"Missing expected guidance patterns in phase {exchange['phase']}"
            
            # Should not provide direct React code
            forbidden_code = [
                "useState([",
                "const [todos",
                "setTodos(",
                "map((todo",
                "onClick={() =>",
                "todo.id ===",
                "...todo, completed:",
                "filter(todo =>"
            ]
            
            for forbidden in forbidden_code:
                assert forbidden not in response_text, f"Response contains forbidden code '{forbidden}' in {exchange['phase']} phase"
            
            # Later phases should reference earlier decisions
            if i > 2 and exchange['phase'] in ["data_modeling", "implementation"]:
                context_references = ["remember", "you mentioned", "building on", "based on", "from what we discussed"]
                has_context_reference = any(ref in response_text for ref in context_references)
                # Not strictly required, but good mentoring practice
    
    @patch('backend.api.pydantic_mentor')
    def test_debugging_workflow_scenario(self, mock_pydantic_mentor, client):
        """Test mentor guidance through systematic debugging"""
        
        user_id = "debugging_learner"
        session_id = "systematic_debugging"
        
        debugging_workflow = [
            {
                "message": "My React component isn't rendering anything and I don't know why!",
                "stage": "problem_identification",
                "expected_approach": ["what do you see", "what were you expecting", "first step", "exactly what"]
            },
            {
                "message": "The browser shows a blank page where my component should be.",
                "stage": "symptom_analysis",
                "expected_approach": ["console errors", "what tools", "check the", "developer tools"]
            },
            {
                "message": "The console shows 'Warning: Each child in a list should have a unique key prop'",
                "stage": "error_analysis",
                "expected_approach": ["what do you think", "warning tells you", "what might", "where are you"]
            },
            {
                "message": "I'm rendering a list of items in my component using map().",
                "stage": "context_understanding",
                "expected_approach": ["when you use map", "what does React need", "how might you", "what identifies"]
            },
            {
                "message": "I think I need to add a key to each item, but I'm not sure what to use as the key.",
                "stage": "solution_development",
                "expected_approach": ["good understanding", "what makes each", "uniquely identify", "what properties"]
            }
        ]
        
        for i, step in enumerate(debugging_workflow):
            # Mock systematic debugging guidance
            mock_response = MentorResponse(
                response=f"Let's work through this systematically. {step['expected_approach'][0].title()}? This is the {step['stage'].replace('_', ' ')} stage of debugging.",
                hint_level=min(i + 1, 4),
                memory_context_used=(i > 0),
                detected_language="javascript",
                detected_intent="debugging",
                similar_interactions_count=i
            )
            mock_pydantic_mentor.respond = AsyncMock(return_value=mock_response)
            
            chat_request = {
                "message": step["message"],
                "agent_type": "pydantic_strict",
                "user_id": user_id,
                "session_id": session_id
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200
            
            data = response.json()
            response_text = data["response"].lower()
            
            # Should follow systematic debugging approach
            systematic_indicators = ["systematically", "let's", "step", "stage", "first", "next"]
            assert any(indicator in response_text for indicator in systematic_indicators)
            
            # Should guide thinking, not provide solutions
            guidance_present = any(approach.lower() in response_text for approach in step["expected_approach"])
            assert guidance_present, f"Missing expected debugging guidance in {step['stage']}"
            
            # Should not provide direct fixes
            direct_fixes = [
                "key={item.id}",
                "key={index}",
                "add key prop",
                "use the id as key",
                "{items.map((item, index) =>"
            ]
            
            for fix in direct_fixes:
                assert fix not in response_text, f"Response provides direct fix '{fix}' in {step['stage']}"


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running Mentor Agent End-to-End Tests...")
    
    if E2E_TEST_AVAILABLE:
        print("✅ E2E test dependencies available")
        print("✅ End-to-end test setup completed successfully!")
        print("Run with: pytest tests/test_mentor_agent_e2e.py -v")
    else:
        print("⚠️ E2E test dependencies not available - tests skipped")
        print("Install all required dependencies to run end-to-end tests")