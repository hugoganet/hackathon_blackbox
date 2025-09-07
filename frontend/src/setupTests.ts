/**
 * Test Setup Configuration
 * Global setup for Jest tests with mocks and utilities
 */

// Mock environment variables for tests
Object.defineProperty(window, 'import.meta', {
  value: {
    env: {
      VITE_API_BASE_URL: 'http://localhost:8000',
      VITE_DEFAULT_USER_ID: 'test-user-123',
      VITE_API_TIMEOUT: '30000',
    },
  },
  writable: true,
});

// Mock fetch globally for tests
global.fetch = jest.fn();

// Helper to create mock fetch responses
export const createMockResponse = (data: any, ok: boolean = true, status: number = 200) => {
  return Promise.resolve({
    ok,
    status,
    statusText: ok ? 'OK' : 'Error',
    headers: new Headers({
      'Content-Type': 'application/json',
    }),
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  } as Response);
};

// Mock successful API responses
export const mockApiResponses = {
  healthCheck: { status: 'healthy', message: 'API is running' },
  
  agents: {
    agents: [
      { id: 'normal', name: 'Normal Agent', description: 'Provides complete answers' },
      { id: 'strict', name: 'Strict Agent', description: 'Guides through hints only' },
    ],
  },
  
  chat: {
    response: 'This is a test response from the mentor.',
    agent_type: 'normal',
    session_id: 'test-session-123',
    related_memories: ['Previous conversation about testing'],
  },
  
  systemStats: {
    database: { users: 5, conversations: 25, interactions: 150, status: 'connected' },
    memory_store: { status: 'active' },
    api: { status: 'running', agents_loaded: true },
  },
  
  userMemory: {
    user_id: 'test-user-123',
    learning_patterns: {
      common_topics: ['React', 'TypeScript'],
      difficulty_preferences: ['intermediate'],
      learning_style: 'hands-on',
      progress_summary: 'Making good progress',
    },
    memory_store_status: 'active',
  },
  
  flashcardCreate: {
    id: 'flashcard-123',
    question: 'Test question',
    answer: 'Test answer',
    difficulty: 3,
    card_type: 'concept',
    next_review_date: '2024-01-02',
    review_count: 0,
    created_at: '2024-01-01T00:00:00Z',
  },
  
  flashcardStats: {
    total_flashcards: 10,
    due_flashcards: 3,
    recent_reviews: 5,
    average_score: 4.2,
    success_rate: 0.85,
    streak_days: 7,
  },
};

// Helper to setup fetch mock for specific test
export const setupFetchMock = (responses: Record<string, any>) => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  mockFetch.mockImplementation((url: string | Request, options?: RequestInit) => {
    const urlString = typeof url === 'string' ? url : url.url;
    const method = options?.method || 'GET';
    const endpoint = urlString.replace('http://localhost:8000', '');
    
    const key = `${method}:${endpoint}`;
    if (responses[key]) {
      return createMockResponse(responses[key]);
    }
    
    // Default to 404 for unmocked endpoints
    return createMockResponse(
      { detail: `Unmocked endpoint: ${key}` },
      false,
      404
    );
  });
};

// Clear all mocks between tests
beforeEach(() => {
  jest.clearAllMocks();
});