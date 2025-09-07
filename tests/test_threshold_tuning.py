#!/usr/bin/env python3
"""
Test different similarity thresholds to find the optimal setting
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from memory_store import ConversationMemory

def test_thresholds():
    """Test various similarity thresholds to see quality vs quantity"""
    
    store = ConversationMemory()
    
    # Add test data
    test_data = [
        ("user1", "How do I fix React useState hook?", "Let's debug this step by step..."),
        ("user1", "React component won't render", "What error do you see in console?"),
        ("user1", "useState not updating state", "Remember useState is async..."),
        ("user1", "Python list comprehension help", "Let's break down the syntax..."),
        ("user1", "JavaScript array methods", "Let's explore map, filter, reduce..."),
        ("user1", "My cat is sleeping", "That's nice but not programming related..."),
    ]
    
    print("Adding test conversations...")
    for user, msg, response in test_data:
        store.add_interaction(user, msg, response, "strict")
    
    # Test query
    query = "React state management issues"
    print(f"\nTesting query: '{query}'\n")
    
    thresholds = [0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8]
    
    for threshold in thresholds:
        print(f"🎯 Threshold: {threshold}")
        
        memories = store.find_similar_interactions(
            query, "user1", 
            limit=10, 
            similarity_threshold=threshold
        )
        
        if memories:
            print(f"   Found {len(memories)} matches:")
            for i, memory in enumerate(memories):
                msg = memory['user_message']
                sim = memory['similarity']
                relevance = "🔥 VERY" if sim > 0.8 else "✅ GOOD" if sim > 0.6 else "⚠️  OK" if sim > 0.4 else "❌ POOR"
                print(f"   {i+1}. {relevance} ({sim:.3f}) {msg}")
        else:
            print("   No matches found")
        print()

if __name__ == "__main__":
    test_thresholds()