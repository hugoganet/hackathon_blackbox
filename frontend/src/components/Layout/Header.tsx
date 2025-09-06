import React from 'react';
import { clsx } from 'clsx';
import { Brain, Github } from 'lucide-react';

interface HeaderProps {
  className?: string;
}

const Header: React.FC<HeaderProps> = ({ className }) => {
  return (
    <header className={clsx(
      'sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm',
      className
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Title */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 bg-primary-500 rounded-lg">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                Dev Mentor AI
              </h1>
              <p className="text-xs text-gray-600 hidden sm:block">
                AI-powered mentoring for developers
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <a
              href="https://github.com/your-repo/dev-mentor-ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors duration-200"
            >
              <Github size={16} />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;