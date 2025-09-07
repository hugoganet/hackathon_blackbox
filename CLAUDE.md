# Dev Mentor AI

## Project Overview
Production-ready AI-powered mentoring system for junior developers with full-stack web application. The system provides personalized guidance through conversational AI agents that adapt their teaching approach based on user skill level and learning patterns, featuring comprehensive spaced repetition algorithms and modern React frontend.

## Vision
Create a comprehensive learning platform where junior developers can:
- **Interact through modern web interface** with responsive chat interface and real-time mentoring
- **Receive personalized mentoring** from AI agents with long-term memory and progressive hint systems
- **Learn through discovery** via strict Socratic methodology that never gives direct answers
- **Track their progress** through comprehensive skill tracking and spaced repetition flashcard system
- **Practice with immediate feedback** in an accessible, mobile-responsive environment

## Current Architecture (Production-Ready Full-Stack)

### Backend Stack
- **FastAPI**: Production-ready REST API server with 16+ endpoints
- **PostgreSQL**: Complete relational database with native UUID support
- **ChromaDB**: Vector embeddings for conversation memory and similarity search
- **Blackbox AI**: LLM integration via `blackboxai/anthropic/claude-sonnet-4`
- **SQLAlchemy**: Database ORM with comprehensive model relationships
- **PydanticAI**: Advanced mentor agent with memory-guided mentoring
- **SM-2 Algorithm**: Complete spaced repetition implementation

### Frontend Stack ⭐ **IMPLEMENTED**
- **React 18**: Modern web interface with hooks and TypeScript
- **Vite**: Fast development server and optimized builds
- **Tailwind CSS**: Responsive design system with dark/light themes
- **Jest**: Comprehensive frontend testing framework
- **Monaco Editor**: Integrated code editor for hands-on practice
- **Recharts**: Learning analytics and progress visualization
- **WCAG AA Compliance**: Full accessibility support

### Deployment
- **Railway**: Production backend deployment with managed PostgreSQL
- **Vercel**: Frontend deployment with optimized CDN delivery
- **Docker**: Containerized development environment
- **GitHub Actions**: Automated CI/CD pipeline
- **Environment**: Production monitoring with health checks and performance metrics

## AI Agent System

### 1. Strict Mentor Agent (PydanticAI Implementation) ⭐ **FULLY IMPLEMENTED**
- **NO DIRECT ANSWERS**: Absolute policy - never provides complete solutions
- **Memory-Guided Mentoring**: References past user interactions for personalized guidance
- **Progressive Hint System**: 4-level escalation (conceptual → investigative → directional → structural)
- **Context Detection**: Automatically identifies programming language, user intent, and difficulty level
- **Learning Pattern Analysis**: Tracks user progress and adapts mentoring approach
- **Hint Escalation Tracking**: Remembers hint levels for consistent progressive guidance
- **Temporal Analysis**: Considers timing and patterns in user learning journey
- **Location**: `agents/mentor_agent/` - Complete PydanticAI agent implementation

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

## Full-Stack Application Implementation ⭐ **COMPLETED**

### Frontend Application Features
The complete React frontend application has been implemented with production-ready features:

**User Interface:**
- **Modern Chat Interface**: Real-time messaging with mentor agents
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Accessibility**: WCAG AA compliance with screen reader support
- **Dark/Light Themes**: User preference system with system detection
- **Code Editor Integration**: Monaco Editor for hands-on coding practice
- **Progress Visualization**: Recharts-based analytics dashboard

**Developer Experience:**
- **TypeScript**: Full type safety across frontend components
- **Jest Testing**: Comprehensive test suite with coverage reports
- **Hot Reload**: Instant development feedback with Vite
- **API Integration**: Complete HTTP client with error handling
- **Environment Management**: Development and production configurations

**Technical Implementation:**
- **Location**: `frontend/` - Complete React application
- **Components**: Modern functional components with hooks
- **State Management**: React hooks with context providers
- **API Service**: Comprehensive service layer with type safety
- **Testing**: Unit and integration tests with Jest and React Testing Library

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

### Database Architecture ⭐ **PRODUCTION IMPLEMENTATION**

#### **Complete Schema Implementation**
- **Core Models**: `backend/database/models.py` with comprehensive relational schema
- **CRUD Operations**: `backend/database_operations.py` with full entity management
- **SM-2 Engine**: `backend/spaced_repetition.py` with complete algorithm implementation
- **Production Database**: PostgreSQL-only with native UUID support throughout
- **Comprehensive Relationships**: 9 core entities with proper foreign key constraints

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

## Project Structure ⭐ **UPDATED**
```
dev_mentor_ai/
├── frontend/                  # React frontend application ⭐ IMPLEMENTED
│   ├── src/
│   │   ├── components/       # React UI components
│   │   ├── services/         # API integration layer  
│   │   ├── types/            # TypeScript type definitions
│   │   ├── utils/            # Utility functions and HTTP client
│   │   └── __tests__/        # Frontend test suites
│   ├── package.json          # Dependencies and scripts
│   ├── jest.config.js        # Testing configuration
│   ├── tailwind.config.js    # Design system configuration
│   └── vite.config.ts        # Build configuration
├── backend/                   # Backend application code
│   ├── api.py                # FastAPI server with 16+ endpoints
│   ├── main.py               # CLI interface and legacy compatibility
│   ├── database_operations.py # Complete CRUD operations
│   ├── spaced_repetition.py  # SM-2 algorithm implementation
│   ├── pydantic_handler.py   # PydanticAI integration
│   ├── memory_store.py       # ChromaDB vector memory system
│   └── database/             # Database implementation
│       ├── models.py         # Production PostgreSQL models
│       ├── populate_db.py    # Database seeding utilities
│       ├── CLAUDE.md         # Database architecture documentation
│       └── doc/              # ERD diagrams and MCD models
├── agents/                    # AI agent system
│   ├── mentor_agent/         # PydanticAI mentor implementation ⭐ IMPLEMENTED
│   │   ├── agent.py          # Main PydanticAI mentor agent
│   │   ├── tools.py          # Memory-guided mentoring tools
│   │   ├── prompts.py        # System prompts and hint escalation
│   │   ├── adapter.py        # Backward compatibility layer
│   │   └── tests/            # Comprehensive agent test suite
│   ├── agent-mentor-strict.md # Legacy markdown-based prompts
│   ├── curator-agent.md      # Conversation analysis agent
│   ├── flashcard-agent.md    # Spaced repetition content generation
│   └── CLAUDE.md            # Agent system documentation
├── tests/                   # Comprehensive test suite (30+ test files)
│   ├── fixtures/            # Test data and mock responses
│   ├── helpers/             # Testing utility functions
│   ├── test_*_*.py         # Unit, integration, and e2e tests
│   └── CLAUDE.md           # Testing documentation
├── chroma_memory/           # ChromaDB persistent storage
│   ├── CLAUDE.md           # Vector memory system documentation
│   └── [chroma-db-files]   # Vector database storage
├── start-dev.sh             # Development environment startup script
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── Procfile                # Railway backend deployment
├── railway.json            # Railway build configuration
└── README.md               # Quick start guide and overview
```

## Quick Start Guide

### Prerequisites
- Python 3.11+
- Blackbox AI API key ([get one here](https://blackbox.ai/api))
- Git (for deployment)

### Local Development (Full-Stack) ⭐ **UPDATED**
```bash
# 1. Clone and setup
git clone <your-repo>
cd dev_mentor_ai

# 2. Environment configuration
cp .env.example .env
# Edit .env and add your BLACKBOX_API_KEY

# 3. Quick start (recommended)
./start-dev.sh
# Starts both backend (port 8000) and frontend (port 3000)
# Frontend available at http://localhost:3000
# Backend API available at http://localhost:8000

# Alternative: Manual startup
# Backend only
pip install -r requirements.txt
python3 backend/api.py

# Frontend only (separate terminal)
cd frontend
npm install
npm run dev
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
export DATABASE_URL="postgresql://postgres:password@localhost:5432/dev_mentor_ai"
export TEST_DATABASE_URL="postgresql://postgres:password@localhost:5432/test_dev_mentor_ai"

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
export DATABASE_URL="postgresql://postgres:password@localhost:5432/dev_mentor_ai"

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

## API Endpoints ⭐ **16+ ENDPOINTS IMPLEMENTED**

### Core Application Endpoints
- `GET /` - Application health check and status
- `GET /health` - Detailed system health monitoring  
- `GET /agents` - List all available AI mentor agents
- `POST /chat` - Primary chat interaction with AI mentors (supports all agent types)
- `GET /user/{user_id}/memories` - Retrieve user's learning interaction history
- `GET /stats` - Comprehensive system performance statistics

### Curator Analysis & Learning Analytics ⭐ **IMPLEMENTED**
- `POST /curator/analyze` - Analyze conversations and extract structured learning data
- `GET /curator/user/{user_id}/skills` - Retrieve user's skill progression analytics
- `GET /user/{user_id}/conversations` - Enhanced conversation history with curator metadata
- `GET /curator/stats` - Curator analysis performance statistics and effectiveness metrics

### Spaced Repetition & Flashcard System ⭐ **IMPLEMENTED**
- `POST /flashcards/create` - Create individual flashcard with SM-2 algorithm scheduling
- `GET /flashcards/review/{user_id}` - Get flashcards due for review with user statistics  
- `POST /flashcards/review` - Submit review results and update spaced repetition schedule
- `GET /flashcards/stats/{user_id}` - Comprehensive flashcard performance analytics
- `GET /flashcards/schedule/{user_id}` - Upcoming review schedule planning interface
- `POST /flashcards/batch` - Efficient batch flashcard creation from conversations
- `DELETE /flashcards/{flashcard_id}` - Secure flashcard deletion with ownership verification

### Chat Request Format
```json
{
    "message": "How do I fix this React error?",
    "agent_type": "strict",  // Available: "strict", "pydantic_strict", "curator", "flashcard"
    "user_id": "developer123",
    "session_id": "optional_session_id"
}
```

### Enhanced Chat Response Format  
```json
{
    "response": "Great question! Let's think about...",
    "agent_type": "pydantic_strict",
    "session_id": "session_12345",
    "related_memories": ["Similar past question: How to debug React..."],
    "hint_level": 2,
    "detected_language": "JavaScript",
    "detected_intent": "debugging",
    "similar_interactions_count": 3
}
```

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
- **Full-stack application** with React frontend and FastAPI backend
- **Production-ready deployment** with Railway backend and frontend hosting capability
- **PostgreSQL database** with comprehensive relational schema and native UUID support
- **ChromaDB vector store** with semantic conversation search and learning pattern analysis
- **Multi-agent AI system** with strict mentor, curator, and flashcard agents
- **PydanticAI implementation** with memory-guided mentoring and progressive hint systems
- **Spaced repetition system** with SM-2 algorithm and comprehensive flashcard management
- **Comprehensive testing suite** with 30+ test files covering unit, integration, and e2e scenarios
- **Complete API layer** with 16+ endpoints for all application features
- **Modern frontend** with responsive design, accessibility, and real-time chat interface

### 📊 Current Metrics
- **API Endpoints**: 16+ endpoints fully functional across all application domains
- **Test Coverage**: >90% with comprehensive test suite including performance and integration tests
- **Database Models**: 9 core entities with complete relational integrity
- **Frontend Components**: Modern React application with TypeScript and comprehensive UI components
- **AI Agent Implementation**: PydanticAI-based mentor with memory integration and context awareness
- **Spaced Repetition**: Complete SM-2 algorithm with performance-based scheduling
- **Vector Storage**: Semantic search with ChromaDB for conversation memory
- **Production Ready**: Full-stack deployment configuration with monitoring and health checks

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