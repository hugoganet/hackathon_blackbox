"""
Test conversation fixtures for curator agent testing
Contains realistic conversations at different skill levels for comprehensive testing
"""

import pytest
from typing import Dict, List, Any

# Junior Developer Conversation Scenarios
JUNIOR_CONVERSATIONS = [
    {
        "scenario": "JavaScript Variable Declaration Confusion",
        "user_id": "junior_dev_1", 
        "skill_level": "beginner",
        "conversation": {
            "user_message": "I'm getting an error 'Cannot access 'name' before initialization'. I declared let name = 'John'; but it's still giving me this error. Why is this happening?",
            "mentor_response": "Great question! This is a common issue with variable hoisting. Let's think about this step by step. Can you show me the exact code where you're trying to access the 'name' variable? Also, what happens if you try to use the variable before the line where you declared it?"
        },
        "expected_curator_output": {
            "skills": ["variable_declaration", "let_keyword", "temporal_dead_zone", "hoisting"],
            "mistakes": ["accessing variable before declaration", "unclear about temporal dead zone"],
            "openQuestions": ["difference between let and var hoisting", "when is variable actually initialized"],
            "nextSteps": ["practice: rewrite using var vs let", "exercise: identify hoisting scenarios"],
            "confidence": 0.3
        }
    },
    {
        "scenario": "React Hook Misunderstanding",
        "user_id": "junior_dev_2",
        "skill_level": "beginner", 
        "conversation": {
            "user_message": "My React component isn't updating when I change the state. I'm using useState like this: const [count, setCount] = useState(0); and then setCount(count + 1); but nothing happens.",
            "mentor_response": "Interesting observation! React state updates can be tricky. Let's explore this together. First, where exactly are you calling setCount(count + 1)? And have you tried adding a console.log to see if the function is being called? What do you think might happen if you click the button multiple times quickly?"
        },
        "expected_curator_output": {
            "skills": ["react_hooks", "useState", "state_updates", "react_rendering"],
            "mistakes": ["missing event handler", "unclear about async state updates"],
            "openQuestions": ["why state updates are asynchronous", "how React batching works"],
            "nextSteps": ["practice: implement counter with proper event handling", "exercise: explore functional state updates"],
            "confidence": 0.4
        }
    },
    {
        "scenario": "SQL Query Syntax Error",
        "user_id": "junior_dev_3",
        "skill_level": "beginner",
        "conversation": {
            "user_message": "I'm trying to get all users who have more than 5 orders, but my SQL query isn't working. I wrote: SELECT * FROM users WHERE orders > 5; but I get an error saying 'orders' doesn't exist.",
            "mentor_response": "Good attempt! You're on the right track thinking about filtering users by their order count. The error message is giving us a clue - 'orders' doesn't exist as a column. What do you think this tells us about the database structure? How do you think orders might be stored in relation to users?"
        },
        "expected_curator_output": {
            "skills": ["sql_queries", "joins", "aggregate_functions", "database_relationships"],
            "mistakes": ["trying to access non-existent column", "missing table relationships understanding"],
            "openQuestions": ["how to join tables", "when to use GROUP BY with COUNT"],
            "nextSteps": ["practice: write JOIN queries", "exercise: explore database schema"],
            "confidence": 0.2
        }
    }
]

# Intermediate Developer Conversation Scenarios  
INTERMEDIATE_CONVERSATIONS = [
    {
        "scenario": "Async/Await Error Handling",
        "user_id": "intermediate_dev_1",
        "skill_level": "intermediate",
        "conversation": {
            "user_message": "I'm working with async/await in my Node.js app, but I'm not sure about the best way to handle errors. I have try/catch blocks, but sometimes errors still slip through. Should I be using .catch() as well?",
            "mentor_response": "Excellent question about async error handling! You're already using try/catch which is great. Let's think about this systematically. In what specific scenarios are you noticing errors slipping through? Are these happening in your main async function or in nested async calls? What happens if an async function you're awaiting doesn't have its own error handling?"
        },
        "expected_curator_output": {
            "skills": ["async_await", "error_handling", "promise_rejection", "nodejs"],
            "mistakes": ["incomplete error handling in nested calls"],
            "openQuestions": ["unhandled promise rejections", "error propagation in async chains"],
            "nextSteps": ["practice: implement comprehensive error handling", "exercise: test different error scenarios"],
            "confidence": 0.6
        }
    },
    {
        "scenario": "React Performance Optimization",
        "user_id": "intermediate_dev_2", 
        "skill_level": "intermediate",
        "conversation": {
            "user_message": "My React app is getting slow with large lists. I've heard about useMemo and useCallback, but I'm not sure when to use each one. I have a component that renders 1000+ items and each item has click handlers.",
            "mentor_response": "Great awareness of performance concerns! You're right that useMemo and useCallback can help here. Let's analyze your specific situation. For your 1000+ item list, what exactly is causing the slowness - is it the initial render or interactions with the items? And tell me more about those click handlers - are they being created fresh on each render?"
        },
        "expected_curator_output": {
            "skills": ["react_performance", "useMemo", "useCallback", "virtualization"],
            "mistakes": ["creating new functions on each render"],
            "openQuestions": ["when to memoize", "list virtualization techniques"],
            "nextSteps": ["practice: implement React.memo for list items", "exercise: add performance profiling"],
            "confidence": 0.5
        }
    }
]

# Senior Developer Conversation Scenarios
SENIOR_CONVERSATIONS = [
    {
        "scenario": "System Architecture Discussion", 
        "user_id": "senior_dev_1",
        "skill_level": "advanced",
        "conversation": {
            "user_message": "I'm designing a microservices architecture for our e-commerce platform. I'm considering event sourcing for inventory management, but I'm concerned about the complexity vs benefits trade-off. What are the key factors I should evaluate?",
            "mentor_response": "Excellent architectural thinking! Event sourcing is indeed powerful but comes with trade-offs. You're wise to evaluate this carefully. What specific inventory challenges are you trying to solve? Are you dealing with high concurrency, audit requirements, or complex business rules? And what's your team's current experience with eventual consistency patterns?"
        },
        "expected_curator_output": {
            "skills": ["microservices", "event_sourcing", "system_design", "architecture_patterns"],
            "mistakes": [],
            "openQuestions": ["event sourcing complexity trade-offs", "team readiness for eventual consistency"],
            "nextSteps": ["evaluate: team experience with distributed systems", "practice: prototype event sourcing for one service"],
            "confidence": 0.8
        }
    }
]

# Error and Edge Case Scenarios
ERROR_CONVERSATIONS = [
    {
        "scenario": "Malformed Conversation",
        "user_id": "test_user_error_1",
        "skill_level": "unknown",
        "conversation": {
            "user_message": "",
            "mentor_response": "I notice you haven't asked a specific question. What would you like to learn about today?"
        },
        "expected_curator_output": {
            "skills": [],
            "mistakes": [],
            "openQuestions": ["what topic to explore"],
            "nextSteps": ["ask specific technical question"],
            "confidence": 0.0
        }
    },
    {
        "scenario": "Non-Technical Conversation",
        "user_id": "test_user_error_2", 
        "skill_level": "beginner",
        "conversation": {
            "user_message": "What's the weather like today?",
            "mentor_response": "I'm here to help with programming and software development questions. Is there a coding challenge or technical concept you'd like to explore?"
        },
        "expected_curator_output": {
            "skills": [],
            "mistakes": ["asking non-technical question"],
            "openQuestions": ["what programming topic to learn"],
            "nextSteps": ["identify learning goals", "ask about specific programming language"],
            "confidence": 0.1
        }
    }
]

# All conversation scenarios combined
ALL_CONVERSATIONS = JUNIOR_CONVERSATIONS + INTERMEDIATE_CONVERSATIONS + SENIOR_CONVERSATIONS + ERROR_CONVERSATIONS

# Test data generators
def get_conversations_by_skill_level(skill_level: str) -> List[Dict[str, Any]]:
    """Get conversations filtered by skill level"""
    return [conv for conv in ALL_CONVERSATIONS if conv.get("skill_level") == skill_level]

def get_conversation_by_scenario(scenario_name: str) -> Dict[str, Any]:
    """Get specific conversation by scenario name"""
    for conv in ALL_CONVERSATIONS:
        if conv["scenario"] == scenario_name:
            return conv
    raise ValueError(f"Scenario '{scenario_name}' not found")

# Mock Blackbox AI responses for testing
MOCK_CURATOR_RESPONSES = {
    "JavaScript Variable Declaration Confusion": {
        "skills": ["variable_declaration", "let_keyword", "temporal_dead_zone", "hoisting"], 
        "mistakes": ["accessing variable before declaration", "unclear about temporal dead zone"],
        "openQuestions": ["difference between let and var hoisting", "when is variable actually initialized"],
        "nextSteps": ["practice: rewrite using var vs let", "exercise: identify hoisting scenarios"],
        "confidence": 0.3
    },
    "React Hook Misunderstanding": {
        "skills": ["react_hooks", "useState", "state_updates", "react_rendering"],
        "mistakes": ["missing event handler", "unclear about async state updates"], 
        "openQuestions": ["why state updates are asynchronous", "how React batching works"],
        "nextSteps": ["practice: implement counter with proper event handling", "exercise: explore functional state updates"],
        "confidence": 0.4
    },
    "System Architecture Discussion": {
        "skills": ["microservices", "event_sourcing", "system_design", "architecture_patterns"],
        "mistakes": [],
        "openQuestions": ["event sourcing complexity trade-offs", "team readiness for eventual consistency"],
        "nextSteps": ["evaluate: team experience with distributed systems", "practice: prototype event sourcing for one service"],
        "confidence": 0.8
    }
}

# Pytest fixtures
@pytest.fixture
def junior_conversations():
    """Fixture for junior developer conversations"""
    return JUNIOR_CONVERSATIONS

@pytest.fixture  
def intermediate_conversations():
    """Fixture for intermediate developer conversations"""
    return INTERMEDIATE_CONVERSATIONS

@pytest.fixture
def senior_conversations():
    """Fixture for senior developer conversations"""
    return SENIOR_CONVERSATIONS

@pytest.fixture
def error_conversations():
    """Fixture for error and edge case conversations"""
    return ERROR_CONVERSATIONS

@pytest.fixture
def all_conversations():
    """Fixture for all conversation scenarios"""
    return ALL_CONVERSATIONS

@pytest.fixture
def mock_curator_responses():
    """Fixture for mock curator AI responses"""
    return MOCK_CURATOR_RESPONSES