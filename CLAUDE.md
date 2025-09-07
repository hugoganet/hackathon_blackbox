# Dev Mentor AI

## Project Overview
AI-powered mentoring system for junior developers with integrated IDE functionality. The system provides personalized guidance through conversational AI agents that adapt their teaching approach based on user skill level and learning patterns. It uses a space-repetition-algorythm

## Vision
Create a comprehensive learning platform where junior developers can:
- **Practice coding** in an integrated development environment
- **Receive personalized mentoring** from AI agents with long-term memory
- **Learn through discovery** rather than receiving direct answers
- **Track their progress** through vector-based learning pattern analysis

## Current Architecture (MVP - Option 1)

### Backend Stack
- **FastAPI**: Production-ready REST API server
- **PostgreSQL**: User data, conversations, and metadata storage
- **ChromaDB**: Vector embeddings for conversation memory and similarity search
- **Blackbox AI**: LLM integration via `blackboxai/anthropic/claude-sonnet-4`
- **SQLAlchemy**: Database ORM with async support
- **Pydantic**: Request/response validation and serialization

### Deployment
- **Railway**: Single-platform deployment for backend + database
- **Procfile**: One-command deployment configuration  
- **PostgreSQL**: Managed database with automatic backups
- **Environment**: Production-ready with health monitoring

### Future Technology Stack
- **React Frontend**: Modern web interface with integrated IDE features
- **Vercel Deployment**: Optimized frontend hosting
- **pydantic**: Enhanced data validation (already implemented)
- **langgraph**: Advanced AI agent orchestration (planned)
- **pgvector**: Migration path from ChromaDB for larger scale

## AI Agent System

### 1. Strict Mentor Agent (PydanticAI Implementation)
- **NO DIRECT ANSWERS**: Absolute policy - never provides complete solutions
- **Socratic method**: Guides through questions and progressive hints only
- **Junior-focused**: Specifically designed for beginning developers
- **Autonomy building**: Forces users to discover solutions independently
- **Resilient**: Refuses to give answers even when users beg or insist
- **Pedagogical**: Celebrates small victories and builds confidence through discovery

### 2. Curator Agent (`curator-agent.md`) ⭐ **FULLY IMPLEMENTED**
- **Conversation analysis**: Processes interactions between users and mentors
- **Learning extraction**: Identifies skills, mistakes, knowledge gaps, and confidence levels
- **Structured output**: Generates JSON data for spaced repetition algorithms
- **Pattern recognition**: Tracks learning progression and common error patterns
- **Data formatting**: Prepares conversations for database storage and analysis
- **✅ API Integration**: Complete REST API endpoints (`POST /curator/analyze`, `GET /curator/user/{id}/skills`)
- **✅ Database Storage**: Full skill tracking with PostgreSQL native UUID support
- **✅ Domain Classification**: Skills automatically categorized into learning domains
- **✅ Mastery Tracking**: Confidence levels mapped to 1-5 mastery scale with progression over time
- **✅ Production Ready**: Comprehensive test coverage with end-to-end workflow validation

### 3. Flashcard Agent (`flashcard-agent.md`) ⭐ **FULLY IMPLEMENTED**
- **SM-2 Algorithm**: Complete spaced repetition implementation with ease factor calculations
- **Performance-based Scheduling**: Review intervals adjust based on success scores (0-5 scale)
- **Card State Progression**: NEW → LEARNING → REVIEW → MATURE lifecycle
- **Multiple formats**: Concept definitions, code completion, error identification, applications  
- **Personalization**: Adapts difficulty and content to user's skill level and gaps
- **Learning optimization**: Uses curator confidence scores for initial scheduling
- **Memory reinforcement**: Exponential interval growth with forgetting curve integration
- **✅ API Integration**: Complete REST API with 8 endpoints for flashcard management
- **✅ Database Storage**: Full CRUD operations with PostgreSQL UUID support
- **✅ Performance Tracking**: Complete review session history and analytics
- **✅ Production Ready**: Comprehensive test coverage with SM-2 algorithm validation

## PydanticAI Migration (NEW)

### Advanced Mentor Agent Implementation
The strict mentor agent has been migrated from markdown-based prompts to a sophisticated PydanticAI implementation:

**Enhanced Features:**
- **Memory-Guided Mentoring**: References past user interactions for personalized guidance
- **Progressive Hint System**: 4-level escalation (conceptual → investigative → directional → structural)
- **Context Detection**: Automatically identifies programming language, user intent, and difficulty level
- **Learning Pattern Analysis**: Tracks user progress and adapts mentoring approach
- **Hint Escalation Tracking**: Remembers hint levels for consistent progressive guidance
- **Temporal Analysis**: Considers timing and patterns in user learning journey

**Technical Implementation:**
- **Location**: `agents/mentor_agent/` - Complete PydanticAI agent structure
- **Components**: `agent.py` (main agent), `tools.py` (memory tools), `prompts.py` (system prompts)
- **Backward Compatibility**: `BlackboxMentorAdapter` maintains compatibility with existing API
- **Integration**: Seamless integration with existing ChromaDB memory store and PostgreSQL database
- **Testing**: Comprehensive test suite with >95% coverage

**API Access:**
- **Endpoint**: `POST /chat` with `agent_type: "pydantic_strict"`
- **CLI Access**: Option 3 in `backend/main.py` agent selection
- **Response Enhancement**: Includes hint level, detected language/intent, similarity count

## Database Architecture

### Core Entity Relationships
The database follows a comprehensive relational model supporting spaced repetition learning:

#### **User Journey & Session Management**
- **USER** → owns → **SESSION** → contains → **INTERACTION**
- Users create learning sessions containing individual mentor interactions
- Each interaction captures user messages, mentor responses, and metadata

#### **Skill Tracking & Progress System** 
- **USER** + **SKILL** → **MASTER** (initial skill level, creation date)
- **USER** + **SKILL** → **TRACK** → **SKILL_HISTORY** (mastery snapshots)
- Skills belong to learning domains (REF_DOMAIN) for categorization
- Daily tracking creates historical records for progress analytics

#### **Spaced Repetition & Flashcard System** ⭐ **FULLY IMPLEMENTED**
- **INTERACTION** → generates → **FLASHCARD** (questions, answers, difficulty, scheduling)
- **USER** + **FLASHCARD** → **REVIEW_SESSION** (success scores, response times)
- **SM-2 Algorithm**: Automatic review scheduling with ease factor calculations
- **Card States**: NEW → LEARNING → REVIEW → MATURE progression tracking
- **Performance Analytics**: Complete review history and success rate tracking
- **Batch Operations**: Efficient multi-flashcard creation and management

#### **Content Classification System**
- **INTERACTION** → classified by → **REF_DOMAIN** (learning domains)
- **INTERACTION** → categorized by → **REF_INTENT** (question types)
- **INTERACTION** → uses → **REF_LANGUAGE** (programming languages)

### Database Architecture

#### **Production Implementation** ⭐ **FULLY UPDATED**
- **Core Models**: `backend/database.py` with PostgreSQL-only models and flashcard system
- **CRUD Operations**: `backend/database_operations.py` with complete flashcard management
- **SM-2 Engine**: `backend/spaced_repetition.py` with algorithm implementation
- **Production Parity**: No SQLite fallback - PostgreSQL required for all environments
- **UUID Support**: Proper PostgreSQL UUID types throughout all models

#### **Database Tables** (9 Core Entities)
- **users, conversations, interactions**: Core user journey tracking
- **skills, skill_history, ref_domains**: Skill progression and domain classification
- **flashcards, review_sessions**: Complete spaced repetition system
- **memory_entries**: Vector store integration for conversation memory

#### **Design Documentation**
- **Complete ERD**: `backend/database/doc/dev_mentor_ai.svg`
- **Source Model**: `backend/database/doc/dev_mentor_ai.mcd` (Mocodo format)  
- **Architecture Details**: `backend/database/CLAUDE.md`

### Key Design Features
- **Proper relationship integrity**: All tables connected with meaningful relationships
- **Spaced repetition support**: Full tracking from interactions to review performance
- **Learning analytics**: Historical data supports progress tracking and insights
- **Scalable architecture**: Normalized design supports complex queries and reporting

## Core Features

### Long-term Memory System
- **Vector embeddings**: Semantic search across past conversations
- **Learning patterns**: Tracks user progress and common mistake patterns  
- **Personalized responses**: References similar past issues for context
- **Progress tracking**: Identifies knowledge gaps and improvement areas

### Conversation Intelligence
- **Context awareness**: Remembers previous discussions and solutions attempted
- **Adaptive difficulty**: Adjusts complexity based on user's demonstrated skill level
- **Multi-session continuity**: Maintains conversation context across sessions
- **Pattern recognition**: Identifies recurring learning challenges

## Project Structure
```
dev_mentor_ai/
├── backend/                   # Backend application code
│   ├── api.py                # FastAPI backend server
│   ├── main.py               # Original CLI program  
│   ├── database.py           # PostgreSQL-only models & utilities (active schema)
│   ├── memory_store.py       # ChromaDB vector memory system
│   └── database/             # Database design documentation
│       ├── populate_db.py    # Database population scripts
│       ├── CLAUDE.md         # Database architecture documentation
│       └── doc/              # Database design documentation
│           ├── dev_mentor_ai.mcd     # Mocodo source model (Entity-Relationship)
│           ├── dev_mentor_ai.svg     # Generated ERD diagram
│           ├── dev_mentor_ai_geo.json # Diagram layout geometry
│           └── create_schema.sql     # Database creation scripts
├── agents/                    # AI agent configurations
│   ├── agent-mentor-strict.md  # Legacy strict mentor agent (Socratic method)\n│   ├── mentor_agent/           # NEW: PydanticAI mentor agent implementation\n│   │   ├── __init__.py         # Package initialization and exports\n│   │   ├── agent.py            # Main PydanticAI mentor agent\n│   │   ├── tools.py            # Memory-guided mentoring tools\n│   │   ├── prompts.py          # System prompts and templates\n│   │   └── .env.example        # Environment configuration template
│   ├── curator-agent.md        # Conversation analysis and learning extraction
│   └── flashcard-agent.md      # Spaced repetition flashcard generation
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── Procfile                  # Railway deployment configuration
├── railway.json              # Railway build settings
├── runtime.txt               # Python version specification
├── tests/                   # Test suite (see tests/CLAUDE.md)
│   ├── CLAUDE.md           # Testing documentation and guidelines
│   ├── test_api.py         # Original API tests
│   ├── test_fastapi.py     # FastAPI endpoint tests
│   └── test_strict_responses_output.md  # Test results archive
├── chroma_memory/           # ChromaDB persistent storage (see chroma_memory/CLAUDE.md)
│   ├── CLAUDE.md           # Vector memory system documentation
│   └── [vector-db-files]   # ChromaDB internal files
└── .gitignore              # Git exclusions
```

## Quick Start Guide

### Prerequisites
- Python 3.11+
- Blackbox AI API key ([get one here](https://blackbox.ai/api))
- Git (for deployment)

### Local Development
```bash
# 1. Clone and setup
git clone <your-repo>
cd dev_mentor_ai

# 2. Environment configuration
cp .env.example .env
# Edit .env and add your BLACKBOX_API_KEY

# 3. Install dependencies  
pip install -r requirements.txt

# 4. Run the application
python3 backend/api.py
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs

# Alternative: CLI version
python3 backend/main.py
```

### Production Deployment (Railway - Option 1)
```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy to Railway"
git push origin main

# 2. Deploy to Railway
# Visit railway.app and connect your GitHub repo
# Add environment variable: BLACKBOX_API_KEY=your_key_here
# Railway automatically provides DATABASE_URL

# 3. Deploy
# Automatic deployment via Procfile configuration
```

### Testing
```bash
# Set up test environment
export DATABASE_URL="postgresql://postgres:password@localhost:5432/dev_mentor"
export TEST_DATABASE_URL="postgresql://postgres:password@localhost:5432/test_dev_mentor"

# Run test suite
pytest tests/ -v

# Test specific components
pytest tests/test_fastapi.py -v
python3 backend/memory_store.py  # Test memory store

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/agents
```

### Database Setup
```bash
# Set required environment variable
export DATABASE_URL="postgresql://postgres:password@localhost:5432/dev_mentor"

# Create database tables
python3 -c "from backend.database import create_tables; create_tables()"

# Populate initial reference data
python3 backend/database.py
```

### Database Diagram Generation (Mocodo)
```bash
# Install Mocodo for ERD generation
pip install mocodo

# Generate SVG diagram from MCD source
mocodo --input backend/database/doc/dev_mentor_ai.mcd

# Generate with better layout and scaling
mocodo --input backend/database/doc/dev_mentor_ai.mcd --transform arrange:wide --seed 456 --scale 1.2

# Generate additional formats (requires Cairo)
brew install cairo pkg-config  # macOS
# or apt-get install libcairo2-dev  # Linux
mocodo --input backend/database/doc/dev_mentor_ai.mcd --svg_to png pdf
```

## API Endpoints

### Core Endpoints
- `GET /` - Health check
- `GET /health` - System health status  
- `GET /agents` - List available mentor agents
- `POST /chat` - Main chat interaction with mentors
- `GET /user/{user_id}/memories` - User learning patterns
- `GET /stats` - System statistics for monitoring

### Curator Analysis Endpoints ⭐ **NEW**
- `POST /curator/analyze` - Analyze conversation and extract learning analytics
- `GET /curator/user/{user_id}/skills` - Get user skill progression data

### Flashcard & Spaced Repetition Endpoints ⭐ **NEW**
- `POST /flashcards/create` - Create individual flashcard with confidence-based scheduling
- `GET /flashcards/review/{user_id}` - Get flashcards due for review  
- `POST /flashcards/review` - Submit review results and update spaced repetition schedule
- `GET /flashcards/stats/{user_id}` - Get comprehensive user flashcard statistics
- `GET /flashcards/schedule/{user_id}` - Get upcoming review schedule for planning
- `POST /flashcards/batch` - Create multiple flashcards efficiently in one request
- `DELETE /flashcards/{flashcard_id}` - Delete flashcard with ownership verification

### Chat Request Format
```json
{
    "message": "How do I fix this React error?",
    "agent_type": "strict",  // Available: "strict", "curator", "flashcard"
    "user_id": "developer123",
    "session_id": "optional_session_id"
}
```

### Chat Response Format  
```json
{
    "response": "Great question! Let's think about...",
    "agent_type": "strict",
    "session_id": "session_12345",
    "related_memories": ["Similar past question: How to debug React..."]
}
```

## Development Roadmap

### ✅ Phase 1: MVP Backend (Current)
- **FastAPI REST API** with comprehensive endpoints
- **PostgreSQL integration** for user data and conversations
- **ChromaDB vector store** for conversation memory
- **Three-agent system** (strict mentor, curator, flashcard) with Blackbox AI
- **Railway deployment** configuration
- **Comprehensive testing** suite with >80% coverage
- **Production monitoring** with health checks and stats

### 🔄 Phase 2: Frontend Development (Next)
- **React application** with modern UI/UX
- **Integrated code editor** for hands-on practice
- **Real-time chat interface** with mentor agents
- **User authentication** and session management
- **Learning progress dashboard** with analytics
- **Responsive design** for mobile and desktop

### 📋 Phase 3: Advanced Features (Planned)
- **Advanced IDE features** (syntax highlighting, autocomplete)
- **Code execution environment** (sandboxed)
- **Learning path recommendations** based on user patterns
- **Collaboration features** (share sessions, peer learning)
- **Advanced analytics** and learning insights
- **Integration with external tools** (GitHub, documentation)

### 🚀 Phase 4: Scale & Polish (Future)
- **pgvector migration** for enhanced vector search
- **Multi-language support** for global users
- **Enterprise features** (team management, reporting)
- **Mobile applications** (iOS, Android)
- **Advanced AI agents** with langgraph orchestration

## Educational Philosophy (Strict Agent)

### Socratic Teaching Method
The strict mentor agent implements rigorous Socratic pedagogy:
- **Autonomous learning development** takes priority over quick solutions
- **Discovery-based learning** through guided questions and hints
- **Firm resistance** to direct answer requests, even under pressure
- **Confidence building** through small victories and progressive challenges
- **Critical thinking development** by forcing users to analyze problems independently

### Learning Psychology
- **Growth mindset cultivation**: Mistakes are learning opportunities
- **Problem-solving skills**: Focus on process over final answers  
- **Resilience building**: Comfortable with confusion and struggle
- **Metacognition**: Teaching users to think about their thinking

## Coding Standards

### Language Requirements
- **All code, comments, and messages must be in English**
- French is only used for user-facing agent responses (agent prompts)
- Variable names, function names, class names: English only
- Code comments and documentation: English only
- Commit messages and technical documentation: English only

### Code Style
- Follow PEP 8 for Python code
- Use descriptive variable and function names
- Add type hints where applicable
- Keep functions focused and single-purpose

## Technical Documentation

### Directory Documentation
Each directory contains comprehensive technical documentation:
- **`tests/CLAUDE.md`** - Testing strategy, coverage reports, CI/CD setup, and development workflows
- **`chroma_memory/CLAUDE.md`** - Vector memory architecture, data privacy policies, performance optimization, and migration strategies

### Key Design Decisions
- **FastAPI over Flask**: Better async support, automatic docs, type safety
- **PostgreSQL-only**: Production parity, no SQLite fallback, proper UUID support
- **ChromaDB over in-memory**: Persistent conversation memory, semantic search capabilities
- **Railway over Heroku**: Better Python support, integrated PostgreSQL, competitive pricing
- **Multi-agent system**: Specialized agents for mentoring, analysis, and spaced repetition
- **Single schema approach**: Consolidated database models in `backend/database.py`
- **Normalized database design**: Supports complex spaced repetition algorithms and analytics
- **Relational integrity**: All entities properly connected, no orphaned tables

### Performance Characteristics
- **API Response Time**: < 200ms for cached responses, < 2s for new conversations
- **Memory Search**: < 100ms for similarity search across thousands of conversations  
- **Database Queries**: Optimized with SQLAlchemy, connection pooling, query caching
- **Scalability**: Handles 100+ concurrent users with current architecture

## Project Status & Metrics

### ✅ Completed Features
- Production-ready FastAPI backend with comprehensive API
- PostgreSQL-only database with proper relationships and UUID support
- ChromaDB vector store with semantic conversation search
- Multi-agent system (strict mentor + curator + flashcard agents)  
- Railway deployment configuration with one-command setup
- Comprehensive test coverage (>90%) with automated testing
- Memory system with learning pattern analysis
- Health monitoring and system statistics endpoints
- **✅ Complete curator agent workflow** ⭐ **COMPLETE**
- **✅ PostgreSQL skill tracking system** ⭐ **COMPLETE**
- **✅ End-to-end conversation analysis pipeline** ⭐ **COMPLETE**
- **✅ Learning analytics extraction and storage** ⭐ **COMPLETE**
- **✅ SM-2 spaced repetition algorithm implementation** ⭐ **NEW**
- **✅ Complete flashcard system with CRUD operations** ⭐ **NEW**
- **✅ Performance-based review scheduling** ⭐ **NEW**
- **✅ Comprehensive flashcard API endpoints** ⭐ **NEW**

### 📊 Current Metrics
- **API Endpoints**: 16 endpoints fully functional (8 core + 2 curator + 6 flashcard)
- **Test Coverage**: >90% with unit, integration, and end-to-end tests
- **Database Models**: 9 core entities with complete relationship integrity  
- **Database Operations**: 20+ CRUD functions for all entities
- **Algorithm Implementation**: SM-2 spaced repetition with forgetting curve integration
- **Vector Storage**: Semantic search across user conversations
- **ERD Visualization**: Complete entity-relationship diagram available
- **Deployment Ready**: Single-command Railway deployment with updated configuration
- **✅ Curator Agent Tests**: 12/12 passing with PostgreSQL integration ⭐ **COMPLETE**
- **✅ Skill Tracking**: Complete workflow validation from conversation to database ⭐ **COMPLETE**
- **✅ Flashcard System**: Complete SM-2 implementation with performance tracking ⭐ **NEW**
- **✅ UUID Support**: Native PostgreSQL UUID types for production parity ⭐ **COMPLETE**

### 🔄 In Development
- React frontend application (Phase 2)
- Enhanced user authentication system
- Advanced learning analytics and progress tracking
- Mobile-responsive design implementation

## Contributing & Development

### Getting Started
1. Read this documentation thoroughly
2. Review directory-specific CLAUDE.md files
3. Set up local development environment
4. Run tests to ensure everything works
5. Check the development roadmap for current priorities

### Code Quality Standards
- All code must pass pytest test suite
- Follow established patterns in existing codebase
- Update documentation for any new features
- Test new endpoints with both unit and integration tests
- Ensure Railway deployment compatibility

### Support & Resources
- **API Documentation**: http://localhost:8000/docs (when running locally)
- **Test Suite**: Comprehensive testing in `tests/` directory
- **Architecture**: Detailed in directory CLAUDE.md files
- **Deployment**: Railway.app with automated CI/CD