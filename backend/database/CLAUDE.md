# Database Architecture Documentation

## Overview
This directory contains the database architecture and modeling documentation for the Dev Mentor AI project. The system uses PostgreSQL as the primary database with ChromaDB for vector embeddings.

## Data Modeling Approach

### Conceptual Data Model (MCD)
- **Location**: `doc/dev_mentor_ai.mcd`
- **Tool**: Mocodo for entity-relationship modeling
- **Methodology**: Merise method for French data modeling standards

### Database Implementation
- **Current**: `database.py` - SQLAlchemy models for PostgreSQL/SQLite
- **Vector Store**: `memory_store.py` - ChromaDB for conversation embeddings

## Core Entities

### User Management
- **USER**: Developers and managers using the platform
- **Role-based access**: `role` field distinguishes developers from managers

### Learning Sessions
- **SESSION**: Conversation sessions between users and AI mentors
- **INTERACTION**: Individual message exchanges within sessions
- **Agent types**: "strict", "normal", "curator", "flashcard"

### Skill Tracking
- **SKILL**: Competencies being developed
- **SKILL_HISTORY**: Daily snapshots for spaced repetition algorithm
- **REF_DOMAIN**: Learning domains (algorithmic, syntax, logic, etc.)

### Spaced Repetition System
- **FLASHCARD**: Generated learning cards from interactions
- **REVIEW_SESSION**: User flashcard review tracking
- **Spaced repetition**: Algorithm-driven review scheduling

### Reference Data
- **REF_LANGUAGE**: Programming languages (controlled vocabulary)
- **REF_INTENT**: Interaction types (debugging, concept explanation, etc.)
- **REF_DOMAIN**: Learning domains for skill classification

## Design Decisions

### Vector Memory Integration
**Choice**: Keep ChromaDB external to relational model
- **Rationale**: Simpler prototyping, optimized performance
- **Implementation**: `vector_id` field links interactions to embeddings
- **Future**: Potential migration to pgvector for scale

### Skill Tracking Granularity
**Choice**: Daily snapshots via SKILL_HISTORY
- **Rationale**: Enables fine-grained progress tracking
- **Use case**: Spaced repetition algorithm optimization
- **Gamification**: Detailed progress visualization

### Reference Tables Strategy
**Choice**: Controlled vocabularies over ENUMs
- **Rationale**: Data consistency and UI standardization
- **Benefits**: Analytics reliability, easy extension
- **Example**: REF_LANGUAGE prevents "JavaScript" vs "javascript" inconsistencies

## Domain Classification

### Learning Domains (REF_DOMAIN)
- **ALGORITHMIC**: Data structures, complexity, optimization
- **SYNTAX**: Language syntax mastery
- **LOGIC**: Programming logic, control structures
- **ARCHITECTURE**: Design patterns, code organization
- **DEBUGGING**: Error resolution, testing, troubleshooting
- **FRAMEWORKS**: React, Angular, Spring, etc.
- **DATABASES**: SQL, NoSQL, data modeling
- **DEVOPS**: Deployment, CI/CD, containerization
- **SECURITY**: Application security, authentication
- **PERFORMANCE**: Optimization, monitoring, scaling

## Mocodo Usage

### Generate SVG Diagram
```bash
# Install Mocodo
pip install mocodo

# Generate diagram from MCD file
mocodo database/doc/dev_mentor_ai.mcd
```

### MCD Syntax Reference
- **Entities**: `ENTITY: attribute1, attribute2, ...`
- **Relationships**: `RELATION, CardinalityA EntityA, CardinalityB EntityB`
- **Association attributes**: Listed after the colon in relationships
- **Cardinalities**: `0N` (zero to many), `1N` (one to many), `11` (one to one), `01` (zero to one)

## Migration Strategy

### Phase 1: Current Implementation
- SQLAlchemy models in `database.py`
- Basic PostgreSQL schema
- ChromaDB for vector storage

### Phase 2: Enhanced Schema (Planned)
- Implement full MCD schema
- Add reference tables
- Skill tracking system
- Flashcard generation

### Phase 3: Scale Optimization (Future)
- Consider pgvector migration
- Advanced indexing strategies
- Performance optimization
- Analytics materialized views

## Development Guidelines

### Schema Changes
1. Update MCD file first (`doc/dev_mentor_ai.mcd`)
2. Generate new Mocodo diagram for validation
3. Update SQLAlchemy models in `database.py`
4. Create Alembic migration scripts
5. Update API endpoints as needed

### Data Consistency
- Use reference tables for controlled vocabularies
- Implement proper foreign key constraints
- Add database-level validation where appropriate
- Maintain referential integrity

### Performance Considerations
- Index frequently queried columns
- Consider partitioning for SKILL_HISTORY (time-series data)
- Optimize vector similarity searches
- Cache reference data in application layer

## Testing Strategy

### Database Testing
- Unit tests for SQLAlchemy models
- Integration tests for complex queries
- Migration testing for schema changes
- Performance testing for vector operations

### Data Validation
- Referential integrity checks
- Business rule validation
- Edge case handling
- Data migration verification

## Monitoring & Analytics

### Key Metrics
- User engagement (sessions per day)
- Learning progression (skill level changes)
- System performance (query response times)
- Memory store efficiency (similarity search accuracy)

### Reporting Needs
- User progress dashboards
- Skill mastery analytics
- Agent effectiveness metrics
- System health monitoring