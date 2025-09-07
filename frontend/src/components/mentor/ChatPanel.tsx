import React from 'react';
import { useChat } from '../../hooks/useChat';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import { Trash2, RefreshCw } from 'lucide-react';

interface ChatPanelProps {
  code: string;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ code: _code }) => {
  const { messages, loading, error, sendMessage, clearChat, retryLastMessage } = useChat();

  const handleSendMessage = async (message: string) => {
    await sendMessage(message, 'normal', 'user123');
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Chat Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">AI Mentor</h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={clearChat}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              title="Clear chat"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>


      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {loading.isLoading && (
          <div className="flex items-center space-x-2 text-gray-500">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
            <span className="text-sm">{loading.message || 'Thinking...'}</span>
          </div>
        )}

        {error.hasError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-red-600 text-sm">❌ {error.message}</span>
              </div>
              <button
                onClick={retryLastMessage}
                className="text-red-600 hover:text-red-800 p-1"
                title="Retry"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Chat Input */}
      <div className="border-t border-gray-200 p-4">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={loading.isLoading}
          placeholder="Ask me anything about your code..."
        />
      </div>
    </div>
  );
};

export default ChatPanel;
