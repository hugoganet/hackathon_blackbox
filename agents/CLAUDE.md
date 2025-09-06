# AI Agents System Documentation

## Overview

This directory contains the comprehensive AI agent system for the Dev Mentor AI platform. The system implements a multi-agent architecture designed to provide personalized learning experiences through specialized AI agents, each optimized for specific educational functions.

## Agent Architecture

### Multi-Agent Design Philosophy

The system employs three specialized agents working in harmony to deliver a complete learning experience:

1. **Educational Interaction** (Strict Mentor Agent)
2. **Learning Analysis** (Curator Agent)  
3. **Memory Reinforcement** (Flashcard Agent)

This separation of concerns ensures each agent can be optimized for its specific function while maintaining system modularity and scalability.

## Agent Specifications

### 1. Strict Mentor Agent (`../agent-mentor-strict.md`)

**Purpose**: Primary educational interface using Socratic methodology

**File Location**: `/Users/hugoganet/Code/dev_mentor_ai/agent-mentor-strict.md`

**Core Principles**:
- **Absolute no-direct-answers policy**: Never provides complete solutions
- **Socratic questioning**: Guides discovery through progressive hints
- **Autonomy development**: Builds independent problem-solving skills
- **Resilient pedagogy**: Maintains teaching approach even under pressure

**Educational Approach**:
- Progressive hint system
- Confidence building through small victories
- Critical thinking development
- Mistake-tolerant learning environment

**Target Audience**: Junior developers and beginners
**Response Style**: Encouraging, patient, methodical questioning
**Success Metric**: Student autonomy and problem-solving capability development

### 2. Curator Agent (`../curator-agent.md`)

**Purpose**: Conversation analysis and learning data extraction

**File Location**: `/Users/hugoganet/Code/dev_mentor_ai/curator-agent.md`

**Core Functions**:
- **Interaction processing**: Analyzes mentor-student conversations
- **Skills identification**: Extracts demonstrated and discussed competencies
- **Mistake cataloging**: Identifies specific errors and misconceptions
- **Gap analysis**: Determines knowledge areas needing reinforcement
- **Confidence assessment**: Evaluates student understanding levels

**Output Format**: Structured JSON for database storage and algorithm input
```json
{
  "skills": ["specific technical skills"],
  "mistakes": ["concrete errors made"],
  "openQuestions": ["knowledge gaps identified"],
  "nextSteps": ["actionable learning recommendations"],
  "confidence": 0.0-1.0
}
```

**Integration**: Feeds spaced repetition algorithm and learning analytics

### 3. Flashcard Agent (`../flashcard-agent.md`)

**Purpose**: Spaced repetition content generation and optimization

**File Location**: `/Users/hugoganet/Code/dev_mentor_ai/flashcard-agent.md`

**Card Types**:
- **Concept Definition**: Basic understanding verification
- **Code Completion**: Practical application testing
- **Error Identification**: Debugging skill development
- **Application Scenarios**: When/why usage understanding
- **Comparison Cards**: Distinguishing similar concepts

**Personalization Features**:
- Difficulty adaptation based on user skill level
- Content prioritization from curator analysis
- Multiple card variations for concept reinforcement
- Progressive complexity building

**Spaced Repetition Optimization**:
- Initial interval assignment based on confidence levels
- Review scheduling integration
- Memory retention tracking
- Adaptive difficulty adjustment

## Agent Interaction Workflow

### 1. Learning Session Flow
```
Student Question → Strict Mentor → Socratic Dialogue → Learning Interaction
                      ↓
Conversation Text → Curator Agent → Structured Analysis → Learning Data
                      ↓
Learning Data → Flashcard Agent → Optimized Cards → Spaced Repetition System
```

### 2. Data Flow Architecture
- **Input**: Raw student questions and learning challenges
- **Processing**: Multi-agent analysis and response generation
- **Output**: Educational responses + structured learning data + spaced repetition content
- **Storage**: PostgreSQL (conversations) + ChromaDB (embeddings) + Flashcard system

### 3. Feedback Loop
- Student progress data informs agent behavior
- Learning pattern analysis improves personalization
- Spaced repetition effectiveness guides content generation
- Long-term memory system enhances context awareness

## Technical Implementation

### Agent Prompts Location
- **Project Root Level**: All agent prompt files are stored in the project root directory (/Users/hugoganet/Code/dev_mentor_ai/)
  - `agent-mentor-strict.md`: Socratic method teaching agent
  - `curator-agent.md`: Conversation analysis and learning extraction agent  
  - `flashcard-agent.md`: Spaced repetition content generation agent
- **Version Control**: All prompts tracked in Git for change management
- **Deployment**: Agents loaded dynamically via FastAPI backend from root directory
- **Documentation**: Agent system documentation maintained in `/agents/CLAUDE.md`

### Integration with Backend Systems

**FastAPI Integration**:
- Agent selection via `agent_type` parameter
- Dynamic prompt loading from markdown files
- Response processing and formatting
- Error handling and fallback mechanisms

**Database Integration**:
- Conversation storage for context continuity
- Learning analytics data persistence
- User progress tracking
- Spaced repetition scheduling

**Memory System Integration**:
- ChromaDB vector storage for semantic search
- Conversation context retrieval
- Learning pattern analysis
- Similar question identification

## Performance Characteristics

### Response Time Targets
- **Mentor Agent**: < 2s for educational responses
- **Curator Agent**: < 500ms for conversation analysis
- **Flashcard Agent**: < 300ms for card generation

### Scalability Considerations
- Stateless agent design for horizontal scaling
- Efficient prompt processing and caching
- Optimized database queries for user data
- Vector search optimization for memory retrieval

### Quality Metrics
- **Educational Effectiveness**: Student progress tracking
- **Engagement Levels**: Session duration and frequency
- **Learning Retention**: Spaced repetition success rates
- **Satisfaction Scores**: User feedback and ratings

## Development Guidelines

### Agent Prompt Engineering
- Clear, specific instructions for consistent behavior
- Comprehensive edge case handling
- Maintainable and modular prompt structure
- Regular testing and validation of agent responses

### Testing Strategy
- Unit tests for individual agent functionality
- Integration tests for agent interaction workflows
- Educational effectiveness testing with real users
- Performance benchmarking and optimization

### Monitoring and Analytics
- Agent response quality tracking
- Learning outcome measurement
- System performance monitoring
- User experience optimization

## Future Enhancements

### Planned Agent Additions
- **Code Review Agent**: Specialized code quality feedback
- **Project Guide Agent**: Long-term project mentoring
- **Collaboration Agent**: Peer learning facilitation
- **Assessment Agent**: Skill evaluation and testing

### Advanced Features
- **Multi-modal Learning**: Support for images, videos, interactive content
- **Personalization Engine**: Advanced user modeling and adaptation
- **Learning Path Optimization**: AI-driven curriculum customization
- **Real-time Collaboration**: Multi-user learning sessions

### Technology Upgrades
- **LangGraph Integration**: Advanced agent orchestration
- **pgvector Migration**: Enhanced vector search capabilities
- **Edge Computing**: Reduced latency agent deployment
- **Advanced Analytics**: ML-powered learning insights

## Agent Configuration

### Environment Variables
```bash
BLACKBOX_API_KEY=your_api_key_here    # Required for all agents
AGENT_RESPONSE_TIMEOUT=30             # Maximum response time in seconds
AGENT_MAX_RETRIES=3                   # Retry attempts for failed requests
CURATOR_CONFIDENCE_THRESHOLD=0.7      # Confidence scoring calibration
FLASHCARD_GENERATION_LIMIT=5          # Maximum cards per request
```

### Agent Behavior Tuning
- Response length limits for optimal user experience
- Difficulty scaling parameters for personalization
- Learning pattern recognition sensitivity
- Spaced repetition algorithm parameters

This multi-agent system represents the core educational engine of the Dev Mentor AI platform, designed to scale from individual learners to enterprise-wide developer education programs.