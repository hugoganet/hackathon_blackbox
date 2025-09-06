export type AgentType = 'normal' | 'strict';

export interface ChatRequest {
  message: string;
  agent_type: AgentType;
  user_id?: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  agent_type: AgentType;
  session_id: string;
  related_memories?: string[];
}

export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  agentType?: AgentType;
}

export interface Agent {
  id: AgentType;
  name: string;
  description: string;
  isStrict: boolean;
}

export interface ApiError {
  detail: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
}

export interface SystemStats {
  total_conversations: number;
  total_interactions: number;
  active_sessions: number;
  memory_entries: number;
}