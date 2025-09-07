import React from 'react';
import { X, TrendingUp, Calendar, Target, Brain, Clock } from 'lucide-react';

interface StudyStatsProps {
  stats: {
    totalCards: number;
    dueCards: number;
    overdueCards: number;
    masteredCards: number;
    totalReviews: number;
    averageEaseFactor: number;
    completionRate: number;
  };
  weeklySchedule: { date: string; count: number }[];
  onClose: () => void;
}

const StudyStats: React.FC<StudyStatsProps> = ({ stats, weeklySchedule, onClose }) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <TrendingUp className="w-5 h-5 mr-2 text-primary-600" />
          Study Statistics
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 p-1"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{stats.totalCards}</div>
          <div className="text-sm text-blue-800">Total Cards</div>
        </div>
        <div className="text-center p-3 bg-orange-50 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">{stats.dueCards}</div>
          <div className="text-sm text-orange-800">Due Today</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{stats.masteredCards}</div>
          <div className="text-sm text-green-800">Mastered</div>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">{stats.completionRate}%</div>
          <div className="text-sm text-purple-800">Completion</div>
        </div>
      </div>

      {/* Detailed Stats */}
      <div className="space-y-4 mb-6">
        <div className="flex items-center justify-between py-2 border-b border-gray-100">
          <div className="flex items-center text-gray-600">
            <Brain className="w-4 h-4 mr-2" />
            <span>Total Reviews</span>
          </div>
          <span className="font-medium text-gray-900">{stats.totalReviews}</span>
        </div>
        <div className="flex items-center justify-between py-2 border-b border-gray-100">
          <div className="flex items-center text-gray-600">
            <Target className="w-4 h-4 mr-2" />
            <span>Average Ease Factor</span>
          </div>
          <span className="font-medium text-gray-900">{stats.averageEaseFactor}</span>
        </div>
        <div className="flex items-center justify-between py-2 border-b border-gray-100">
          <div className="flex items-center text-gray-600">
            <Clock className="w-4 h-4 mr-2" />
            <span>Overdue Cards</span>
          </div>
          <span className="font-medium text-gray-900">{stats.overdueCards}</span>
        </div>
      </div>

      {/* Weekly Schedule */}
      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
          <Calendar className="w-4 h-4 mr-2" />
          Next 7 Days Schedule
        </h4>
        <div className="grid grid-cols-7 gap-2">
          {weeklySchedule.map((day, index) => (
            <div key={index} className="text-center">
              <div className="text-xs text-gray-500 mb-1">
                {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
              </div>
              <div className={`text-sm font-medium py-1 px-2 rounded ${
                day.count > 0
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                {day.count}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance Insights */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Performance Insights</h4>
        <div className="space-y-2 text-sm text-gray-600">
          {stats.completionRate >= 80 && (
            <p className="text-green-600">🎉 Excellent progress! You're mastering most concepts.</p>
          )}
          {stats.overdueCards > 5 && (
            <p className="text-orange-600">⚠️ You have several overdue cards. Consider reviewing them soon.</p>
          )}
          {stats.averageEaseFactor < 2.0 && (
            <p className="text-blue-600">💡 Focus on difficult topics to improve your ease factor.</p>
          )}
          {stats.dueCards === 0 && (
            <p className="text-green-600">✅ No cards due today! Great job staying on schedule.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudyStats;
