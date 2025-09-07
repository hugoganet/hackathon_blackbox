"""
Enhanced database population script for hackathon demo
Creates 3 realistic junior developer profiles at different career stages with comprehensive data
showcasing spaced repetition flashcards, SM-2 algorithm, and learning progression
"""

from datetime import datetime, timedelta, date
import uuid
import random
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

# Import all models
from models import (
    Base, User, Session as ChatSession, Interaction, Skill, SkillHistory,
    Flashcard, ReviewSession, RefDomain, RefLanguage, RefIntent, MemoryEntry
)

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/dev_mentor_ai")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base date for consistent timeline
BASE_DATE = datetime(2024, 8, 1)

def clear_database():
    """Clear all existing data and recreate tables"""
    print("🗑️  Clearing existing data...")
    
    with engine.connect() as conn:
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
    
    # Create all tables from models
    print("  - Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database cleared and recreated")


def populate_reference_data(db: Session):
    """Populate reference tables with comprehensive data"""
    print("📚 Populating reference data...")
    
    # Learning domains
    domains = [
        RefDomain(name='ALGORITHMIC', description='Data structures, algorithms, complexity analysis', display_order=1),
        RefDomain(name='SYNTAX', description='Language syntax mastery and best practices', display_order=2),
        RefDomain(name='LOGIC', description='Programming logic and control structures', display_order=3),
        RefDomain(name='ARCHITECTURE', description='Design patterns and code organization', display_order=4),
        RefDomain(name='DEBUGGING', description='Error resolution and troubleshooting skills', display_order=5),
        RefDomain(name='FRAMEWORKS', description='Modern frameworks and libraries', display_order=6),
        RefDomain(name='DATABASES', description='Database design and query optimization', display_order=7),
        RefDomain(name='DEVOPS', description='Deployment and development operations', display_order=8),
        RefDomain(name='TESTING', description='Unit testing and quality assurance', display_order=9),
        RefDomain(name='PERFORMANCE', description='Code optimization and performance tuning', display_order=10),
    ]
    db.add_all(domains)
    
    # Programming languages and technologies
    languages = [
        RefLanguage(name='JavaScript', category='Frontend'),
        RefLanguage(name='TypeScript', category='Frontend'),
        RefLanguage(name='Python', category='Backend'),
        RefLanguage(name='Java', category='Backend'),
        RefLanguage(name='React', category='Framework'),
        RefLanguage(name='Vue.js', category='Framework'),
        RefLanguage(name='Node.js', category='Runtime'),
        RefLanguage(name='Express.js', category='Framework'),
        RefLanguage(name='SQL', category='Database'),
        RefLanguage(name='MongoDB', category='Database'),
        RefLanguage(name='Git', category='Tool'),
        RefLanguage(name='HTML', category='Markup'),
        RefLanguage(name='CSS', category='Styling'),
    ]
    db.add_all(languages)
    
    # Interaction intent types
    intents = [
        RefIntent(name='debugging', description='Error resolution and bug fixing'),
        RefIntent(name='concept_explanation', description='Understanding programming concepts'),
        RefIntent(name='code_review', description='Code quality improvement'),
        RefIntent(name='best_practices', description='Industry standards and conventions'),
        RefIntent(name='architecture', description='System design discussions'),
        RefIntent(name='performance', description='Optimization strategies'),
        RefIntent(name='learning_path', description='Educational guidance'),
        RefIntent(name='project_help', description='Assistance with specific projects'),
    ]
    db.add_all(intents)
    
    db.commit()
    print("✅ Reference data populated")
    return domains, languages, intents


def populate_skills(db: Session, domains):
    """Populate comprehensive skills for junior developers"""
    print("🎯 Populating skills...")
    
    skills = [
        # ALGORITHMIC (0-2)
        Skill(name='Array Manipulation', description='Working with arrays and collections effectively', id_domain=domains[0].id_domain),
        Skill(name='Basic Sorting', description='Understanding and implementing sorting algorithms', id_domain=domains[0].id_domain),
        Skill(name='Big O Notation', description='Analyzing algorithm time and space complexity', id_domain=domains[0].id_domain),
        
        # SYNTAX (3-5)
        Skill(name='Variable Declaration', description='Proper variable naming and scoping rules', id_domain=domains[1].id_domain),
        Skill(name='Function Syntax', description='Function declaration patterns and best practices', id_domain=domains[1].id_domain),
        Skill(name='ES6+ Features', description='Modern JavaScript syntax and features', id_domain=domains[1].id_domain),
        
        # LOGIC (6-8)
        Skill(name='Conditional Logic', description='If/else statements and boolean expressions', id_domain=domains[2].id_domain),
        Skill(name='Loop Structures', description='For, while, and array iteration patterns', id_domain=domains[2].id_domain),
        Skill(name='Recursion Basics', description='Understanding recursive function patterns', id_domain=domains[2].id_domain),
        
        # ARCHITECTURE (9-11)
        Skill(name='Component Design', description='Building reusable UI components', id_domain=domains[3].id_domain),
        Skill(name='State Management', description='Managing application state effectively', id_domain=domains[3].id_domain),
        Skill(name='API Integration', description='Connecting frontend to backend services', id_domain=domains[3].id_domain),
        
        # DEBUGGING (12-14)
        Skill(name='Console Debugging', description='Using browser dev tools effectively', id_domain=domains[4].id_domain),
        Skill(name='Error Handling', description='Try/catch blocks and error management', id_domain=domains[4].id_domain),
        Skill(name='Stack Trace Reading', description='Understanding and interpreting error messages', id_domain=domains[4].id_domain),
        
        # FRAMEWORKS (15-17)
        Skill(name='React Hooks', description='useState, useEffect, and custom hooks', id_domain=domains[5].id_domain),
        Skill(name='React Router', description='Client-side routing in single page apps', id_domain=domains[5].id_domain),
        Skill(name='Component Lifecycle', description='Understanding component mounting and updates', id_domain=domains[5].id_domain),
        
        # DATABASES (18-20)
        Skill(name='SQL Queries', description='SELECT, JOIN, and data retrieval', id_domain=domains[6].id_domain),
        Skill(name='Database Relations', description='Understanding foreign keys and relationships', id_domain=domains[6].id_domain),
        Skill(name='Query Optimization', description='Writing efficient database queries', id_domain=domains[6].id_domain),
    ]
    
    db.add_all(skills)
    db.commit()
    print(f"✅ {len(skills)} skills populated")
    return skills


def create_hackathon_users(db: Session):
    """Create 3 junior developers at different career stages"""
    print("👥 Creating hackathon demo users...")
    
    users = [
        # User 1: 3 days experience - Complete beginner
        User(
            id_user=uuid.UUID('11111111-1111-1111-1111-111111111111'),
            username='emma_newbie',
            email='emma.chen@bootcamp.dev',
            role='developer',
            created_at=BASE_DATE + timedelta(days=-3),  # Started 3 days ago
            is_active=True
        ),
        
        # User 2: 1 month experience - Learning fundamentals
        User(
            id_user=uuid.UUID('22222222-2222-2222-2222-222222222222'),
            username='alex_junior',
            email='alex.rodriguez@startup.io',
            role='developer',
            created_at=BASE_DATE + timedelta(days=-30),  # Started 1 month ago
            is_active=True
        ),
        
        # User 3: 6 months experience - Gaining confidence
        User(
            id_user=uuid.UUID('33333333-3333-3333-3333-333333333333'),
            username='sarah_growing',
            email='sarah.kim@techcorp.com',
            role='developer',
            created_at=BASE_DATE + timedelta(days=-180),  # Started 6 months ago
            is_active=True
        ),
    ]
    
    db.add_all(users)
    db.commit()
    print("✅ Hackathon users created")
    return users


def create_realistic_conversations(db: Session, users, domains, languages, intents):
    """Create extensive conversation history for each user"""
    print("💬 Creating realistic conversation history...")
    
    sessions = []
    interactions = []
    
    # EMMA (3 days) - Very basic questions, lots of confusion
    emma_conversations = [
        {
            'title': 'First HTML Page Help',
            'date': BASE_DATE + timedelta(days=-3, hours=2),
            'messages': [
                ("I'm trying to create my first HTML page but nothing shows up in the browser. What am I doing wrong?", 
                 "Great first step! Let's think about this systematically. When you say 'nothing shows up', can you tell me what you see in the browser? A blank page? An error message? And what code did you write in your HTML file?"),
                ("I just see a blank page. I wrote <p>Hello World</p> in a file called hello.txt", 
                 "Ah, I see the issue! You're on the right track with the paragraph tag. But here's a question for you: what do you think might be different between a .txt file and an .html file? What file extension should we use for web pages?"),
            ],
            'domain': 'SYNTAX', 'language': 'HTML', 'intent': 'debugging'
        },
        {
            'title': 'Understanding Variables',
            'date': BASE_DATE + timedelta(days=-2, hours=5),
            'messages': [
                ("What's the difference between var, let, and const in JavaScript? I'm so confused.", 
                 "That's a great question that even experienced developers had to learn! Instead of me telling you the differences, let's explore this together. Can you think about what the word 'const' might stand for? What do you think it implies about the variable?"),
                ("Does const mean constant? Like it can't change?", 
                 "Excellent thinking! You're absolutely right. Now, can you guess what might happen if you try to reassign a value to a const variable? Want to try a small experiment?"),
            ],
            'domain': 'SYNTAX', 'language': 'JavaScript', 'intent': 'concept_explanation'
        },
        {
            'title': 'CSS Not Working',
            'date': BASE_DATE + timedelta(days=-1, hours=3),
            'messages': [
                ("My CSS isn't working! I wrote p { color: red; } but my paragraph is still black.", 
                 "CSS not applying is a common challenge! Let's debug this step by step. First, tell me: how are you connecting your CSS to your HTML? Are you using a separate CSS file or putting it directly in the HTML?"),
                ("I put it in a separate file called styles.css", 
                 "Good choice! Now here's the key question: did you tell your HTML page about this CSS file? How do you think the HTML knows to use the styles from styles.css?"),
            ],
            'domain': 'SYNTAX', 'language': 'CSS', 'intent': 'debugging'
        },
    ]
    
    # ALEX (1 month) - Understanding fundamentals, making progress
    alex_conversations = [
        {
            'title': 'React Components Not Rendering',
            'date': BASE_DATE + timedelta(days=-25, hours=4),
            'messages': [
                ("I created a React component but it's not showing up. I'm getting a 'React is not defined' error.", 
                 "That's a classic React error! You're making great progress by working with components. Let's think about this: when you use JSX like <div>, React needs to know what that syntax means. What do you think you might need to import at the top of your file?"),
                ("Oh! Do I need to import React from 'react'?", 
                 "Exactly! You're getting it. Now, once you add that import, what do you think will happen? And here's another question: are you also importing ReactDOM somewhere to render your component?"),
            ],
            'domain': 'FRAMEWORKS', 'language': 'React', 'intent': 'debugging'
        },
        {
            'title': 'State Management with Hooks',
            'date': BASE_DATE + timedelta(days=-20, hours=6),
            'messages': [
                ("I'm trying to update state with useState but the component isn't re-rendering. What am I missing?", 
                 "Great question about state! You're working with one of React's core concepts. Let me ask: when you call your state setter function, are you passing it a completely new value, or are you modifying the existing state object?"),
                ("I think I'm modifying the existing object. Is that wrong?", 
                 "You're thinking in the right direction! React has specific rules about how it detects changes. What do you think React compares to decide if it should re-render? Think about whether React does a deep comparison or something simpler."),
            ],
            'domain': 'FRAMEWORKS', 'language': 'React', 'intent': 'concept_explanation'
        },
        {
            'title': 'API Integration Problems',
            'date': BASE_DATE + timedelta(days=-15, hours=2),
            'messages': [
                ("My fetch request isn't working. I'm getting a CORS error. How do I fix this?", 
                 "CORS errors are super common when learning APIs! You're encountering browser security in action. Before we solve it, let's understand what's happening. Can you tell me: are you making a request from localhost:3000 to a different domain or port?"),
                ("Yes, I'm calling an API on port 8000 from my React app on port 3000.", 
                 "Perfect! That's exactly what's causing the CORS issue. The browser is protecting you. Now, there are a few ways to handle this. What do you think would be the difference between solving this on the frontend vs. the backend?"),
            ],
            'domain': 'ARCHITECTURE', 'language': 'JavaScript', 'intent': 'debugging'
        },
        {
            'title': 'Array Methods Confusion',
            'date': BASE_DATE + timedelta(days=-10, hours=5),
            'messages': [
                ("I'm confused about when to use map() vs forEach(). They seem to do the same thing.", 
                 "That's an excellent question about array methods! They do seem similar at first glance. Let me ask you this: after you call forEach() on an array, what do you get back? And what about when you call map()?"),
                ("forEach doesn't return anything, and map returns a new array?", 
                 "Exactly right! Now, knowing that difference, can you think of a scenario where you'd want to use map() instead of forEach()? What would you be trying to accomplish?"),
            ],
            'domain': 'SYNTAX', 'language': 'JavaScript', 'intent': 'concept_explanation'
        },
    ]
    
    # SARAH (6 months) - More complex topics, building confidence
    sarah_conversations = [
        {
            'title': 'Advanced React Patterns',
            'date': BASE_DATE + timedelta(days=-150, hours=3),
            'messages': [
                ("I'm building a complex form and wondering about performance. Should I use controlled or uncontrolled components?", 
                 "Great question about React performance! You're thinking like a developer who cares about user experience. Let's explore this: what do you think happens on every keystroke with a controlled component? How might that affect performance with a large form?"),
                ("With controlled components, React re-renders on every keystroke, which could be slow with many fields?", 
                 "Exactly! You're understanding the trade-offs. Now, what are the benefits of controlled components that might make that re-rendering worthwhile? Think about form validation and data flow."),
            ],
            'domain': 'FRAMEWORKS', 'language': 'React', 'intent': 'performance'
        },
        {
            'title': 'Database Design Questions',
            'date': BASE_DATE + timedelta(days=-120, hours=4),
            'messages': [
                ("I'm designing a blog database. Should I store tags as a JSON column or separate table? What are the pros and cons?", 
                 "Excellent database design question! You're thinking about normalization vs denormalization. Let's consider both approaches. If you store tags as JSON, what might be easy and what might be difficult when querying?"),
                ("JSON would be easy to store and retrieve all tags for a post, but hard to find all posts with a specific tag?", 
                 "Perfect analysis! You're understanding the trade-offs. Now, if you went with a separate tags table and a junction table, what would that enable you to do? Think about queries and data integrity."),
            ],
            'domain': 'DATABASES', 'language': 'SQL', 'intent': 'architecture'
        },
        {
            'title': 'Code Review Feedback',
            'date': BASE_DATE + timedelta(days=-90, hours=2),
            'messages': [
                ("My teammate said my component has too many responsibilities. How do I know when to split a component?", 
                 "That's a sophisticated question about component design! Your teammate is helping you write cleaner code. Let's think about this: what are some signs that a component might be doing too much? What would make it hard to test or reuse?"),
                ("If it's handling state, API calls, and rendering different UI sections, that's probably too much?", 
                 "Great insight! You're applying the single responsibility principle. Now, how might you split those concerns? What would each new component be responsible for?"),
            ],
            'domain': 'ARCHITECTURE', 'language': 'React', 'intent': 'code_review'
        },
        {
            'title': 'Performance Optimization',
            'date': BASE_DATE + timedelta(days=-60, hours=6),
            'messages': [
                ("My React app is getting slow with a large list. I heard about virtualization but don't understand when to use it.", 
                 "Performance optimization is a great skill to develop! You're right that virtualization can help with large lists. Let's think about this: what's the main problem when rendering thousands of DOM elements at once?"),
                ("It uses too much memory and makes scrolling slow?", 
                 "Exactly! Now, how do you think virtualization solves this? What would be different about rendering only the visible items plus a small buffer?"),
            ],
            'domain': 'PERFORMANCE', 'language': 'React', 'intent': 'performance'
        },
        {
            'title': 'Testing Strategy Discussion',
            'date': BASE_DATE + timedelta(days=-30, hours=3),
            'messages': [
                ("I want to start writing tests but I'm not sure what to test first. Should I focus on unit tests or integration tests?", 
                 "Testing is crucial for reliable code! You're asking a great strategic question. Let's think about this: what parts of your application would cause the most problems if they broke? What would affect users the most?"),
                ("Probably the user registration and login flows, and the main features users interact with?", 
                 "Perfect prioritization! Those are your critical paths. Now, for those flows, what do you think would be more valuable to test: the individual functions or the entire user journey?"),
            ],
            'domain': 'TESTING', 'language': 'JavaScript', 'intent': 'best_practices'
        },
    ]
    
    # Process each user's conversations
    user_conversations = [
        (users[0], emma_conversations),  # Emma - 3 days
        (users[1], alex_conversations),  # Alex - 1 month  
        (users[2], sarah_conversations), # Sarah - 6 months
    ]
    
    domain_map = {d.name: d for d in domains}
    language_map = {l.name: l for l in languages}
    intent_map = {i.name: i for i in intents}
    
    for user, conversations in user_conversations:
        for conv_data in conversations:
            # Create session
            session = ChatSession(
                id_session=uuid.uuid4(),
                id_user=user.id_user,
                title=conv_data['title'],
                agent_type='strict',
                created_at=conv_data['date'],
                ended_at=conv_data['date'] + timedelta(minutes=45),
                is_active=False
            )
            sessions.append(session)
            db.add(session)
            
            # Create interactions
            for i, (user_msg, mentor_msg) in enumerate(conv_data['messages']):
                interaction = Interaction(
                    id_interaction=uuid.uuid4(),
                    id_session=session.id_session,
                    user_message=user_msg,
                    mentor_response=mentor_msg,
                    response_time_ms=random.randint(800, 2000),
                    created_at=conv_data['date'] + timedelta(minutes=i*10),
                    id_domain=domain_map[conv_data['domain']].id_domain,
                    id_language=language_map[conv_data['language']].id_language,
                    id_intent=intent_map[conv_data['intent']].id_intent
                )
                interactions.append(interaction)
                db.add(interaction)
    
    db.commit()
    print(f"✅ {len(sessions)} sessions and {len(interactions)} interactions created")
    return sessions, interactions


def create_skill_progression(db: Session, users, skills):
    """Create realistic skill progression for each user"""
    print("📈 Creating skill progression history...")
    
    skill_histories = []
    
    # Emma (3 days) - Just starting, low mastery levels
    emma_skills = [
        (skills[3], [1, 1]),      # Variable Declaration - still learning
        (skills[4], [1]),         # Function Syntax - just introduced
        (skills[6], [1]),         # Conditional Logic - basic understanding
        (skills[12], [1]),        # Console Debugging - just learned
    ]
    
    # Alex (1 month) - Making steady progress
    alex_skills = [
        (skills[3], [1, 2, 2, 3]),   # Variable Declaration - good progress
        (skills[4], [1, 2, 3]),      # Function Syntax - improving
        (skills[5], [1, 1, 2]),      # ES6+ Features - learning modern syntax
        (skills[6], [2, 2, 3, 3]),   # Conditional Logic - solid understanding
        (skills[7], [1, 2, 2, 3]),   # Loop Structures - getting comfortable
        (skills[15], [1, 1, 2, 2]),  # React Hooks - key focus area
        (skills[11], [1, 2]),        # API Integration - recent learning
        (skills[13], [2, 3]),        # Error Handling - improving
    ]
    
    # Sarah (6 months) - More advanced, showing expertise in some areas
    sarah_skills = [
        (skills[3], [2, 3, 4, 4, 5]),     # Variable Declaration - mastered
        (skills[4], [2, 3, 4, 4]),        # Function Syntax - very good
        (skills[5], [2, 3, 3, 4, 4]),     # ES6+ Features - strong
        (skills[6], [3, 4, 4, 5]),        # Conditional Logic - expert level
        (skills[7], [3, 3, 4, 4, 4]),     # Loop Structures - very good
        (skills[8], [1, 2, 2, 3]),        # Recursion - still learning
        (skills[9], [2, 3, 4, 4, 5]),     # Component Design - strong skill
        (skills[10], [2, 3, 3, 4]),       # State Management - good progress
        (skills[15], [3, 4, 4, 5]),       # React Hooks - expert level
        (skills[16], [2, 3, 3, 4]),       # React Router - solid
        (skills[11], [3, 3, 4, 4]),       # API Integration - strong
        (skills[18], [2, 2, 3, 3]),       # SQL Queries - decent
        (skills[13], [3, 4, 4, 5]),       # Error Handling - expert
    ]
    
    user_skill_data = [
        (users[0], emma_skills, 3),    # Emma - 3 days of data
        (users[1], alex_skills, 30),   # Alex - 30 days of data  
        (users[2], sarah_skills, 180), # Sarah - 180 days of data
    ]
    
    for user, user_skills, days_back in user_skill_data:
        for skill, progression in user_skills:
            # Create progression over time
            days_per_entry = max(1, days_back // len(progression))
            
            for i, mastery in enumerate(progression):
                snapshot_date = BASE_DATE.date() - timedelta(days=days_back - (i * days_per_entry))
                
                history_entry = SkillHistory(
                    id_history=uuid.uuid4(),
                    id_user=user.id_user,
                    id_skill=skill.id_skill,
                    mastery_level=mastery,
                    snapshot_date=snapshot_date,
                    created_at=datetime.combine(snapshot_date, datetime.min.time())
                )
                skill_histories.append(history_entry)
                db.add(history_entry)
    
    db.commit()
    print(f"✅ {len(skill_histories)} skill history entries created")
    return skill_histories


def create_comprehensive_flashcards(db: Session, users, interactions, skills):
    """Create extensive flashcard system showcasing SM-2 algorithm"""
    print("🃏 Creating comprehensive flashcard system...")
    
    flashcards = []
    review_sessions = []
    
    # Flashcard templates for different skill levels and topics
    flashcard_templates = {
        'syntax': [
            ("What is the difference between 'let' and 'const' in JavaScript?", 
             "'let' allows reassignment of the variable, while 'const' creates a constant that cannot be reassigned after initialization."),
            ("What is the correct syntax for declaring a function in JavaScript?", 
             "function functionName() { /* code */ } or const functionName = () => { /* code */ }"),
            ("How do you properly link a CSS file to an HTML document?", 
             "Use the <link> tag in the <head> section: <link rel='stylesheet' href='styles.css'>"),
        ],
        'react': [
            ("What is the purpose of the useState hook in React?", 
             "useState allows functional components to have local state. It returns an array with the current state value and a function to update it."),
            ("What happens when you forget to import React in a JSX file?", 
             "You get a 'React is not defined' error because JSX needs React to convert JSX syntax into React.createElement calls."),
            ("How do you handle events in React components?", 
             "Use camelCase event handlers like onClick, onChange, etc., and pass a function reference: onClick={handleClick}"),
        ],
        'debugging': [
            ("What is the first step when encountering a bug in your code?", 
             "Read the error message carefully and identify the exact line and type of error before making any changes."),
            ("How can you inspect variable values during code execution?", 
             "Use console.log(), browser debugging tools, or debugger statements to examine variable values at runtime."),
            ("What does a CORS error mean and why does it happen?", 
             "CORS (Cross-Origin Resource Sharing) error occurs when a web page tries to access a resource from a different domain, port, or protocol than itself."),
        ],
        'architecture': [
            ("When should you split a React component into smaller components?", 
             "When a component has multiple responsibilities, is hard to test, or when parts of it could be reused elsewhere."),
            ("What is the difference between controlled and uncontrolled components?", 
             "Controlled components have their state managed by React state, while uncontrolled components manage their own state internally."),
            ("How do you decide between using props vs state in React?", 
             "Use props for data passed down from parent components, and state for data that changes within the component itself."),
        ],
    }
    
    # Create flashcards for each user based on their level
    user_flashcard_data = [
        # Emma (3 days) - Basic concepts, mostly NEW and LEARNING cards
        {
            'user': users[0],
            'topics': ['syntax'],
            'card_count': 8,
            'difficulty_range': (1, 2),
            'review_performance': [1, 2, 1, 2, 3, 2, 1, 2],  # Struggling
        },
        # Alex (1 month) - Mixed topics, variety of card states
        {
            'user': users[1], 
            'topics': ['syntax', 'react', 'debugging'],
            'card_count': 15,
            'difficulty_range': (1, 3),
            'review_performance': [2, 3, 4, 2, 3, 4, 3, 5, 2, 3, 4, 3, 2, 4, 3],  # Improving
        },
        # Sarah (6 months) - Advanced topics, many REVIEW and MATURE cards
        {
            'user': users[2],
            'topics': ['react', 'debugging', 'architecture'],
            'card_count': 25,
            'difficulty_range': (2, 5),
            'review_performance': [4, 5, 4, 5, 5, 3, 4, 5, 4, 5, 3, 4, 5, 5, 4, 3, 5, 4, 5, 3, 4, 5, 4, 3, 5],  # Strong
        },
    ]
    
    # SM-2 algorithm implementation for scheduling
    def calculate_sm2_schedule(performance_score, ease_factor=2.5, interval=1, repetitions=0):
        """Calculate next review date using SM-2 algorithm"""
        if performance_score < 3:
            # Poor performance - reset to learning phase
            repetitions = 0
            interval = 1
        else:
            # Good performance - increase interval
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 6
            else:
                interval = round(interval * ease_factor)
            
            repetitions += 1
            
            # Adjust ease factor based on performance
            ease_factor = ease_factor + (0.1 - (5 - performance_score) * (0.08 + (5 - performance_score) * 0.02))
            ease_factor = max(1.3, ease_factor)  # Minimum ease factor
        
        return interval, ease_factor, repetitions
    
    card_id_counter = 1
    
    for user_data in user_flashcard_data:
        user = user_data['user']
        topics = user_data['topics']
        card_count = user_data['card_count']
        difficulty_range = user_data['difficulty_range']
        performances = user_data['review_performance']
        
        # Find relevant interactions for this user
        user_interactions = [i for i in interactions if any(s.id_user == user.id_user for s in db.query(ChatSession).filter_by(id_session=i.id_session))]
        
        for i in range(card_count):
            # Select topic and template
            topic = random.choice(topics)
            template = random.choice(flashcard_templates[topic])
            
            # Find matching skill based on topic
            topic_skills = {
                'syntax': skills[3:6],      # Variable Declaration, Function Syntax, ES6+
                'react': skills[15:18],     # React Hooks, Router, Lifecycle
                'debugging': skills[12:15], # Console Debugging, Error Handling, Stack Traces
                'architecture': skills[9:12], # Component Design, State Management, API Integration
            }
            
            skill = random.choice(topic_skills[topic])
            interaction = random.choice(user_interactions) if user_interactions else None
            
            # Create flashcard
            flashcard = Flashcard(
                id_flashcard=uuid.uuid4(),
                question=f"{template[0]} (Card #{card_id_counter})",
                answer=template[1],
                difficulty=random.randint(*difficulty_range),
                card_type='concept',
                created_at=user.created_at + timedelta(days=random.randint(1, 30)),
                next_review_date=(BASE_DATE + timedelta(days=random.randint(-5, 5))).date(),
                review_count=0,
                id_interaction=interaction.id_interaction if interaction else None,
                id_skill=skill.id_skill
            )
            flashcards.append(flashcard)
            db.add(flashcard)
            
            # Create review history for this flashcard
            if i < len(performances):
                performance_score = performances[i]
                review_count = random.randint(1, 5)
                ease_factor = 2.5
                interval = 1
                repetitions = 0
                
                for review_num in range(review_count):
                    # Simulate review session
                    review_date = flashcard.created_at + timedelta(days=interval * review_num + random.randint(0, 2))
                    
                    review = ReviewSession(
                        id_review=uuid.uuid4(),
                        id_user=user.id_user,
                        id_flashcard=flashcard.id_flashcard,
                        success_score=performance_score + random.randint(-1, 1),  # Add some variation
                        response_time=random.randint(15, 120),  # 15-120 seconds
                        review_date=review_date
                    )
                    review_sessions.append(review)
                    db.add(review)
                    
                    # Update SM-2 scheduling
                    actual_performance = max(0, min(5, review.success_score))
                    interval, ease_factor, repetitions = calculate_sm2_schedule(
                        actual_performance, ease_factor, interval, repetitions
                    )
                
                # Update flashcard with final scheduling
                flashcard.next_review_date = (review_date + timedelta(days=interval)).date()
                flashcard.review_count = review_count
            
            card_id_counter += 1
    
    db.commit()
    print(f"✅ {len(flashcards)} flashcards and {len(review_sessions)} review sessions created")
    return flashcards, review_sessions


def create_memory_entries(db: Session, users, interactions):
    """Create memory entries for personalized learning insights"""
    print("🧠 Creating memory entries for learning patterns...")
    
    memory_entries = []
    
    # Create memory patterns for each user
    user_memories = [
        # Emma (3 days) - Basic concepts, many struggles
        {
            'user': users[0],
            'patterns': [
                ('html_basics', 1, 'Forgets file extensions, confuses .txt with .html', 'step_by_step'),
                ('css_linking', 1, 'Doesn\'t know how to connect CSS to HTML', 'visual'),
                ('javascript_syntax', 1, 'Confused by basic syntax rules', 'hands_on'),
            ]
        },
        # Alex (1 month) - Understanding fundamentals
        {
            'user': users[1],
            'patterns': [
                ('react_imports', 2, 'Sometimes forgets React import statement', 'visual'),
                ('state_updates', 2, 'Learning immutability patterns in React', 'hands_on'),
                ('api_cors', 2, 'Understanding cross-origin request concepts', 'conceptual'),
                ('array_methods', 3, 'Good grasp of map vs forEach differences', 'conceptual'),
                ('component_structure', 3, 'Building well-organized React components', 'systematic'),
            ]
        },
        # Sarah (6 months) - Advanced concepts
        {
            'user': users[2],
            'patterns': [
                ('performance_optimization', 4, 'Understands virtualization and memoization', 'analytical'),
                ('component_architecture', 4, 'Designs reusable component systems', 'systematic'),
                ('database_design', 3, 'Learning normalization tradeoffs', 'analytical'),
                ('testing_strategy', 3, 'Developing comprehensive test approaches', 'systematic'),
                ('code_review', 4, 'Applies single responsibility principle', 'analytical'),
                ('async_patterns', 4, 'Masters promises and async/await', 'hands_on'),
            ]
        }
    ]
    
    for user_memory in user_memories:
        user = user_memory['user']
        patterns = user_memory['patterns']
        
        for concept, mastery, mistakes, style in patterns:
            # Calculate practice frequency based on mastery level
            practice_count = mastery * random.randint(3, 8)
            first_encountered = user.created_at + timedelta(days=random.randint(1, 10))
            last_practiced = BASE_DATE - timedelta(days=random.randint(0, 7))
            
            memory_entry = MemoryEntry(
                id=uuid.uuid4(),
                id_user=user.id_user,
                concept=concept,
                mastery_level=mastery,
                common_mistakes=f'["{mistakes}"]',  # JSON format
                learning_style=style,
                first_encountered=first_encountered,
                last_practiced=last_practiced,
                practice_count=practice_count
            )
            memory_entries.append(memory_entry)
            db.add(memory_entry)
    
    db.commit()
    print(f"✅ {len(memory_entries)} memory entries created")
    return memory_entries


def populate_hackathon_demo():
    """Main function to populate database with comprehensive hackathon demo data"""
    print("\n🚀 STARTING HACKATHON DEMO DATABASE POPULATION\n")
    print("Creating realistic data for 3 junior developers at different career stages:")
    print("  🔸 Emma (3 days) - Complete beginner, basic HTML/CSS/JS")
    print("  🔸 Alex (1 month) - Learning React, making steady progress") 
    print("  🔸 Sarah (6 months) - Advanced concepts, building expertise\n")
    
    # Clear and recreate database
    clear_database()
    
    with SessionLocal() as db:
        try:
            # Populate reference data
            domains, languages, intents = populate_reference_data(db)
            
            # Create skills and users
            skills = populate_skills(db, domains)
            users = create_hackathon_users(db)
            
            # Create realistic conversation history
            sessions, interactions = create_realistic_conversations(db, users, domains, languages, intents)
            
            # Build skill progression over time
            skill_histories = create_skill_progression(db, users, skills)
            
            # Create comprehensive flashcard system with SM-2 algorithm
            flashcards, review_sessions = create_comprehensive_flashcards(db, users, interactions, skills)
            
            # Add memory entries for learning patterns
            memory_entries = create_memory_entries(db, users, interactions)
            
            # Final statistics
            print("\n📊 HACKATHON DEMO DATABASE SUMMARY:")
            print("=" * 50)
            print(f"👥 Users: {len(users)} (3 different career stages)")
            print(f"💬 Sessions: {len(sessions)} conversation sessions")
            print(f"📝 Interactions: {len(interactions)} mentor exchanges")
            print(f"🎯 Skills: {len(skills)} tracked competencies")
            print(f"📈 Skill History: {len(skill_histories)} progression snapshots")
            print(f"🃏 Flashcards: {len(flashcards)} spaced repetition cards")
            print(f"⭐ Review Sessions: {len(review_sessions)} SM-2 algorithm reviews")
            print(f"🧠 Memory Entries: {len(memory_entries)} learning pattern insights")
            print(f"📚 Reference Data: {len(domains)} domains, {len(languages)} languages, {len(intents)} intents")
            
            # Detailed user breakdown
            print(f"\n🔍 USER BREAKDOWN:")
            for i, user in enumerate(users):
                user_sessions = len([s for s in sessions if s.id_user == user.id_user])
                user_flashcards = len([f for f in flashcards if any(r.id_user == user.id_user for r in review_sessions if r.id_flashcard == f.id_flashcard)])
                user_reviews = len([r for r in review_sessions if r.id_user == user.id_user])
                user_skills = len([h for h in skill_histories if h.id_user == user.id_user])
                
                stage = ["3 days (Beginner)", "1 month (Learning)", "6 months (Growing)"][i]
                print(f"  {user.username} ({stage}): {user_sessions} sessions, {user_flashcards} flashcards, {user_reviews} reviews, {user_skills} skill entries")
            
            print(f"\n✅ HACKATHON DEMO DATABASE READY!")
            print(f"🎯 Perfect for showcasing:")
            print(f"   • Spaced repetition with SM-2 algorithm")
            print(f"   • Learning progression across different skill levels")
            print(f"   • Realistic conversation patterns and mentoring")
            print(f"   • Comprehensive skill tracking and analytics")
            print(f"   • Memory-based personalized learning insights")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            db.rollback()
            raise


if __name__ == "__main__":
    populate_hackathon_demo()