"""
PydanticAI Mentor Agent Tools
Memory-guided mentoring tools for the strict mentor agent
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import json
from datetime import datetime, timedelta

class SimilarInteraction(BaseModel):
    """Model for similar past interactions"""
    memory_id: str
    user_message: str
    mentor_response: str
    similarity: float
    metadata: Dict[str, Any]

class LearningPatterns(BaseModel):
    """Model for user learning patterns"""
    total_interactions: int
    most_common_language: tuple[str, int]
    most_common_intent: tuple[str, int] 
    difficulty_distribution: Dict[str, int]
    languages_practiced: List[str]

class MemoryContext(BaseModel):
    """Memory context for enhanced mentoring"""
    similar_interactions: List[SimilarInteraction]
    learning_patterns: LearningPatterns
    recent_topics: List[str]
    skill_progression: Dict[str, Any]

class HintTracker(BaseModel):
    """Track hint escalation levels for users"""
    user_id: str
    session_id: str
    current_question_hash: str
    hint_level: int = Field(default=1, ge=1, le=4)
    hints_given: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

class MentorTools:
    """
    Tools for the PydanticAI Mentor Agent
    Provides memory-guided mentoring capabilities
    """
    
    def __init__(self, memory_store=None, db_session=None):
        """
        Initialize mentor tools
        
        Args:
            memory_store: ConversationMemory instance for vector search
            db_session: Database session for persistent storage
        """
        self.memory_store = memory_store
        self.db_session = db_session
        self.hint_trackers: Dict[str, HintTracker] = {}  # In-memory hint tracking
        
    async def get_memory_context(
        self, 
        user_id: str, 
        current_message: str,
        session_id: Optional[str] = None
    ) -> MemoryContext:
        """
        Retrieve memory context for personalized mentoring
        
        Args:
            user_id: User identifier
            current_message: Current user question
            session_id: Current session identifier
            
        Returns:
            MemoryContext with similar interactions and learning patterns
        """
        similar_interactions = []
        learning_patterns = None
        recent_topics = []
        skill_progression = {}
        
        if self.memory_store:
            try:
                # Find similar past interactions
                similar_results = self.memory_store.find_similar_interactions(
                    current_message=current_message,
                    user_id=user_id,
                    limit=3,
                    similarity_threshold=0.7
                )
                
                similar_interactions = [
                    SimilarInteraction(
                        memory_id=result["memory_id"],
                        user_message=result["user_message"],
                        mentor_response=result["mentor_response"],
                        similarity=result["similarity"],
                        metadata=result["metadata"]
                    )
                    for result in similar_results
                ]
                
                # Get learning patterns
                patterns_data = self.memory_store.get_user_learning_patterns(user_id)
                if patterns_data and "total_interactions" in patterns_data:
                    learning_patterns = LearningPatterns(
                        total_interactions=patterns_data["total_interactions"],
                        most_common_language=patterns_data["most_common_language"],
                        most_common_intent=patterns_data["most_common_intent"],
                        difficulty_distribution=patterns_data["difficulty_distribution"],
                        languages_practiced=patterns_data["languages_practiced"]
                    )
                
                # Extract recent topics from similar interactions
                recent_topics = list(set([
                    interaction.metadata.get("programming_language", "unknown")
                    for interaction in similar_interactions
                    if interaction.metadata.get("programming_language") != "unknown"
                ]))[:5]
                
            except Exception as e:
                print(f"Warning: Error retrieving memory context: {e}")
        
        # Get skill progression from database if available
        if self.db_session:
            try:
                from backend.database import get_user_skill_progression, get_user_by_username
                user = get_user_by_username(self.db_session, user_id)
                if user:
                    skill_data = get_user_skill_progression(self.db_session, str(user.id), limit=10)
                    skill_progression = {
                        "recent_skills": skill_data[:5] if skill_data else [],
                        "total_skills_tracked": len(set(skill["skill_name"] for skill in skill_data)) if skill_data else 0
                    }
            except Exception as e:
                print(f"Warning: Error retrieving skill progression: {e}")
        
        return MemoryContext(
            similar_interactions=similar_interactions,
            learning_patterns=learning_patterns or LearningPatterns(
                total_interactions=0,
                most_common_language=("unknown", 0),
                most_common_intent=("general", 0),
                difficulty_distribution={},
                languages_practiced=[]
            ),
            recent_topics=recent_topics,
            skill_progression=skill_progression
        )
    
    async def track_hint_escalation(
        self, 
        user_id: str, 
        session_id: str, 
        question: str,
        hint: str
    ) -> int:
        """
        Track hint escalation for progressive guidance
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            question: Current question being asked
            hint: Hint being provided
            
        Returns:
            Current hint level (1-4)
        """
        # Create unique key for this question context
        question_hash = str(hash(question.lower().strip()))
        tracker_key = f"{user_id}_{session_id}_{question_hash}"
        
        # Get or create hint tracker
        if tracker_key in self.hint_trackers:
            tracker = self.hint_trackers[tracker_key]
            
            # Check if this is still the same question (within reasonable time)
            time_diff = datetime.now() - tracker.timestamp
            if time_diff > timedelta(hours=1):  # Reset after 1 hour
                tracker.hint_level = 1
                tracker.hints_given = []
                tracker.timestamp = datetime.now()
        else:
            tracker = HintTracker(
                user_id=user_id,
                session_id=session_id,
                current_question_hash=question_hash,
                hint_level=1
            )
            self.hint_trackers[tracker_key] = tracker
        
        # Add hint and potentially escalate
        tracker.hints_given.append(hint)
        
        # Don't escalate beyond level 4
        if tracker.hint_level < 4:
            # Simple escalation: increase level every 2 hints
            if len(tracker.hints_given) >= tracker.hint_level * 2:
                tracker.hint_level += 1
        
        tracker.timestamp = datetime.now()
        return tracker.hint_level
    
    async def classify_user_intent(self, message: str) -> str:
        """
        Classify user intent from their message
        
        Args:
            message: User's message/question
            
        Returns:
            Classified intent string
        """
        message_lower = message.lower()
        
        # Simple keyword-based classification
        if any(word in message_lower for word in ["error", "bug", "doesn't work", "not working", "issue"]):
            return "debugging"
        elif any(word in message_lower for word in ["how do i", "how to", "what is", "explain", "understand"]):
            return "concept_explanation"
        elif any(word in message_lower for word in ["improve", "better", "optimize", "best practice"]):
            return "improvement"
        elif any(word in message_lower for word in ["test", "testing", "unit test"]):
            return "testing"
        elif any(word in message_lower for word in ["deploy", "production", "hosting"]):
            return "deployment"
        else:
            return "general"
    
    async def detect_programming_language(self, message: str) -> str:
        """
        Detect programming language from user message
        
        Args:
            message: User's message/question
            
        Returns:
            Detected programming language
        """
        message_lower = message.lower()
        
        # Language detection based on keywords and syntax patterns
        language_patterns = {
            "javascript": ["javascript", "js", "node", "npm", "react", "vue", "angular", "const ", "let ", "var ", "=>"],
            "python": ["python", "py", "django", "flask", "pandas", "numpy", "def ", "import ", "__init__"],
            "java": ["java", "spring", "maven", "gradle", "class ", "public ", "private ", "static "],
            "html": ["html", "div", "span", "class=", "id=", "<body>", "<head>", "<!DOCTYPE"],
            "css": ["css", "style", "color:", "margin:", "padding:", "background:", "flex", "grid"],
            "sql": ["sql", "select", "from", "where", "insert", "update", "delete", "join"],
            "typescript": ["typescript", "ts", "interface", "type ", ": string", ": number", "generic"],
            "php": ["php", "<?php", "$", "->", "array(", "echo ", "function "],
            "c++": ["c++", "cpp", "#include", "std::", "int main", "cout", "cin"],
            "c#": ["c#", "csharp", "using System", "public class", "string ", "int "],
            "go": ["golang", " go ", "func ", "package ", "import ", "var ", "make("],
            "rust": ["rust", "fn ", "let ", "mut ", "String::", "Vec<", "Result<"]
        }
        
        detected_scores = {}
        for language, patterns in language_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message_lower)
            if score > 0:
                detected_scores[language] = score
        
        if detected_scores:
            return max(detected_scores, key=detected_scores.get)
        return "unknown"
    
    async def analyze_difficulty_level(self, message: str, learning_patterns: Optional[LearningPatterns] = None) -> str:
        """
        Analyze difficulty level of the question
        
        Args:
            message: User's message/question
            learning_patterns: User's learning history for context
            
        Returns:
            Difficulty level: beginner, intermediate, advanced
        """
        message_lower = message.lower()
        
        # Beginner indicators
        beginner_keywords = [
            "what is", "how do i start", "basic", "simple", "tutorial", 
            "first time", "new to", "learning", "beginner"
        ]
        
        # Advanced indicators  
        advanced_keywords = [
            "optimize", "performance", "architecture", "design pattern", 
            "scalability", "concurrency", "algorithm", "complexity",
            "microservices", "distributed", "async", "threading"
        ]
        
        beginner_score = sum(1 for keyword in beginner_keywords if keyword in message_lower)
        advanced_score = sum(1 for keyword in advanced_keywords if keyword in message_lower)
        
        # Factor in learning patterns if available
        if learning_patterns and learning_patterns.total_interactions > 0:
            if learning_patterns.total_interactions < 5:
                beginner_score += 1
            elif learning_patterns.total_interactions > 20:
                advanced_score += 1
        
        if advanced_score > beginner_score:
            return "advanced"
        elif beginner_score > 0:
            return "beginner"
        else:
            return "intermediate"
    
    async def store_interaction(
        self,
        user_id: str,
        user_message: str,
        mentor_response: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Store the interaction in memory for future reference
        
        Args:
            user_id: User identifier
            user_message: User's question/message
            mentor_response: Mentor's response
            session_id: Session identifier
            metadata: Additional metadata
            
        Returns:
            Memory ID if successful, None otherwise
        """
        if not self.memory_store:
            return None
        
        try:
            # Classify the interaction
            intent = await self.classify_user_intent(user_message)
            language = await self.detect_programming_language(user_message)
            difficulty = await self.analyze_difficulty_level(user_message)
            
            # Store in memory
            memory_id = self.memory_store.add_interaction(
                user_id=user_id,
                user_message=user_message,
                mentor_response=mentor_response,
                agent_type="pydantic_strict",
                programming_language=language,
                difficulty_level=difficulty,
                user_intent=intent
            )
            
            return memory_id
        except Exception as e:
            print(f"Warning: Error storing interaction: {e}")
            return None
    
    def cleanup_old_trackers(self, hours_old: int = 24):
        """Clean up old hint trackers to prevent memory leaks"""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        keys_to_remove = [
            key for key, tracker in self.hint_trackers.items()
            if tracker.timestamp < cutoff_time
        ]
        for key in keys_to_remove:
            del self.hint_trackers[key]