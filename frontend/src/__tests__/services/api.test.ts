/**
 * API Service Tests
 * Comprehensive tests for all API service functions with real backend integration
 */

import { apiService } from '../../services/api';
import { setupFetchMock, mockApiResponses, createMockResponse } from '../../setupTests';
import { ApiHttpError } from '../../utils/http';

describe('API Service', () => {
  describe('Core System APIs', () => {
    test('healthCheck should return system health status', async () => {
      setupFetchMock({
        'GET:/health': mockApiResponses.healthCheck,
      });

      const result = await apiService.healthCheck();
      
      expect(result).toEqual(mockApiResponses.healthCheck);
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/health', {
        method: 'GET',
        signal: expect.any(AbortSignal),
        headers: { 'Content-Type': 'application/json' },
      });
    });

    test('getSystemStats should return database and memory store stats', async () => {
      setupFetchMock({
        'GET:/stats': mockApiResponses.systemStats,
      });

      const result = await apiService.getSystemStats();
      
      expect(result).toEqual(mockApiResponses.systemStats);
      expect(result.database.status).toBe('connected');
      expect(result.api.agents_loaded).toBe(true);
    });

    test('getAgents should return list of available agents', async () => {
      setupFetchMock({
        'GET:/agents': mockApiResponses.agents,
      });

      const result = await apiService.getAgents();
      
      expect(result).toEqual(mockApiResponses.agents);
      expect(result.agents).toHaveLength(2);
      expect(result.agents[0].id).toBe('normal');
      expect(result.agents[1].id).toBe('strict');
    });
  });

  describe('Chat API', () => {
    test('sendMessage should send chat request and return response', async () => {
      const chatRequest = {
        message: 'Hello, how do I fix this React error?',
        agent_type: 'normal' as const,
        user_id: 'test-user-123',
        session_id: 'test-session',
      };

      setupFetchMock({
        'POST:/chat': mockApiResponses.chat,
      });

      const result = await apiService.sendMessage(chatRequest);
      
      expect(result).toEqual(mockApiResponses.chat);
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/chat', {
        method: 'POST',
        signal: expect.any(AbortSignal),
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(chatRequest),
      });
    });

    test('sendMessage should use default user_id when not provided', async () => {
      const chatRequest = {
        message: 'Test message',
        agent_type: 'strict' as const,
      };

      setupFetchMock({
        'POST:/chat': mockApiResponses.chat,
      });

      await apiService.sendMessage(chatRequest);
      
      const expectedRequest = {
        ...chatRequest,
        user_id: 'test-user-123', // From environment mock
      };

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/chat', {
        method: 'POST',
        signal: expect.any(AbortSignal),
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(expectedRequest),
      });\n    });\n\n    test('sendMessage should handle different agent types', async () => {\n      const agentTypes = ['normal', 'strict', 'pydantic_strict', 'curator'] as const;\n      \n      for (const agentType of agentTypes) {\n        const chatRequest = {\n          message: `Test message for ${agentType}`,\n          agent_type: agentType,\n        };\n\n        const mockResponse = {\n          ...mockApiResponses.chat,\n          agent_type: agentType,\n        };\n\n        setupFetchMock({\n          'POST:/chat': mockResponse,\n        });\n\n        const result = await apiService.sendMessage(chatRequest);\n        expect(result.agent_type).toBe(agentType);\n      }\n    });\n  });\n\n  describe('User Memory API', () => {\n    test('getUserMemories should fetch user learning patterns', async () => {\n      const userId = 'test-user-123';\n      \n      setupFetchMock({\n        [`GET:/user/${userId}/memories`]: mockApiResponses.userMemory,\n      });\n\n      const result = await apiService.getUserMemories(userId);\n      \n      expect(result).toEqual(mockApiResponses.userMemory);\n      expect(result.user_id).toBe(userId);\n      expect(result.learning_patterns.common_topics).toContain('React');\n    });\n\n    test('getUserMemories should use default user_id and limit', async () => {\n      setupFetchMock({\n        'GET:/user/test-user-123/memories': mockApiResponses.userMemory,\n      });\n\n      await apiService.getUserMemories();\n      \n      expect(fetch).toHaveBeenCalledWith(\n        'http://localhost:8000/user/test-user-123/memories?limit=10',\n        expect.objectContaining({ method: 'GET' })\n      );\n    });\n  });\n\n  describe('Curator Analysis API', () => {\n    test('analyzeCurator should analyze conversation and return insights', async () => {\n      const analysisRequest = {\n        user_message: 'How do I use useState in React?',\n        mentor_response: 'What do you think useState is used for?',\n        user_id: 'test-user-123',\n        session_id: 'test-session',\n      };\n\n      const mockAnalysisResponse = {\n        skills: ['React Hooks', 'State Management'],\n        mistakes: [],\n        openQuestions: ['useState usage'],\n        nextSteps: ['Practice with useState examples'],\n        confidence: 0.7,\n        analysis_time_ms: 150,\n        skill_tracking: { skills_updated: ['React Hooks'] },\n      };\n\n      setupFetchMock({\n        'POST:/curator/analyze': mockAnalysisResponse,\n      });\n\n      const result = await apiService.analyzeCurator(analysisRequest);\n      \n      expect(result).toEqual(mockAnalysisResponse);\n      expect(result.skills).toContain('React Hooks');\n      expect(result.confidence).toBeGreaterThan(0);\n    });\n\n    test('getUserSkills should return user skill progression', async () => {\n      const userId = 'test-user-123';\n      const mockSkillsResponse = {\n        user_id: userId,\n        user_uuid: 'uuid-123',\n        total_skills_tracked: 5,\n        skill_progression: [\n          {\n            skill_name: 'React Hooks',\n            domain: 'Frontend',\n            mastery_level: 3,\n            snapshot_date: '2024-01-01',\n          },\n        ],\n        skills_summary: {\n          'React Hooks': {\n            mastery_level: 3,\n            domain: 'Frontend',\n            last_updated: '2024-01-01',\n          },\n        },\n        domains_summary: {\n          Frontend: {\n            skills_count: 1,\n            avg_mastery: 3,\n            total_mastery: 3,\n          },\n        },\n        message: 'Skills retrieved successfully',\n      };\n\n      setupFetchMock({\n        [`GET:/curator/user/${userId}/skills`]: mockSkillsResponse,\n      });\n\n      const result = await apiService.getUserSkills(userId);\n      \n      expect(result).toEqual(mockSkillsResponse);\n      expect(result.total_skills_tracked).toBe(5);\n      expect(result.skill_progression[0].skill_name).toBe('React Hooks');\n    });\n  });\n\n  describe('Flashcard API', () => {\n    test('createFlashcard should create new flashcard', async () => {\n      const createRequest = {\n        question: 'What is useState?',\n        answer: 'A React hook for managing state',\n        difficulty: 2,\n        card_type: 'concept',\n        confidence_score: 0.6,\n      };\n\n      setupFetchMock({\n        'POST:/flashcards/create': mockApiResponses.flashcardCreate,\n      });\n\n      const result = await apiService.createFlashcard(createRequest);\n      \n      expect(result).toEqual(mockApiResponses.flashcardCreate);\n      expect(result.id).toBe('flashcard-123');\n      expect(result.difficulty).toBe(3);\n    });\n\n    test('getDueFlashcards should return flashcards due for review', async () => {\n      const userId = 'test-user-123';\n      const mockFlashcardsResponse = {\n        flashcards: [mockApiResponses.flashcardCreate],\n        total_due: 1,\n      };\n\n      setupFetchMock({\n        [`GET:/flashcards/review/${userId}`]: mockFlashcardsResponse,\n      });\n\n      const result = await apiService.getDueFlashcards(userId);\n      \n      expect(result).toEqual(mockFlashcardsResponse);\n      expect(result.flashcards).toHaveLength(1);\n      expect(result.total_due).toBe(1);\n    });\n\n    test('submitFlashcardReview should submit review and return scheduling info', async () => {\n      const reviewRequest = {\n        flashcard_id: 'flashcard-123',\n        user_id: 'test-user-123',\n        success_score: 5,\n        response_time: 30,\n      };\n\n      const mockReviewResponse = {\n        success: true,\n        next_review_date: '2024-01-05',\n        interval_days: 4,\n        difficulty_factor: 2.5,\n        card_state: 'REVIEW' as const,\n        message: 'Review submitted successfully',\n      };\n\n      setupFetchMock({\n        'POST:/flashcards/review': mockReviewResponse,\n      });\n\n      const result = await apiService.submitFlashcardReview(reviewRequest);\n      \n      expect(result).toEqual(mockReviewResponse);\n      expect(result.success).toBe(true);\n      expect(result.card_state).toBe('REVIEW');\n    });\n\n    test('getFlashcardStats should return user flashcard statistics', async () => {\n      const userId = 'test-user-123';\n      \n      setupFetchMock({\n        [`GET:/flashcards/stats/${userId}`]: mockApiResponses.flashcardStats,\n      });\n\n      const result = await apiService.getFlashcardStats(userId);\n      \n      expect(result).toEqual(mockApiResponses.flashcardStats);\n      expect(result.success_rate).toBeGreaterThan(0.8);\n      expect(result.streak_days).toBe(7);\n    });\n\n    test('deleteFlashcard should remove flashcard', async () => {\n      const flashcardId = 'flashcard-123';\n      const userId = 'test-user-123';\n      const mockDeleteResponse = {\n        success: true,\n        message: 'Flashcard deleted successfully',\n      };\n\n      setupFetchMock({\n        [`DELETE:/flashcards/${flashcardId}`]: mockDeleteResponse,\n      });\n\n      const result = await apiService.deleteFlashcard(flashcardId, userId);\n      \n      expect(result).toEqual(mockDeleteResponse);\n      expect(result.success).toBe(true);\n    });\n  });\n\n  describe('Legacy Compatibility Methods', () => {\n    test('getDashboardMetrics should transform backend data to legacy format', async () => {\n      const mockSkillsResponse = {\n        user_id: 'test-user-123',\n        user_uuid: 'uuid-123',\n        total_skills_tracked: 3,\n        skills_summary: {\n          'React': { mastery_level: 3, domain: 'Frontend', last_updated: '2024-01-01' },\n          'TypeScript': { mastery_level: 4, domain: 'Frontend', last_updated: '2024-01-02' },\n        },\n        skill_progression: [\n          { skill_name: 'React', domain: 'Frontend', mastery_level: 3, snapshot_date: '2024-01-01' },\n          { skill_name: 'TypeScript', domain: 'Frontend', mastery_level: 4, snapshot_date: '2024-01-02' },\n        ],\n        domains_summary: {},\n        message: 'Success',\n      };\n\n      setupFetchMock({\n        'GET:/curator/user/test-user-123/skills': mockSkillsResponse,\n      });\n\n      const result = await apiService.getDashboardMetrics();\n      \n      expect(result).toHaveLength(1);\n      expect(result[0].id).toBe('test-user-123');\n      expect(result[0].skillsAcquired).toContain('React');\n      expect(result[0].skillsAcquired).toContain('TypeScript');\n      expect(result[0].totalSessions).toBe(3);\n    });\n\n    test('getDashboardMetrics should handle backend errors gracefully', async () => {\n      const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;\n      mockFetch.mockRejectedValue(new Error('Network error'));\n\n      const result = await apiService.getDashboardMetrics();\n      \n      expect(result).toEqual([]);\n    });\n  });\n\n  describe('Error Handling', () => {\n    test('should throw ApiHttpError for HTTP errors', async () => {\n      const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;\n      mockFetch.mockResolvedValue({\n        ok: false,\n        status: 500,\n        statusText: 'Internal Server Error',\n        json: () => Promise.resolve({ detail: 'Server error occurred' }),\n      } as Response);\n\n      await expect(apiService.healthCheck()).rejects.toThrow('Server error occurred');\n      await expect(apiService.healthCheck()).rejects.toBeInstanceOf(ApiHttpError);\n    });\n\n    test('should handle network timeout errors', async () => {\n      const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;\n      const abortError = new Error('Request timeout');\n      abortError.name = 'AbortError';\n      mockFetch.mockRejectedValue(abortError);\n\n      await expect(apiService.healthCheck()).rejects.toThrow('Request timeout');\n    });\n\n    test('should handle malformed JSON responses', async () => {\n      const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;\n      mockFetch.mockResolvedValue({\n        ok: false,\n        status: 400,\n        statusText: 'Bad Request',\n        json: () => Promise.reject(new Error('Invalid JSON')),\n      } as Response);\n\n      await expect(apiService.healthCheck()).rejects.toThrow('HTTP 400: Bad Request');\n    });\n  });\n\n  describe('Environment Configuration', () => {\n    test('should use environment variables for API configuration', () => {\n      expect(import.meta.env.VITE_API_BASE_URL).toBe('http://localhost:8000');\n      expect(import.meta.env.VITE_DEFAULT_USER_ID).toBe('test-user-123');\n      expect(import.meta.env.VITE_API_TIMEOUT).toBe('30000');\n    });\n  });\n});