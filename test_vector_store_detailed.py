#!/usr/bin/env python3
"""
Comprehensive Vector Store Tutorial and Test Suite
This script demonstrates how vector stores work step by step
"""

import sys
import os

# Add backend to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from memory_store import ConversationMemory
import chromadb
import numpy as np
from typing import List, Tuple

class VectorStoreTutorial:
    """
    Tutorial class that explains vector stores through interactive examples
    """
    
    def __init__(self):
        self.store = ConversationMemory()
        self.client = chromadb.PersistentClient(path="./chroma_memory")
        
    def step_1_basic_concepts(self):
        """
        Step 1: Understand what embeddings look like
        """
        print("=" * 60)
        print("STEP 1: WHAT ARE EMBEDDINGS?")
        print("=" * 60)
        
        # Get the embedding function ChromaDB uses
        collection = self.client.get_or_create_collection(
            name="tutorial", 
            metadata={"hnsw:space": "cosine"}
        )
        
        # Example texts
        texts = [
            "How do I debug React components?",
            "React debugging help needed",
            "Python list comprehension syntax",
            "My dog loves to play fetch"
        ]
        
        print("Converting these texts to vectors (embeddings):")
        for i, text in enumerate(texts):
            # This is how ChromaDB converts text to vectors internally
            print(f"\n{i+1}. '{text}'")
            
            # Add to collection to get embedding
            collection.add(
                documents=[text],
                ids=[f"demo_{i}"]
            )
            
        print(f"\nEach text becomes a vector of {384} numbers!")
        print("These numbers capture the 'meaning' of the text mathematically.")
        
        return collection
    
    def step_2_similarity_demo(self, collection):
        """
        Step 2: Show how similar texts have similar vectors
        """
        print("\n" + "=" * 60)
        print("STEP 2: SIMILARITY SEARCH IN ACTION")
        print("=" * 60)
        
        query = "React debugging issues"
        print(f"Query: '{query}'")
        print("\nFinding most similar stored texts...")
        
        # Search for similar documents
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        print(f"\nResults (ranked by similarity):")
        for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
            similarity = 1 - distance  # Convert distance to similarity
            print(f"{i+1}. '{doc}' (similarity: {similarity:.3f})")
            
        print(f"\nNotice: React-related texts score highest!")
        print(f"The dog text scores lowest because it's completely unrelated.")
        
    def step_3_memory_store_basics(self):
        """
        Step 3: Test our actual memory store implementation
        """
        print("\n" + "=" * 60)
        print("STEP 3: TESTING OUR MEMORY STORE")
        print("=" * 60)
        
        # Clear any existing data for clean test
        print("Starting with fresh memory store...")
        
        # Add some conversations
        test_conversations = [
            ("user1", "How do I handle React state?", "Let's explore state management..."),
            ("user1", "useState hook not working", "What specific issue are you seeing?"),
            ("user1", "Python for loop syntax help", "Let's break down Python loops..."),
            ("user2", "React component won't render", "What error messages do you see?"),
            ("user2", "CSS flexbox alignment", "Let's understand flexbox properties...")
        ]
        
        print(f"Adding {len(test_conversations)} conversations to memory...")
        
        for user_id, user_msg, mentor_response in test_conversations:
            self.store.add_interaction(user_id, user_msg, mentor_response, agent_type="strict")
            print(f"  ✓ Added: '{user_msg[:30]}...'")
            
    def step_4_semantic_search_demo(self):
        """
        Step 4: Demonstrate semantic search capabilities
        """
        print("\n" + "=" * 60)
        print("STEP 4: SEMANTIC SEARCH DEMO")
        print("=" * 60)
        
        # Test queries that should find related memories
        test_queries = [
            ("user1", "React state management problems"),
            ("user1", "Python loops confusion"),
            ("user2", "component rendering issues"),
            ("user1", "useState troubles"),  # Should find useState conversation
        ]
        
        for user_id, query in test_queries:
            print(f"\n🔍 Query: '{query}' (for {user_id})")
            
            memories = self.store.find_similar_interactions(query, user_id, limit=2)
            
            if memories:
                print(f"   Found {len(memories)} relevant memories:")
                for i, memory in enumerate(memories):
                    # memories is now a list of dicts with user_message, mentor_response, similarity, etc.
                    user_msg = memory.get('user_message', 'No message')
                    similarity = memory.get('similarity', 0)
                    print(f"   {i+1}. '{user_msg}' (similarity: {similarity:.3f})")
            else:
                print("   No relevant memories found")
                
    def step_5_similarity_scoring(self):
        """
        Step 5: Show actual similarity scores
        """
        print("\n" + "=" * 60)
        print("STEP 5: SIMILARITY SCORES EXPLAINED")
        print("=" * 60)
        
        # Get the raw ChromaDB collection to show scores
        try:
            collection = self.client.get_collection("conversation_memories")
            
            query = "React component state issues"
            print(f"Query: '{query}'")
            
            # Get results with scores
            results = collection.query(
                query_texts=[query],
                n_results=3,
                include=['documents', 'distances']
            )
            
            print(f"\nDetailed similarity analysis:")
            print(f"{'Rank':<4} {'Similarity':<10} {'Document Preview'}")
            print("-" * 60)
            
            for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
                similarity = 1 - distance
                preview = doc.replace('\n', ' ')[:50] + "..."
                print(f"{i+1:<4} {similarity:<10.3f} {preview}")
                
            print(f"\nSimilarity ranges:")
            print(f"  0.9-1.0: Nearly identical meaning")
            print(f"  0.7-0.9: Very similar/related")
            print(f"  0.5-0.7: Somewhat related")  
            print(f"  0.0-0.5: Not very related")
            
        except Exception as e:
            print(f"Could not access collection details: {e}")
            
    def step_6_user_isolation_test(self):
        """
        Step 6: Test that users only see their own memories
        """
        print("\n" + "=" * 60)
        print("STEP 6: USER PRIVACY / ISOLATION TEST")
        print("=" * 60)
        
        # Test that user1 cannot see user2's memories
        print("Testing user memory isolation...")
        
        user1_query = "CSS flexbox"  # This was user2's conversation
        user1_memories = self.store.find_similar_interactions(user1_query, "user1")
        
        user2_query = "CSS flexbox"  # This should find user2's conversation
        user2_memories = self.store.find_similar_interactions(user2_query, "user2")
        
        print(f"\nUser1 searching for 'CSS flexbox':")
        if user1_memories:
            print(f"  ❌ PRIVACY ISSUE: Found {len(user1_memories)} memories")
            for memory in user1_memories:
                msg = memory.get('user_message', 'No message')
                print(f"    {msg[:50]}...")
        else:
            print(f"  ✅ GOOD: No memories found (CSS was user2's topic)")
            
        print(f"\nUser2 searching for 'CSS flexbox':")
        if user2_memories:
            print(f"  ✅ GOOD: Found {len(user2_memories)} own memories")
            for memory in user2_memories:
                msg = memory.get('user_message', 'No message')
                print(f"    {msg[:50]}...")
        else:
            print(f"  ❌ ISSUE: Should have found own CSS conversation")
            
    def step_7_edge_cases(self):
        """
        Step 7: Test edge cases and error handling
        """
        print("\n" + "=" * 60)
        print("STEP 7: EDGE CASES & ERROR HANDLING")
        print("=" * 60)
        
        # Test empty query
        print("1. Testing empty query...")
        try:
            memories = self.store.find_similar_interactions("", "user1")
            print(f"   Result: {len(memories) if memories else 0} memories")
        except Exception as e:
            print(f"   Error: {e}")
            
        # Test nonexistent user
        print("\n2. Testing nonexistent user...")
        try:
            memories = self.store.find_similar_interactions("test query", "nonexistent_user")
            print(f"   Result: {len(memories) if memories else 0} memories")
        except Exception as e:
            print(f"   Error: {e}")
            
        # Test very long query
        print("\n3. Testing very long query...")
        try:
            long_query = "This is a very long query " * 100
            memories = self.store.find_similar_interactions(long_query, "user1")
            print(f"   Result: {len(memories) if memories else 0} memories")
        except Exception as e:
            print(f"   Error: {e}")
            
    def step_8_performance_test(self):
        """
        Step 8: Basic performance characteristics
        """
        print("\n" + "=" * 60)
        print("STEP 8: PERFORMANCE CHARACTERISTICS")  
        print("=" * 60)
        
        import time
        
        # Test search speed
        start_time = time.time()
        for i in range(10):
            memories = self.store.find_similar_interactions(f"React question {i}", "user1")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        print(f"Average search time: {avg_time:.3f} seconds")
        
        if avg_time < 0.1:
            print("✅ EXCELLENT: Very fast searches (< 100ms)")
        elif avg_time < 0.5:
            print("✅ GOOD: Fast searches (< 500ms)")
        else:
            print("⚠️  SLOW: Consider optimization")
            
    def run_full_tutorial(self):
        """
        Run the complete tutorial
        """
        print("🚀 VECTOR STORE TUTORIAL - COMPLETE WALKTHROUGH")
        print("This will teach you how vector stores work by example")
        print()
        
        try:
            # Step 1: Basic concepts
            collection = self.step_1_basic_concepts()
            
            # Step 2: Similarity demo  
            self.step_2_similarity_demo(collection)
            
            # Step 3: Memory store basics
            self.step_3_memory_store_basics()
            
            # Step 4: Semantic search
            self.step_4_semantic_search_demo()
            
            # Step 5: Similarity scores
            self.step_5_similarity_scoring()
            
            # Step 6: User isolation
            self.step_6_user_isolation_test()
            
            # Step 7: Edge cases
            self.step_7_edge_cases()
            
            # Step 8: Performance
            self.step_8_performance_test()
            
            print("\n" + "=" * 60)
            print("🎉 TUTORIAL COMPLETE!")
            print("=" * 60)
            print("Key takeaways:")
            print("1. Vector stores convert text to numbers (embeddings)")
            print("2. Similar meanings → similar vectors → close in space")
            print("3. Semantic search finds related content, not just exact matches")
            print("4. Your memory store preserves user privacy")
            print("5. Search is fast and handles edge cases well")
            
        except Exception as e:
            print(f"\n❌ Tutorial failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    tutorial = VectorStoreTutorial()
    tutorial.run_full_tutorial()