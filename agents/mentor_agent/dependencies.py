"""
Dependencies for Mentor Agent with memory-enhanced capabilities.
Integrates with existing ChromaDB and PostgreSQL infrastructure.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import uuid

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
    
    def __post_init__(self):
        """Initialize session ID if not provided."""
        if self.session_id is None:
            self.session_id = str(uuid.uuid4())
    
    @property
    def conversation_memory(self):
        """Lazy initialization of ConversationMemory-like functionality."""
        if self._conversation_memory is None:
            # Mock conversation memory for now - would integrate with existing system
            class MockConversationMemory:
                def __init__(self, chroma_path: str, user_id: str):
                    self.chroma_path = chroma_path
                    self.user_id = user_id
                
                async def find_similar_interactions(self, query: str, limit: int = 3, threshold: float = 0.7):
                    """Mock method - would call real ChromaDB integration."""
                    # Return empty list for now - real implementation would search ChromaDB
                    return []
                
                async def add_interaction(self, user_message: str, assistant_response: str, metadata: dict = None):
                    """Mock method - would save to ChromaDB."""
                    return {"id": str(uuid.uuid4()), "status": "saved"}
                
                async def close(self):
                    """Mock cleanup."""
                    pass
            
            self._conversation_memory = MockConversationMemory(
                chroma_path=self.chroma_path,
                user_id=self.user_id
            )
            logger.info(f"Initialized ConversationMemory for user {self.user_id}")
        return self._conversation_memory
    
    @property
    def db_session(self):
        """Lazy initialization of database session."""
        if self._db_session is None and self.database_url:
            try:
                import sqlalchemy as sa
                from sqlalchemy.orm import sessionmaker
                engine = sa.create_engine(self.database_url)
                Session = sessionmaker(bind=engine)
                self._db_session = Session()
                logger.info("Initialized database session")
            except ImportError:
                logger.warning("SQLAlchemy not available, using mock session")
                self._db_session = type('MockSession', (), {'add': lambda x: None, 'commit': lambda: None, 'close': lambda: None})()
        return self._db_session
    
    @property
    def chroma_client(self):
        """Lazy initialization of ChromaDB client."""
        if self._chroma_client is None:
            try:
                import chromadb
                self._chroma_client = chromadb.PersistentClient(path=self.chroma_path)
                logger.info("Initialized ChromaDB client")
            except ImportError:
                logger.warning("ChromaDB not available, using mock client")
                self._chroma_client = type('MockChromaClient', (), {})()
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
        if hasattr(self._db_session, 'close'):
            self._db_session.close()
        if hasattr(self._conversation_memory, 'close'):
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