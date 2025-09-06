import React from 'react';
import { AgentType } from '../../types';
import { clsx } from 'clsx';

interface AgentSelectorProps {
  selectedAgent: AgentType;
  onAgentChange: (agent: AgentType) => void;
  className?: string;
}

const AgentSelector: React.FC<AgentSelectorProps> = ({
  selectedAgent,
  onAgentChange,
  className
}) => {
  const agents = [
    {
      id: 'normal' as AgentType,
      name: 'Mentor Agent',
      description: 'Provides complete answers and detailed guidance',
      icon: '🤖'
    },
    {
      id: 'strict' as AgentType, 
      name: 'Strict Mentor Agent',
      description: 'Guides through hints only, ideal for learning',
      icon: '🎯'
    }
  ];

  return (
    <div className={clsx('space-y-3', className)}>
      <h3 className="text-sm font-medium text-gray-700 mb-3">Choose your mentor agent:</h3>
      
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {agents.map((agent) => (
          <button
            key={agent.id}
            onClick={() => onAgentChange(agent.id)}
            className={clsx(
              'p-4 rounded-lg border-2 text-left transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
              selectedAgent === agent.id
                ? 'border-primary-500 bg-primary-50 text-primary-900'
                : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
            )}
          >
            <div className="flex items-start space-x-3">
              <span className="text-2xl" role="img" aria-label={agent.name}>
                {agent.icon}
              </span>
              <div className="flex-1 min-w-0">
                <h4 className={clsx(
                  'text-sm font-medium',
                  selectedAgent === agent.id ? 'text-primary-900' : 'text-gray-900'
                )}>
                  {agent.name}
                </h4>
                <p className={clsx(
                  'text-xs mt-1',
                  selectedAgent === agent.id ? 'text-primary-700' : 'text-gray-600'
                )}>
                  {agent.description}
                </p>
              </div>
              
              {selectedAgent === agent.id && (
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-primary-500 rounded-full" />
                </div>
              )}
            </div>
          </button>
        ))}
      </div>
      
      {selectedAgent === 'strict' && (
        <div className="mt-3 p-3 bg-warning-50 border border-warning-200 rounded-lg">
          <div className="flex items-start">
            <span className="text-warning-500 mr-2">⚠️</span>
            <p className="text-xs text-warning-700">
              The Strict Mentor will <strong>never give direct answers</strong>. 
              It will guide you to discover solutions through questions and hints.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentSelector;