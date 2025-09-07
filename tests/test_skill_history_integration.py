"""
Tests for skill_history table integration with curator agent workflow
Tests the complete data flow from curator analysis to skill tracking database storage
"""

import pytest
import json
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import shutil
import os

<<<<<<< HEAD
# Import application components
=======
# Test database setup - PostgreSQL for proper UUID and production parity
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:password@localhost:5432/test_dev_mentor_ai")
# Set the DATABASE_URL environment variable BEFORE importing backend modules
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Import application components (AFTER setting environment variables)
>>>>>>> 5800e139677ff61d9ee54bd663ae118b4dd44003
from backend.api import app
from backend.database import (
    Base, get_db, User, RefDomain, Skill, SkillHistory,
    create_or_update_skill, update_skill_history, process_curator_analysis,
    get_user_skill_progression, populate_initial_data
)
from backend.main import BlackboxMentor
<<<<<<< HEAD
from backend import api
=======
import backend.api as api
>>>>>>> 5800e139677ff61d9ee54bd663ae118b4dd44003

# Import test utilities
from tests.helpers.curator_test_utils import CuratorTestHelper
from tests.fixtures.curator_conversations import JUNIOR_CONVERSATIONS

# Create engine with PostgreSQL
engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=True  # Set to True for SQL debugging
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override dependencies
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="session")
def setup_test_db():
    """Set up test database with skill tracking tables"""
    Base.metadata.create_all(bind=engine)
    
    # Populate initial data
    db = TestingSessionLocal()
    try:
        populate_initial_data(db)
    finally:
        db.close()
        
    yield
    # Cleanup - Drop all tables in PostgreSQL
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session") 
def setup_curator_agent():
    """Initialize curator agent for testing"""
    try:
        api.curator_agent = BlackboxMentor("agents/curator-agent.md")
        yield api.curator_agent
    except Exception as e:
        pytest.skip(f"Could not initialize curator agent: {e}")
    finally:
        api.curator_agent = None

class TestSkillDatabaseModels:
    """Test the skill tracking database models"""
    
    def test_ref_domain_creation(self, setup_test_db):
        """Test creating reference domains"""
        db = TestingSessionLocal()
        try:
            # Check if domains were populated
            domains = db.query(RefDomain).all()
            assert len(domains) >= 10  # Should have at least the standard domains
            
            domain_names = [d.name for d in domains]
            assert "SYNTAX" in domain_names
            assert "FRAMEWORKS" in domain_names
            assert "DATABASES" in domain_names
            
        finally:
            db.close()
    
    def test_skill_creation_and_update(self, setup_test_db):
        """Test creating and updating skills"""
        db = TestingSessionLocal()
        try:
            # Create a new skill
            skill = create_or_update_skill(db, "test_skill", "Test skill description", "SYNTAX")
            
            assert skill.name == "test_skill"
            assert skill.description == "Test skill description"
            assert skill.domain.name == "SYNTAX"
            
            # Test getting existing skill
            same_skill = create_or_update_skill(db, "test_skill", "Different description", "FRAMEWORKS")
            assert same_skill.id_skill == skill.id_skill  # Should be the same skill
            
        finally:
            db.close()
    
    def test_skill_history_creation(self, setup_test_db):
        """Test creating skill history entries"""
        db = TestingSessionLocal()
        try:
            # Create a test user
            user = User(username="test_skill_user")
            db.add(user)
            db.commit()
            
            # Create skill history
            skill_history = update_skill_history(db, str(user.id), "javascript_variables", 0.7, "SYNTAX")
            
            assert skill_history.mastery_level == 3  # 0.7 confidence -> mastery level 3
            assert skill_history.snapshot_date == date.today()
            assert skill_history.skill.name == "javascript_variables"
            assert skill_history.user.id == user.id
            
        finally:
            db.close()
    
    def test_skill_history_daily_uniqueness(self, setup_test_db):
        """Test that only one skill history entry per skill per day is allowed"""
        db = TestingSessionLocal()
        try:
            # Create a test user
            user = User(username="test_unique_user")
            db.add(user)
            db.commit()
            
            # Create first skill history entry
            history1 = update_skill_history(db, str(user.id), "react_hooks", 0.5, "FRAMEWORKS")
            assert history1.mastery_level == 3
            
            # Create second entry same day - should update existing
            history2 = update_skill_history(db, str(user.id), "react_hooks", 0.9, "FRAMEWORKS")
            assert history2.id_history == history1.id_history  # Same entry
            assert history2.mastery_level == 4  # Updated to higher mastery (0.9 -> mastery 4)
            
        finally:
            db.close()

class TestCuratorSkillIntegration:
    """Test curator analysis integration with skill tracking"""
    
    def test_process_curator_analysis(self, setup_test_db):
        """Test processing curator analysis into skill history"""
        db = TestingSessionLocal()
        try:
            # Create a test user
            user = User(username="test_curator_integration")
            db.add(user)
            db.commit()
            
            # Mock curator analysis
            curator_analysis = {
                "skills": ["variable_declaration", "react_hooks", "sql_queries"],
                "mistakes": ["forgot semicolon"],
                "openQuestions": ["how does hoisting work"],
                "nextSteps": ["practice more"],
                "confidence": 0.6
            }
            
            # Process the analysis
            results = process_curator_analysis(db, str(user.id), curator_analysis)
            
            # Verify results
            assert results["skill_histories_created"] == 3
            assert len(results["skills_updated"]) == 3
            
            # Check skill history was created
            skill_histories = db.query(SkillHistory).filter(SkillHistory.id_user == user.id).all()
            assert len(skill_histories) == 3
            
            # Check skills were created with proper domains
            skill_names = [sh.skill.name for sh in skill_histories]
            assert "variable_declaration" in skill_names
            assert "react_hooks" in skill_names
            assert "sql_queries" in skill_names
            
        finally:
            db.close()
    
    def test_get_user_skill_progression(self, setup_test_db):
        """Test retrieving user skill progression"""
        db = TestingSessionLocal()
        try:
            # Create a test user with skill history
            user = User(username="test_progression_user")
            db.add(user)
            db.commit()
            
            # Add some skill history
            update_skill_history(db, str(user.id), "javascript_functions", 0.8, "SYNTAX")
            update_skill_history(db, str(user.id), "react_components", 0.6, "FRAMEWORKS")
            
            # Get progression
            progression = get_user_skill_progression(db, str(user.id))
            
            assert len(progression) == 2
            
            # Verify structure
            for entry in progression:
                assert "skill_name" in entry
                assert "domain" in entry
                assert "mastery_level" in entry
                assert "snapshot_date" in entry
                
        finally:
            db.close()

class TestSkillTrackingAPI:
    """Test skill tracking through API endpoints"""
    
    def test_curator_analyze_with_skill_tracking(self, setup_test_db, setup_curator_agent):
        """Test curator analyze endpoint creates skill history"""
        
        # Use conversation data from fixtures
        conversation = JUNIOR_CONVERSATIONS[0]  # JavaScript Variable Declaration
        mock_response = json.dumps(conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            request_data = {
                "user_message": conversation["conversation"]["user_message"],
                "mentor_response": conversation["conversation"]["mentor_response"],
                "user_id": "test_skill_api_user"
            }
            
            response = client.post("/curator/analyze", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have skill tracking results
            assert "skill_tracking" in data
            assert data["skill_tracking"] is not None
            assert "skills_updated" in data["skill_tracking"]
            assert "skill_histories_created" in data["skill_tracking"]
            
            # Should have created skill histories
            assert data["skill_tracking"]["skill_histories_created"] > 0
    
    def test_get_user_skills_endpoint(self, setup_test_db, setup_curator_agent):
        """Test the GET /curator/user/{user_id}/skills endpoint"""
        
        # First, create some skill data via curator analysis
        conversation = JUNIOR_CONVERSATIONS[1]  # React Hook conversation
        mock_response = json.dumps(conversation["expected_curator_output"])
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            # Create skill data
            request_data = {
                "user_message": conversation["conversation"]["user_message"],
                "mentor_response": conversation["conversation"]["mentor_response"],
                "user_id": "test_skills_endpoint_user"
            }
            
            analyze_response = client.post("/curator/analyze", json=request_data)
            assert analyze_response.status_code == 200
            
            # Now get the skills
            skills_response = client.get("/curator/user/test_skills_endpoint_user/skills")
            assert skills_response.status_code == 200
            
            data = skills_response.json()
            
            # Verify response structure
            assert "user_id" in data
            assert "total_skills_tracked" in data
            assert "skill_progression" in data
            assert "skills_summary" in data
            assert "domains_summary" in data
            
            # Should have tracked some skills
            assert data["total_skills_tracked"] > 0
            assert len(data["skill_progression"]) > 0
    
    def test_skill_mastery_level_calculation(self, setup_test_db):
        """Test confidence to mastery level conversion"""
        db = TestingSessionLocal()
        try:
            user = User(username="test_mastery_user")
            db.add(user)
            db.commit()
            
            # Test different confidence levels
            test_cases = [
                (0.0, 1),   # Very low confidence -> mastery level 1
                (0.25, 2),  # Low confidence -> mastery level 2  
                (0.5, 3),   # Medium confidence -> mastery level 3
                (0.75, 4),  # High confidence -> mastery level 4
                (1.0, 5),   # Very high confidence -> mastery level 5
            ]
            
            for confidence, expected_mastery in test_cases:
                skill_name = f"test_skill_confidence_{confidence}"
                skill_history = update_skill_history(db, str(user.id), skill_name, confidence)
                assert skill_history.mastery_level == expected_mastery, \
                    f"Confidence {confidence} should map to mastery level {expected_mastery}"
                
        finally:
            db.close()

class TestSkillDomainMapping:
    """Test skill to domain mapping logic"""
    
    def test_skill_domain_classification(self, setup_test_db):
        """Test that skills are correctly classified into domains"""
        db = TestingSessionLocal()
        try:
            user = User(username="test_domain_user")
            db.add(user)
            db.commit()
            
            # Test skill domain mappings
            test_mappings = [
                ("variable_declaration", "SYNTAX"),
                ("react_hooks", "FRAMEWORKS"),
                ("sql_queries", "DATABASES"),
                ("error_handling", "DEBUGGING"),
                ("system_design", "ARCHITECTURE"),
            ]
            
            for skill_name, expected_domain in test_mappings:
                skill = create_or_update_skill(db, skill_name, domain_name=expected_domain)
                assert skill.domain.name == expected_domain, \
                    f"Skill '{skill_name}' should be in domain '{expected_domain}'"
                    
        finally:
            db.close()
    
    def test_skill_progression_summary(self, setup_test_db):
        """Test skill progression summary calculations"""
        db = TestingSessionLocal()
        try:
            user = User(username="test_summary_user")
            db.add(user)
            db.commit()
            
            # Create skills in different domains with different mastery levels
            update_skill_history(db, str(user.id), "javascript_variables", 0.8, "SYNTAX")     # mastery 4
            update_skill_history(db, str(user.id), "javascript_functions", 0.6, "SYNTAX")     # mastery 3
            update_skill_history(db, str(user.id), "react_hooks", 0.4, "FRAMEWORKS")         # mastery 2
            
            # Get progression
            progression = get_user_skill_progression(db, str(user.id))
            
            # Calculate summary (simulating API logic)
            skills_summary = {}
            domains_summary = {}
            
            for entry in progression:
                skill_name = entry["skill_name"]
                domain = entry["domain"]
                mastery_level = entry["mastery_level"]
                
                skills_summary[skill_name] = {
                    "mastery_level": mastery_level,
                    "domain": domain
                }
                
                if domain not in domains_summary:
                    domains_summary[domain] = {"skills_count": 0, "total_mastery": 0}
                domains_summary[domain]["skills_count"] += 1
                domains_summary[domain]["total_mastery"] += mastery_level
            
            # Verify summary calculations
            assert "SYNTAX" in domains_summary
            assert domains_summary["SYNTAX"]["skills_count"] == 2
            assert domains_summary["SYNTAX"]["total_mastery"] == 7  # 4 + 3
            
            assert "FRAMEWORKS" in domains_summary
            assert domains_summary["FRAMEWORKS"]["skills_count"] == 1
            assert domains_summary["FRAMEWORKS"]["total_mastery"] == 2
            
        finally:
            db.close()

class TestCompleteWorkflow:
    """Test the complete curator to skill tracking workflow"""
    
    def test_complete_conversation_to_skill_tracking_workflow(self, setup_test_db, setup_curator_agent):
        """Test the complete workflow from conversation to skill database storage"""
        
        # Step 1: Simulate a conversation between user and mentor
        user_message = "I'm having trouble with React useState. The state isn't updating when I click the button."
        mentor_response = "Great question! Let's think about how React state updates work. What do you think might be happening with the state update?"
        
        # Expected curator analysis (this would normally come from the AI)
        expected_analysis = {
            "skills": ["react_hooks", "useState", "state_updates", "event_handling"],
            "mistakes": ["missing event handler", "state update misunderstanding"],
            "openQuestions": ["how React batching works", "async state updates"],
            "nextSteps": ["practice functional state updates", "review React state concepts"],
            "confidence": 0.4  # Junior level understanding
        }
        
        mock_response = json.dumps(expected_analysis)
        
        with CuratorTestHelper.mock_blackbox_api(mock_response):
            # Step 2: Call curator analysis API
            request_data = {
                "user_message": user_message,
                "mentor_response": mentor_response,
                "user_id": "workflow_test_user"
            }
            
            response = client.post("/curator/analyze", json=request_data)
            
            # Step 3: Verify curator analysis response
            if response.status_code != 200:
                print(f"API Error Response: {response.json()}")
            assert response.status_code == 200
            data = response.json()
            
            assert data["skills"] == expected_analysis["skills"]
            assert data["confidence"] == expected_analysis["confidence"]
            assert "skill_tracking" in data
            assert data["skill_tracking"]["skill_histories_created"] == 4  # 4 skills
            
            # Step 4: Verify skills were stored in database
            skills_response = client.get("/curator/user/workflow_test_user/skills")
            assert skills_response.status_code == 200
            
            skills_data = skills_response.json()
            assert skills_data["total_skills_tracked"] == 4
            
            # Step 5: Verify skill domains were correctly assigned
            skills_summary = skills_data["skills_summary"]
            assert "react_hooks" in skills_summary
            assert "useState" in skills_summary
            assert skills_summary["react_hooks"]["domain"] == "FRAMEWORKS"
            
            # Step 6: Verify mastery levels calculated correctly
            # Confidence 0.4 should map to mastery level 2
            for skill_name in ["react_hooks", "useState", "state_updates", "event_handling"]:
                assert skills_summary[skill_name]["mastery_level"] == 2
            
            # Step 7: Test skill progression over time (simulate another analysis)
            # Higher confidence this time
            improved_analysis = expected_analysis.copy()
            improved_analysis["confidence"] = 0.75  # Improved understanding
            
            mock_improved_response = json.dumps(improved_analysis)
            
            with CuratorTestHelper.mock_blackbox_api(mock_improved_response):
                response2 = client.post("/curator/analyze", json=request_data)
                assert response2.status_code == 200
                
                # Get updated skills
                skills_response2 = client.get("/curator/user/workflow_test_user/skills")
                skills_data2 = skills_response2.json()
                
                # Should show improved mastery (confidence 0.75 -> mastery level 4)
                skills_summary2 = skills_data2["skills_summary"]
                for skill_name in ["react_hooks", "useState", "state_updates", "event_handling"]:
                    assert skills_summary2[skill_name]["mastery_level"] == 4

if __name__ == "__main__":
    pytest.main(["-v", __file__])