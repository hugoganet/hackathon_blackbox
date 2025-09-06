# Dev Mentor AI - Logical Data Model (LDM)

## Overview

This document defines the Logical Data Model (LDM) for Dev Mentor AI, transforming the conceptual model into a PostgreSQL relational structure optimized for SQLAlchemy.

---

## Core Tables

### 1. USERS (Platform Users)
Storage for developers and managers using the platform.

```sql
CREATE TABLE users (
    id_user UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(20) NOT NULL DEFAULT 'developer',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Validation constraints
    CONSTRAINT users_role_check CHECK (role IN ('developer', 'manager')),
    CONSTRAINT users_username_length CHECK (length(username) >= 3),
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);
```

**Recommended Indexes:**
- `CREATE INDEX idx_users_username ON users(username);` (user lookup)
- `CREATE INDEX idx_users_email ON users(email);` (authentication)
- `CREATE INDEX idx_users_role_active ON users(role, is_active);` (role filtering)

---

### 2. SESSIONS (Conversation Sessions)
Logical grouping of interactions between user and AI agent.

```sql
CREATE TABLE sessions (
    id_session UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_user UUID NOT NULL,
    title VARCHAR(255),
    agent_type VARCHAR(20) NOT NULL DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Foreign keys
    FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE,
    
    -- Validation constraints
    CONSTRAINT sessions_agent_type_check CHECK (agent_type IN ('normal', 'strict', 'curator', 'flashcard')),
    CONSTRAINT sessions_end_after_start CHECK (ended_at IS NULL OR ended_at >= created_at)
);
```

**Recommended Indexes:**
- `CREATE INDEX idx_sessions_user_active ON sessions(id_user, is_active);` (active sessions per user)
- `CREATE INDEX idx_sessions_agent_type ON sessions(agent_type);` (filtering by agent type)
- `CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);` (chronological sorting)

---

### 3. INTERACTIONS (Question/Answer Exchanges)
Storage of individual messages within a session.

```sql
CREATE TABLE interactions (
    id_interaction UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_session UUID NOT NULL,
    user_message TEXT NOT NULL,
    mentor_response TEXT NOT NULL,
    vector_id VARCHAR(255), -- Reference to ChromaDB
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Relations to reference tables
    id_domain INTEGER,
    id_language INTEGER,
    id_intent INTEGER,
    
    -- Foreign keys
    FOREIGN KEY (id_session) REFERENCES sessions(id_session) ON DELETE CASCADE,
    FOREIGN KEY (id_domain) REFERENCES ref_domains(id_domain),
    FOREIGN KEY (id_language) REFERENCES ref_languages(id_language),
    FOREIGN KEY (id_intent) REFERENCES ref_intents(id_intent),
    
    -- Validation constraints
    CONSTRAINT interactions_message_length CHECK (length(user_message) > 0),
    CONSTRAINT interactions_response_length CHECK (length(mentor_response) > 0),
    CONSTRAINT interactions_response_time_positive CHECK (response_time_ms IS NULL OR response_time_ms >= 0)
);
```

**Recommended Indexes:**
- `CREATE INDEX idx_interactions_session ON interactions(id_session, created_at DESC);` (session history)
- `CREATE INDEX idx_interactions_domain ON interactions(id_domain);` (domain analysis)
- `CREATE INDEX idx_interactions_language ON interactions(id_language);` (language filtering)
- `CREATE INDEX idx_interactions_vector_id ON interactions(vector_id);` (ChromaDB link)
- `CREATE INDEX idx_interactions_created_at ON interactions(created_at DESC);` (temporal queries)

---

### 4. SKILLS (Competencies)
Definition of skills to be mastered.

```sql
CREATE TABLE skills (
    id_skill SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    id_domain INTEGER NOT NULL,
    
    -- Foreign keys
    FOREIGN KEY (id_domain) REFERENCES ref_domains(id_domain),
    
    -- Constraints
    CONSTRAINT skills_name_length CHECK (length(name) >= 2)
);
```

**Recommended Indexes:**
- `CREATE INDEX idx_skills_domain ON skills(id_domain);` (grouping by domain)
- `CREATE INDEX idx_skills_name ON skills(name);` (text search)

---

### 5. SKILL_HISTORY (Skill Progress History)
Daily snapshots for spaced repetition algorithm.

```sql
CREATE TABLE skill_history (
    id_history UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_user UUID NOT NULL,
    id_skill INTEGER NOT NULL,
    mastery_level INTEGER NOT NULL DEFAULT 1,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign keys
    FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_skill) REFERENCES skills(id_skill) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT skill_history_mastery_range CHECK (mastery_level BETWEEN 1 AND 5),
    CONSTRAINT skill_history_unique_daily UNIQUE (id_user, id_skill, snapshot_date)
);
```

**Recommended Indexes:**
- `CREATE INDEX idx_skill_history_user_date ON skill_history(id_user, snapshot_date DESC);` (user evolution)
- `CREATE INDEX idx_skill_history_skill_date ON skill_history(id_skill, snapshot_date DESC);` (skill progression)
- `CREATE INDEX idx_skill_history_mastery ON skill_history(mastery_level);` (mastery analysis)

---

### 6. FLASHCARDS (Review Cards)
Spaced repetition system based on interactions.

```sql
CREATE TABLE flashcards (
    id_flashcard UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    difficulty INTEGER NOT NULL DEFAULT 1,
    card_type VARCHAR(50) NOT NULL DEFAULT 'concept',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    next_review_date DATE NOT NULL DEFAULT CURRENT_DATE,
    review_count INTEGER NOT NULL DEFAULT 0,
    
    -- Relations
    id_interaction UUID, -- Flashcard generated from this interaction
    id_skill INTEGER,
    
    -- Foreign keys
    FOREIGN KEY (id_interaction) REFERENCES interactions(id_interaction) ON DELETE SET NULL,
    FOREIGN KEY (id_skill) REFERENCES skills(id_skill),
    
    -- Constraints
    CONSTRAINT flashcards_difficulty_range CHECK (difficulty BETWEEN 1 AND 5),
    CONSTRAINT flashcards_card_type_check CHECK (card_type IN ('concept', 'code_completion', 'error_identification', 'application')),
    CONSTRAINT flashcards_review_count_positive CHECK (review_count >= 0)
);
```

**Recommended Indexes:**
- `CREATE INDEX idx_flashcards_next_review ON flashcards(next_review_date);` (cards to review)
- `CREATE INDEX idx_flashcards_skill ON flashcards(id_skill);` (cards per skill)
- `CREATE INDEX idx_flashcards_difficulty ON flashcards(difficulty);` (difficulty filtering)
- `CREATE INDEX idx_flashcards_interaction ON flashcards(id_interaction);` (link to source interaction)

---

### 7. REVIEW_SESSIONS (Review History)
History of flashcard reviews per user.

```sql
CREATE TABLE review_sessions (
    id_review UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_user UUID NOT NULL,
    id_flashcard UUID NOT NULL,
    success_score INTEGER NOT NULL,
    response_time INTEGER, -- in seconds
    review_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign keys
    FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_flashcard) REFERENCES flashcards(id_flashcard) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT review_sessions_score_range CHECK (success_score BETWEEN 0 AND 5),
    CONSTRAINT review_sessions_response_time_positive CHECK (response_time IS NULL OR response_time > 0)
);
```

**Recommended Indexes:**
- `CREATE INDEX idx_review_sessions_user_date ON review_sessions(id_user, review_date DESC);` (user history)
- `CREATE INDEX idx_review_sessions_flashcard ON review_sessions(id_flashcard, review_date DESC);` (card performance)
- `CREATE INDEX idx_review_sessions_score ON review_sessions(success_score);` (success analysis)

---

## Reference Tables

### REF_DOMAINS (Learning Domains)
```sql
CREATE TABLE ref_domains (
    id_domain SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Initial data
INSERT INTO ref_domains (name, description, display_order) VALUES
('ALGORITHMIC', 'Data structures, complexity, optimization', 1),
('SYNTAX', 'Language syntax mastery', 2),
('LOGIC', 'Programming logic, control structures', 3),
('ARCHITECTURE', 'Design patterns, code organization', 4),
('DEBUGGING', 'Error resolution, testing, troubleshooting', 5),
('FRAMEWORKS', 'React, Angular, Spring, etc.', 6),
('DATABASES', 'SQL, NoSQL, data modeling', 7),
('DEVOPS', 'Deployment, CI/CD, containerization', 8),
('SECURITY', 'Application security, authentication', 9),
('PERFORMANCE', 'Optimization, monitoring, scaling', 10);
```

### REF_LANGUAGES (Programming Languages)
```sql
CREATE TABLE ref_languages (
    id_language SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(30),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Initial data
INSERT INTO ref_languages (name, category) VALUES
('JavaScript', 'Frontend'),
('TypeScript', 'Frontend'),
('Python', 'Backend'),
('Java', 'Backend'),
('Go', 'Backend'),
('React', 'Framework'),
('Vue.js', 'Framework'),
('Angular', 'Framework'),
('Node.js', 'Runtime'),
('SQL', 'Database');
```

### REF_INTENTS (Intent Types)
```sql
CREATE TABLE ref_intents (
    id_intent SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- Initial data
INSERT INTO ref_intents (name, description) VALUES
('debugging', 'Error resolution and troubleshooting'),
('concept_explanation', 'Understanding programming concepts'),
('code_review', 'Code quality and best practices'),
('architecture', 'System design and architecture'),
('best_practices', 'Industry standards and conventions'),
('performance', 'Optimization and performance tuning'),
('learning_path', 'Educational guidance and progression');
```

---

## Constraints and Triggers

### Automatic update trigger
```sql
-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to users table
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Additional business constraints
```sql
-- A user cannot review the same flashcard multiple times on the same day
CREATE UNIQUE INDEX idx_one_review_per_day 
ON review_sessions(id_user, id_flashcard, DATE(review_date));

-- Sessions must have at least one interaction to be considered complete
-- (to be implemented via application logic or deferred CHECK constraint)
```

---

## Partitioning Strategy

### For high-volume tables
```sql
-- Partitioning skill_history by month (for historical data)
CREATE TABLE skill_history_template (
    LIKE skill_history INCLUDING DEFAULTS INCLUDING CONSTRAINTS
);

-- Example monthly partition
CREATE TABLE skill_history_2024_01 
PARTITION OF skill_history_template 
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

---

## Performance and Monitoring

### Recommended materialized views
```sql
-- User statistics view
CREATE MATERIALIZED VIEW user_stats AS
SELECT 
    u.id_user,
    u.username,
    COUNT(DISTINCT s.id_session) as total_sessions,
    COUNT(i.id_interaction) as total_interactions,
    AVG(sh.mastery_level) as avg_mastery_level,
    MAX(i.created_at) as last_activity
FROM users u
LEFT JOIN sessions s ON u.id_user = s.id_user
LEFT JOIN interactions i ON s.id_session = i.id_session
LEFT JOIN skill_history sh ON u.id_user = sh.id_user
WHERE u.is_active = true
GROUP BY u.id_user, u.username;

-- Periodic refresh recommended
CREATE INDEX ON user_stats(id_user);
```

### Performance monitoring
```sql
-- Monitor slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE query LIKE '%interactions%' 
ORDER BY mean_time DESC;
```

---

## Migration from Current Schema

### Migration script
```sql
-- 1. Backup existing data
CREATE TABLE users_backup AS SELECT * FROM users;
CREATE TABLE conversations_backup AS SELECT * FROM conversations;
CREATE TABLE interactions_backup AS SELECT * FROM interactions;

-- 2. Add new columns
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'developer';
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);

-- 3. Data migration
-- (specific scripts depending on required transformations)

-- 4. Create new tables
-- (use CREATE TABLE scripts above)
```

This LDM is optimized for PostgreSQL with SQLAlchemy and ready for implementation of the AI mentoring system with spaced repetition.