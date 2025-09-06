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

### 1. Strict Mentor Agent (`agent-mentor-strict.md`)
- **NO DIRECT ANSWERS**: Absolute policy - never provides complete solutions
- **Socratic method**: Guides through questions and progressive hints only
- **Junior-focused**: Specifically designed for beginning developers
- **Autonomy building**: Forces users to discover solutions independently
- **Resilient**: Refuses to give answers even when users beg or insist
- **Pedagogical**: Celebrates small victories and builds confidence through discovery

### 2. Curator Agent (`curator-agent.md`)
- **Conversation analysis**: Processes interactions between users and mentors
- **Learning extraction**: Identifies skills, mistakes, knowledge gaps, and confidence levels
- **Structured output**: Generates JSON data for spaced repetition algorithms
- **Pattern recognition**: Tracks learning progression and common error patterns
- **Data formatting**: Prepares conversations for database storage and analysis

### 3. Flashcard Agent (`flashcard-agent.md`)
- **Spaced repetition**: Creates optimized flashcards for long-term retention
- **Multiple formats**: Concept definitions, code completion, error identification, applications
- **Personalization**: Adapts difficulty and content to user's skill level and gaps
- **Learning optimization**: Uses curator analysis to prioritize important concepts
- **Memory reinforcement**: Designs cards for multiple review cycles and progressive difficulty

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
├── api.py                     # FastAPI backend server
├── main.py                    # Original CLI program  
├── database.py                # PostgreSQL models & utilities
├── memory_store.py            # ChromaDB vector memory system
├── agent-mentor-strict.md     # Strict mentor agent (Socratic method)
├── curator-agent.md           # Conversation analysis and learning extraction
├── flashcard-agent.md         # Spaced repetition flashcard generation
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
python3 api.py
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs

# Alternative: CLI version
python3 main.py
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
# Run test suite
pytest tests/ -v

# Test specific components
pytest tests/test_fastapi.py -v
python3 memory_store.py  # Test memory store

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/agents
```

## API Endpoints

### Core Endpoints
- `GET /` - Health check
- `GET /health` - System health status  
- `GET /agents` - List available mentor agents
- `POST /chat` - Main chat interaction with mentors
- `GET /user/{user_id}/memories` - User learning patterns
- `GET /stats` - System statistics for monitoring

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
- **PostgreSQL over SQLite**: Production scalability, concurrent users, advanced features
- **ChromaDB over in-memory**: Persistent conversation memory, semantic search capabilities
- **Railway over Heroku**: Better Python support, integrated PostgreSQL, competitive pricing
- **Multi-agent system**: Specialized agents for mentoring, analysis, and spaced repetition

### Performance Characteristics
- **API Response Time**: < 200ms for cached responses, < 2s for new conversations
- **Memory Search**: < 100ms for similarity search across thousands of conversations  
- **Database Queries**: Optimized with SQLAlchemy, connection pooling, query caching
- **Scalability**: Handles 100+ concurrent users with current architecture

## Project Status & Metrics

### ✅ Completed Features
- Production-ready FastAPI backend with comprehensive API
- PostgreSQL database with proper relationships and migrations
- ChromaDB vector store with semantic conversation search
- Multi-agent system (strict mentor + curator + flashcard agents)  
- Railway deployment configuration with one-command setup
- Comprehensive test coverage (>80%) with automated testing
- Memory system with learning pattern analysis
- Health monitoring and system statistics endpoints

### 📊 Current Metrics
- **API Endpoints**: 6 core endpoints fully functional
- **Test Coverage**: >80% with unit and integration tests
- **Database Models**: 4 tables with proper relationships
- **Vector Storage**: Semantic search across user conversations
- **Deployment Ready**: Single-command Railway deployment

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