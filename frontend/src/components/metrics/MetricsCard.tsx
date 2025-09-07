import React from 'react';
import { JuniorMetrics } from '../../types';
import ProgressChart from './ProgressChart';
import { Calendar, Clock, Target, AlertTriangle, HelpCircle, ArrowRight } from 'lucide-react';

interface MetricsCardProps {
  junior: JuniorMetrics;
}

const MetricsCard: React.FC<MetricsCardProps> = ({ junior }) => {
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const getProgressColor = (skillCount: number) => {
    if (skillCount >= 5) return 'text-green-600 bg-green-100';
    if (skillCount >= 3) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
            <span className="text-lg font-semibold text-primary-600">
              {junior.name.split(' ').map(n => n[0]).join('').toUpperCase()}
            </span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{junior.name}</h3>
            <p className="text-sm text-gray-500">{junior.email}</p>
          </div>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${getProgressColor(junior.skillsAcquired.length)}`}>
          {junior.skillsAcquired.length} skills
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <Target className="w-4 h-4 text-gray-400 mr-1" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{junior.totalSessions}</p>
          <p className="text-xs text-gray-500">Sessions</p>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <Clock className="w-4 h-4 text-gray-400 mr-1" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{junior.averageSessionTime}m</p>
          <p className="text-xs text-gray-500">Avg Time</p>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <Calendar className="w-4 h-4 text-gray-400 mr-1" />
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {Math.floor((Date.now() - junior.lastActive.getTime()) / (1000 * 60 * 60 * 24))}d
          </p>
          <p className="text-xs text-gray-500">Last Active</p>
        </div>
      </div>

      {/* Progress Chart */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Weekly Progress</h4>
        <ProgressChart data={junior.progressData} />
      </div>

      {/* Skills Acquired */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Skills Acquired</h4>
        <div className="flex flex-wrap gap-1">
          {junior.skillsAcquired.slice(0, 3).map((skill, index) => (
            <span
              key={index}
              className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full"
            >
              {skill}
            </span>
          ))}
          {junior.skillsAcquired.length > 3 && (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
              +{junior.skillsAcquired.length - 3} more
            </span>
          )}
        </div>
      </div>

      {/* Mistakes Identified */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
          <AlertTriangle className="w-4 h-4 mr-1 text-orange-500" />
          Recent Mistakes
        </h4>
        <div className="space-y-1">
          {junior.mistakesIdentified.slice(0, 2).map((mistake, index) => (
            <p key={index} className="text-xs text-gray-600 bg-orange-50 px-2 py-1 rounded">
              {mistake}
            </p>
          ))}
          {junior.mistakesIdentified.length > 2 && (
            <p className="text-xs text-gray-500">
              +{junior.mistakesIdentified.length - 2} more mistakes identified
            </p>
          )}
        </div>
      </div>

      {/* Open Questions */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
          <HelpCircle className="w-4 h-4 mr-1 text-blue-500" />
          Open Questions
        </h4>
        <div className="space-y-1">
          {junior.openQuestions.slice(0, 2).map((question, index) => (
            <p key={index} className="text-xs text-gray-600 bg-blue-50 px-2 py-1 rounded">
              {question}
            </p>
          ))}
          {junior.openQuestions.length > 2 && (
            <p className="text-xs text-gray-500">
              +{junior.openQuestions.length - 2} more questions
            </p>
          )}
        </div>
      </div>

      {/* Next Steps */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
          <ArrowRight className="w-4 h-4 mr-1 text-purple-500" />
          Next Steps
        </h4>
        <div className="space-y-1">
          {junior.nextSteps.slice(0, 2).map((step, index) => (
            <p key={index} className="text-xs text-gray-600 bg-purple-50 px-2 py-1 rounded">
              {step}
            </p>
          ))}
          {junior.nextSteps.length > 2 && (
            <p className="text-xs text-gray-500">
              +{junior.nextSteps.length - 2} more steps
            </p>
          )}
        </div>
      </div>

      {/* Action Button */}
      <button className="w-full mt-4 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors duration-200">
        View Detailed Report
      </button>
    </div>
  );
};

export default MetricsCard;
