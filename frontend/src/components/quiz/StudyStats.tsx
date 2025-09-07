import React from 'react';
import { X, TrendingUp, Calendar, Brain } from 'lucide-react';

interface StudyStatsProps {
  stats: {
    totalCards: number;
    dueCards: number;
    overdueCards: number;
    masteredCards: number;
    learningCards: number;
    totalReviews: number;
    averageEaseFactor: number;
    // Statistiques de la journée
    todayCorrect: number;
    todayTotal: number;
    todaySuccessRate: number;
  };
  weeklySchedule: { date: string; count: number }[];
  onClose: () => void;
}

const StudyStats: React.FC<StudyStatsProps> = ({ stats, onClose }) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <TrendingUp className="w-5 h-5 mr-2 text-primary-600" />
          Statistiques d'étude
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 p-1"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Statistiques de la journée */}
      <div className="mb-8">
        <h4 className="text-md font-semibold text-gray-800 mb-3 flex items-center">
          <Calendar className="w-4 h-4 mr-2 text-blue-600" />
          Aujourd'hui
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{stats.todaySuccessRate}%</div>
            <div className="text-sm text-blue-800">Taux de réussite</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{stats.todayCorrect}/{stats.todayTotal}</div>
            <div className="text-sm text-green-800">Réponses correctes</div>
          </div>
        </div>
      </div>

      {/* Statistiques globales */}
      <div className="mb-6">
        <h4 className="text-md font-semibold text-gray-800 mb-3 flex items-center">
          <Brain className="w-4 h-4 mr-2 text-purple-600" />
          Vue d'ensemble
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{stats.masteredCards}</div>
            <div className="text-sm text-green-800">Cartes maîtrisées</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">{stats.learningCards}</div>
            <div className="text-sm text-orange-800">Cartes en apprentissages</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudyStats;
