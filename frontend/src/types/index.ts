// API Types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface ChatRequest {
  message: string;
  agent_type: 'normal' | 'strict';
  user_id?: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  agent_type: string;
  session_id: string;
  related_memories?: string[];
}

// Metrics Types
export interface JuniorMetrics {
  id: string;
  name: string;
  email: string;
  skillsAcquired: string[];
  mistakesIdentified: string[];
  openQuestions: string[];
  nextSteps: string[];
  progressData: ProgressDataPoint[];
  lastActive: Date;
  totalSessions: number;
  averageSessionTime: number;
}

export interface ProgressDataPoint {
  date: string;
  skillsLearned: number;
  questionsAsked: number;
  mistakesMade: number;
  timeSpent: number;
}

// Quiz Types
export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  topic: string;
  programmingLanguage?: string;
}

export interface QuizCard extends QuizQuestion {
  easeFactor: number;
  interval: number;
  repetitions: number;
  nextReview: Date;
  lastReviewed?: Date;
}

export interface QuizAttempt {
  questionId: string;
  selectedAnswer: number;
  isCorrect: boolean;
  timeSpent: number;
  timestamp: Date;
}

export interface SpacedRepetitionData {
  easeFactor: number;
  interval: number;
  repetitions: number;
  nextReview: Date;
}

// UI Types
export type TabType = 'mentor' | 'metrics' | 'quizzes';

export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface ErrorState {
  hasError: boolean;
  message?: string;
}

// Agent Types
export interface Agent {
  id: string;
  name: string;
  description: string;
  type: 'normal' | 'strict';
}

// Memory Types
export interface UserMemory {
  user_id: string;
  learning_patterns: {
    common_topics: string[];
    difficulty_preferences: string[];
    learning_style: string;
    progress_summary: string;
  };
  memory_store_status: string;
}
