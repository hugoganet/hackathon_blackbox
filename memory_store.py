"""
Vector memory store using ChromaDB for conversation memory
Stores and retrieves similar past interactions for personalized mentoring
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
import uuid
import os
import json
from datetime import datetime

class ConversationMemory:
    """
    Manages vector embeddings of conversations for memory-based mentoring
    
    This class:
    1. Creates embeddings of user questions and interactions
    2. Stores them in ChromaDB with metadata
    3. Searches for similar past conversations to inform mentor responses
    """
    
    def __init__(self, persist_directory: str = "./chroma_memory"):
        """
        Initialize the conversation memory system
        
        Args:
            persist_directory: Where to store ChromaDB files (persistent storage)
        """
        # Create the persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB with persistent storage
        # This allows data to survive server restarts
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create or get the collection for storing conversation memories
        self.collection = self.client.get_or_create_collection(
            name="conversation_memories",
            metadata={"description": "User conversation memories for personalized mentoring"}
        )
        
        # Initialize the sentence transformer for creating embeddings
        # This model creates vector representations of text
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print(f"✅ Memory store initialized with {self.collection.count()} existing memories")
    
    def add_interaction(
        self,
        user_id: str,
        user_message: str,
        mentor_response: str,
        agent_type: str,
        programming_language: Optional[str] = None,
        difficulty_level: Optional[str] = "beginner",
        user_intent: Optional[str] = None
    ) -> str:
        """
        Store a new interaction in the memory system
        
        Args:
            user_id: Unique identifier for the user
            user_message: The question/message from the user
            mentor_response: The mentor's response
            agent_type: "normal" or "strict"
            programming_language: Language being discussed (e.g., "javascript")
            difficulty_level: "beginner", "intermediate", "advanced"
            user_intent: Classified intent (e.g., "debugging", "concept_explanation")
            
        Returns:
            memory_id: Unique ID for this memory entry
        """
        
        # Create embedding of the user's message
        # This vector representation allows us to find similar questions later
        embedding = self.embedding_model.encode([user_message])[0].tolist()
        
        # Generate unique memory ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata for filtering and context
        metadata = {
            "user_id": user_id,
            "agent_type": agent_type,
            "timestamp": datetime.utcnow().isoformat(),
            "programming_language": programming_language or "unknown",
            "difficulty_level": difficulty_level,
            "user_intent": user_intent or "general",
            "response_length": len(mentor_response)
        }
        
        # Store in ChromaDB
        self.collection.add(
            embeddings=[embedding],
            documents=[user_message],  # The actual text for reference
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        # Also store the mentor response separately for retrieval
        # We store this as a separate document to avoid embedding confusion
        response_id = f"{memory_id}_response"
        self.collection.add(
            embeddings=[embedding],  # Same embedding, different document
            documents=[mentor_response],
            metadatas={**metadata, "type": "response"},
            ids=[response_id]
        )
        
        return memory_id
    
    def find_similar_interactions(
        self,
        current_message: str,
        user_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        agent_type: Optional[str] = None,
        programming_language: Optional[str] = None
    ) -> List[Dict]:
        """
        Find similar past interactions for context
        
        Args:
            current_message: The current user message to find similarities for
            user_id: User to search memories for
            limit: Maximum number of similar interactions to return
            similarity_threshold: Minimum similarity score (0-1)
            agent_type: Filter by agent type
            programming_language: Filter by programming language
            
        Returns:
            List of similar interactions with metadata
        """
        
        # Create embedding for the current message
        query_embedding = self.embedding_model.encode([current_message])[0].tolist()
        
        # Build filter conditions - ChromaDB expects specific operator format
        where_conditions = {"user_id": {"$eq": user_id}}
        
        if agent_type:
            where_conditions["agent_type"] = {"$eq": agent_type}
            
        if programming_language:
            where_conditions["programming_language"] = {"$eq": programming_language}
        
        try:
            # Query ChromaDB for similar interactions
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_conditions,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results and filter by similarity threshold
            similar_interactions = []
            
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0], 
                results["distances"][0]
            )):
                # Convert distance to similarity (ChromaDB uses cosine distance)
                similarity = 1 - distance
                
                if similarity >= similarity_threshold:
                    # Get the corresponding response
                    response_id = f"{results['ids'][0][i]}_response"
                    try:
                        response_result = self.collection.get(
                            ids=[response_id],
                            include=["documents"]
                        )
                        response = response_result["documents"][0] if response_result["documents"] else "No response found"
                    except:
                        response = "Response not available"
                    
                    similar_interactions.append({
                        "memory_id": results["ids"][0][i],
                        "user_message": doc,
                        "mentor_response": response,
                        "similarity": similarity,
                        "metadata": metadata
                    })
            
            # Sort by similarity (highest first)
            similar_interactions.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similar_interactions
            
        except Exception as e:
            print(f"❌ Error searching memories: {e}")
            return []
    
    def get_user_learning_patterns(self, user_id: str) -> Dict:
        """
        Analyze user's learning patterns from stored interactions
        
        Args:
            user_id: User to analyze
            
        Returns:
            Dictionary with learning insights
        """
        try:
            # Get all user interactions
            user_memories = self.collection.get(
                where={"user_id": user_id},
                include=["metadatas"]
            )
            
            if not user_memories["metadatas"]:
                return {"message": "No learning history available"}
            
            # Analyze patterns
            languages = {}
            intents = {}
            difficulty_levels = {}
            
            for metadata in user_memories["metadatas"]:
                # Count programming languages
                lang = metadata.get("programming_language", "unknown")
                languages[lang] = languages.get(lang, 0) + 1
                
                # Count interaction types
                intent = metadata.get("user_intent", "general")
                intents[intent] = intents.get(intent, 0) + 1
                
                # Count difficulty levels
                level = metadata.get("difficulty_level", "beginner")
                difficulty_levels[level] = difficulty_levels.get(level, 0) + 1
            
            return {
                "total_interactions": len(user_memories["metadatas"]),
                "most_common_language": max(languages.items(), key=lambda x: x[1]) if languages else ("unknown", 0),
                "most_common_intent": max(intents.items(), key=lambda x: x[1]) if intents else ("general", 0),
                "difficulty_distribution": difficulty_levels,
                "languages_practiced": list(languages.keys())
            }
            
        except Exception as e:
            print(f"❌ Error analyzing learning patterns: {e}")
            return {"error": str(e)}
    
    def cleanup_old_memories(self, days_old: int = 90):
        """
        Remove old memories to manage storage (optional maintenance)
        
        Args:
            days_old: Remove memories older than this many days
        """
        try:
            from datetime import timedelta
            cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
            
            # This would require implementing date filtering in ChromaDB
            # For now, we'll just log the intent
            print(f"🧹 Memory cleanup requested for entries older than {days_old} days")
            # TODO: Implement actual cleanup logic
            
        except Exception as e:
            print(f"❌ Error during memory cleanup: {e}")
    
    def get_stats(self) -> Dict:
        """Get statistics about the memory store"""
        try:
            total_memories = self.collection.count()
            return {
                "total_memories": total_memories,
                "status": "operational"
            }
        except Exception as e:
            return {
                "total_memories": 0,
                "status": f"error: {e}"
            }

# Global memory store instance
memory_store: Optional[ConversationMemory] = None

def get_memory_store() -> ConversationMemory:
    """
    Get or create the global memory store instance
    This ensures we reuse the same ChromaDB connection
    """
    global memory_store
    if memory_store is None:
        memory_store = ConversationMemory()
    return memory_store

# Development testing
if __name__ == "__main__":
    # Test the memory store
    print("🧠 Testing Conversation Memory Store...")
    
    memory = ConversationMemory()
    
    # Add a test interaction
    memory_id = memory.add_interaction(
        user_id="test_user",
        user_message="How do I fix a React useState hook error?",
        mentor_response="Let's think about this step by step...",
        agent_type="strict",
        programming_language="javascript",
        user_intent="debugging"
    )
    
    print(f"✅ Added memory: {memory_id}")
    
    # Search for similar interactions
    similar = memory.find_similar_interactions(
        current_message="I'm getting an error with React hooks",
        user_id="test_user"
    )
    
    print(f"✅ Found {len(similar)} similar interactions")
    
    # Get learning patterns
    patterns = memory.get_user_learning_patterns("test_user")
    print(f"✅ Learning patterns: {patterns}")
    
    print("🧠 Memory store test completed!")