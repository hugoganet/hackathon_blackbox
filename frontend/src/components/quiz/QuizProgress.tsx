import React from 'react';
import { Trophy, Target, Zap } from 'lucide-react';

interface QuizProgressProps {
  correct: number;
  total: number;
  streak: number;
}

const QuizProgress: React.FC<QuizProgressProps> = ({ correct, total, streak }) => {
  const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0;
  const progressWidth = total > 0 ? (correct / total) * 100 : 0;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900">Session Progress</h3>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center text-green-600">
            <Target className="w-4 h-4 mr-1" />
            <span className="font-medium">{correct}/{total}</span>
          </div>
          <div className="flex items-center text-blue-600">
            <Zap className="w-4 h-4 mr-1" />
            <span className="font-medium">{streak}</span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div
          className="bg-primary-600 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progressWidth}%` }}
        />
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>Accuracy: {accuracy}%</span>
        <div className="flex items-center">
          {streak > 0 && (
            <>
              <Trophy className="w-3 h-3 mr-1 text-yellow-500" />
              <span className="text-yellow-600 font-medium">{streak} streak</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuizProgress;
