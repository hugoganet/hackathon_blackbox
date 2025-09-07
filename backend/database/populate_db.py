"""
Populate database with mock data using SQLAlchemy ORM
Run this script to seed the database with realistic test data
"""

from datetime import datetime, timedelta, date
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

# Import all models
from models import (
    Base, User, Session as ChatSession, Interaction, Skill, SkillHistory,
    Flashcard, ReviewSession, RefDomain, RefLanguage, RefIntent
)

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/dev_mentor_ai")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def clear_database():
    """Clear all existing data (careful!)"""
    print("🗑️  Clearing existing data...")
    
    # Use raw SQL to force drop all tables with CASCADE
    with engine.connect() as conn:
        print("  - Force dropping all tables...")
        
        # Get all table names
        result = conn.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT LIKE 'pg_%'
        """))
        
        tables = [row[0] for row in result.fetchall()]
        
        # Drop each table with CASCADE
        for table in tables:
            print(f"    - Dropping {table}")
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        
        conn.commit()
    
    # Now create all tables from our models
    print("  - Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database cleared and recreated")


def populate_reference_data(db: Session):
    """Populate reference tables"""
    print("📚 Populating reference data...")
    
    # Domains
    domains = [
        RefDomain(name='ALGORITHMIC', description='Data structures, complexity, optimization', display_order=1),
        RefDomain(name='SYNTAX', description='Language syntax mastery', display_order=2),
        RefDomain(name='LOGIC', description='Programming logic, control structures', display_order=3),
        RefDomain(name='ARCHITECTURE', description='Design patterns, code organization', display_order=4),
        RefDomain(name='DEBUGGING', description='Error resolution, testing, troubleshooting', display_order=5),
        RefDomain(name='FRAMEWORKS', description='React, Angular, Spring, etc.', display_order=6),
        RefDomain(name='DATABASES', description='SQL, NoSQL, data modeling', display_order=7),
        RefDomain(name='DEVOPS', description='Deployment, CI/CD, containerization', display_order=8),
        RefDomain(name='SECURITY', description='Application security, authentication', display_order=9),
        RefDomain(name='PERFORMANCE', description='Optimization, monitoring, scaling', display_order=10),
    ]
    db.add_all(domains)
    
    # Languages
    languages = [
        RefLanguage(name='JavaScript', category='Frontend'),
        RefLanguage(name='TypeScript', category='Frontend'),
        RefLanguage(name='Python', category='Backend'),
        RefLanguage(name='Java', category='Backend'),
        RefLanguage(name='Go', category='Backend'),
        RefLanguage(name='React', category='Framework'),
        RefLanguage(name='Vue.js', category='Framework'),
        RefLanguage(name='Angular', category='Framework'),
        RefLanguage(name='Node.js', category='Runtime'),
        RefLanguage(name='SQL', category='Database'),
        RefLanguage(name='HTML', category='Markup'),
        RefLanguage(name='CSS', category='Styling'),
    ]
    db.add_all(languages)
    
    # Intents
    intents = [
        RefIntent(name='debugging', description='Error resolution and troubleshooting'),
        RefIntent(name='concept_explanation', description='Understanding programming concepts'),
        RefIntent(name='code_review', description='Code quality and best practices'),
        RefIntent(name='architecture', description='System design and architecture'),
        RefIntent(name='best_practices', description='Industry standards and conventions'),
        RefIntent(name='performance', description='Optimization and performance tuning'),
        RefIntent(name='learning_path', description='Educational guidance and progression'),
    ]
    db.add_all(intents)
    
    db.commit()
    print("✅ Reference data populated")
    return domains, languages, intents


def populate_skills(db: Session, domains):
    """Populate skills table"""
    print("🎯 Populating skills...")
    
    skills = [
        Skill(name='Array Manipulation', description='Working with arrays and collections', domain_id=domains[0].id),
        Skill(name='Big O Notation', description='Understanding algorithm complexity', domain_id=domains[0].id),
        Skill(name='Variable Declaration', description='Proper variable naming and scoping', domain_id=domains[1].id),
        Skill(name='Function Syntax', description='Function declaration and expression syntax', domain_id=domains[1].id),
        Skill(name='Conditional Logic', description='If/else statements and boolean logic', domain_id=domains[2].id),
        Skill(name='Loop Structures', description='For, while, and iterator patterns', domain_id=domains[2].id),
        Skill(name='MVC Pattern', description='Model-View-Controller architecture', domain_id=domains[3].id),
        Skill(name='Component Design', description='Reusable component architecture', domain_id=domains[3].id),
        Skill(name='Console Debugging', description='Using browser and IDE debugging tools', domain_id=domains[4].id),
        Skill(name='Error Handling', description='Try/catch and error management', domain_id=domains[4].id),
        Skill(name='React Hooks', description='useState, useEffect, and custom hooks', domain_id=domains[5].id),
        Skill(name='React Router', description='Client-side routing in React applications', domain_id=domains[5].id),
        Skill(name='SQL Queries', description='SELECT, JOIN, and data retrieval', domain_id=domains[6].id),
        Skill(name='Database Design', description='Normalization and schema design', domain_id=domains[6].id),
    ]
    db.add_all(skills)
    db.commit()
    print("✅ Skills populated")
    return skills


def create_users(db: Session):
    """Create three different developer profiles"""
    print("👥 Creating users...")
    
    users = [
        User(
            id=uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            username='alex_frontend',
            email='alex@devcompany.com',
            role='developer',
            created_at=datetime(2024, 1, 15, 9, 0, 0)
        ),
        User(
            id=uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            username='maria_fullstack',
            email='maria@techstartup.io',
            role='developer',
            created_at=datetime(2023, 8, 20, 14, 30, 0)
        ),
        User(
            id=uuid.UUID('550e8400-e29b-41d4-a716-446655440003'),
            username='david_backend',
            email='david@enterprise.com',
            role='developer',
            created_at=datetime(2022, 11, 10, 11, 15, 0)
        ),
    ]
    db.add_all(users)
    db.commit()
    print("✅ Users created")
    return users


def create_sessions_and_interactions(db: Session, users, domains, languages, intents):
    """Create realistic conversation sessions with interactions"""
    print("💬 Creating sessions and interactions...")
    
    # Alex's session (Junior Frontend)
    alex_session1 = ChatSession(
        id=uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),
        user_id=users[0].id,
        title='Understanding React Hooks',
        agent_type='strict',
        created_at=datetime(2024, 1, 15, 10, 0, 0),
        ended_at=datetime(2024, 1, 15, 10, 45, 0),
        is_active=False
    )
    db.add(alex_session1)
    
    # Alex's interactions
    alex_interaction1 = Interaction(
        id=uuid.UUID('770e8400-e29b-41d4-a716-446655440001'),
        session_id=alex_session1.id,
        user_message='I\'m getting an error "Cannot read property of undefined" when using useState in React. Can you help me fix this?',
        mentor_response='Great question! Before I help you fix it, let me ask - can you show me the exact line where you\'re declaring your useState? What are you trying to store in that state variable?',
        response_time_ms=1250,
        created_at=datetime(2024, 1, 15, 10, 5, 0),
        domain_id=domains[5].id,  # FRAMEWORKS
        language_id=languages[5].id,  # React
        intent_id=intents[0].id  # debugging
    )
    db.add(alex_interaction1)
    
    # Maria's session (Full-Stack)
    maria_session1 = ChatSession(
        id=uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),
        user_id=users[1].id,
        title='API Design Best Practices',
        agent_type='normal',
        created_at=datetime(2024, 1, 10, 16, 0, 0),
        ended_at=datetime(2024, 1, 10, 16, 30, 0),
        is_active=False
    )
    db.add(maria_session1)
    
    # Maria's interaction
    maria_interaction1 = Interaction(
        id=uuid.UUID('770e8400-e29b-41d4-a716-446655440004'),
        session_id=maria_session1.id,
        user_message='What\'s the best way to structure REST API endpoints for a blog application with posts, comments, and users?',
        mentor_response='For a blog API, you\'ll want to follow RESTful conventions. Consider these endpoints: GET /posts, POST /posts, GET /posts/:id, GET /posts/:id/comments, POST /posts/:id/comments.',
        response_time_ms=1450,
        created_at=datetime(2024, 1, 10, 16, 3, 0),
        domain_id=domains[3].id,  # ARCHITECTURE
        language_id=languages[2].id,  # Python
        intent_id=intents[3].id  # architecture
    )
    db.add(maria_interaction1)
    
    # David's session (Senior Backend)
    david_session1 = ChatSession(
        id=uuid.UUID('660e8400-e29b-41d4-a716-446655440007'),
        user_id=users[2].id,
        title='Microservices Architecture',
        agent_type='normal',
        created_at=datetime(2024, 1, 8, 10, 30, 0),
        ended_at=datetime(2024, 1, 8, 11, 0, 0),
        is_active=False
    )
    db.add(david_session1)
    
    db.commit()
    print("✅ Sessions and interactions created")
    return [alex_interaction1, maria_interaction1]


def create_skill_history(db: Session, users, skills):
    """Create skill progression history"""
    print("📈 Creating skill history...")
    
    skill_history = [
        # Alex's progression (Junior - React focus)
        SkillHistory(
            user_id=users[0].id,
            skill_id=skills[10].id,  # React Hooks
            mastery_level=1,
            snapshot_date=date(2024, 1, 15)
        ),
        SkillHistory(
            user_id=users[0].id,
            skill_id=skills[10].id,  # React Hooks
            mastery_level=2,
            snapshot_date=date(2024, 1, 20)
        ),
        
        # Maria's progression (Full-Stack)
        SkillHistory(
            user_id=users[1].id,
            skill_id=skills[6].id,  # MVC Pattern
            mastery_level=3,
            snapshot_date=date(2024, 1, 10)
        ),
        SkillHistory(
            user_id=users[1].id,
            skill_id=skills[6].id,  # MVC Pattern
            mastery_level=4,
            snapshot_date=date(2024, 1, 25)
        ),
        
        # David's progression (Senior - Expert level)
        SkillHistory(
            user_id=users[2].id,
            skill_id=skills[12].id,  # SQL Queries
            mastery_level=5,
            snapshot_date=date(2024, 1, 22)
        ),
    ]
    db.add_all(skill_history)
    db.commit()
    print("✅ Skill history created")


def create_flashcards_and_reviews(db: Session, users, interactions, skills):
    """Create flashcards from interactions and review sessions"""
    print("🃏 Creating flashcards and review sessions...")
    
    # Flashcard from Alex's interaction
    flashcard1 = Flashcard(
        id=uuid.UUID('880e8400-e29b-41d4-a716-446655440001'),
        question='What happens when you call useState() without an initial value in React?',
        answer='useState() without arguments returns undefined as the initial state value. Always provide an initial value.',
        difficulty=2,
        card_type='concept',
        next_review_date=date(2024, 2, 6),
        review_count=0,
        interaction_id=interactions[0].id,
        skill_id=skills[10].id  # React Hooks
    )
    db.add(flashcard1)
    
    # Review session for Alex
    review1 = ReviewSession(
        user_id=users[0].id,
        flashcard_id=flashcard1.id,
        success_score=2,
        response_time=45,
        review_date=datetime(2024, 1, 16, 9, 30, 0)
    )
    db.add(review1)
    
    db.commit()
    print("✅ Flashcards and reviews created")


def populate_database():
    """Main function to populate the entire database"""
    print("\n🚀 Starting database population with mock data...\n")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as db:
        try:
            # Optional: Clear existing data first
            clear_database()
            
            # Populate in order
            domains, languages, intents = populate_reference_data(db)
            skills = populate_skills(db, domains)
            users = create_users(db)
            interactions = create_sessions_and_interactions(db, users, domains, languages, intents)
            create_skill_history(db, users, skills)
            create_flashcards_and_reviews(db, users, interactions, skills)
            
            # Summary statistics
            print("\n📊 Population Summary:")
            print(f"  - Users: {db.query(User).count()}")
            print(f"  - Sessions: {db.query(ChatSession).count()}")
            print(f"  - Interactions: {db.query(Interaction).count()}")
            print(f"  - Skills: {db.query(Skill).count()}")
            print(f"  - Skill History: {db.query(SkillHistory).count()}")
            print(f"  - Flashcards: {db.query(Flashcard).count()}")
            print(f"  - Review Sessions: {db.query(ReviewSession).count()}")
            
            print("\n✅ Database populated successfully!")
            
        except Exception as e:
            print(f"\n❌ Error populating database: {e}")
            db.rollback()
            raise


if __name__ == "__main__":
    populate_database()