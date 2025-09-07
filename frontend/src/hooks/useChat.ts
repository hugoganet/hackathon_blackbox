import { useState, useCallback } from 'react';
import { ChatMessage, ChatRequest, LoadingState, ErrorState } from '../types';
import { apiService } from '../services/api';

export const useChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<LoadingState>({ isLoading: false });
  const [error, setError] = useState<ErrorState>({ hasError: false });
  const [sessionId, setSessionId] = useState<string>('');

  const sendMessage = useCallback(async (
    content: string,
    agentType: 'normal' | 'strict' = 'normal',
    userId?: string
  ) => {
    if (!content.trim()) return;

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      content: content.trim(),
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading({ isLoading: true, message: 'Mentor is thinking...' });
    setError({ hasError: false });

    try {
      const request: ChatRequest = {
        message: content.trim(),
        agent_type: agentType,
        user_id: userId,
        session_id: sessionId
      };

      const response = await apiService.sendMessage(request);

      // Update session ID if it changed
      if (response.session_id !== sessionId) {
        setSessionId(response.session_id);
      }

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: `assistant_${Date.now()}`,
        content: response.response,
        role: 'assistant',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError({ hasError: true, message: errorMessage });

      // Add error message to chat
      const errorChatMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        content: `❌ Error: ${errorMessage}`,
        role: 'assistant',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorChatMessage]);
    } finally {
      setLoading({ isLoading: false });
    }
  }, [sessionId]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setSessionId('');
    setError({ hasError: false });
  }, []);

  const retryLastMessage = useCallback(() => {
    if (messages.length >= 2) {
      const lastUserMessage = messages[messages.length - 2];
      if (lastUserMessage.role === 'user') {
        // Remove the last two messages (user + error response)
        setMessages(prev => prev.slice(0, -2));
        // Resend the message
        sendMessage(lastUserMessage.content);
      }
    }
  }, [messages, sendMessage]);

  return {
    messages,
    loading,
    error,
    sessionId,
    sendMessage,
    clearChat,
    retryLastMessage
  };
};
