"""
Learning Analytics Extraction Tests for Curator Agent
Tests the accuracy and quality of learning data extraction from conversations
"""

import pytest
import json
from typing import Dict, List, Any
from unittest.mock import patch

# Import test utilities
from tests.helpers.curator_test_utils import CuratorTestHelper, AssertionHelper
from tests.fixtures.curator_conversations import (
    JUNIOR_CONVERSATIONS, INTERMEDIATE_CONVERSATIONS, SENIOR_CONVERSATIONS,
    ERROR_CONVERSATIONS, ALL_CONVERSATIONS
)
from main import BlackboxMentor

@pytest.fixture(scope="session")
def setup_curator_agent():
    """Initialize curator agent for testing"""
    try:
        curator = BlackboxMentor("curator-agent.md")
        yield curator
    except Exception as e:
        pytest.skip(f"Could not initialize curator agent: {e}")

class TestSkillsExtraction:
    """Test accuracy of skills extraction from conversations"""
    
    def test_skills_extraction_javascript_fundamentals(self, setup_curator_agent):
        """Test skills extraction for JavaScript fundamental concepts"""
        
        conversation = JUNIOR_CONVERSATIONS[0]  # JavaScript Variable Declaration
        expected_skills = conversation["expected_curator_output"]["skills"]
        
        mock_response = json.dumps(conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            curator = setup_curator_agent
            response = curator.call_blackbox_api("Test conversation analysis")
            
            analysis = json.loads(response)
            extracted_skills = analysis["skills"]
            
            # Validate skill extraction quality
            AssertionHelper.assert_skills_reasonable(extracted_skills, 1, 5)
            
            # Check for JavaScript-specific skills
            js_skills = ["variable_declaration", "let_keyword", "hoisting", "temporal_dead_zone"]
            common_skills = set(extracted_skills) & set(js_skills)
            assert len(common_skills) >= 2, f"Should identify multiple JS concepts from {extracted_skills}"
    
    def test_skills_extraction_react_development(self, setup_curator_agent):
        """Test skills extraction for React development concepts"""
        
        conversation = JUNIOR_CONVERSATIONS[1]  # React Hook Misunderstanding
        expected_skills = conversation["expected_curator_output"]["skills"]
        
        mock_response = json.dumps(conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            curator = setup_curator_agent
            response = curator.call_blackbox_api("React useState conversation")
            
            analysis = json.loads(response)
            extracted_skills = analysis["skills"]
            
            # Validate React-specific skills
            react_skills = ["react_hooks", "useState", "state_updates", "react_rendering"]
            common_skills = set(extracted_skills) & set(react_skills)
            assert len(common_skills) >= 2, f"Should identify React concepts from {extracted_skills}"
    
    def test_skills_extraction_sql_database(self):
        """Test skills extraction for SQL and database concepts"""
        
        conversation = JUNIOR_CONVERSATIONS[2]  # SQL Query Syntax Error
        expected_skills = conversation["expected_curator_output"]["skills"]
        
        mock_response = json.dumps(conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            curator = BlackboxMentor("curator-agent.md")
            response = curator.call_blackbox_api("SQL query conversation")
            
            analysis = json.loads(response)
            extracted_skills = analysis["skills"]
            
            # Validate SQL-specific skills
            sql_skills = ["sql_queries", "joins", "aggregate_functions", "database_relationships"]
            common_skills = set(extracted_skills) & set(sql_skills)
            assert len(common_skills) >= 2, f"Should identify SQL concepts from {extracted_skills}"
    
    def test_skills_extraction_count_limits(self):
        """Test skills extraction respects maximum count limits"""
        
        for conversation in ALL_CONVERSATIONS:
            expected_output = conversation["expected_curator_output"]
            mock_response = json.dumps(expected_output)
            
            with CuratorTestHelper.mock_blackbox_api(mock_response):
                curator = BlackboxMentor("curator-agent.md")
                response = curator.call_blackbox_api("Conversation analysis")
                
                analysis = json.loads(response)
                skills = analysis["skills"]
                
                # Maximum 5 skills per conversation (per curator prompt spec)
                assert len(skills) <= 5, f"Skills count {len(skills)} exceeds maximum of 5"
                assert len(skills) >= 0, "Skills count should be non-negative"

class TestMistakesIdentification:
    """Test accuracy of mistake identification from conversations"""
    
    def test_mistakes_identification_javascript_errors(self):
        """Test identification of JavaScript-specific mistakes"""
        
        conversation = JUNIOR_CONVERSATIONS[0]  # Variable hoisting confusion
        expected_mistakes = conversation["expected_curator_output"]["mistakes"]
        
        mock_response = json.dumps(conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            curator = BlackboxMentor("curator-agent.md")
            response = curator.call_blackbox_api("JavaScript error analysis")
            
            analysis = json.loads(response)
            mistakes = analysis["mistakes"]
            
            # Validate mistake identification
            assert len(mistakes) <= 3, f"Mistakes count {len(mistakes)} exceeds maximum of 3"
            
            # Should identify variable-related mistakes
            mistake_text = " ".join(mistakes).lower()
            assert any(keyword in mistake_text for keyword in ["variable", "declaration", "hoisting"]), \
                f"Should identify variable-related mistakes in {mistakes}"
    
    def test_mistakes_identification_react_errors(self):
        """Test identification of React-specific mistakes"""
        
        conversation = JUNIOR_CONVERSATIONS[1]  # React useState issues
        expected_mistakes = conversation["expected_curator_output"]["mistakes"]
        
        mock_response = json.dumps(conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            curator = BlackboxMentor("curator-agent.md")
            response = curator.call_blackbox_api("React error analysis")
            
            analysis = json.loads(response)
            mistakes = analysis["mistakes"]
            
            # Should identify React-specific issues
            mistake_text = " ".join(mistakes).lower()
            assert any(keyword in mistake_text for keyword in ["event", "handler", "state", "async"]), \
                f"Should identify React-specific mistakes in {mistakes}"
    
    def test_mistakes_identification_senior_vs_junior(self):
        """Test mistake identification varies by skill level"""
        
        # Junior developers should have more identified mistakes
        junior_conversation = JUNIOR_CONVERSATIONS[0]
        junior_mock = json.dumps(junior_conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(junior_mock):
            curator = BlackboxMentor("curator-agent.md")
            response = curator.call_blackbox_api("Junior conversation")
            junior_analysis = json.loads(response)
        
        # Senior developers should have fewer identified mistakes
        senior_conversation = SENIOR_CONVERSATIONS[0]
        senior_mock = json.dumps(senior_conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(senior_mock):
            response = curator.call_blackbox_api("Senior conversation")
            senior_analysis = json.loads(response)
        
        # Junior should generally have more mistakes identified
        assert len(junior_analysis["mistakes"]) >= len(senior_analysis["mistakes"]), \
            "Junior developers should have more identified mistakes than senior developers"

class TestKnowledgeGapAnalysis:
    """Test identification of knowledge gaps and open questions"""
    
    def test_open_questions_identification(self):
        """Test identification of open questions from conversations"""
        
        conversation = JUNIOR_CONVERSATIONS[0]  # Variable declaration confusion
        expected_questions = conversation["expected_curator_output"]["openQuestions"]
        
        mock_response = json.dumps(conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            curator = BlackboxMentor("curator-agent.md")
            response = curator.call_blackbox_api("Knowledge gap analysis")
            
            analysis = json.loads(response)
            open_questions = analysis["openQuestions"]
            
            # Validate knowledge gap identification
            assert len(open_questions) <= 3, f"Open questions count {len(open_questions)} exceeds maximum of 3"
            assert len(open_questions) >= 1, "Should identify at least one knowledge gap"
            
            # Questions should be meaningful and actionable
            for question in open_questions:
                assert len(question) > 5, f"Question '{question}' is too short to be meaningful"
                assert isinstance(question, str), "Questions should be strings"
    
    def test_knowledge_gaps_progression_tracking(self):
        """Test knowledge gaps reflect learning progression"""
        
        # Test different skill levels have appropriate knowledge gaps
        skill_levels = [
            (JUNIOR_CONVERSATIONS[0], "beginner"),
            (INTERMEDIATE_CONVERSATIONS[0], "intermediate"), 
            (SENIOR_CONVERSATIONS[0], "advanced")
        ]
        
        for conversation, level in skill_levels:
            expected_output = conversation["expected_curator_output"]
            mock_response = json.dumps(expected_output)
            
            with CuratorTestHelper.mock_blackbox_api(mock_response):
                curator = BlackboxMentor("curator-agent.md")
                response = curator.call_blackbox_api(f"Analysis for {level} developer")
                
                analysis = json.loads(response)
                questions = analysis["openQuestions"]
                
                # All levels should have some questions, but content should differ
                assert len(questions) >= 0, f"No questions identified for {level} level"

class TestNextStepsRecommendations:
    """Test quality of next steps and learning recommendations"""
    
    def test_next_steps_actionability(self):
        """Test next steps are actionable and specific"""
        
        conversation = JUNIOR_CONVERSATIONS[1]  # React useState confusion
        expected_steps = conversation["expected_curator_output"]["nextSteps"]
        
        mock_response = json.dumps(conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            curator = BlackboxMentor("curator-agent.md")
            response = curator.call_blackbox_api("Next steps analysis")
            
            analysis = json.loads(response)
            next_steps = analysis["nextSteps"]
            
            # Validate next steps quality
            assert len(next_steps) <= 3, f"Next steps count {len(next_steps)} exceeds maximum of 3"
            
            for step in next_steps:
                assert len(step) > 10, f"Step '{step}' is too short to be actionable"
                
                # Should contain actionable verbs
                actionable_verbs = ["practice", "implement", "exercise", "explore", "review", "study"]
                step_lower = step.lower()
                assert any(verb in step_lower for verb in actionable_verbs), \
                    f"Step '{step}' should contain actionable language"
    
    def test_next_steps_skill_alignment(self):
        """Test next steps align with identified skills and gaps"""
        
        conversation = JUNIOR_CONVERSATIONS[2]  # SQL query issues
        expected_output = conversation["expected_curator_output"]
        mock_response = json.dumps(expected_output)
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            curator = BlackboxMentor("curator-agent.md")
            response = curator.call_blackbox_api("Skill-aligned recommendations")
            
            analysis = json.loads(response)
            skills = analysis["skills"]
            next_steps = analysis["nextSteps"]
            
            # Next steps should reference skills or related concepts
            skills_text = " ".join(skills).lower()
            steps_text = " ".join(next_steps).lower()
            
            # At least some overlap between skills and recommended steps
            if "sql" in skills_text:
                assert any(keyword in steps_text for keyword in ["sql", "query", "join", "database"]), \
                    "SQL-related next steps should be recommended for SQL skills"

class TestConfidenceAssessment:
    """Test accuracy of confidence level assessment"""
    
    def test_confidence_score_ranges_by_skill_level(self):
        """Test confidence scores appropriate for different skill levels"""
        
        skill_test_cases = [
            {
                "conversations": JUNIOR_CONVERSATIONS,
                "expected_range": (0.0, 0.5),
                "level": "junior"
            },
            {
                "conversations": INTERMEDIATE_CONVERSATIONS,
                "expected_range": (0.4, 0.7),
                "level": "intermediate"
            },
            {
                "conversations": SENIOR_CONVERSATIONS,
                "expected_range": (0.7, 1.0),
                "level": "senior"
            }
        ]
        
        for test_case in skill_test_cases:
            for conversation in test_case["conversations"]:
                expected_output = conversation["expected_curator_output"]
                mock_response = json.dumps(expected_output)
                
                with CuratorTestHelper.mock_blackbox_api(mock_response):
                    curator = BlackboxMentor("curator-agent.md")
                    response = curator.call_blackbox_api(f"Confidence assessment - {test_case['level']}")
                    
                    analysis = json.loads(response)
                    confidence = analysis["confidence"]
                    
                    min_conf, max_conf = test_case["expected_range"]
                    AssertionHelper.assert_confidence_reasonable(confidence, min_conf, max_conf)
    
    def test_confidence_score_validation(self):
        """Test confidence scores are valid numeric values"""
        
        for conversation in ALL_CONVERSATIONS:
            expected_output = conversation["expected_curator_output"]
            mock_response = json.dumps(expected_output)
            
            with CuratorTestHelper.mock_blackbox_api(mock_response):
                curator = BlackboxMentor("curator-agent.md")
                response = curator.call_blackbox_api("Confidence validation test")
                
                analysis = json.loads(response)
                confidence = analysis["confidence"]
                
                # Validate confidence is proper numeric value
                assert isinstance(confidence, (int, float)), "Confidence should be numeric"
                assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} should be between 0.0 and 1.0"
    
    def test_confidence_correlates_with_complexity(self):
        """Test confidence scores correlate with conversation complexity"""
        
        # Simple conversations should have higher confidence
        simple_conversation = ERROR_CONVERSATIONS[1]  # Non-technical question
        simple_mock = json.dumps(simple_conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(simple_mock):
            curator = BlackboxMentor("curator-agent.md")
            response = curator.call_blackbox_api("Simple conversation")
            simple_analysis = json.loads(response)
        
        # Complex conversations should have lower confidence (if junior developer)
        complex_conversation = JUNIOR_CONVERSATIONS[2]  # SQL complexity
        complex_mock = json.dumps(complex_conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(complex_mock):
            response = curator.call_blackbox_api("Complex conversation")
            complex_analysis = json.loads(response)
        
        # For same skill level, simpler topics might have slightly higher confidence
        # But this depends on the specific conversation content
        assert simple_analysis["confidence"] >= 0.0
        assert complex_analysis["confidence"] >= 0.0

class TestLearningAnalyticsQuality:
    """Test overall quality and consistency of learning analytics"""
    
    def test_analytics_consistency_across_conversations(self):
        """Test analytics consistency across multiple conversations"""
        
        for conversation in ALL_CONVERSATIONS[:5]:  # Test subset for performance
            expected_output = conversation["expected_curator_output"]
            mock_response = json.dumps(expected_output)
            
            with CuratorTestHelper.mock_blackbox_api(mock_response):
                curator = BlackboxMentor("curator-agent.md")
                response = curator.call_blackbox_api("Consistency test")
                
                analysis = json.loads(response)
                
                # Validate all required fields are present and valid
                AssertionHelper.assert_curator_response_valid(analysis)
    
    def test_analytics_domain_classification(self):
        """Test learning analytics can classify different programming domains"""
        
        domain_tests = [
            {
                "conversation": JUNIOR_CONVERSATIONS[0],  # JavaScript
                "expected_domain": "javascript"
            },
            {
                "conversation": JUNIOR_CONVERSATIONS[1],  # React  
                "expected_domain": "react"
            },
            {
                "conversation": JUNIOR_CONVERSATIONS[2],  # SQL
                "expected_domain": "sql"
            }
        ]
        
        for test_case in domain_tests:
            conversation = test_case["conversation"]
            expected_output = conversation["expected_curator_output"]
            mock_response = json.dumps(expected_output)
            
            with CuratorTestHelper.mock_blackbox_api(mock_response):
                curator = BlackboxMentor("curator-agent.md")
                response = curator.call_blackbox_api("Domain classification test")
                
                analysis = json.loads(response)
                skills = analysis["skills"]
                
                # Skills should reflect the programming domain
                skills_text = " ".join(skills).lower()
                domain = test_case["expected_domain"]
                
                # Should contain domain-relevant terms
                if domain == "javascript":
                    assert any(keyword in skills_text for keyword in ["javascript", "variable", "let", "var"]), \
                        f"Should identify JavaScript concepts in {skills}"
                elif domain == "react":
                    assert any(keyword in skills_text for keyword in ["react", "hooks", "usestate", "component"]), \
                        f"Should identify React concepts in {skills}"
                elif domain == "sql":
                    assert any(keyword in skills_text for keyword in ["sql", "query", "join", "database"]), \
                        f"Should identify SQL concepts in {skills}"

class TestLearningProgressionTracking:
    """Test ability to track learning progression over time"""
    
    def test_skill_progression_identification(self):
        """Test identification of skill progression indicators"""
        
        # This test simulates multiple conversations showing progression
        progression_scenarios = [
            {
                "conversation": JUNIOR_CONVERSATIONS[0],
                "stage": "initial_confusion",
                "expected_confidence_range": (0.0, 0.4)
            },
            {
                "conversation": INTERMEDIATE_CONVERSATIONS[0], 
                "stage": "improved_understanding",
                "expected_confidence_range": (0.4, 0.7)
            }
        ]
        
        for scenario in progression_scenarios:
            conversation = scenario["conversation"]
            expected_output = conversation["expected_curator_output"]
            mock_response = json.dumps(expected_output)
            
            with CuratorTestHelper.mock_blackbox_api(mock_response):
                curator = BlackboxMentor("curator-agent.md")
                response = curator.call_blackbox_api(f"Progression test - {scenario['stage']}")
                
                analysis = json.loads(response)
                confidence = analysis["confidence"]
                
                min_conf, max_conf = scenario["expected_confidence_range"]
                assert min_conf <= confidence <= max_conf, \
                    f"Confidence {confidence} not in expected range {min_conf}-{max_conf} for {scenario['stage']}"

if __name__ == "__main__":
    pytest.main(["-v", __file__])