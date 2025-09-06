import axios from 'axios';
import { ChatRequest, ChatResponse, Agent, HealthStatus, SystemStats, ApiError } from '../types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout for chat requests
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.detail) {
      console.error('API Error:', error.response.data.detail);
      throw new Error(error.response.data.detail);
    }
    
    if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout - please try again');
    }
    
    if (error.response?.status === 500) {
      throw new Error('Server error - please try again later');
    }
    
    throw new Error(error.message || 'An unexpected error occurred');
  }
);

export const chatApi = {
  // Send a chat message to the mentor agent
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat', request);
    return response.data;
  },

  // Get available agents
  async getAgents(): Promise<Agent[]> {
    const response = await api.get<Agent[]>('/agents');
    return response.data;
  },

  // Get system health status
  async getHealth(): Promise<HealthStatus> {
    const response = await api.get<HealthStatus>('/health');
    return response.data;
  },

  // Get system statistics
  async getStats(): Promise<SystemStats> {
    const response = await api.get<SystemStats>('/stats');
    return response.data;
  },

  // Get user memories (if user_id is provided)
  async getUserMemories(userId: string): Promise<string[]> {
    const response = await api.get<string[]>(`/user/${userId}/memories`);
    return response.data;
  }
};

export default api;