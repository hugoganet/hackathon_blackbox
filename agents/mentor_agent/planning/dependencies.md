# Mentor Agent - Dependencies Configuration

This specification defines the minimal dependency configuration for the mentor agent, leveraging existing infrastructure while adding essential components for memory-enhanced Socratic mentoring.

## Environment Configuration

### settings.py - Environment Variables
```python
"""
Configuration management for mentor agent using existing environment variables.
Leverages existing BLACKBOX_API_KEY and DATABASE_URL from main system.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class MentorSettings(BaseSettings):
    """Mentor agent settings leveraging existing environment configuration."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration (Using existing BlackboxAI setup)
    llm_provider: str = Field(default="blackboxai", description="LLM provider")
    llm_api_key: str = Field(..., env="BLACKBOX_API_KEY", description="BlackboxAI API key")
    llm_model: str = Field(default="anthropic/claude-sonnet-4", description="Model name")
    
    # Database Configuration (Using existing PostgreSQL)
    database_url: str = Field(..., env="DATABASE_URL", description="PostgreSQL connection string")
    
    # ChromaDB Configuration (Using existing vector store)
    chroma_path: str = Field(default="./chroma_memory", description="ChromaDB storage path")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model")
    
    # Mentor-Specific Configuration
    max_memory_results: int = Field(default=3, description="Max past interactions to retrieve")
    hint_escalation_levels: int = Field(default=4, description="Number of hint levels")
    similarity_threshold: float = Field(default=0.7, description="Memory similarity threshold")
    recent_repeat_days: int = Field(default=7, description="Days to consider recent repeat")
    pattern_recognition_days: int = Field(default=30, description="Days for pattern recognition")
    
    # Application Configuration
    app_env: str = Field(default="development", description="Environment")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")
    max_retries: int = Field(default=3, description="Max retry attempts")
    timeout_seconds: int = Field(default=30, description="Default timeout")
    
    @field_validator("llm_api_key")
    @classmethod
    def validate_llm_key(cls, v):
        """Ensure BlackboxAI API key is not empty."""
        if not v or v.strip() == "":
            raise ValueError("BLACKBOX_API_KEY cannot be empty")
        return v
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        """Ensure database URL is properly formatted."""
        if not v or not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL connection string")
        return v


def load_mentor_settings() -> MentorSettings:
    """Load mentor settings with proper error handling."""
    try:
        return MentorSettings()
    except Exception as e:
        error_msg = f"Failed to load mentor settings: {e}"
        if "BLACKBOX_API_KEY" in str(e):
            error_msg += "\nMake sure BLACKBOX_API_KEY is set in your .env file"
        elif "DATABASE_URL" in str(e):
            error_msg += "\nMake sure DATABASE_URL is set in your .env file"
        raise ValueError(error_msg) from e


# Global settings instance
mentor_settings = load_mentor_settings()
```

## Provider Configuration

### providers.py - BlackboxAI Model Setup
```python
"""
BlackboxAI provider configuration for the mentor agent.
Maintains consistency with existing system setup.
"""

from typing import Optional
from pydantic_ai.models import Model
from pydantic_ai.providers.blackboxai import BlackboxAIProvider
from pydantic_ai.models.blackboxai import BlackboxAIModel
from .settings import mentor_settings


def get_mentor_llm_model(model_choice: Optional[str] = None) -> BlackboxAIModel:
    """
    Get BlackboxAI model configuration for mentor agent.
    
    Args:
        model_choice: Optional override for model choice
    
    Returns:
        Configured BlackboxAI model instance
    """
    model_name = model_choice or mentor_settings.llm_model
    
    provider = BlackboxAIProvider(
        api_key=mentor_settings.llm_api_key
    )
    
    return BlackboxAIModel(model_name, provider=provider)


def get_fallback_model() -> Optional[BlackboxAIModel]:
    """
    Get fallback model for reliability.
    Uses a lighter Claude model for basic interactions.
    
    Returns:
        Fallback BlackboxAI model or None
    """
    if mentor_settings.app_env == "production":
        provider = BlackboxAIProvider(api_key=mentor_settings.llm_api_key)
        return BlackboxAIModel("anthropic/claude-3-haiku-20240307", provider=provider)
    return None
```

## Agent Dependencies

### dependencies.py - Mentor Agent Context
```python
"""
Dependencies for Mentor Agent with memory-enhanced capabilities.
Integrates with existing ChromaDB and PostgreSQL infrastructure.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class LearningMemory:
    """Structure for past learning interactions."""
    id: str
    question: str
    response: str
    timestamp: datetime
    similarity_score: float
    days_ago: int
    learning_type: str  # "recent_repeat", "pattern_recognition", "skill_building"
    topics: List[str]
    hint_level_reached: int


@dataclass 
class MentorDependencies:
    """
    Dependencies injected into mentor agent runtime context.
    
    Provides access to memory store, database, and session management
    while maintaining clean separation from existing infrastructure.
    """
    
    # User Context
    user_id: str
    session_id: Optional[str] = None
    
    # API Configuration (from settings)
    blackbox_api_key: Optional[str] = None
    database_url: Optional[str] = None
    
    # Memory Configuration
    chroma_path: str = "./chroma_memory"
    max_memory_results: int = 3
    similarity_threshold: float = 0.7
    
    # Learning Pattern Configuration
    recent_repeat_days: int = 7
    pattern_recognition_days: int = 30
    hint_escalation_levels: int = 4
    
    # Session State
    current_hint_level: int = 1
    referenced_memories: List[str] = field(default_factory=list)
    conversation_depth: int = 0
    
    # Runtime Context
    debug: bool = False
    max_retries: int = 3
    timeout: int = 30
    
    # External Service Clients (initialized lazily)
    _conversation_memory: Optional[Any] = field(default=None, init=False, repr=False)
    _db_session: Optional[Any] = field(default=None, init=False, repr=False)
    _chroma_client: Optional[Any] = field(default=None, init=False, repr=False)
    
    @property
    def conversation_memory(self):
        """Lazy initialization of ConversationMemory from existing system."""
        if self._conversation_memory is None:
            # Import existing ConversationMemory class
            from backend.memory_store import ConversationMemory
            self._conversation_memory = ConversationMemory(
                chroma_path=self.chroma_path,
                user_id=self.user_id
            )
            logger.info(f"Initialized ConversationMemory for user {self.user_id}")
        return self._conversation_memory
    
    @property
    def db_session(self):
        """Lazy initialization of database session."""
        if self._db_session is None and self.database_url:
            import sqlalchemy as sa
            from sqlalchemy.orm import sessionmaker
            engine = sa.create_engine(self.database_url)
            Session = sessionmaker(bind=engine)
            self._db_session = Session()
            logger.info("Initialized database session")
        return self._db_session
    
    @property
    def chroma_client(self):
        """Lazy initialization of ChromaDB client."""
        if self._chroma_client is None:
            import chromadb
            self._chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            logger.info("Initialized ChromaDB client")
        return self._chroma_client
    
    def increment_hint_level(self) -> int:
        """Increment hint level for escalation tracking."""
        if self.current_hint_level < self.hint_escalation_levels:
            self.current_hint_level += 1
        self.conversation_depth += 1
        return self.current_hint_level
    
    def add_referenced_memory(self, memory_id: str):
        """Track which memories have been referenced."""
        if memory_id not in self.referenced_memories:
            self.referenced_memories.append(memory_id)
    
    async def cleanup(self):
        """Cleanup resources when done."""
        if self._db_session:
            self._db_session.close()
        if self._conversation_memory:
            await self._conversation_memory.close()
    
    @classmethod
    def from_settings(cls, settings, user_id: str, session_id: Optional[str] = None, **kwargs):
        """
        Create dependencies from settings with user context.
        
        Args:
            settings: MentorSettings instance
            user_id: User identifier for memory retrieval
            session_id: Optional session identifier
            **kwargs: Override values
        
        Returns:
            Configured MentorDependencies instance
        """
        return cls(
            user_id=user_id,
            session_id=session_id,
            blackbox_api_key=kwargs.get('blackbox_api_key', settings.llm_api_key),
            database_url=kwargs.get('database_url', settings.database_url),
            chroma_path=kwargs.get('chroma_path', settings.chroma_path),
            max_memory_results=kwargs.get('max_memory_results', settings.max_memory_results),
            similarity_threshold=kwargs.get('similarity_threshold', settings.similarity_threshold),
            recent_repeat_days=kwargs.get('recent_repeat_days', settings.recent_repeat_days),
            pattern_recognition_days=kwargs.get('pattern_recognition_days', settings.pattern_recognition_days),
            hint_escalation_levels=kwargs.get('hint_escalation_levels', settings.hint_escalation_levels),
            debug=kwargs.get('debug', settings.debug),
            max_retries=kwargs.get('max_retries', settings.max_retries),
            timeout=kwargs.get('timeout', settings.timeout_seconds),
            **{k: v for k, v in kwargs.items() 
               if k not in ['blackbox_api_key', 'database_url', 'chroma_path', 'max_memory_results', 
                           'similarity_threshold', 'recent_repeat_days', 'pattern_recognition_days',
                           'hint_escalation_levels', 'debug', 'max_retries', 'timeout']}
        )
```

## Database Models

### models.py - Session and Hint Tracking
```python
"""
Database models for mentor agent session management and hint escalation tracking.
Extends existing PostgreSQL schema with mentor-specific tables.
"""

from sqlalchemy import Column, String, Integer, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional

Base = declarative_base()


class MentorSession(Base):
    """
    Track mentor agent sessions for hint escalation and learning progress.
    Links to existing user management if available.
    """
    __tablename__ = "mentor_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime, nullable=True)
    
    # Session Tracking
    total_interactions = Column(Integer, default=0)
    max_hint_level_reached = Column(Integer, default=1)
    topic_focus = Column(String, nullable=True)
    learning_outcome = Column(String, nullable=True)  # "solved", "abandoned", "escalated"
    
    # Memory References
    referenced_memory_ids = Column(Text, nullable=True)  # JSON string of memory IDs
    
    # Relationships
    interactions = relationship("MentorInteraction", back_populates="session")


class MentorInteraction(Base):
    """
    Individual interactions within a mentor session.
    Tracks hint progression and memory usage.
    """
    __tablename__ = "mentor_interactions"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("mentor_sessions.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)  # Order within session
    
    # Interaction Content
    user_question = Column(Text, nullable=False)
    mentor_response = Column(Text, nullable=False)
    hint_level = Column(Integer, nullable=False)
    
    # Memory Context
    memories_referenced = Column(Text, nullable=True)  # JSON string
    learning_pattern_type = Column(String, nullable=True)  # "recent_repeat", etc.
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Float, nullable=True)
    
    # Relationships
    session = relationship("MentorSession", back_populates="interactions")


class LearningPattern(Base):
    """
    Track user learning patterns over time for personalized mentoring.
    """
    __tablename__ = "learning_patterns"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    
    # Pattern Classification
    topic = Column(String, nullable=False)
    pattern_type = Column(String, nullable=False)  # "recurring_struggle", "mastery_area", etc.
    confidence_score = Column(Float, nullable=False)
    
    # Temporal Data
    first_observed = Column(DateTime, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)
    
    # Pattern Details
    description = Column(Text, nullable=True)
    suggested_approach = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


def create_mentor_tables(engine):
    """Create mentor-specific tables in existing database."""
    Base.metadata.create_all(engine)
```

## Agent Initialization

### agent.py - Mentor Agent Setup
```python
"""
Mentor Agent - Memory-Enhanced Socratic Mentoring
"""

import logging
from typing import Optional
from pydantic_ai import Agent

from .providers import get_mentor_llm_model, get_fallback_model
from .dependencies import MentorDependencies
from .settings import mentor_settings

logger = logging.getLogger(__name__)

# System prompt (will be provided by prompt-engineer subagent)
SYSTEM_PROMPT = """
[System prompt will be inserted here by prompt-engineer]
"""

# Initialize the mentor agent with BlackboxAI
mentor_agent = Agent(
    get_mentor_llm_model(),
    deps_type=MentorDependencies,
    system_prompt=SYSTEM_PROMPT,
    retries=mentor_settings.max_retries
)

# Register fallback model if available
fallback = get_fallback_model()
if fallback:
    mentor_agent.models.append(fallback)
    logger.info("Fallback model configured for mentor agent")

# Tools will be registered by tool-integrator subagent
# from .tools import register_mentor_tools
# register_mentor_tools(mentor_agent, MentorDependencies)


# Convenience functions for mentor agent usage
async def run_mentor_agent(
    prompt: str,
    user_id: str,
    session_id: Optional[str] = None,
    **dependency_overrides
) -> str:
    """
    Run the mentor agent with automatic dependency injection.
    
    Args:
        prompt: User's programming question
        user_id: User identifier for memory retrieval
        session_id: Optional session identifier for hint tracking
        **dependency_overrides: Override default dependencies
    
    Returns:
        Mentor's Socratic response as string
    """
    deps = MentorDependencies.from_settings(
        mentor_settings,
        user_id=user_id,
        session_id=session_id,
        **dependency_overrides
    )
    
    try:
        result = await mentor_agent.run(prompt, deps=deps)
        return result.data
    finally:
        await deps.cleanup()


def create_mentor_agent_with_deps(user_id: str, **dependency_overrides):
    """
    Create mentor agent instance with custom dependencies.
    
    Args:
        user_id: User identifier for memory context
        **dependency_overrides: Custom dependency values
    
    Returns:
        Tuple of (agent, dependencies)
    """
    deps = MentorDependencies.from_settings(
        mentor_settings, 
        user_id=user_id, 
        **dependency_overrides
    )
    return mentor_agent, deps
```

## Environment File Template

### .env.example - Configuration Template
```bash
# EXISTING ENVIRONMENT VARIABLES (Already configured)
# LLM Configuration
BLACKBOX_API_KEY=your-blackbox-api-key-here

# Database Configuration  
DATABASE_URL=postgresql://user:password@localhost:5432/dev_mentor_db

# MENTOR-SPECIFIC CONFIGURATION (Optional overrides)
# ChromaDB Configuration
CHROMA_PATH=./chroma_memory
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Memory Retrieval Settings
MAX_MEMORY_RESULTS=3
SIMILARITY_THRESHOLD=0.7
RECENT_REPEAT_DAYS=7
PATTERN_RECOGNITION_DAYS=30

# Hint System Configuration
HINT_ESCALATION_LEVELS=4

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=false
MAX_RETRIES=3
TIMEOUT_SECONDS=30
```

## Python Dependencies

### requirements.txt - Package Requirements
```txt
# Core dependencies (already in existing system)
pydantic-ai>=0.1.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0

# BlackboxAI Provider (existing)
blackboxai>=1.0.0

# Database and ORM (existing)
sqlalchemy>=2.0.0
asyncpg>=0.28.0
psycopg2-binary>=2.9.0

# Vector Database and Embeddings (existing)
chromadb>=0.4.0
sentence-transformers>=2.2.0

# Async utilities (existing)
httpx>=0.25.0
aiofiles>=23.0.0

# Development tools
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
ruff>=0.1.0

# Monitoring and logging
loguru>=0.7.0
```

## Integration Patterns

### Memory Integration Pattern
```python
# Integration with existing ConversationMemory
from backend.memory_store import ConversationMemory

async def search_learning_memories(deps: MentorDependencies, query: str):
    """Search for relevant past learning interactions."""
    memory_store = deps.conversation_memory
    similar_interactions = await memory_store.find_similar_interactions(
        query=query,
        limit=deps.max_memory_results,
        threshold=deps.similarity_threshold
    )
    
    return [
        LearningMemory(
            id=interaction.id,
            question=interaction.user_message,
            response=interaction.assistant_response,
            timestamp=interaction.timestamp,
            similarity_score=interaction.similarity,
            days_ago=(datetime.now() - interaction.timestamp).days,
            learning_type=classify_learning_type(interaction, deps),
            topics=extract_topics(interaction.user_message),
            hint_level_reached=interaction.metadata.get('hint_level', 1)
        )
        for interaction in similar_interactions
    ]
```

### Session Management Pattern
```python
# Session and hint tracking integration
async def track_mentor_session(deps: MentorDependencies, interaction_data: dict):
    """Track mentor session for hint escalation."""
    session = deps.db_session.query(MentorSession).filter_by(
        id=deps.session_id
    ).first()
    
    if not session:
        session = MentorSession(
            id=deps.session_id,
            user_id=deps.user_id,
            topic_focus=interaction_data.get('topic')
        )
        deps.db_session.add(session)
    
    # Update session metrics
    session.total_interactions += 1
    session.max_hint_level_reached = max(
        session.max_hint_level_reached,
        deps.current_hint_level
    )
    
    deps.db_session.commit()
```

## Security Considerations

### API Key Management
- **Reuse existing BLACKBOX_API_KEY** - No new API keys required
- **Database security** - Leverage existing DATABASE_URL security measures
- **ChromaDB access** - Local file system, existing security model
- **Input validation** - All user inputs validated through Pydantic models

### Data Protection
- **Memory isolation** - User memories stored with user_id isolation
- **Session security** - Session IDs generated securely
- **Conversation privacy** - No sharing of user conversations across users
- **Audit trail** - All interactions logged with proper timestamps

## Testing Configuration

### conftest.py - Test Setup
```python
import pytest
from unittest.mock import Mock, AsyncMock
from pydantic_ai.models.test import TestModel

@pytest.fixture
def test_mentor_settings():
    """Mock mentor settings for testing."""
    return Mock(
        llm_provider="blackboxai",
        llm_api_key="test-blackbox-key",
        llm_model="anthropic/claude-sonnet-4",
        database_url="sqlite:///:memory:",
        chroma_path="./test_chroma",
        max_memory_results=3,
        debug=True
    )

@pytest.fixture
def test_mentor_dependencies():
    """Test dependencies with mocked external services."""
    from .dependencies import MentorDependencies
    deps = MentorDependencies(
        user_id="test-user-123",
        session_id="test-session-456",
        blackbox_api_key="test-key",
        debug=True
    )
    
    # Mock external services
    deps._conversation_memory = AsyncMock()
    deps._db_session = Mock()
    deps._chroma_client = Mock()
    
    return deps

@pytest.fixture
def test_mentor_agent():
    """Test mentor agent with TestModel."""
    from pydantic_ai import Agent
    from .dependencies import MentorDependencies
    
    return Agent(
        TestModel(),
        deps_type=MentorDependencies,
        system_prompt="Test mentor prompt"
    )
```

## Quality Checklist

Before finalizing mentor agent configuration:
- ✅ Leverages existing BLACKBOX_API_KEY and DATABASE_URL
- ✅ Integrates with existing ConversationMemory class
- ✅ Uses existing ChromaDB at ./chroma_memory
- ✅ Maintains consistency with existing system architecture
- ✅ Provides memory-enhanced Socratic mentoring capabilities
- ✅ Includes hint escalation tracking
- ✅ Implements learning pattern recognition
- ✅ Handles session management properly
- ✅ Includes comprehensive error handling
- ✅ Provides testing configuration
- ✅ Maintains security best practices
- ✅ Documents all dependencies clearly

## Dependency File Structure

```
dependencies/
├── __init__.py              # Package initialization
├── settings.py             # Environment configuration using existing vars
├── providers.py            # BlackboxAI model provider setup
├── dependencies.py         # Agent dependencies with memory integration
├── models.py              # SQLAlchemy models for session tracking
├── agent.py               # Mentor agent initialization
├── .env.example           # Environment template (minimal additions)
└── requirements.txt       # Python dependencies (mostly existing)
```

This configuration leverages your existing infrastructure while adding only the essential components needed for memory-enhanced Socratic mentoring. The mentor agent will integrate seamlessly with your current ChromaDB memory store and PostgreSQL database, requiring no new environment variables while providing powerful learning pattern recognition and hint escalation capabilities.