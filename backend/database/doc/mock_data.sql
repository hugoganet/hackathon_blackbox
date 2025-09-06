-- Dev Mentor AI - Coherent Mock Data
-- 3 Realistic Developer Profiles with Learning Progression

-- ===========================================
-- MOCK USERS (3 Different Developer Profiles)
-- ===========================================

-- Junior Frontend Developer (Alex)
INSERT INTO users (id_user, username, email, role, created_at) VALUES 
('550e8400-e29b-41d4-a716-446655440001', 'alex_frontend', 'alex@devcompany.com', 'developer', '2024-01-15 09:00:00+00');

-- Mid-level Full-Stack Developer (Maria)
INSERT INTO users (id_user, username, email, role, created_at) VALUES 
('550e8400-e29b-41d4-a716-446655440002', 'maria_fullstack', 'maria@techstartup.io', 'developer', '2023-08-20 14:30:00+00');

-- Senior Backend Developer (David) 
INSERT INTO users (id_user, username, email, role, created_at) VALUES 
('550e8400-e29b-41d4-a716-446655440003', 'david_backend', 'david@enterprise.com', 'developer', '2022-11-10 11:15:00+00');

-- ===========================================
-- REALISTIC SESSIONS FOR EACH DEVELOPER
-- ===========================================

-- Alex's Sessions (Junior Frontend - React struggles)
INSERT INTO sessions (id_session, id_user, title, agent_type, created_at, ended_at, is_active) VALUES 
('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'Understanding React Hooks', 'strict', '2024-01-15 10:00:00+00', '2024-01-15 10:45:00+00', false),
('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'CSS Grid Layout Help', 'strict', '2024-01-18 14:20:00+00', '2024-01-18 15:10:00+00', false),
('660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'JavaScript Array Methods', 'strict', '2024-02-05 09:30:00+00', NULL, true);

-- Maria's Sessions (Full-Stack - Architecture questions)
INSERT INTO sessions (id_session, id_user, title, agent_type, created_at, ended_at, is_active) VALUES 
('660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440002', 'API Design Best Practices', 'normal', '2024-01-10 16:00:00+00', '2024-01-10 16:30:00+00', false),
('660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 'Database Normalization', 'normal', '2024-01-25 11:45:00+00', '2024-01-25 12:15:00+00', false),
('660e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440002', 'React State Management', 'strict', '2024-02-01 13:20:00+00', NULL, true);

-- David's Sessions (Senior Backend - Performance & Architecture)
INSERT INTO sessions (id_session, id_user, title, agent_type, created_at, ended_at, is_active) VALUES 
('660e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440003', 'Microservices Architecture', 'normal', '2024-01-08 10:30:00+00', '2024-01-08 11:00:00+00', false),
('660e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440003', 'Database Performance Tuning', 'normal', '2024-01-22 15:45:00+00', '2024-01-22 16:20:00+00', false),
('660e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440003', 'Kubernetes Deployment', 'curator', '2024-02-03 14:10:00+00', NULL, true);

-- ===========================================
-- REALISTIC INTERACTIONS (Learning Conversations)
-- ===========================================

-- Alex's Interactions (Junior Frontend)
INSERT INTO interactions (id_interaction, id_session, user_message, mentor_response, response_time_ms, created_at, id_domain, id_language, id_intent) VALUES 
('770e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 
 'I''m getting an error "Cannot read property of undefined" when using useState in React. Can you help me fix this?',
 'Great question! Before I help you fix it, let me ask - can you show me the exact line where you''re declaring your useState? What are you trying to store in that state variable?',
 1250, '2024-01-15 10:05:00+00', 6, 6, 1),

('770e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440001',
 'Here''s my code: const [user, setUser] = useState(); and I''m trying to access user.name later',
 'I see the issue! What do you think happens when useState() is called without an initial value? What would user contain before any data is loaded?',
 980, '2024-01-15 10:08:00+00', 6, 6, 1),

('770e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440002',
 'How do I center a div both horizontally and vertically using CSS Grid?',
 'Excellent question! Think about CSS Grid''s alignment properties. What two properties do you think control horizontal and vertical alignment in a grid container?',
 750, '2024-01-18 14:25:00+00', 2, 12, 2);

-- Maria's Interactions (Full-Stack)
INSERT INTO interactions (id_interaction, id_session, user_message, mentor_response, response_time_ms, created_at, id_domain, id_language, id_intent) VALUES 
('770e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440004',
 'What''s the best way to structure REST API endpoints for a blog application with posts, comments, and users?',
 'For a blog API, you''ll want to follow RESTful conventions. Consider these endpoints: GET /posts, POST /posts, GET /posts/:id, GET /posts/:id/comments, POST /posts/:id/comments. The key is to think hierarchically - comments belong to posts, posts belong to users. What HTTP methods would you use for updating a post?',
 1450, '2024-01-10 16:03:00+00', 4, 3, 4),

('770e8400-e29b-41d4-a716-446655440005', '660e8400-e29b-41d4-a716-446655440005',
 'I have a users table with repeated address information. Should I normalize this into a separate addresses table?',
 'Good observation! This depends on your use case. If multiple users can share the same address (like family members), or if you need to track address history, normalization makes sense. However, if each user has unique address info and it rarely changes, keeping it denormalized might be simpler. What''s your specific scenario?',
 1120, '2024-01-25 11:50:00+00', 7, 10, 4);

-- David's Interactions (Senior Backend)
INSERT INTO interactions (id_interaction, id_session, user_message, mentor_response, response_time_ms, created_at, id_domain, id_language, id_intent) VALUES 
('770e8400-e29b-41d4-a716-446655440006', '660e8400-e29b-41d4-a716-446655440007',
 'We''re considering breaking our monolith into microservices. What are the key factors to consider for service boundaries?',
 'Service boundaries are crucial for microservices success. Key factors include: business domain boundaries (Domain-Driven Design), data ownership (each service owns its data), team structure (Conway''s Law), and communication patterns. Start by identifying bounded contexts in your domain. What are the main business capabilities in your current monolith?',
 2100, '2024-01-08 10:35:00+00', 4, 3, 4),

('770e8400-e29b-41d4-a716-446655440007', '660e8400-e29b-41d4-a716-446655440008',
 'Our PostgreSQL queries are getting slow as data grows. What indexing strategies should I consider?',
 'Database performance tuning requires analyzing your specific query patterns. Start with EXPLAIN ANALYZE on your slowest queries. Common strategies include: composite indexes for multi-column WHERE clauses, partial indexes for filtered queries, and covering indexes to avoid table lookups. What types of queries are performing poorly? Are they SELECT, JOIN, or aggregate operations?',
 1850, '2024-01-22 15:50:00+00', 10, 10, 6);

-- ===========================================
-- SKILL PROGRESSION DATA (Historical)
-- ===========================================

-- Alex's Skill Progression (Junior Frontend - React focus)
INSERT INTO skill_history (id_user, id_skill, mastery_level, snapshot_date, created_at) VALUES 
('550e8400-e29b-41d4-a716-446655440001', 11, 1, '2024-01-15', '2024-01-15 23:59:00+00'), -- React Hooks - started
('550e8400-e29b-41d4-a716-446655440001', 11, 2, '2024-01-20', '2024-01-20 23:59:00+00'), -- React Hooks - improving
('550e8400-e29b-41d4-a716-446655440001', 11, 2, '2024-02-01', '2024-02-01 23:59:00+00'), -- React Hooks - stable
('550e8400-e29b-41d4-a716-446655440001', 1, 2, '2024-01-15', '2024-01-15 23:59:00+00'),  -- Array Manipulation
('550e8400-e29b-41d4-a716-446655440001', 1, 3, '2024-02-05', '2024-02-05 23:59:00+00'),  -- Array Manipulation - improved
('550e8400-e29b-41d4-a716-446655440001', 3, 2, '2024-01-18', '2024-01-18 23:59:00+00'),  -- Variable Declaration
('550e8400-e29b-41d4-a716-446655440001', 5, 1, '2024-01-18', '2024-01-18 23:59:00+00');  -- Conditional Logic

-- Maria's Skill Progression (Full-Stack - Well-rounded)
INSERT INTO skill_history (id_user, id_skill, mastery_level, snapshot_date, created_at) VALUES 
('550e8400-e29b-41d4-a716-446655440002', 7, 3, '2024-01-10', '2024-01-10 23:59:00+00'), -- MVC Pattern
('550e8400-e29b-41d4-a716-446655440002', 7, 4, '2024-01-25', '2024-01-25 23:59:00+00'), -- MVC Pattern - advanced
('550e8400-e29b-41d4-a716-446655440002', 13, 3, '2024-01-10', '2024-01-10 23:59:00+00'), -- SQL Queries
('550e8400-e29b-41d4-a716-446655440002', 14, 2, '2024-01-25', '2024-01-25 23:59:00+00'), -- Database Design
('550e8400-e29b-41d4-a716-446655440002', 14, 3, '2024-02-01', '2024-02-01 23:59:00+00'), -- Database Design - improved
('550e8400-e29b-41d4-a716-446655440002', 11, 3, '2024-02-01', '2024-02-01 23:59:00+00'), -- React Hooks
('550e8400-e29b-41d4-a716-446655440002', 17, 4, '2024-01-10', '2024-01-10 23:59:00+00'); -- Authentication

-- David's Skill Progression (Senior Backend - Expert level)
INSERT INTO skill_history (id_user, id_skill, mastery_level, snapshot_date, created_at) VALUES 
('550e8400-e29b-41d4-a716-446655440003', 7, 5, '2024-01-08', '2024-01-08 23:59:00+00'),  -- MVC Pattern - expert
('550e8400-e29b-41d4-a716-446655440003', 8, 4, '2024-01-08', '2024-01-08 23:59:00+00'),  -- Component Design
('550e8400-e29b-41d4-a716-446655440003', 13, 5, '2024-01-22', '2024-01-22 23:59:00+00'), -- SQL Queries - expert
('550e8400-e29b-41d4-a716-446655440003', 14, 5, '2024-01-22', '2024-01-22 23:59:00+00'), -- Database Design - expert
('550e8400-e29b-41d4-a716-446655440003', 15, 3, '2024-02-03', '2024-02-03 23:59:00+00'), -- Docker Basics
('550e8400-e29b-41d4-a716-446655440003', 16, 2, '2024-02-03', '2024-02-03 23:59:00+00'), -- CI/CD Pipelines
('550e8400-e29b-41d4-a716-446655440003', 19, 5, '2024-01-22', '2024-01-22 23:59:00+00'), -- Code Optimization - expert
('550e8400-e29b-41d4-a716-446655440003', 20, 4, '2024-01-22', '2024-01-22 23:59:00+00'); -- Memory Management

-- ===========================================
-- FLASHCARDS GENERATED FROM INTERACTIONS
-- ===========================================

-- Alex's Flashcards (React fundamentals)
INSERT INTO flashcards (id_flashcard, question, answer, difficulty, card_type, next_review_date, review_count, id_interaction, id_skill, created_at) VALUES 
('880e8400-e29b-41d4-a716-446655440001',
 'What happens when you call useState() without an initial value in React?',
 'useState() without arguments returns undefined as the initial state value. Always provide an initial value like useState(null) or useState({}) to avoid "Cannot read property" errors.',
 2, 'concept', '2024-02-06', 0, '770e8400-e29b-41d4-a716-446655440001', 11, '2024-01-15 11:00:00+00'),

('880e8400-e29b-41d4-a716-446655440002',
 'Complete this CSS Grid centering code:\n```css\n.container {\n  display: grid;\n  /* Add properties to center content */\n}\n```',
 '```css\n.container {\n  display: grid;\n  place-items: center;\n  /* OR */\n  justify-items: center;\n  align-items: center;\n}\n```',
 3, 'code_completion', '2024-02-07', 1, '770e8400-e29b-41d4-a716-446655440003', 1, '2024-01-18 15:30:00+00');

-- Maria's Flashcards (Architecture concepts)
INSERT INTO flashcards (id_flashcard, question, answer, difficulty, card_type, next_review_date, review_count, id_interaction, id_skill, created_at) VALUES 
('880e8400-e29b-41d4-a716-446655440003',
 'What HTTP methods should be used for these REST operations:\n- Get all posts\n- Create new post\n- Update existing post\n- Delete post',
 'GET /posts (retrieve all)\nPOST /posts (create new)\nPUT /posts/:id (update existing)\nDELETE /posts/:id (remove)',
 3, 'application', '2024-02-08', 2, '770e8400-e29b-41d4-a716-446655440004', 7, '2024-01-10 16:45:00+00');

-- David's Flashcards (Advanced backend)
INSERT INTO flashcards (id_flashcard, question, answer, difficulty, card_type, next_review_date, review_count, id_interaction, id_skill, created_at) VALUES 
('880e8400-e29b-41d4-a716-446655440004',
 'What are the key factors for defining microservice boundaries?',
 '1. Business domain boundaries (DDD)\n2. Data ownership (each service owns its data)\n3. Team structure (Conway''s Law)\n4. Communication patterns\n5. Bounded contexts',
 4, 'concept', '2024-02-09', 1, '770e8400-e29b-41d4-a716-446655440006', 8, '2024-01-08 11:15:00+00'),

('880e8400-e29b-41d4-a716-446655440005',
 'Identify the performance issue:\n```sql\nSELECT * FROM users u \nJOIN orders o ON u.id = o.user_id \nWHERE u.created_at > ''2024-01-01'' \nAND o.status = ''pending'';\n```',
 'Missing indexes! Need:\n1. Index on users.created_at\n2. Composite index on orders(user_id, status)\n3. Avoid SELECT * - specify needed columns\n4. Consider covering index',
 5, 'error_identification', '2024-02-10', 3, '770e8400-e29b-41d4-a716-446655440007', 19, '2024-01-22 16:30:00+00');

-- ===========================================
-- REVIEW SESSIONS (Learning Activity)
-- ===========================================

-- Alex's Review Sessions (Struggling but improving)
INSERT INTO review_sessions (id_user, id_flashcard, success_score, response_time, review_date) VALUES 
('550e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 2, 45, '2024-01-16 09:30:00+00'), -- First attempt - poor
('550e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 4, 32, '2024-01-18 10:15:00+00'), -- Second attempt - better
('550e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440002', 3, 78, '2024-01-19 14:20:00+00'), -- CSS Grid - moderate
('550e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440002', 4, 55, '2024-01-22 11:45:00+00'); -- CSS Grid - improved

-- Maria's Review Sessions (Consistent performance)
INSERT INTO review_sessions (id_user, id_flashcard, success_score, response_time, review_date) VALUES 
('550e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440003', 4, 25, '2024-01-11 16:30:00+00'), -- REST APIs - good
('550e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440003', 5, 18, '2024-01-15 13:45:00+00'), -- REST APIs - excellent
('550e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440003', 5, 15, '2024-01-28 10:20:00+00'); -- REST APIs - mastered

-- David's Review Sessions (Expert level performance)
INSERT INTO review_sessions (id_user, id_flashcard, success_score, response_time, review_date) VALUES 
('550e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440004', 5, 12, '2024-01-09 15:20:00+00'), -- Microservices - expert
('550e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440005', 4, 35, '2024-01-23 11:30:00+00'), -- SQL Performance - good
('550e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440005', 5, 28, '2024-01-25 09:45:00+00'), -- SQL Performance - mastered
('550e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440004', 5, 8, '2024-02-01 14:15:00+00');  -- Microservices - consistent expert

-- ===========================================
-- SUMMARY STATISTICS
-- ===========================================

-- Refresh materialized views to reflect mock data
REFRESH MATERIALIZED VIEW user_stats;
REFRESH MATERIALIZED VIEW domain_stats;

-- Display summary of created mock data
SELECT 'Mock Data Summary' as info;

SELECT 
    'Users Created' as category,
    COUNT(*) as count,
    string_agg(username, ', ') as details
FROM users;

SELECT 
    'Sessions Created' as category,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE is_active = true) as active_sessions
FROM sessions;

SELECT 
    'Interactions Created' as category,
    COUNT(*) as count,
    ROUND(AVG(response_time_ms)) as avg_response_time_ms
FROM interactions;

SELECT 
    'Skill History Records' as category,
    COUNT(*) as count,
    ROUND(AVG(mastery_level), 1) as avg_mastery_level
FROM skill_history;

SELECT 
    'Flashcards Created' as category,
    COUNT(*) as count,
    string_agg(DISTINCT card_type, ', ') as card_types
FROM flashcards;

SELECT 
    'Review Sessions' as category,
    COUNT(*) as count,
    ROUND(AVG(success_score), 1) as avg_success_score
FROM review_sessions;

-- Learning progression by user
SELECT 
    u.username,
    COUNT(DISTINCT s.id_session) as sessions,
    COUNT(i.id_interaction) as interactions,
    ROUND(AVG(sh.mastery_level), 1) as avg_skill_level,
    COUNT(DISTINCT f.id_flashcard) as flashcards_generated,
    COUNT(rs.id_review) as reviews_completed
FROM users u
LEFT JOIN sessions s ON u.id_user = s.id_user
LEFT JOIN interactions i ON s.id_session = i.id_session
LEFT JOIN skill_history sh ON u.id_user = sh.id_user
LEFT JOIN flashcards f ON i.id_interaction = f.id_interaction
LEFT JOIN review_sessions rs ON u.id_user = rs.id_user
GROUP BY u.id_user, u.username
ORDER BY u.username;