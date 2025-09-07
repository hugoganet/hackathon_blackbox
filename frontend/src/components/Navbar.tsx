import React, { useState } from 'react';
import { TabType } from '../types';
import { Code, BarChart3, Brain, ChevronDown, User } from 'lucide-react';

interface NavbarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  viewType: 'junior' | 'manager';
  onViewChange: (view: 'junior' | 'manager') => void;
}

const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange, viewType, onViewChange }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const tabs = [
    { id: 'mentor' as TabType, label: 'Mentor', icon: Code },
    { id: 'metrics' as TabType, label: 'Metrics', icon: BarChart3 },
    { id: 'quizzes' as TabType, label: 'Quizzes', icon: Brain },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 bg-white border-b border-gray-200 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-gray-900">
                Blackbox <span className="text-primary-600">Mentor</span>
              </h1>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* View Toggle */}
            <div className="bg-gray-100 rounded-lg p-1 flex">
              <button
                onClick={() => onViewChange('junior')}
                className={`
                  px-3 py-1 rounded-md text-sm font-medium transition-colors
                  ${viewType === 'junior'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                  }
                `}
              >
                Junior
              </button>
              <button
                onClick={() => onViewChange('manager')}
                className={`
                  px-3 py-1 rounded-md text-sm font-medium transition-colors
                  ${viewType === 'manager'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                  }
                `}
              >
                Manager
              </button>
            </div>

            {/* User Menu with Dropdown */}
            <div className="relative">
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors duration-200"
              aria-haspopup="true"
              aria-expanded={isDropdownOpen}
            >
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <ChevronDown className="w-4 h-4 text-gray-500" />
            </button>

            {isDropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                <div className="py-1">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;

                    return (
                      <button
                        key={tab.id}
                        onClick={() => {
                          onTabChange(tab.id);
                          setIsDropdownOpen(false);
                        }}
                        className={`
                          flex items-center w-full px-4 py-2 text-sm transition-colors duration-200
                          ${isActive
                            ? 'bg-primary-50 text-primary-700'
                            : 'text-gray-700 hover:bg-gray-100'
                          }
                        `}
                      >
                        <Icon className="w-4 h-4 mr-3" />
                        {tab.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
