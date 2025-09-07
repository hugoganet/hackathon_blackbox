# Database Architecture Documentation

## Overview
This directory contains the database architecture and modeling documentation for the Dev Mentor AI project. The system uses PostgreSQL as the primary database with ChromaDB for vector embeddings.

## Data Modeling Approach

### Conceptual Data Model (MCD)
- **Location**: `doc/dev_mentor_ai.mcd`
- **Tool**: Mocodo for entity-relationship modeling
- **Methodology**: Merise method for French data modeling standards

### Database Implementation ⭐ **PRODUCTION READY**
- **Current**: `models.py` - Comprehensive PostgreSQL-only SQLAlchemy models with native UUID support
- **Operations Layer**: `../database_operations.py` - Complete CRUD operations for all entities
- **Vector Store**: `../memory_store.py` - ChromaDB integration for conversation embeddings
- **Spaced Repetition**: `../spaced_repetition.py` - SM-2 algorithm implementation

## Core Entities

### User Management ⭐ **IMPLEMENTED**
- **USER**: Complete user model with native PostgreSQL UUID primary keys
- **Role-based access**: Multi-role support (developer, manager, admin)
- **Authentication ready**: Password hashing and session management support

### Learning Sessions ⭐ **IMPLEMENTED**
- **SESSION**: Comprehensive session tracking with user relationships and agent type classification
- **INTERACTION**: Detailed message exchanges with response time tracking and vector store integration
- **Agent types**: Full support for "strict", "pydantic_strict", "curator", "flashcard" agents
- **Memory integration**: Vector ID references for ChromaDB embedding storage

### Skill Tracking System ⭐ **IMPLEMENTED**
- **SKILL**: Complete skill taxonomy with domain classification and relationship mapping
- **SKILL_HISTORY**: Daily snapshot system with unique constraints for spaced repetition optimization
- **REF_DOMAIN**: Comprehensive learning domain taxonomy (algorithmic, syntax, debugging, frameworks, etc.)
- **Mastery tracking**: 1-5 scale progression with confidence-based skill level calculation

### Spaced Repetition System ⭐ **IMPLEMENTED**
- **FLASHCARD**: Full SM-2 algorithm integration with difficulty scaling and review scheduling
- **REVIEW_SESSION**: Comprehensive performance tracking with success scores and response times
- **Algorithm implementation**: Complete SM-2 spaced repetition with ease factor calculations and interval optimization
- **Performance analytics**: Success rate tracking and learning curve analysis

### Reference Data System ⭐ **IMPLEMENTED**
- **REF_LANGUAGE**: Complete programming language taxonomy with category classification
- **REF_INTENT**: Interaction type classification for learning analytics
- **REF_DOMAIN**: Skill domain categorization with display ordering and status management
- **Data integrity**: Foreign key constraints and referential integrity throughout all tables

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

## Implementation Status ⭐ **COMPLETED**

### ✅ Phase 1: Foundation (Completed)
- Complete SQLAlchemy models in `models.py` with PostgreSQL-only implementation
- Comprehensive relational schema with 9 core entities
- ChromaDB vector store integration with proper referencing

### ✅ Phase 2: Advanced Features (Completed)
- Complete MCD schema implementation with all entity relationships
- Full reference table system with controlled vocabularies
- Comprehensive skill tracking with daily snapshots and progression analytics
- Complete spaced repetition system with SM-2 algorithm integration

### ✅ Phase 3: Production Optimization (Completed)
- Native PostgreSQL UUID support throughout all models
- Advanced indexing strategies for performance optimization
- Comprehensive CRUD operations layer with error handling
- Production-ready deployment with monitoring and health checks

### 🔄 Phase 4: Advanced Analytics (Ongoing)
- Enhanced materialized views for complex learning analytics
- Advanced reporting and dashboard support
- Performance monitoring and query optimization
- Potential pgvector migration evaluation for large-scale deployment

## Development Guidelines

### Schema Changes ⭐ **PRODUCTION PROCESS**
1. Update MCD file first (`doc/dev_mentor_ai.mcd`) for design validation
2. Generate new Mocodo diagram for visual verification and documentation
3. Update SQLAlchemy models in `models.py` with proper relationships and constraints
4. Update CRUD operations in `../database_operations.py` for new functionality
5. Create comprehensive test coverage in `../../tests/` for all changes
6. Update API endpoints in `../api.py` as needed for new features

### Data Consistency ⭐ **IMPLEMENTED**
- **Reference Tables**: Complete controlled vocabularies for languages, intents, and domains
- **Foreign Key Constraints**: Comprehensive referential integrity across all relationships
- **Database Validation**: Unique constraints and check constraints for data quality
- **UUID Consistency**: Native PostgreSQL UUID types throughout all models

### Performance Optimization ⭐ **IMPLEMENTED**
- **Strategic Indexing**: Optimized indexes on frequently queried columns and relationships
- **Query Optimization**: Efficient JOIN operations and properly structured queries
- **Connection Pooling**: SQLAlchemy session management with connection optimization
- **Caching Strategy**: Reference data caching and query result optimization

## Testing Strategy ⭐ **COMPREHENSIVE**

### Database Testing (30+ Test Files)
- **Unit Tests**: Complete SQLAlchemy model testing with PostgreSQL integration
- **Integration Tests**: Complex query testing and relationship validation
- **End-to-End Tests**: Full workflow testing from API to database
- **Performance Tests**: Query optimization and indexing validation
- **Schema Tests**: Comprehensive MCD model validation and constraint testing

### Data Validation ⭐ **IMPLEMENTED**
- **Referential Integrity**: Automated constraint violation testing
- **Business Rule Validation**: Skill progression logic and spaced repetition algorithm testing
- **Edge Case Handling**: UUID conversion testing and error scenario validation
- **Migration Testing**: Schema change validation and data consistency verification

## Monitoring & Analytics

### Key Metrics ⭐ **OPERATIONAL**
- **User Engagement**: Real-time session tracking and interaction frequency analysis
- **Learning Progression**: Daily skill level changes and mastery progression analytics
- **System Performance**: Sub-50ms query response times with connection pooling
- **Spaced Repetition**: SM-2 algorithm effectiveness and retention rate tracking
- **Data Integrity**: Referential integrity monitoring and constraint validation

### Reporting & Analytics ⭐ **IMPLEMENTED**
- **User Progress Dashboards**: Comprehensive skill progression and learning analytics
- **Flashcard Performance**: Success rate tracking and spaced repetition effectiveness
- **Agent Interaction Analytics**: Conversation analysis and learning outcome measurement
- **System Health Monitoring**: Database performance metrics and error tracking
- **Learning Pattern Analysis**: Knowledge gap identification and personalized recommendation systems