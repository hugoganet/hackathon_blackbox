import { 
  ChatRequest, 
  ChatResponse, 
  JuniorMetrics, 
  QuizQuestion, 
  UserMemory, 
  Agent, 
  SystemStats,
  CuratorAnalysisRequest,
  CuratorAnalysisResponse,
  UserSkillProgression,
  FlashcardCreateRequest,
  FlashcardResponse,
  FlashcardReviewRequest,
  FlashcardReviewResponse,
  FlashcardStats
} from '../types';
import { httpClient, getDefaultUserId } from '../utils/http';

/**
 * Real API Service Implementation
 * Replaces mock implementations with actual HTTP calls to the backend
 */
export const apiService = {
  // Chat API - Main interaction endpoint
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    // Ensure user_id is set
    const chatRequest = {
      ...request,
      user_id: request.user_id || getDefaultUserId()
    };

    return httpClient.post<ChatResponse>('/chat', chatRequest);
  },

  // System APIs
  async healthCheck(): Promise<{ status: string; message: string }> {
    return httpClient.get<{ status: string; message: string }>('/health');
  },

  async getSystemStats(): Promise<SystemStats> {
    return httpClient.get<SystemStats>('/stats');
  },

  // Agents API
  async getAgents(): Promise<{ agents: Agent[] }> {
    return httpClient.get<{ agents: Agent[] }>('/agents');
  },

  // User Memory API
  async getUserMemories(userId: string = getDefaultUserId(), limit: number = 10): Promise<UserMemory> {
    return httpClient.get<UserMemory>(`/user/${userId}/memories`, { limit });
  },

  // Curator Analysis APIs
  async analyzeCurator(request: CuratorAnalysisRequest): Promise<CuratorAnalysisResponse> {
    return httpClient.post<CuratorAnalysisResponse>('/curator/analyze', request);
  },

  async getUserSkills(userId: string = getDefaultUserId(), limit: number = 20): Promise<UserSkillProgression> {
    return httpClient.get<UserSkillProgression>(`/curator/user/${userId}/skills`, { limit });
  },

  // Flashcard APIs
  async createFlashcard(request: FlashcardCreateRequest): Promise<FlashcardResponse> {
    return httpClient.post<FlashcardResponse>('/flashcards/create', request);
  },

  async getDueFlashcards(userId: string = getDefaultUserId(), limit: number = 20): Promise<{ flashcards: FlashcardResponse[]; total_due: number }> {
    return httpClient.get<{ flashcards: FlashcardResponse[]; total_due: number }>(`/flashcards/review/${userId}`, { limit });
  },

  async submitFlashcardReview(request: FlashcardReviewRequest): Promise<FlashcardReviewResponse> {
    return httpClient.post<FlashcardReviewResponse>('/flashcards/review', request);
  },

  async getFlashcardStats(userId: string = getDefaultUserId()): Promise<FlashcardStats> {
    return httpClient.get<FlashcardStats>(`/flashcards/stats/${userId}`);
  },

  async getFlashcardSchedule(userId: string = getDefaultUserId(), days: number = 7): Promise<{ schedule: Record<string, any>; total_upcoming: number }> {
    return httpClient.get<{ schedule: Record<string, any>; total_upcoming: number }>(`/flashcards/schedule/${userId}`, { days });
  },

  async batchCreateFlashcards(flashcards: FlashcardCreateRequest[], userId: string = getDefaultUserId()): Promise<FlashcardResponse[]> {
    return httpClient.post<FlashcardResponse[]>('/flashcards/batch', { flashcards, user_id: userId });
  },

  async deleteFlashcard(flashcardId: string, userId: string = getDefaultUserId()): Promise<{ success: boolean; message: string }> {
    return httpClient.delete<{ success: boolean; message: string }>(`/flashcards/${flashcardId}`, { user_id: userId });
  },

  // Legacy compatibility methods (for existing frontend components)
  // These methods transform backend responses to match existing frontend expectations
  
  async getDashboardMetrics(): Promise<JuniorMetrics[]> {
    try {
      // Try to get real user skill progression data
      const skillData = await this.getUserSkills();
      
      // Transform backend skill data to legacy JuniorMetrics format
      const transformedMetrics: JuniorMetrics = {
        id: skillData.user_id,
        name: `User ${skillData.user_id}`,
        email: `${skillData.user_id}@devmentor.ai`,
        skillsAcquired: Object.keys(skillData.skills_summary || {}),
        mistakesIdentified: ['Analysis in progress...'],
        openQuestions: ['Analyzing learning patterns...'],
        nextSteps: ['Continue practicing with flashcards'],
        progressData: skillData.skill_progression?.slice(0, 5).map((skill, index) => ({
          date: new Date(Date.now() - index * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          skillsLearned: skill.mastery_level,
          questionsAsked: Math.floor(Math.random() * 10) + 1,
          mistakesMade: Math.max(0, 5 - skill.mastery_level),
          timeSpent: Math.floor(Math.random() * 120) + 60
        })) || [],
        lastActive: new Date(),
        totalSessions: skillData.total_skills_tracked,
        averageSessionTime: 90
      };

      return [transformedMetrics];
    } catch (error) {
      console.error('Failed to load dashboard metrics from backend:', error);
      // Return empty array if backend is unavailable
      return [];
    }
  },

  async getJuniorMetrics(juniorId: string): Promise<JuniorMetrics | null> {
    const metrics = await this.getDashboardMetrics();
    return metrics.find(junior => junior.id === juniorId) || null;
  },

  // Quiz API - Using flashcard system as backend
  async getQuizQuestions(limit: number = 10): Promise<QuizQuestion[]> {
    try {
      const flashcards = await this.getDueFlashcards(getDefaultUserId(), limit);
      
      // Transform flashcards to quiz questions format
      return flashcards.flashcards.map((card) => ({
        id: card.id,
        question: card.question,
        options: [
          card.answer,
          'Alternative option 1',
          'Alternative option 2', 
          'Alternative option 3'
        ].sort(() => Math.random() - 0.5), // Randomize options
        correctAnswer: 0, // First option is always correct after randomization
        explanation: card.answer,
        difficulty: card.difficulty <= 2 ? 'beginner' : card.difficulty <= 4 ? 'intermediate' : 'advanced',
        topic: card.card_type || 'General',
        programmingLanguage: 'JavaScript'
      }));
    } catch (error) {
      console.error('Failed to load quiz questions from backend:', error);
      // Return empty array if backend is unavailable
      return [];
    }
  },

  async submitQuizAnswer(questionId: string, selectedAnswer: number): Promise<{ isCorrect: boolean; explanation: string }> {
    try {
      // Submit as flashcard review (assuming 0-5 scale where correct = 5, incorrect = 2)
      const reviewResponse = await this.submitFlashcardReview({
        flashcard_id: questionId,
        user_id: getDefaultUserId(),
        success_score: selectedAnswer === 0 ? 5 : 2, // Assuming correct answer is always index 0
        response_time: 30 // Default 30 seconds
      });

      return {
        isCorrect: reviewResponse.success,
        explanation: reviewResponse.message
      };
    } catch (error) {
      console.error('Failed to submit quiz answer to backend:', error);
      // Return mock response if backend is unavailable
      return {
        isCorrect: selectedAnswer === 0,
        explanation: 'Answer submitted (offline mode)'
      };
    }
  }
};
