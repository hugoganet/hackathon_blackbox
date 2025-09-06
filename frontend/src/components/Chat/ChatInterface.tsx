import React, { useEffect, useRef } from 'react';
import { clsx } from 'clsx';
import useChat from '../../hooks/useChat';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import AgentSelector from './AgentSelector';
import Card from '../UI/Card';
import Button from '../UI/Button';
import { RotateCcw, AlertCircle } from 'lucide-react';

interface ChatInterfaceProps {
  className?: string;
  userId?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className, userId }) => {
  const {
    messages,
    currentAgent,
    isLoading,
    error,
    sendMessage,
    setCurrentAgent,
    clearMessages,
    clearError,
  } = useChat({ userId });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'nearest'
      });
    }
  }, [messages]);

  const handleClearChat = () => {
    if (window.confirm('Are you sure you want to clear the chat? This action cannot be undone.')) {
      clearMessages();
    }
  };

  return (
    <div className={clsx('flex flex-col h-full max-w-4xl mx-auto', className)}>
      {/* Agent Selector */}
      <Card className="mb-4" padding="medium">
        <AgentSelector
          selectedAgent={currentAgent}
          onAgentChange={setCurrentAgent}
        />
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="mb-4 border-error bg-red-50" padding="medium">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-error flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-error mb-1">
                Something went wrong
              </h4>
              <p className="text-sm text-red-700">{error}</p>
            </div>
            <Button
              variant="secondary"
              size="small"
              onClick={clearError}
              className="flex-shrink-0 !text-error !border-error hover:!bg-red-50"
            >
              Dismiss
            </Button>
          </div>
        </Card>
      )}

      {/* Messages Container */}
      <Card className="flex-1 flex flex-col min-h-0" padding="none">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Chat with {currentAgent === 'strict' ? 'Strict Mentor' : 'Mentor Agent'}
          </h2>
          
          {messages.length > 1 && (
            <Button
              variant="tertiary"
              size="small"
              onClick={handleClearChat}
              className="!text-gray-600 hover:!text-gray-900"
            >
              <RotateCcw size={16} className="mr-1" />
              Clear Chat
            </Button>
          )}
        </div>

        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto scroll-smooth p-4 space-y-4"
          style={{ minHeight: '400px', maxHeight: '600px' }}
        >
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
            />
          ))}
          
          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 px-4 py-3 bg-gray-100 rounded-2xl">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                </div>
                <span className="text-sm text-gray-600">
                  {currentAgent === 'strict' ? 'Strict Mentor' : 'Mentor'} is thinking...
                </span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input */}
        <div className="border-t border-gray-200 p-4">
          <MessageInput
            onSendMessage={sendMessage}
            disabled={isLoading}
            loading={isLoading}
            placeholder={
              currentAgent === 'strict'
                ? "What challenge are you working on? (Remember: I'll guide you to the solution!)"
                : "Ask your mentor anything about development..."
            }
          />
        </div>
      </Card>
    </div>
  );
};

export default ChatInterface;