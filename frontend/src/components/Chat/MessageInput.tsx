import React, { useState, useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import { Send, Loader2 } from 'lucide-react';
import Button from '../UI/Button';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
  className?: string;
}

const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  disabled = false,
  loading = false,
  placeholder = "Ask your mentor a question...",
  className
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled && !loading) {
      onSendMessage(message.trim());
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [message]);

  return (
    <form onSubmit={handleSubmit} className={clsx('w-full', className)}>
      <div className="relative flex items-end gap-3 p-4 bg-white border border-gray-200 rounded-xl shadow-elevation-2">
        <div className="flex-1">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || loading}
            className={clsx(
              'w-full resize-none border-none outline-none placeholder:text-gray-500 text-gray-900',
              'min-h-[20px] max-h-[120px] text-sm leading-relaxed',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            rows={1}
            style={{ field: 'none' }}
          />
        </div>
        
        <Button
          type="submit"
          size="medium"
          disabled={!message.trim() || disabled || loading}
          loading={loading}
          className="flex-shrink-0 !px-4 !py-2 !h-9"
        >
          {loading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Send size={16} />
          )}
        </Button>
      </div>
      
      <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
        <span>Press Enter to send, Shift+Enter for new line</span>
        {message.length > 0 && (
          <span className={clsx(
            message.length > 500 ? 'text-warning-600' : 'text-gray-400'
          )}>
            {message.length}/1000
          </span>
        )}
      </div>
    </form>
  );
};

export default MessageInput;