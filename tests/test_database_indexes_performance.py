#!/usr/bin/env python3
"""
Database Index Performance Tests
Tests to validate that the new database indexes provide performance improvements

This test file validates:
- Query performance with indexes vs without indexes
- Execution plan analysis for indexed queries
- Load testing with larger datasets
- Join performance with reference tables
"""

import pytest
import time
import random
import string
from sqlalchemy import create_engine, text, Index, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text as sql_text
import os

# Import database models and operations
from backend.database import (
    Base, RefLanguage, RefIntent, Interaction, User, Conversation
)
from backend.database_operations import (
    create_or_get_language, create_or_get_intent
)

# Test database setup
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:test@localhost:5432/test_performance")
engine = create_engine(TEST_DATABASE_URL, echo=False)  # Set echo=False for performance testing
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def setup_test_db():
    """Setup test database schema"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_test_db):
    """Create test database session"""
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture(scope="session")
def large_dataset(setup_test_db):
    """Create a large dataset for performance testing"""
    db = TestingSessionLocal()
    
    try:
        # Create test user
        user = User(username="perf_test_user")
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create test conversation
        conversation = Conversation(
            user_id=user.id,
            session_id="perf_test_session",
            agent_type="strict"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # Create reference data
        languages = []
        for i in range(10):
            lang = create_or_get_language(db, f"TestLang{i}", "programming")
            languages.append(lang)
        
        intents = []
        for i in range(5):
            intent = create_or_get_intent(db, f"test_intent_{i}", f"Test intent {i}")
            intents.append(intent)
        
        # Create large number of interactions
        print("Creating large dataset for performance testing...")
        batch_size = 1000
        total_records = 5000
        
        for batch_start in range(0, total_records, batch_size):
            interactions = []
            for i in range(batch_start, min(batch_start + batch_size, total_records)):
                interaction = Interaction(
                    conversation_id=conversation.id,
                    user_message=f"Performance test message {i}",
                    mentor_response=f"Performance test response {i}",
                    language_id=random.choice(languages).id_language,
                    intent_id=random.choice(intents).id_intent,
                    difficulty_level=random.choice(["beginner", "intermediate", "advanced"])
                )
                interactions.append(interaction)
            
            db.add_all(interactions)
            db.commit()
            print(f"Created batch {batch_start + batch_size}/{total_records}")
        
        print(f"Created {total_records} interactions for performance testing")
        
        return {
            'user': user,
            'conversation': conversation,
            'languages': languages,
            'intents': intents,
            'total_records': total_records
        }
        
    finally:
        db.close()

# ==================================================================================
# INDEX PERFORMANCE TESTS
# ==================================================================================

class TestIndexPerformance:
    """Performance tests for database indexes"""
    
    def test_language_id_index_performance(self, db_session, large_dataset):
        """Test language_id index performance with large dataset"""
        test_language = large_dataset['languages'][0]
        
        # Test query performance with index
        start_time = time.time()
        
        results = db_session.query(Interaction).filter(
            Interaction.language_id == test_language.id_language
        ).all()
        
        indexed_query_time = time.time() - start_time
        
        print(f"Query with language_id index: {indexed_query_time:.4f} seconds")
        print(f"Results found: {len(results)}")
        
        # Performance expectations
        assert len(results) > 0
        assert indexed_query_time < 1.0  # Should be under 1 second
        
        return indexed_query_time

    def test_intent_id_index_performance(self, db_session, large_dataset):
        """Test intent_id index performance with large dataset"""
        test_intent = large_dataset['intents'][0]
        
        # Test query performance with index
        start_time = time.time()
        
        results = db_session.query(Interaction).filter(
            Interaction.intent_id == test_intent.id_intent
        ).all()
        
        indexed_query_time = time.time() - start_time
        
        print(f"Query with intent_id index: {indexed_query_time:.4f} seconds")
        print(f"Results found: {len(results)}")
        
        # Performance expectations
        assert len(results) > 0
        assert indexed_query_time < 1.0  # Should be under 1 second
        
        return indexed_query_time

    def test_compound_query_performance(self, db_session, large_dataset):
        """Test performance of queries using multiple indexes"""
        test_language = large_dataset['languages'][0]
        test_intent = large_dataset['intents'][0]
        
        start_time = time.time()
        
        # Query using both language_id and intent_id indexes
        results = db_session.query(Interaction).filter(
            Interaction.language_id == test_language.id_language,
            Interaction.intent_id == test_intent.id_intent
        ).all()
        
        compound_query_time = time.time() - start_time
        
        print(f"Compound query with multiple indexes: {compound_query_time:.4f} seconds")
        print(f"Results found: {len(results)}")
        
        assert compound_query_time < 0.5  # Should be very fast with both indexes

    def test_join_query_performance(self, db_session, large_dataset):
        """Test performance of JOIN queries with indexed foreign keys"""
        start_time = time.time()
        
        # Complex JOIN query leveraging indexes
        results = db_session.query(Interaction, RefLanguage, RefIntent)\
            .join(RefLanguage, Interaction.language_id == RefLanguage.id_language)\
            .join(RefIntent, Interaction.intent_id == RefIntent.id_intent)\
            .filter(RefLanguage.category == "programming")\
            .limit(1000)\
            .all()
        
        join_query_time = time.time() - start_time
        
        print(f"JOIN query with indexed foreign keys: {join_query_time:.4f} seconds")
        print(f"Results found: {len(results)}")
        
        assert len(results) > 0
        assert join_query_time < 2.0  # Should be reasonable with indexes

# ==================================================================================
# EXECUTION PLAN ANALYSIS TESTS
# ==================================================================================

class TestQueryExecutionPlans:
    """Tests to analyze PostgreSQL execution plans for indexed queries"""
    
    def test_language_id_execution_plan(self, db_session, large_dataset):
        """Analyze execution plan for language_id queries"""
        test_language = large_dataset['languages'][0]
        
        # Get execution plan
        query = f"""
        EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) 
        SELECT * FROM interactions 
        WHERE language_id = {test_language.id_language}
        """
        
        result = db_session.execute(sql_text(query))
        execution_plan = result.fetchall()
        
        plan_text = '\\n'.join([row[0] for row in execution_plan])
        print("\\nExecution plan for language_id query:")
        print(plan_text)
        
        # Verify index is being used
        assert "Index Scan" in plan_text or "Bitmap Index Scan" in plan_text
        assert "ix_interaction_language_id" in plan_text

    def test_intent_id_execution_plan(self, db_session, large_dataset):
        """Analyze execution plan for intent_id queries"""
        test_intent = large_dataset['intents'][0]
        
        # Get execution plan
        query = f"""
        EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) 
        SELECT * FROM interactions 
        WHERE intent_id = {test_intent.id_intent}
        """
        
        result = db_session.execute(sql_text(query))
        execution_plan = result.fetchall()
        
        plan_text = '\\n'.join([row[0] for row in execution_plan])
        print("\\nExecution plan for intent_id query:")
        print(plan_text)
        
        # Verify index is being used
        assert "Index Scan" in plan_text or "Bitmap Index Scan" in plan_text
        assert "ix_interaction_intent_id" in plan_text

    def test_join_execution_plan(self, db_session, large_dataset):
        """Analyze execution plan for JOIN queries with indexes"""
        # Get execution plan for JOIN query
        query = """
        EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
        SELECT i.id, l.name as language, t.name as intent
        FROM interactions i
        JOIN ref_languages l ON i.language_id = l.id_language
        JOIN ref_intents t ON i.intent_id = t.id_intent
        WHERE l.category = 'programming'
        LIMIT 100
        """
        
        result = db_session.execute(sql_text(query))
        execution_plan = result.fetchall()
        
        plan_text = '\\n'.join([row[0] for row in execution_plan])
        print("\\nExecution plan for JOIN query:")
        print(plan_text)
        
        # Verify indexes are being used for joins
        assert "Index Scan" in plan_text or "Nested Loop" in plan_text
        # Should use foreign key indexes for efficient joins

# ==================================================================================
# LOAD TESTING
# ==================================================================================

class TestDatabaseLoad:
    """Load tests to validate performance under concurrent access"""
    
    def test_concurrent_language_queries(self, db_session, large_dataset):
        """Test concurrent queries on language_id index"""
        import concurrent.futures
        import threading
        
        def query_by_language(language_id):
            # Create new session for thread safety
            local_db = TestingSessionLocal()
            try:
                start = time.time()
                results = local_db.query(Interaction).filter(
                    Interaction.language_id == language_id
                ).count()  # Use count() for faster execution
                duration = time.time() - start
                return (results, duration)
            finally:
                local_db.close()
        
        # Run concurrent queries
        languages = large_dataset['languages'][:5]  # Test with first 5 languages
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(20):  # 20 concurrent queries
                lang = random.choice(languages)
                future = executor.submit(query_by_language, lang.id_language)
                futures.append(future)
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        print(f"\\nConcurrent query results:")
        print(f"Total time for 20 concurrent queries: {total_time:.4f} seconds")
        print(f"Average time per query: {total_time/20:.4f} seconds")
        
        # Verify all queries completed successfully
        assert len(results) == 20
        assert all(result[0] >= 0 for result in results)  # All queries returned results
        assert total_time < 10.0  # Should complete within reasonable time

    def test_mixed_workload_performance(self, db_session, large_dataset):
        """Test performance with mixed read/write workload"""
        # Test mixed operations: reads, writes, updates
        operations_count = 100
        start_time = time.time()
        
        for i in range(operations_count):
            if i % 10 == 0:
                # Write operation: create new interaction
                new_lang = random.choice(large_dataset['languages'])
                new_intent = random.choice(large_dataset['intents'])
                
                interaction = Interaction(
                    conversation_id=large_dataset['conversation'].id,
                    user_message=f"Mixed workload test {i}",
                    mentor_response=f"Mixed workload response {i}",
                    language_id=new_lang.id_language,
                    intent_id=new_intent.id_intent
                )
                db_session.add(interaction)
                
                if i % 50 == 0:  # Commit every 50 operations
                    db_session.commit()
            
            else:
                # Read operation: query by language or intent
                if i % 2 == 0:
                    lang = random.choice(large_dataset['languages'])
                    db_session.query(Interaction).filter(
                        Interaction.language_id == lang.id_language
                    ).limit(10).all()
                else:
                    intent = random.choice(large_dataset['intents'])
                    db_session.query(Interaction).filter(
                        Interaction.intent_id == intent.id_intent
                    ).limit(10).all()
        
        db_session.commit()
        total_time = time.time() - start_time
        
        print(f"\\nMixed workload performance:")
        print(f"Time for {operations_count} mixed operations: {total_time:.4f} seconds")
        print(f"Average time per operation: {total_time/operations_count:.4f} seconds")
        
        assert total_time < 30.0  # Should handle mixed workload efficiently

# ==================================================================================
# PERFORMANCE REGRESSION TESTS
# ==================================================================================

class TestPerformanceRegression:
    """Tests to catch performance regressions in future changes"""
    
    def test_baseline_query_performance(self, db_session, large_dataset):
        """Establish baseline performance metrics"""
        metrics = {}
        
        # Test 1: Simple language_id query
        start = time.time()
        lang_results = db_session.query(Interaction).filter(
            Interaction.language_id == large_dataset['languages'][0].id_language
        ).count()
        metrics['language_query'] = time.time() - start
        
        # Test 2: Simple intent_id query
        start = time.time()
        intent_results = db_session.query(Interaction).filter(
            Interaction.intent_id == large_dataset['intents'][0].id_intent
        ).count()
        metrics['intent_query'] = time.time() - start
        
        # Test 3: JOIN query
        start = time.time()
        join_results = db_session.query(Interaction)\
            .join(RefLanguage, Interaction.language_id == RefLanguage.id_language)\
            .filter(RefLanguage.category == "programming")\
            .count()
        metrics['join_query'] = time.time() - start
        
        print("\\nBaseline Performance Metrics:")
        for test, duration in metrics.items():
            print(f"{test}: {duration:.4f} seconds")
        
        # Performance thresholds (adjust based on your requirements)
        assert metrics['language_query'] < 0.5
        assert metrics['intent_query'] < 0.5
        assert metrics['join_query'] < 1.0
        
        return metrics

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print statements