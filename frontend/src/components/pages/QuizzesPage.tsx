import React, { useState } from 'react';
import { useQuiz } from '../../hooks/useQuiz';
import FlashCard from '../quiz/FlashCard';
import QuizProgress from '../quiz/QuizProgress';
import StudyStats from '../quiz/StudyStats';
import { Brain, Play, RotateCcw, TrendingUp } from 'lucide-react';

const QuizzesPage: React.FC = () => {
  const {
    currentCard,
    loading,
    error,
    showAnswer,
    sessionStats,
    submitAnswer,
    nextCard,
    resetSession,
    getStudyStats,
    getWeeklySchedule
  } = useQuiz();

  const [showStats, setShowStats] = useState(false);

  const studyStats = getStudyStats();
  const weeklySchedule = getWeeklySchedule();

  if (loading.isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">{loading.message}</p>
        </div>
      </div>
    );
  }

  if (error.hasError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Quiz</h2>
          <p className="text-gray-600 mb-4">{error.message}</p>
          <button
            onClick={resetSession}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!currentCard) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Great Job!</h2>
          <p className="text-gray-600 mb-6">
            You've completed all available quiz cards for now. Check back later for new questions based on your learning progress.
          </p>
          <div className="space-y-3">
            <button
              onClick={resetSession}
              className="btn-primary w-full"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Review Cards Again
            </button>
            <button
              onClick={() => setShowStats(true)}
              className="btn-secondary w-full"
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              View Study Statistics
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
                <Brain className="w-8 h-8 mr-3 text-primary-600" />
                Smart Flashcards
              </h1>
              <p className="text-gray-600">
                Spaced repetition system to reinforce your learning
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowStats(!showStats)}
                className="btn-secondary"
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                Stats
              </button>
              <button
                onClick={resetSession}
                className="btn-secondary"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* Session Progress */}
        <div className="mb-6">
          <QuizProgress
            correct={sessionStats.correct}
            total={sessionStats.total}
            streak={sessionStats.streak}
          />
        </div>

        {/* Study Stats Panel */}
        {showStats && (
          <div className="mb-6">
            <StudyStats
              stats={studyStats}
              weeklySchedule={weeklySchedule}
              onClose={() => setShowStats(false)}
            />
          </div>
        )}

        {/* Main Quiz Area */}
        <div className="flex justify-center">
          <div className="w-full max-w-2xl">
            <FlashCard
              card={currentCard}
              showAnswer={showAnswer}
              onSubmitAnswer={submitAnswer}
              onNextCard={nextCard}
              disabled={loading.isLoading}
            />
          </div>
        </div>



        {/* Quick Stats Footer */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-primary-600">{studyStats.totalCards}</p>
            <p className="text-sm text-gray-600">Total Cards</p>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-green-600">{studyStats.masteredCards}</p>
            <p className="text-sm text-gray-600">Mastered</p>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-orange-600">{studyStats.dueCards}</p>
            <p className="text-sm text-gray-600">Due Today</p>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{studyStats.completionRate}%</p>
            <p className="text-sm text-gray-600">Completion</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuizzesPage;
