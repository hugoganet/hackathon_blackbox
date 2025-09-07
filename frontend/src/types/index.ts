// API Types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface ChatRequest {
  message: string;
  agent_type: 'normal' | 'strict' | 'pydantic_strict' | 'curator';
  user_id?: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  agent_type: string;
  session_id: string;
  related_memories?: string[];
  // Enhanced PydanticAI fields
  hint_level?: number;
  detected_language?: string;
  detected_intent?: string;
  similar_interactions_count?: number;
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
export type TabType = 'mentor' | 'metrics' | 'quizzes' | 'settings';

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
  type?: 'normal' | 'strict' | 'pydantic_strict' | 'curator';
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

// Backend API Types
export interface SystemStats {
  database: {
    users: number;
    conversations: number;
    interactions: number;
    status: 'connected' | 'error';
  };
  memory_store: {
    status: string;
  };
  api: {
    status: 'running';
    agents_loaded: boolean;
  };
}

// Curator Analysis Types
export interface CuratorAnalysisRequest {
  user_message: string;
  mentor_response: string;
  user_id: string;
  session_id?: string;
}

export interface CuratorAnalysisResponse {
  skills: string[];
  mistakes: string[];
  openQuestions: string[];
  nextSteps: string[];
  confidence: number;
  analysis_time_ms: number;
  skill_tracking?: {
    skills_updated: string[];
  };
}

export interface UserSkillProgression {
  user_id: string;
  user_uuid: string;
  total_skills_tracked: number;
  skill_progression: Array<{
    skill_name: string;
    domain: string;
    mastery_level: number;
    snapshot_date: string;
  }>;
  skills_summary: {
    [skillName: string]: {
      mastery_level: number;
      domain: string;
      last_updated: string;
    };
  };
  domains_summary: {
    [domain: string]: {
      skills_count: number;
      avg_mastery: number;
      total_mastery: number;
    };
  };
  message: string;
}

// Flashcard Types for Backend API
export interface FlashcardCreateRequest {
  question: string;
  answer: string;
  difficulty?: number;
  card_type?: string;
  skill_id?: number;
  interaction_id?: string;
  confidence_score?: number;
}

export interface FlashcardResponse {
  id: string;
  question: string;
  answer: string;
  difficulty: number;
  card_type: string;
  next_review_date: string;
  review_count: number;
  created_at: string;
  skill_id?: number;
}

export interface FlashcardReviewRequest {
  flashcard_id: string;
  user_id: string;
  success_score: number;
  response_time?: number;
}

export interface FlashcardReviewResponse {
  success: boolean;
  next_review_date: string;
  interval_days: number;
  difficulty_factor: number;
  card_state: 'NEW' | 'LEARNING' | 'REVIEW' | 'MATURE';
  message: string;
}

export interface FlashcardStats {
  total_flashcards: number;
  due_flashcards: number;
  recent_reviews: number;
  average_score: number;
  success_rate: number;
  streak_days: number;
}
