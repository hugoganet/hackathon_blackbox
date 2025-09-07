import React from 'react';
import { ChatMessage } from '../../types';
import { User, Bot, Copy, Check } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [copied, setCopied] = React.useState(false);
  const isUser = message.role === 'user';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  const formatContent = (content: string) => {
    // Simple code block detection and formatting
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const inlineCodeRegex = /`([^`]+)`/g;

    let formattedContent = content;

    // Replace code blocks
    formattedContent = formattedContent.replace(codeBlockRegex, (_match, _language, code) => {
      return `<pre class="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto my-2"><code class="text-sm font-mono">${code.trim()}</code></pre>`;
    });

    // Replace inline code
    formattedContent = formattedContent.replace(inlineCodeRegex, (_match, code) => {
      return `<code class="bg-gray-100 text-gray-800 px-1 py-0.5 rounded text-sm font-mono">${code}</code>`;
    });

    // Replace line breaks
    formattedContent = formattedContent.replace(/\n/g, '<br>');

    return formattedContent;
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-600'
          }`}>
            {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
          </div>
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          {/* Message Bubble */}
          <div className={`relative px-4 py-2 rounded-lg ${
            isUser
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}>
            {/* Message Text */}
            <div
              className="text-sm leading-relaxed"
              dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
            />

            {/* Copy Button */}
            {!isUser && (
              <button
                onClick={handleCopy}
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-gray-200"
                title="Copy message"
              >
                {copied ? (
                  <Check className="w-3 h-3 text-green-600" />
                ) : (
                  <Copy className="w-3 h-3 text-gray-500" />
                )}
              </button>
            )}
          </div>

          {/* Timestamp */}
          <div className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {message.timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
