import React, { useState } from 'react';
import { useQuiz } from '../../hooks/useQuiz';
import FlashCard from '../quiz/FlashCard';
import StudyStats from '../quiz/StudyStats';

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
    totalAvailableCards
  } = useQuiz();

  const [showStats, setShowStats] = useState(false);
  const studyStats = getStudyStats();

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

  // Show stats modal (disponible partout)
  if (showStats) {
    const weeklySchedule = [
      { date: new Date().toISOString(), count: sessionStats.total },
      { date: new Date(Date.now() + 86400000).toISOString(), count: studyStats.dueCards },
      { date: new Date(Date.now() + 2 * 86400000).toISOString(), count: Math.floor(studyStats.dueCards * 0.7) },
      { date: new Date(Date.now() + 3 * 86400000).toISOString(), count: Math.floor(studyStats.dueCards * 0.5) },
      { date: new Date(Date.now() + 4 * 86400000).toISOString(), count: Math.floor(studyStats.dueCards * 0.3) },
      { date: new Date(Date.now() + 5 * 86400000).toISOString(), count: Math.floor(studyStats.dueCards * 0.2) },
      { date: new Date(Date.now() + 6 * 86400000).toISOString(), count: Math.floor(studyStats.dueCards * 0.1) },
    ];

    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto p-6">
          <StudyStats
            stats={studyStats}
            weeklySchedule={weeklySchedule}
            onClose={() => setShowStats(false)}
          />
        </div>
      </div>
    );
  }

  if (!currentCard) {
    // Show completion screen
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {sessionStats.total > 0 ? 'Session terminée !' : 'Rien à réviser aujourd\'hui !'}
          </h2>
          <p className="text-gray-600 mb-6">
            {sessionStats.total > 0
              ? `Vous avez révisé ${sessionStats.total} cartes avec ${sessionStats.correct} bonnes réponses sur ${totalAvailableCards} cartes disponibles.`
              : 'Revenez demain pour de nouvelles révisions basées sur votre progression.'
            }
          </p>
          <div className="space-y-3">
            <button
              onClick={() => setShowStats(true)}
              className="bg-primary-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-primary-700 w-full"
            >
              📊 Voir ma progression
            </button>
            {sessionStats.total > 0 && (
              <button
                onClick={resetSession}
                className="bg-gray-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-gray-700 w-full"
              >
                🔄 Réviser à nouveau
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto p-6">
        {/* En-tête simplifié */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Révisions du jour
          </h1>
          <p className="text-gray-600">
            {totalAvailableCards} cartes à réviser
          </p>
        </div>

        {/* Session Progress simplifié */}
        <div className="mb-6">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
            <span>Progression</span>
            <span>{sessionStats.total} / {totalAvailableCards}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{
                width: totalAvailableCards > 0
                  ? `${(sessionStats.total / totalAvailableCards) * 100}%`
                  : '0%'
              }}
            ></div>
          </div>
          {sessionStats.streak > 0 && (
            <div className="text-center mt-2">
              <span className="text-sm text-green-600 font-medium">
                🔥 {sessionStats.streak} bonnes réponses d'affilée
              </span>
            </div>
          )}
        </div>

        {/* Bouton Stats en haut à droite */}
        <div className="text-right mb-6">
          <button
            onClick={() => setShowStats(true)}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            📊 Voir ma progression
          </button>
        </div>

        {/* Zone de carte principale */}
        {currentCard && (
          <FlashCard
            card={currentCard}
            showAnswer={showAnswer}
            onSubmitAnswer={submitAnswer}
            onNextCard={nextCard}
            disabled={loading.isLoading}
          />
        )}
      </div>
    </div>
  );
};

export default QuizzesPage;
