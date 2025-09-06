import React from 'react';
import { clsx } from 'clsx';
import { Message, AgentType } from '../../types';
import { Bot, User } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
  className?: string;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, className }) => {
  const isUser = message.isUser;
  const isStrict = message.agentType === 'strict';
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={clsx(
      'flex gap-3 max-w-4xl mx-auto',
      isUser ? 'justify-end' : 'justify-start',
      className
    )}>
      {!isUser && (
        <div className={clsx(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium',
          isStrict ? 'bg-warning-500' : 'bg-primary-500'
        )}>
          <Bot size={16} />
        </div>
      )}
      
      <div className={clsx(
        'flex flex-col max-w-[70%] min-w-[120px]',
        isUser ? 'items-end' : 'items-start'
      )}>
        <div className={clsx(
          'px-4 py-3 rounded-2xl shadow-elevation-1',
          isUser 
            ? 'bg-primary-500 text-white' 
            : isStrict
              ? 'bg-warning-50 border border-warning-200 text-gray-900'
              : 'bg-white border border-gray-200 text-gray-900'
        )}>
          <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
            {message.content}
          </div>
        </div>
        
        <div className="flex items-center gap-2 mt-1">
          {!isUser && message.agentType && (
            <span className={clsx(
              'text-xs font-medium px-2 py-0.5 rounded-full',
              isStrict 
                ? 'bg-warning-100 text-warning-800' 
                : 'bg-primary-100 text-primary-800'
            )}>
              {isStrict ? 'Strict Mentor' : 'Mentor'}
            </span>
          )}
          <time className="text-xs text-gray-500">
            {formatTime(message.timestamp)}
          </time>
        </div>
      </div>
      
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-white">
          <User size={16} />
        </div>
      )}
    </div>
  );
};

export default MessageBubble;