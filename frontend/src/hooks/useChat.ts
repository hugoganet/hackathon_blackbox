import { useState, useCallback, useRef, useEffect } from 'react';
import { Message, AgentType, ChatRequest } from '../types';
import { chatApi } from '../services/api';

interface UseChatOptions {
  initialAgent?: AgentType;
  userId?: string;
}

interface UseChatReturn {
  messages: Message[];
  currentAgent: AgentType;
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;
  sendMessage: (content: string) => Promise<void>;
  setCurrentAgent: (agent: AgentType) => void;
  clearMessages: () => void;
  clearError: () => void;
}

const useChat = (options: UseChatOptions = {}): UseChatReturn => {
  const { initialAgent = 'normal', userId } = options;
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentAgent, setCurrentAgent] = useState<AgentType>(initialAgent);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Keep track of message IDs to avoid duplicates
  const messageIdRef = useRef(0);
  
  const generateMessageId = () => {
    messageIdRef.current += 1;
    return `msg-${Date.now()}-${messageIdRef.current}`;
  };

  const addMessage = useCallback((message: Omit<Message, 'id'>) => {
    const newMessage: Message = {
      ...message,
      id: generateMessageId(),
    };
    
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Clear any previous errors
    setError(null);
    setIsLoading(true);

    // Add user message immediately
    const userMessage = addMessage({
      content: content.trim(),
      isUser: true,
      timestamp: new Date(),
    });

    try {
      const request: ChatRequest = {
        message: content.trim(),
        agent_type: currentAgent,
        user_id: userId,
        session_id: sessionId || undefined,
      };

      const response = await chatApi.sendMessage(request);

      // Update session ID if we got one back
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
      }

      // Add AI response message
      addMessage({
        content: response.response,
        isUser: false,
        timestamp: new Date(),
        agentType: response.agent_type,
      });

    } catch (err) {
      console.error('Failed to send message:', err);
      
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'Failed to send message. Please try again.';
      
      setError(errorMessage);
      
      // Add error message to chat
      addMessage({
        content: `❌ Error: ${errorMessage}`,
        isUser: false,
        timestamp: new Date(),
        agentType: currentAgent,
      });
    } finally {
      setIsLoading(false);
    }
  }, [currentAgent, userId, sessionId, isLoading, addMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setError(null);
    messageIdRef.current = 0;
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const handleAgentChange = useCallback((agent: AgentType) => {
    setCurrentAgent(agent);
    // Optionally clear error when switching agents
    setError(null);
  }, []);

  // Add welcome message when agent changes
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage = currentAgent === 'strict'
        ? "👋 Hi! I'm your Strict Mentor. I'll help you learn by guiding you to discover solutions yourself. I won't give direct answers, but I'll ask questions and give hints to help you think through problems. What would you like to work on?"
        : "👋 Hello! I'm your AI Mentor. I'm here to help you with development questions, provide detailed explanations, and guide you through learning. What can I help you with today?";

      addMessage({
        content: welcomeMessage,
        isUser: false,
        timestamp: new Date(),
        agentType: currentAgent,
      });
    }
  }, [currentAgent, messages.length, addMessage]);

  return {
    messages,
    currentAgent,
    isLoading,
    error,
    sessionId,
    sendMessage,
    setCurrentAgent: handleAgentChange,
    clearMessages,
    clearError,
  };
};

export default useChat;