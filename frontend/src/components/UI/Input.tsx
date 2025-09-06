import React, { forwardRef } from 'react';
import { clsx } from 'clsx';

type InputState = 'default' | 'focus' | 'error' | 'success' | 'disabled';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  errorMessage?: string;
  state?: InputState;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  helperText,
  errorMessage,
  state = 'default',
  disabled,
  className,
  id,
  ...props
}, ref) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const hasError = state === 'error' || !!errorMessage;
  const hasSuccess = state === 'success';
  
  const baseClasses = 'w-full h-10 px-4 py-3 text-base bg-white border rounded-lg transition-all duration-200 focus:outline-none focus:ring-3 focus:ring-primary-100 placeholder:text-gray-500';
  
  const stateClasses = {
    default: 'border-gray-300 hover:border-gray-400 focus:border-primary-500',
    focus: 'border-primary-500 ring-3 ring-primary-100',
    error: 'border-error bg-red-50 focus:border-error focus:ring-red-100',
    success: 'border-success bg-green-50 focus:border-success focus:ring-green-100',
    disabled: 'bg-gray-100 text-gray-500 cursor-not-allowed border-gray-300'
  };

  const currentState = disabled ? 'disabled' : hasError ? 'error' : hasSuccess ? 'success' : state;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          {label}
        </label>
      )}
      
      <input
        ref={ref}
        id={inputId}
        disabled={disabled}
        className={clsx(
          baseClasses,
          stateClasses[currentState],
          className
        )}
        {...props}
      />
      
      {(helperText || errorMessage) && (
        <p className={clsx(
          'mt-1 text-xs',
          hasError ? 'text-error' : 'text-gray-600'
        )}>
          {errorMessage || helperText}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;