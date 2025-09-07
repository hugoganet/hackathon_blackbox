import { ChatRequest, ChatResponse, JuniorMetrics, QuizQuestion, UserMemory, Agent } from '../types';

// Mock API base URL - in production this would be your actual backend
const API_BASE_URL = 'http://localhost:8000';

// Mock data for development
const mockJuniorMetrics: JuniorMetrics[] = [
  {
    id: '1',
    name: 'Alice Johnson',
    email: 'alice@example.com',
    skillsAcquired: ['React Hooks', 'TypeScript Basics', 'CSS Grid', 'API Integration'],
    mistakesIdentified: ['Missing error handling', 'Inefficient re-renders', 'Poor state management'],
    openQuestions: ['How to optimize performance?', 'Best practices for testing?'],
    nextSteps: ['Learn React Testing Library', 'Practice advanced TypeScript', 'Study performance optimization'],
    progressData: [
      { date: '2024-01-01', skillsLearned: 2, questionsAsked: 5, mistakesMade: 3, timeSpent: 120 },
      { date: '2024-01-02', skillsLearned: 1, questionsAsked: 8, mistakesMade: 2, timeSpent: 90 },
      { date: '2024-01-03', skillsLearned: 3, questionsAsked: 6, mistakesMade: 1, timeSpent: 150 },
      { date: '2024-01-04', skillsLearned: 2, questionsAsked: 4, mistakesMade: 2, timeSpent: 110 },
      { date: '2024-01-05', skillsLearned: 1, questionsAsked: 7, mistakesMade: 1, timeSpent: 95 },
    ],
    lastActive: new Date('2024-01-05'),
    totalSessions: 15,
    averageSessionTime: 113
  },
  {
    id: '2',
    name: 'Bob Smith',
    email: 'bob@example.com',
    skillsAcquired: ['JavaScript ES6+', 'Node.js Basics', 'Express.js'],
    mistakesIdentified: ['Callback hell', 'Memory leaks', 'Synchronous operations'],
    openQuestions: ['How to handle async operations?', 'Database optimization?'],
    nextSteps: ['Learn async/await patterns', 'Study database indexing', 'Practice error handling'],
    progressData: [
      { date: '2024-01-01', skillsLearned: 1, questionsAsked: 3, mistakesMade: 4, timeSpent: 80 },
      { date: '2024-01-02', skillsLearned: 2, questionsAsked: 6, mistakesMade: 3, timeSpent: 100 },
      { date: '2024-01-03', skillsLearned: 1, questionsAsked: 4, mistakesMade: 2, timeSpent: 75 },
      { date: '2024-01-04', skillsLearned: 3, questionsAsked: 8, mistakesMade: 1, timeSpent: 130 },
      { date: '2024-01-05', skillsLearned: 2, questionsAsked: 5, mistakesMade: 2, timeSpent: 105 },
    ],
    lastActive: new Date('2024-01-05'),
    totalSessions: 12,
    averageSessionTime: 98
  },
  {
    id: '3',
    name: 'Carol Davis',
    email: 'carol@example.com',
    skillsAcquired: ['Python Basics', 'Django Framework', 'REST APIs', 'Database Design'],
    mistakesIdentified: ['N+1 queries', 'Insecure endpoints', 'Poor validation'],
    openQuestions: ['How to scale Django apps?', 'Best security practices?'],
    nextSteps: ['Learn Django optimization', 'Study security patterns', 'Practice deployment'],
    progressData: [
      { date: '2024-01-01', skillsLearned: 3, questionsAsked: 7, mistakesMade: 2, timeSpent: 140 },
      { date: '2024-01-02', skillsLearned: 2, questionsAsked: 5, mistakesMade: 3, timeSpent: 120 },
      { date: '2024-01-03', skillsLearned: 1, questionsAsked: 9, mistakesMade: 1, timeSpent: 160 },
      { date: '2024-01-04', skillsLearned: 4, questionsAsked: 6, mistakesMade: 2, timeSpent: 180 },
      { date: '2024-01-05', skillsLearned: 2, questionsAsked: 8, mistakesMade: 1, timeSpent: 145 },
    ],
    lastActive: new Date('2024-01-05'),
    totalSessions: 20,
    averageSessionTime: 149
  }
];

const mockQuizQuestions: QuizQuestion[] = [
  {
    id: '1',
    question: 'What is the correct way to handle state in a React functional component?',
    options: [
      'Using this.setState()',
      'Using useState hook',
      'Directly modifying variables',
      'Using class properties'
    ],
    correctAnswer: 1,
    explanation: 'The useState hook is the correct way to manage state in functional components. It returns a state variable and a setter function.',
    difficulty: 'beginner',
    topic: 'React State Management',
    programmingLanguage: 'JavaScript'
  },
  {
    id: '2',
    question: 'Which of the following is NOT a valid HTTP method?',
    options: ['GET', 'POST', 'FETCH', 'DELETE'],
    correctAnswer: 2,
    explanation: 'FETCH is not an HTTP method. It\'s a JavaScript API for making HTTP requests. The valid HTTP methods include GET, POST, PUT, DELETE, PATCH, etc.',
    difficulty: 'beginner',
    topic: 'HTTP Methods',
    programmingLanguage: 'General'
  },
  {
    id: '3',
    question: 'What does the "async/await" syntax do in JavaScript?',
    options: [
      'Makes code run faster',
      'Handles asynchronous operations more readably',
      'Creates new threads',
      'Prevents errors from occurring'
    ],
    correctAnswer: 1,
    explanation: 'async/await provides a more readable way to handle asynchronous operations compared to callbacks or promise chains.',
    difficulty: 'intermediate',
    topic: 'Asynchronous JavaScript',
    programmingLanguage: 'JavaScript'
  },
  {
    id: '4',
    question: 'In TypeScript, what is the purpose of interfaces?',
    options: [
      'To create classes',
      'To define the structure of objects',
      'To handle errors',
      'To import modules'
    ],
    correctAnswer: 1,
    explanation: 'Interfaces in TypeScript define the structure/shape of objects, specifying what properties and methods an object should have.',
    difficulty: 'intermediate',
    topic: 'TypeScript Interfaces',
    programmingLanguage: 'TypeScript'
  }
];

// API functions with mock implementations
export const apiService = {
  // Chat API
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

    // Mock response based on agent type
    const responses = {
      normal: [
        "Here's a complete solution to your problem. Let me explain step by step...",
        "I can help you with that! Here's the full implementation with explanations...",
        "Great question! Here's a comprehensive answer with code examples..."
      ],
      strict: [
        "That's an interesting question! What do you think might be the first step to solve this?",
        "Before I give you hints, can you tell me what you've already tried?",
        "Let's think about this together. What concepts do you think are relevant here?"
      ]
    };

    const agentResponses = responses[request.agent_type] || responses.normal;
    const randomResponse = agentResponses[Math.floor(Math.random() * agentResponses.length)];

    return {
      response: randomResponse,
      agent_type: request.agent_type,
      session_id: request.session_id || `session_${Date.now()}`,
      related_memories: [
        "Similar question about React hooks from last week",
        "Previous discussion on error handling patterns"
      ]
    };
  },

  // Dashboard API
  async getDashboardMetrics(): Promise<JuniorMetrics[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    return mockJuniorMetrics;
  },

  async getJuniorMetrics(juniorId: string): Promise<JuniorMetrics | null> {
    await new Promise(resolve => setTimeout(resolve, 500));
    return mockJuniorMetrics.find(junior => junior.id === juniorId) || null;
  },

  // Quiz API
  async getQuizQuestions(limit: number = 10): Promise<QuizQuestion[]> {
    await new Promise(resolve => setTimeout(resolve, 600));
    return mockQuizQuestions.slice(0, limit);
  },

  async submitQuizAnswer(questionId: string, selectedAnswer: number): Promise<{ isCorrect: boolean; explanation: string }> {
    await new Promise(resolve => setTimeout(resolve, 300));
    const question = mockQuizQuestions.find(q => q.id === questionId);
    if (!question) {
      throw new Error('Question not found');
    }

    return {
      isCorrect: selectedAnswer === question.correctAnswer,
      explanation: question.explanation
    };
  },

  // User Memory API
  async getUserMemories(userId: string): Promise<UserMemory> {
    await new Promise(resolve => setTimeout(resolve, 400));
    return {
      user_id: userId,
      learning_patterns: {
        common_topics: ['React', 'JavaScript', 'TypeScript', 'API Integration'],
        difficulty_preferences: ['intermediate', 'beginner'],
        learning_style: 'hands-on',
        progress_summary: 'Making steady progress with React concepts and TypeScript fundamentals'
      },
      memory_store_status: 'active'
    };
  },

  // Agents API
  async getAgents(): Promise<Agent[]> {
    await new Promise(resolve => setTimeout(resolve, 200));
    return [
      {
        id: 'normal',
        name: 'Mentor Agent',
        description: 'Provides complete answers and detailed guidance',
        type: 'normal'
      },
      {
        id: 'strict',
        name: 'Strict Mentor Agent',
        description: 'Guides through hints only, refuses to give direct answers',
        type: 'strict'
      }
    ];
  },

  // Health check
  async healthCheck(): Promise<{ status: string; message: string }> {
    return {
      status: 'healthy',
      message: 'Frontend API service is running with mock data'
    };
  }
};
