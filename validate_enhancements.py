#!/usr/bin/env python3
"""
Validation script for PR #10 enhancements
Tests all the improvements made to the reference tables implementation
"""

import sys
import traceback

def test_imports():
    """Test that all imports work correctly"""
    try:
        print("🔍 Testing imports...")
        
        # Test database model imports
        from backend.database import (
            Base, RefLanguage, RefIntent, Interaction, User, Conversation,
            get_db, SessionLocal
        )
        
        # Test database operations imports
        from backend.database_operations import (
            create_or_get_language, create_or_get_intent,
            get_all_languages, get_all_intents, populate_reference_data
        )
        
        print("✅ All imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_model_structure():
    """Test that models have the expected structure"""
    try:
        print("🔍 Testing model structure...")
        
        from backend.database.models import RefLanguage, RefIntent, Interaction
        
        # Test RefLanguage model
        assert RefLanguage.__tablename__ == "ref_languages"
        assert hasattr(RefLanguage, '__table_args__'), "RefLanguage should have constraints"
        
        # Test RefIntent model
        assert RefIntent.__tablename__ == "ref_intents"
        
        # Test Interaction model
        assert hasattr(Interaction, '__table_args__'), "Interaction should have indexes"
        
        # Test that deprecated fields are removed
        interaction_cols = [col.name for col in Interaction.__table__.columns]
        assert 'user_intent' not in interaction_cols, "user_intent should be removed"
        assert 'programming_language' not in interaction_cols, "programming_language should be removed"
        assert 'intent_id' in interaction_cols, "intent_id should exist"
        assert 'language_id' in interaction_cols, "language_id should exist"
        
        print("✅ Model structure validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Model structure validation failed: {e}")
        traceback.print_exc()
        return False

def test_indexes():
    """Test that indexes are properly defined"""
    try:
        print("🔍 Testing database indexes...")
        
        from backend.database.models import Interaction
        from sqlalchemy import Index
        
        # Get table args (should contain indexes)
        table_args = Interaction.__table_args__
        
        # Check that we have the expected indexes
        index_names = []
        for arg in table_args:
            if isinstance(arg, Index):
                index_names.append(arg.name)
        
        expected_indexes = [
            'ix_interaction_intent_id',
            'ix_interaction_language_id', 
            'ix_interaction_domain_id'
        ]
        
        for expected_index in expected_indexes:
            assert expected_index in index_names, f"Missing index: {expected_index}"
        
        print("✅ Database indexes validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Database indexes validation failed: {e}")
        traceback.print_exc()
        return False

def test_constraints():
    """Test that validation constraints are properly defined"""
    try:
        print("🔍 Testing validation constraints...")
        
        from backend.database.models import RefLanguage
        from sqlalchemy import CheckConstraint
        
        # Get table args (should contain check constraints)
        table_args = RefLanguage.__table_args__
        
        # Check that we have a check constraint
        has_check_constraint = False
        for arg in table_args:
            if isinstance(arg, CheckConstraint):
                has_check_constraint = True
                assert arg.name == 'valid_language_category', "Wrong constraint name"
                break
        
        assert has_check_constraint, "RefLanguage should have a check constraint"
        
        print("✅ Validation constraints passed")
        return True
        
    except Exception as e:
        print(f"❌ Validation constraints failed: {e}")
        traceback.print_exc()
        return False

def test_case_insensitive_function():
    """Test case-insensitive language lookup function"""
    try:
        print("🔍 Testing case-insensitive function...")
        
        from backend.database_operations import create_or_get_language
        from sqlalchemy import func
        import inspect
        
        # Check function signature
        sig = inspect.signature(create_or_get_language)
        assert 'name' in sig.parameters, "Function should have 'name' parameter"
        assert 'category' in sig.parameters, "Function should have 'category' parameter"
        
        # Check function source contains case-insensitive logic
        source = inspect.getsource(create_or_get_language)
        assert 'func.lower' in source, "Function should use func.lower for case-insensitive lookup"
        assert '.title()' in source, "Function should normalize names to title case"
        
        print("✅ Case-insensitive function validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Case-insensitive function validation failed: {e}")
        traceback.print_exc()
        return False

def test_package_exports():
    """Test that package exports are properly defined"""
    try:
        print("🔍 Testing package exports...")
        
        from backend.database import __all__
        
        expected_exports = [
            'Base', 'SessionLocal', 'engine', 'create_engine', 'create_tables', 'get_db',
            'User', 'Conversation', 'Interaction', 'MemoryEntry',
            'Skill', 'SkillHistory', 'RefDomain', 'RefLanguage', 'RefIntent',
            'Flashcard', 'ReviewSession', 'Session'
        ]
        
        for expected in expected_exports:
            assert expected in __all__, f"Missing export: {expected}"
        
        print("✅ Package exports validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Package exports validation failed: {e}")
        traceback.print_exc()
        return False

def test_relationships():
    """Test that relationships are properly defined"""
    try:
        print("🔍 Testing model relationships...")
        
        from backend.database.models import RefLanguage, RefIntent, Interaction
        
        # Test RefLanguage relationships
        assert hasattr(RefLanguage, 'interactions'), "RefLanguage should have interactions relationship"
        
        # Test RefIntent relationships  
        assert hasattr(RefIntent, 'interactions'), "RefIntent should have interactions relationship"
        
        # Test Interaction relationships
        assert hasattr(Interaction, 'intent'), "Interaction should have intent relationship"
        assert hasattr(Interaction, 'language'), "Interaction should have language relationship"
        
        print("✅ Model relationships validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Model relationships validation failed: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all validation tests"""
    print("🚀 Starting PR #10 enhancements validation...\n")
    
    tests = [
        test_imports,
        test_model_structure,
        test_indexes,
        test_constraints,
        test_case_insensitive_function,
        test_package_exports,
        test_relationships
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Empty line for readability
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 60)
    print(f"📊 VALIDATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL ENHANCEMENTS VALIDATED SUCCESSFULLY!")
        print("\n✨ PR #10 enhancements summary:")
        print("   ✅ Database indexes added for performance")
        print("   ✅ Backward compatibility fields removed")
        print("   ✅ Validation constraints implemented")
        print("   ✅ Case-insensitive language lookup")
        print("   ✅ Package exports organized with __all__")
        print("   ✅ Comprehensive test coverage added")
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)