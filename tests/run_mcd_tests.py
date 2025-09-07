#!/usr/bin/env python3
"""
MCD Database Schema Test Runner
Based on backend/database/doc/dev_mentor_ai.mcd

Runs comprehensive tests for:
1. All database tables and their fields
2. All relationships and their cardinalities  
3. All constraints and business rules
4. Data integrity and referential constraints
5. Cascade behaviors and foreign keys

Usage:
    python3 tests/run_mcd_tests.py [options]
    
Options:
    --comprehensive     Run all test suites
    --schema-only       Run only basic schema tests
    --relationships     Run only relationship tests
    --business-rules    Run only business rules and integrity tests
    --verbose          Show detailed test output
    --coverage         Generate test coverage report
    --database-url     Specify test database URL
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_test_environment():
    """Setup test environment and verify prerequisites"""
    print("🔧 Setting up MCD test environment...")
    
    # Check if test database URL is configured
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if not test_db_url:
        print("❌ TEST_DATABASE_URL environment variable not set")
        print("   Set it to: postgresql://postgres:password@localhost:5432/test_db_name")
        return False
    
    print(f"✅ Test database configured: {test_db_url}")
    
    # Check required dependencies
    try:
        import pytest
        import sqlalchemy
        from backend.database import Base
        print("✅ All required dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install pytest sqlalchemy")
        return False

def run_schema_tests(verbose=False):
    """Run comprehensive schema tests"""
    print("\n📋 Running Database Schema Tests...")
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/test_database_schema_comprehensive.py",
        "-v" if verbose else "-q"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_relationship_tests(verbose=False):
    """Run detailed relationship tests"""
    print("\n🔗 Running Database Relationship Tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_mcd_relationships_detailed.py", 
        "-v" if verbose else "-q"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_business_rules_tests(verbose=False):
    """Run business rules and integrity tests"""
    print("\n⚖️  Running Business Rules and Data Integrity Tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_mcd_business_rules_integrity.py",
        "-v" if verbose else "-q"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_coverage_report():
    """Generate test coverage report"""
    print("\n📊 Generating Test Coverage Report...")
    
    # Run all MCD tests with coverage
    cmd = [
        "python", "-m", "pytest",
        "tests/test_database_schema_comprehensive.py",
        "tests/test_mcd_relationships_detailed.py", 
        "tests/test_mcd_business_rules_integrity.py",
        "--cov=backend.database",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode == 0:
        print("✅ Coverage report generated in htmlcov/ directory")
    else:
        print("❌ Coverage report generation failed")
    
    return result.returncode == 0

def run_comprehensive_tests(verbose=False, coverage=False):
    """Run all MCD-related tests"""
    print("\n🚀 Running Comprehensive MCD Database Tests...")
    print("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    # Run each test suite
    if run_schema_tests(verbose):
        success_count += 1
        print("✅ Schema tests passed")
    else:
        print("❌ Schema tests failed")
    
    if run_relationship_tests(verbose):
        success_count += 1
        print("✅ Relationship tests passed")
    else:
        print("❌ Relationship tests failed")
        
    if run_business_rules_tests(verbose):
        success_count += 1
        print("✅ Business rules tests passed")
    else:
        print("❌ Business rules tests failed")
    
    # Generate coverage report if requested
    if coverage:
        if not run_coverage_report():
            print("⚠️  Coverage report generation had issues")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Summary: {success_count}/{total_tests} test suites passed")
    
    if success_count == total_tests:
        print("🎉 All MCD database tests passed successfully!")
        print("\n✅ Your database implementation matches the MCD schema:")
        print("   • All tables and fields are correctly implemented")
        print("   • All relationships and cardinalities work as designed")  
        print("   • All constraints and business rules are enforced")
        print("   • Data integrity and referential constraints are working")
        return True
    else:
        print("🔧 Some tests failed - database implementation needs attention")
        print("\n❌ Issues found in database implementation:")
        print("   • Check failed tests for specific constraint violations")
        print("   • Verify foreign key relationships match MCD design")
        print("   • Ensure all required fields and constraints are implemented")
        return False

def validate_mcd_compliance():
    """Validate that database implementation complies with MCD design"""
    print("\n🔍 Validating MCD Compliance...")
    
    # Set a temporary DATABASE_URL for validation if not set
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql://temp:temp@localhost:5432/temp"
    
    try:
        from backend.database import (
            User, Conversation, Interaction, Skill, SkillHistory, RefDomain
        )
        
        # Check that currently implemented entities exist (partial MCD implementation)
        current_entities = [
            "User", "Conversation", "Interaction", "Skill", "SkillHistory", "RefDomain"
        ]
        
        implemented_entities = [
            User.__name__, Conversation.__name__, Interaction.__name__,
            Skill.__name__, SkillHistory.__name__, RefDomain.__name__
        ]
        
        # MCD entities not yet implemented
        missing_mcd_entities = [
            "Session", "Flashcard", "ReviewSession", "RefLanguage", "RefIntent"
        ]
        
        print("✅ Currently implemented entities:", implemented_entities)
        print("⚠️  MCD entities not yet implemented:", missing_mcd_entities)
        print("   Note: This is a partial MCD implementation")
        
        # Check key relationships exist in current implementation
        relationship_checks = [
            (Conversation, "user_id", "User owns Conversations"),
            (Interaction, "conversation_id", "Conversation contains Interactions"),
            (Skill, "id_domain", "BELONG_TO relationship - Skill belongs to Domain"),
            (SkillHistory, "id_user", "TRACK relationship - SkillHistory tracks User"),
            (SkillHistory, "id_skill", "TRACK relationship - SkillHistory tracks Skill"),
        ]
        
        for entity, field, description in relationship_checks:
            if hasattr(entity, field):
                print(f"✅ {description}")
            else:
                print(f"❌ Missing field {entity.__name__}.{field} for {description}")
                return False
        
        print("✅ Current implementation relationships validated")
        print("📋 Next steps: Implement remaining MCD entities for full compliance")
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import database models: {e}")
        return False

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="MCD Database Schema Test Runner")
    parser.add_argument("--comprehensive", action="store_true", help="Run all test suites")
    parser.add_argument("--schema-only", action="store_true", help="Run only schema tests")
    parser.add_argument("--relationships", action="store_true", help="Run only relationship tests")
    parser.add_argument("--business-rules", action="store_true", help="Run only business rules tests")
    parser.add_argument("--verbose", action="store_true", help="Show detailed test output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--database-url", help="Override test database URL")
    parser.add_argument("--validate-only", action="store_true", help="Only validate MCD compliance")
    
    args = parser.parse_args()
    
    # Override database URL if provided
    if args.database_url:
        os.environ["TEST_DATABASE_URL"] = args.database_url
    
    print("🗄️  MCD Database Schema Test Runner")
    print("Based on: backend/database/doc/dev_mentor_ai.mcd")
    print("=" * 60)
    
    # Validate MCD compliance first
    if not validate_mcd_compliance():
        print("\n❌ MCD compliance validation failed")
        print("   Fix database model implementation before running tests")
        return 1
    
    if args.validate_only:
        print("\n✅ MCD compliance validation passed")
        return 0
    
    # Setup test environment
    if not setup_test_environment():
        return 1
    
    success = False
    
    # Run requested tests
    if args.comprehensive or not any([args.schema_only, args.relationships, args.business_rules]):
        success = run_comprehensive_tests(args.verbose, args.coverage)
    else:
        if args.schema_only:
            success = run_schema_tests(args.verbose)
        elif args.relationships:
            success = run_relationship_tests(args.verbose)
        elif args.business_rules:
            success = run_business_rules_tests(args.verbose)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)