import React from 'react';
import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  elevated?: boolean;
  interactive?: boolean;
  padding?: 'none' | 'small' | 'medium' | 'large';
}

const Card: React.FC<CardProps> = ({
  children,
  className,
  elevated = true,
  interactive = false,
  padding = 'medium'
}) => {
  const baseClasses = 'bg-white rounded-xl border border-gray-200';
  
  const elevationClasses = elevated
    ? 'shadow-elevation-1'
    : '';
  
  const interactiveClasses = interactive
    ? 'transition-all duration-200 hover:shadow-elevation-2 cursor-pointer'
    : '';
  
  const paddingClasses = {
    none: '',
    small: 'p-4',
    medium: 'p-6',
    large: 'p-8'
  };

  return (
    <div
      className={clsx(
        baseClasses,
        elevationClasses,
        interactiveClasses,
        paddingClasses[padding],
        className
      )}
    >
      {children}
    </div>
  );
};

export default Card;