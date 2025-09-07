# Mentor Agent - Integrated Architecture Planning

## What This Agent Does
A programming mentor that guides junior developers through learning using the Socratic method - never giving direct answers but instead asking leading questions and providing progressively more detailed hints until the user discovers the solution themselves. **Key Innovation**: References user's past similar issues to reinforce learning patterns.

## Core Features (MVP)
1. **Memory-Guided Socratic Questions**: Ask targeted questions that reference user's past similar issues
2. **Progressive Hint System with Context**: Escalate guidance while connecting to previous learning experiences
3. **Temporal Learning Classification**: Identify if issue is recent repeat, pattern recognition, or skill building
4. **Persistent Knowledge Management**: Store all interactions in existing ChromaDB for future reference

## Technical Setup

### Model
- **Provider**: blackboxai (consistency with existing system)
- **Model**: anthropic/claude-sonnet-4 (already configured)
- **Alternative**: OpenAI GPT-4 (if advanced reasoning needed)
- **Why**: Maintain consistency with existing agents while ensuring quality Socratic guidance

### Required Tools (PydanticAI Functions)

#### 1. **memory_search**
- **Purpose**: Retrieve relevant past learning sessions from user's ChromaDB history
- **Integration**: Calls existing `ConversationMemory.find_similar_interactions()`
- **Returns**: Past issues with similarity scores, timestamps, and learning opportunity classification
- **Parameters**:
  - `query`: Current user question
  - `user_id`: User identifier
  - `limit`: Max results (default: 3)

#### 2. **save_interaction**
- **Purpose**: Store current learning session in ChromaDB
- **Integration**: Calls existing `ConversationMemory.add_interaction()`
- **Parameters**:
  - `user_id`: User identifier
  - `user_message`: Current question
  - `mentor_response`: Agent's Socratic response
  - `hint_level`: Current escalation level (1-4)
  - `referenced_memories`: IDs of past issues referenced

#### 3. **analyze_learning_pattern**
- **Purpose**: Classify learning opportunity type based on temporal and similarity data
- **Integration**: New function analyzing ChromaDB metadata
- **Returns**: Classification (recent_repeat, pattern_recognition, skill_building)
- **Parameters**:
  - `similarity_score`: How similar to past issue
  - `days_ago`: Time since past issue
  - `user_id`: For personalized patterns

#### 4. **hint_escalation_tracker**
- **Purpose**: Track conversation depth and determine hint level
- **Integration**: Session-based counter with ChromaDB persistence
- **Returns**: Current hint level (1-4) and suggested escalation
- **Parameters**:
  - `session_id`: Current conversation session
  - `user_confusion_signals`: Keywords indicating stuck user

### Integration with Existing System

#### Use Existing Infrastructure
- **Vector Database**: Your existing ChromaDB at `./chroma_memory`
- **Memory Store**: Enhance `backend/memory_store.py` with temporal analysis
- **Database**: PostgreSQL for hint escalation tracking and session management
- **API**: Integrate as new endpoint in existing FastAPI (`backend/api.py`)

#### New Enhancements to Existing Code
```python
# backend/memory_store.py additions:
- add_temporal_context()  # Add time-based analysis
- classify_learning_opportunity()  # Categorize memory type
- get_user_learning_journey()  # Track progress over time

# backend/api.py additions:
- /chat/mentor endpoint  # PydanticAI mentor agent
- Session management for hint escalation
```

## Environment Variables (Already Configured)
```bash
BLACKBOX_API_KEY=your-existing-key  # Already in .env
DATABASE_URL=your-postgresql-url    # Already configured
# No new environment variables needed!
```

## Success Criteria

### Core Behaviors
- [ ] Agent asks questions referencing specific past issues: "Remember your useState problem from Tuesday?"
- [ ] Progressive hints connect to user's learning history
- [ ] Retrieves 2-3 most relevant past issues per query
- [ ] Classifies memories as recent_repeat/pattern/skill_building
- [ ] Stores all interactions with proper metadata for future retrieval
- [ ] Maintains strict no-direct-answers policy even with memory context

### Learning Reinforcement
- [ ] Recent repeats (< 1 week): "We just covered this - what did you discover?"
- [ ] Pattern recognition (< 1 month): "Notice the similarity with your async issue?"
- [ ] Skill building: "This builds on your previous array methods knowledge"
- [ ] No relevant history: Falls back to standard Socratic method

## Implementation Architecture

### Data Flow
```
User Question
    ↓
PydanticAI Mentor Agent
    ↓
Tool: memory_search(query, user_id)
    ↓
ChromaDB (via ConversationMemory)
    ↓
Returns: Similar past issues + temporal context
    ↓
Tool: analyze_learning_pattern(memories)
    ↓
Returns: Learning opportunity classification
    ↓
Agent generates Socratic response with memory context
    ↓
Tool: save_interaction(full_context)
    ↓
Response to user with memory-guided questions
```

### Hint Escalation Framework with Memory

1. **Level 1 - Memory Probe**:
   - "This is similar to your [past issue]. What approach worked then?"
   - References most similar past issue

2. **Level 2 - Pattern Recognition**:
   - "I see a pattern with your [topic] questions. What's the common thread?"
   - Connects multiple past issues

3. **Level 3 - Specific Memory Guidance**:
   - "In your [past issue], you discovered [concept]. How does that apply here?"
   - Direct reference to past solution approach

4. **Level 4 - Guided Discovery with History**:
   - "Let's build on what you learned about [past concept]. First step..."
   - Step-by-step using their learning history

### Memory Context Injection

The agent receives enriched context:
```python
{
    "current_question": "React state not updating",
    "past_similar_issues": [
        {
            "question": "useState not working immediately",
            "days_ago": 3,
            "similarity": 0.85,
            "learning_type": "recent_repeat",
            "key_discovery": "React batches state updates"
        }
    ],
    "user_skill_level": "beginner",
    "topics_mastered": ["basic loops", "functions"],
    "recurring_struggles": ["async concepts", "state management"]
}
```

## Key Differences from Original Planning

### Changed
- **Vector DB**: Use existing ChromaDB instead of new Pinecone
- **LLM**: Keep BlackboxAI for consistency (not OpenAI)
- **Tools**: Renamed to match existing codebase patterns
- **Integration**: Direct integration with existing `memory_store.py`

### Added
- **Temporal Analysis**: Time-based learning classification
- **Learning Patterns**: Recent repeat vs pattern vs skill building
- **Memory Context**: Past issues directly referenced in responses
- **Progress Tracking**: User's learning journey over time

### Maintained
- **Socratic Method**: Still never gives direct answers
- **Progressive Hints**: 4-level escalation system
- **Supportive Tone**: Encouraging throughout
- **Knowledge Storage**: Every interaction saved

---
Generated: 2025-09-07
Note: This planning integrates perfectly with your existing dev_mentor_ai architecture, enhancing rather than replacing current systems.