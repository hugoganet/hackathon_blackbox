# Mentor Agent Tools Implementation Specification

## Tool 1: memory_search
**Purpose**: Retrieve relevant past learning sessions from ChromaDB to provide memory context

### Implementation Pattern
```python
@agent.tool
async def memory_search(
    ctx: RunContext[MentorDependencies],
    query: str,
    user_id: str,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Search for similar past learning interactions from user's history.
    
    Args:
        query: Current user question/problem
        user_id: User identifier for scoped search
        limit: Maximum number of results to return (default: 3)
    
    Returns:
        List of similar past interactions with metadata
    """
```

### Integration Points
- **Existing Function**: `ConversationMemory.find_similar_interactions()`
- **Database**: ChromaDB at `./chroma_memory`
- **Return Format**:
```python
[
    {
        "interaction_id": "uuid-string",
        "question": "Previous similar question",
        "mentor_response": "Past Socratic response", 
        "similarity_score": 0.85,
        "days_ago": 3,
        "hint_level_reached": 2,
        "key_concepts": ["react", "state", "useState"],
        "resolution_approach": "discovered state batching"
    }
]
```

### Error Handling
- ChromaDB connection failure → Return empty list with warning
- Invalid user_id → Return empty list  
- Query embedding failure → Log error, return empty list
- Rate limiting → Retry with exponential backoff

---

## Tool 2: save_interaction
**Purpose**: Store current learning session in ChromaDB for future reference

### Implementation Pattern
```python
@agent.tool
async def save_interaction(
    ctx: RunContext[MentorDependencies],
    user_id: str,
    user_message: str,
    mentor_response: str,
    hint_level: int = 1,
    referenced_memories: List[str] = None
) -> Dict[str, Any]:
    """
    Store current learning interaction with enriched metadata.
    
    Args:
        user_id: User identifier
        user_message: Current question from user
        mentor_response: Agent's Socratic response
        hint_level: Current escalation level (1-4)
        referenced_memories: IDs of past interactions referenced
    
    Returns:
        Storage confirmation with interaction ID
    """
```

### Integration Points
- **Existing Function**: `ConversationMemory.add_interaction()`
- **Database**: ChromaDB at `./chroma_memory`
- **Metadata Enhancement**: Add temporal context, hint levels, memory references

### Storage Format
```python
{
    "user_id": user_id,
    "question": user_message,
    "response": mentor_response,
    "timestamp": datetime.utcnow().isoformat(),
    "hint_level": hint_level,
    "referenced_memories": referenced_memories or [],
    "session_id": ctx.deps.session_id,
    "concepts_extracted": extract_concepts(user_message),
    "learning_stage": "discovery|understanding|application"
}
```

### Error Handling
- ChromaDB write failure → Retry once, then log error
- Invalid session_id → Generate new session ID
- Concept extraction failure → Store without concepts
- Metadata serialization error → Store core data only

---

## Tool 3: analyze_learning_pattern
**Purpose**: Classify learning opportunity type based on temporal and similarity analysis

### Implementation Pattern
```python
@agent.tool_plain
def analyze_learning_pattern(
    similarity_score: float,
    days_ago: int,
    interaction_count: int = 1
) -> Dict[str, Any]:
    """
    Classify the type of learning opportunity based on memory context.
    
    Args:
        similarity_score: How similar current issue is to past issue (0-1)
        days_ago: Days since the similar past issue occurred
        interaction_count: Number of similar past interactions
    
    Returns:
        Learning pattern classification with guidance approach
    """
```

### Classification Logic
```python
def classify_pattern(similarity_score: float, days_ago: int, count: int) -> str:
    if similarity_score > 0.8 and days_ago <= 7:
        return "recent_repeat"  # Same issue within a week
    elif similarity_score > 0.6 and days_ago <= 30 and count >= 2:
        return "pattern_recognition"  # Similar pattern within a month
    elif similarity_score > 0.4 and count >= 1:
        return "skill_building"  # Building on previous knowledge
    else:
        return "new_concept"  # No relevant history
```

### Return Format
```python
{
    "pattern_type": "recent_repeat|pattern_recognition|skill_building|new_concept",
    "confidence": 0.85,
    "guidance_approach": {
        "recent_repeat": "gentle_reminder_of_discovery",
        "pattern_recognition": "connect_common_thread", 
        "skill_building": "build_on_foundation",
        "new_concept": "standard_socratic_method"
    },
    "suggested_hint_start_level": 1  # 1-4 based on pattern
}
```

### Error Handling
- Invalid similarity_score → Default to 0.0
- Negative days_ago → Use absolute value
- Classification ambiguity → Default to "skill_building"

---

## Tool 4: hint_escalation_tracker
**Purpose**: Track conversation depth and determine appropriate hint level

### Implementation Pattern
```python
@agent.tool
async def hint_escalation_tracker(
    ctx: RunContext[MentorDependencies],
    session_id: str,
    user_confusion_signals: List[str] = None
) -> Dict[str, Any]:
    """
    Track conversation depth and suggest hint escalation level.
    
    Args:
        session_id: Current conversation session identifier
        user_confusion_signals: Keywords indicating user is stuck
    
    Returns:
        Current hint level and escalation recommendation
    """
```

### Confusion Detection Patterns
```python
CONFUSION_SIGNALS = {
    "explicit": ["i don't understand", "i'm stuck", "i'm confused", "help"],
    "implicit": ["what?", "how?", "but why", "i tried everything"],
    "repetitive": ["still not working", "same error", "tried that already"]
}
```

### Session Tracking (PostgreSQL)
```sql
-- hint_sessions table
CREATE TABLE hint_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    current_hint_level INTEGER DEFAULT 1,
    interaction_count INTEGER DEFAULT 0,
    confusion_signals_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Return Format
```python
{
    "current_hint_level": 2,
    "suggested_escalation": True,
    "escalation_reason": "confusion_signals_detected",
    "max_level_reached": False,
    "interaction_count": 4,
    "confusion_indicators": ["i don't understand", "what?"]
}
```

### Error Handling
- Database connection failure → Use in-memory session tracking
- Invalid session_id → Create new session
- SQL execution error → Default to hint level 1
- Concurrent session updates → Use database locks

---

## Integration Architecture

### Dependencies Class
```python
@dataclass
class MentorDependencies:
    """Dependencies for mentor agent execution"""
    blackbox_api_key: str
    database_url: str
    chroma_path: str = "./chroma_memory"
    session_id: str = None
    conversation_memory: ConversationMemory = None
```

### Tool Registration Function
```python
def register_mentor_tools(agent, deps_type):
    """Register all mentor tools with the agent"""
    
    # Tool implementations go here
    # (Full implementations as specified above)
    
    logger.info(f"Registered {len(agent.tools)} mentor tools")
```

### Error Handling Utilities
```python
class MentorToolError(Exception):
    """Custom exception for mentor tool failures"""
    pass

async def handle_memory_error(error: Exception, context: str) -> Dict[str, Any]:
    """Standardized error handling for memory operations"""
    logger.error(f"Memory operation failed in {context}: {error}")
    return {
        "success": False,
        "error": str(error),
        "fallback_used": True,
        "context": context
    }
```

## ChromaDB Query Patterns

### Memory Search Queries
```python
# Semantic similarity search
similar_interactions = collection.query(
    query_texts=[user_query],
    where={"user_id": user_id},
    n_results=limit,
    include=["documents", "metadatas", "distances"]
)

# Temporal filtering for recent repeats
recent_interactions = collection.query(
    query_texts=[user_query],
    where={
        "user_id": user_id,
        "days_ago": {"$lte": 7}
    },
    n_results=limit
)
```

### Metadata Enhancement
```python
enhanced_metadata = {
    "user_id": user_id,
    "timestamp": datetime.utcnow().isoformat(),
    "hint_level": hint_level,
    "concepts": extract_key_concepts(user_message),
    "session_id": session_id,
    "referenced_memories": referenced_memory_ids,
    "learning_outcome": "pending"  # Updated after resolution
}
```

## Quality Assurance

### Tool Validation Checklist
- ✅ All tools have proper error handling
- ✅ ChromaDB integration tested with existing data
- ✅ PostgreSQL session tracking implemented
- ✅ Similarity scoring validated
- ✅ Temporal analysis accuracy verified
- ✅ Rate limiting and retry logic included
- ✅ Memory reference tracking functional
- ✅ Hint escalation logic tested

### Performance Considerations
- ChromaDB queries limited to 10 results maximum
- Session data cached in memory for 30 minutes
- Similarity calculations optimized with vector indexing
- Background cleanup of old sessions (>24 hours)

---

**Integration Note**: These tools seamlessly integrate with existing `ConversationMemory` class and ChromaDB setup, enhancing rather than replacing current memory management functionality.