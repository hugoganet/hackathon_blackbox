-- Dev Mentor AI - PostgreSQL Schema Creation Script
-- Generated from LDM specification
-- Compatible with SQLAlchemy migrations

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ===========================================
-- REFERENCE TABLES (Create first for FK dependencies)
-- ===========================================

-- Learning domains reference
CREATE TABLE ref_domains (
    id_domain SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Programming languages reference
CREATE TABLE ref_languages (
    id_language SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(30),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Intent types reference
CREATE TABLE ref_intents (
    id_intent SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ===========================================
-- CORE TABLES
-- ===========================================

-- Users table
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

-- Sessions table
CREATE TABLE sessions (
    id_session UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_user UUID NOT NULL,
    title VARCHAR(255),
    agent_type VARCHAR(20) NOT NULL DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Foreign keys
    CONSTRAINT fk_sessions_user FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE,
    
    -- Validation constraints
    CONSTRAINT sessions_agent_type_check CHECK (agent_type IN ('normal', 'strict', 'curator', 'flashcard')),
    CONSTRAINT sessions_end_after_start CHECK (ended_at IS NULL OR ended_at >= created_at)
);

-- Skills table
CREATE TABLE skills (
    id_skill SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    id_domain INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign keys
    CONSTRAINT fk_skills_domain FOREIGN KEY (id_domain) REFERENCES ref_domains(id_domain),
    
    -- Constraints
    CONSTRAINT skills_name_length CHECK (length(name) >= 2)
);

-- Interactions table
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
    CONSTRAINT fk_interactions_session FOREIGN KEY (id_session) REFERENCES sessions(id_session) ON DELETE CASCADE,
    CONSTRAINT fk_interactions_domain FOREIGN KEY (id_domain) REFERENCES ref_domains(id_domain),
    CONSTRAINT fk_interactions_language FOREIGN KEY (id_language) REFERENCES ref_languages(id_language),
    CONSTRAINT fk_interactions_intent FOREIGN KEY (id_intent) REFERENCES ref_intents(id_intent),
    
    -- Validation constraints
    CONSTRAINT interactions_message_length CHECK (length(user_message) > 0),
    CONSTRAINT interactions_response_length CHECK (length(mentor_response) > 0),
    CONSTRAINT interactions_response_time_positive CHECK (response_time_ms IS NULL OR response_time_ms >= 0)
);

-- Skill history table
CREATE TABLE skill_history (
    id_history UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_user UUID NOT NULL,
    id_skill INTEGER NOT NULL,
    mastery_level INTEGER NOT NULL DEFAULT 1,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign keys
    CONSTRAINT fk_skill_history_user FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE,
    CONSTRAINT fk_skill_history_skill FOREIGN KEY (id_skill) REFERENCES skills(id_skill) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT skill_history_mastery_range CHECK (mastery_level BETWEEN 1 AND 5),
    CONSTRAINT skill_history_unique_daily UNIQUE (id_user, id_skill, snapshot_date)
);

-- Flashcards table
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
    CONSTRAINT fk_flashcards_interaction FOREIGN KEY (id_interaction) REFERENCES interactions(id_interaction) ON DELETE SET NULL,
    CONSTRAINT fk_flashcards_skill FOREIGN KEY (id_skill) REFERENCES skills(id_skill),
    
    -- Constraints
    CONSTRAINT flashcards_difficulty_range CHECK (difficulty BETWEEN 1 AND 5),
    CONSTRAINT flashcards_card_type_check CHECK (card_type IN ('concept', 'code_completion', 'error_identification', 'application')),
    CONSTRAINT flashcards_review_count_positive CHECK (review_count >= 0)
);

-- Review sessions table
CREATE TABLE review_sessions (
    id_review UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_user UUID NOT NULL,
    id_flashcard UUID NOT NULL,
    success_score INTEGER NOT NULL,
    response_time INTEGER, -- in seconds
    review_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign keys
    CONSTRAINT fk_review_sessions_user FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE,
    CONSTRAINT fk_review_sessions_flashcard FOREIGN KEY (id_flashcard) REFERENCES flashcards(id_flashcard) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT review_sessions_score_range CHECK (success_score BETWEEN 0 AND 5),
    CONSTRAINT review_sessions_response_time_positive CHECK (response_time IS NULL OR response_time > 0)
);

-- ===========================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ===========================================

-- Users indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role_active ON users(role, is_active);

-- Sessions indexes
CREATE INDEX idx_sessions_user_active ON sessions(id_user, is_active);
CREATE INDEX idx_sessions_agent_type ON sessions(agent_type);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);

-- Interactions indexes
CREATE INDEX idx_interactions_session ON interactions(id_session, created_at DESC);
CREATE INDEX idx_interactions_domain ON interactions(id_domain);
CREATE INDEX idx_interactions_language ON interactions(id_language);
CREATE INDEX idx_interactions_intent ON interactions(id_intent);
CREATE INDEX idx_interactions_vector_id ON interactions(vector_id);
CREATE INDEX idx_interactions_created_at ON interactions(created_at DESC);

-- Skills indexes
CREATE INDEX idx_skills_domain ON skills(id_domain);
CREATE INDEX idx_skills_name ON skills(name);

-- Skill history indexes
CREATE INDEX idx_skill_history_user_date ON skill_history(id_user, snapshot_date DESC);
CREATE INDEX idx_skill_history_skill_date ON skill_history(id_skill, snapshot_date DESC);
CREATE INDEX idx_skill_history_mastery ON skill_history(mastery_level);

-- Flashcards indexes
CREATE INDEX idx_flashcards_next_review ON flashcards(next_review_date);
CREATE INDEX idx_flashcards_skill ON flashcards(id_skill);
CREATE INDEX idx_flashcards_difficulty ON flashcards(difficulty);
CREATE INDEX idx_flashcards_interaction ON flashcards(id_interaction);

-- Review sessions indexes
CREATE INDEX idx_review_sessions_user_date ON review_sessions(id_user, review_date DESC);
CREATE INDEX idx_review_sessions_flashcard ON review_sessions(id_flashcard, review_date DESC);
CREATE INDEX idx_review_sessions_score ON review_sessions(success_score);

-- Special constraint index
CREATE UNIQUE INDEX idx_one_review_per_day 
ON review_sessions(id_user, id_flashcard, DATE(review_date));

-- ===========================================
-- TRIGGERS AND FUNCTIONS
-- ===========================================

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

-- ===========================================
-- INITIAL REFERENCE DATA
-- ===========================================

-- Insert learning domains
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

-- Insert programming languages
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
('SQL', 'Database'),
('HTML', 'Markup'),
('CSS', 'Styling'),
('Docker', 'DevOps'),
('Kubernetes', 'DevOps'),
('Git', 'VCS');

-- Insert intent types
INSERT INTO ref_intents (name, description) VALUES
('debugging', 'Error resolution and troubleshooting'),
('concept_explanation', 'Understanding programming concepts'),
('code_review', 'Code quality and best practices'),
('architecture', 'System design and architecture'),
('best_practices', 'Industry standards and conventions'),
('performance', 'Optimization and performance tuning'),
('learning_path', 'Educational guidance and progression'),
('project_setup', 'Environment and project configuration'),
('testing', 'Testing strategies and implementation'),
('deployment', 'Application deployment and DevOps');

-- Insert initial skills (examples)
INSERT INTO skills (name, description, id_domain) VALUES
('Array Manipulation', 'Working with arrays and collections', 1),
('Big O Notation', 'Understanding algorithm complexity', 1),
('Variable Declaration', 'Proper variable naming and scoping', 2),
('Function Syntax', 'Function declaration and expression syntax', 2),
('Conditional Logic', 'If/else statements and boolean logic', 3),
('Loop Structures', 'For, while, and iterator patterns', 3),
('MVC Pattern', 'Model-View-Controller architecture', 4),
('Component Design', 'Reusable component architecture', 4),
('Console Debugging', 'Using browser and IDE debugging tools', 5),
('Error Handling', 'Try/catch and error management', 5),
('React Hooks', 'useState, useEffect, and custom hooks', 6),
('React Router', 'Client-side routing in React applications', 6),
('SQL Queries', 'SELECT, JOIN, and data retrieval', 7),
('Database Design', 'Normalization and schema design', 7),
('Docker Basics', 'Container creation and management', 8),
('CI/CD Pipelines', 'Automated testing and deployment', 8),
('Authentication', 'User login and session management', 9),
('Input Validation', 'Sanitization and security checks', 9),
('Code Optimization', 'Performance improvement techniques', 10),
('Memory Management', 'Efficient resource utilization', 10);

-- ===========================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- ===========================================

-- User statistics view
CREATE MATERIALIZED VIEW user_stats AS
SELECT 
    u.id_user,
    u.username,
    u.role,
    COUNT(DISTINCT s.id_session) as total_sessions,
    COUNT(i.id_interaction) as total_interactions,
    COALESCE(AVG(sh.mastery_level), 1) as avg_mastery_level,
    MAX(i.created_at) as last_activity,
    u.created_at as user_since
FROM users u
LEFT JOIN sessions s ON u.id_user = s.id_user
LEFT JOIN interactions i ON s.id_session = i.id_session
LEFT JOIN skill_history sh ON u.id_user = sh.id_user AND sh.snapshot_date = CURRENT_DATE
WHERE u.is_active = true
GROUP BY u.id_user, u.username, u.role, u.created_at;

CREATE INDEX idx_user_stats_user ON user_stats(id_user);
CREATE INDEX idx_user_stats_activity ON user_stats(last_activity DESC);

-- Domain popularity view
CREATE MATERIALIZED VIEW domain_stats AS
SELECT 
    rd.name as domain_name,
    rd.id_domain,
    COUNT(i.id_interaction) as interaction_count,
    COUNT(DISTINCT i.id_session) as session_count,
    AVG(i.response_time_ms) as avg_response_time,
    COUNT(DISTINCT DATE(i.created_at)) as active_days
FROM ref_domains rd
LEFT JOIN interactions i ON rd.id_domain = i.id_domain
WHERE rd.is_active = true
GROUP BY rd.id_domain, rd.name
ORDER BY interaction_count DESC;

CREATE INDEX idx_domain_stats_domain ON domain_stats(id_domain);

-- ===========================================
-- COMMENTS FOR DOCUMENTATION
-- ===========================================

COMMENT ON TABLE users IS 'Platform users (developers and managers)';
COMMENT ON TABLE sessions IS 'Conversation sessions between users and AI agents';
COMMENT ON TABLE interactions IS 'Individual message exchanges within sessions';
COMMENT ON TABLE skills IS 'Learning competencies to be mastered';
COMMENT ON TABLE skill_history IS 'Daily snapshots of user skill progression';
COMMENT ON TABLE flashcards IS 'Spaced repetition learning cards';
COMMENT ON TABLE review_sessions IS 'History of flashcard review performance';

COMMENT ON TABLE ref_domains IS 'Learning domain categories';
COMMENT ON TABLE ref_languages IS 'Programming languages reference';
COMMENT ON TABLE ref_intents IS 'Interaction intent categories';

COMMENT ON COLUMN interactions.vector_id IS 'Reference to ChromaDB embedding';
COMMENT ON COLUMN skill_history.mastery_level IS 'Skill level from 1 (novice) to 5 (expert)';
COMMENT ON COLUMN flashcards.next_review_date IS 'Calculated by spaced repetition algorithm';

-- ===========================================
-- SCHEMA VALIDATION
-- ===========================================

-- Verify all tables were created
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public'
    AND tablename IN (
        'users', 'sessions', 'interactions', 'skills', 
        'skill_history', 'flashcards', 'review_sessions',
        'ref_domains', 'ref_languages', 'ref_intents'
    )
ORDER BY tablename;

-- Verify reference data was inserted
SELECT 'ref_domains' as table_name, count(*) as record_count FROM ref_domains
UNION ALL
SELECT 'ref_languages' as table_name, count(*) as record_count FROM ref_languages
UNION ALL
SELECT 'ref_intents' as table_name, count(*) as record_count FROM ref_intents
UNION ALL
SELECT 'skills' as table_name, count(*) as record_count FROM skills;

-- Success message
SELECT 'Dev Mentor AI database schema created successfully!' as status;