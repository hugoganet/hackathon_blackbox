import { useState, useCallback, useEffect } from 'react';
import { QuizCard, QuizAttempt, LoadingState, ErrorState } from '../types';
import { apiService } from '../services/api';
import { SpacedRepetitionService } from '../services/spacedRepetition';

export const useQuiz = () => {
  const [allCards, setAllCards] = useState<QuizCard[]>([]);
  const [availableCards, setAvailableCards] = useState<QuizCard[]>([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [currentCard, setCurrentCard] = useState<QuizCard | null>(null);
  const [attempts, setAttempts] = useState<QuizAttempt[]>([]);
  const [loading, setLoading] = useState<LoadingState>({ isLoading: false });
  const [error, setError] = useState<ErrorState>({ hasError: false });
  const [showAnswer, setShowAnswer] = useState(false);
  const [sessionStats, setSessionStats] = useState({
    correct: 0,
    total: 0,
    streak: 0
  });

  // Load quiz questions and convert to cards
  const loadQuestions = useCallback(async () => {
    setLoading({ isLoading: true, message: 'Chargement des questions...' });
    setError({ hasError: false });

    try {
      const questions = await apiService.getQuizQuestions(10);

      // Convert questions to cards with spaced repetition data
      const quizCards: QuizCard[] = questions.map(question => ({
        ...question,
        ...SpacedRepetitionService.initializeCard()
      }));

      setAllCards(quizCards);
      setAvailableCards(quizCards);
      setCurrentCardIndex(0);

      // Set first card as current
      if (quizCards.length > 0) {
        setCurrentCard(quizCards[0]);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors du chargement des questions';
      setError({ hasError: true, message: errorMessage });
    } finally {
      setLoading({ isLoading: false });
    }
  }, []);

  // Submit answer for current card
  const submitAnswer = useCallback(async (selectedAnswer: number) => {
    if (!currentCard) return;

    setLoading({ isLoading: true, message: 'Vérification de la réponse...' });
    setError({ hasError: false });

    try {
      // Vérifier la réponse localement
      const isCorrect = selectedAnswer === currentCard.correctAnswer;

      // Record attempt
      const attempt: QuizAttempt = {
        questionId: currentCard.id,
        selectedAnswer,
        isCorrect,
        timeSpent: 2,
        timestamp: new Date()
      };

      setAttempts(prev => [...prev, attempt]);

      // Update session stats
      setSessionStats(prev => ({
        correct: prev.correct + (isCorrect ? 1 : 0),
        total: prev.total + 1,
        streak: isCorrect ? prev.streak + 1 : 0
      }));

      setShowAnswer(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de la soumission';
      setError({ hasError: true, message: errorMessage });
    } finally {
      setLoading({ isLoading: false });
    }
  }, [currentCard]);

  // Move to next card
  const nextCard = useCallback(() => {
    const nextIndex = currentCardIndex + 1;

    if (nextIndex < availableCards.length) {
      setCurrentCardIndex(nextIndex);
      setCurrentCard(availableCards[nextIndex]);
    } else {
      // No more cards
      setCurrentCard(null);
    }

    setShowAnswer(false);
    setError({ hasError: false });
  }, [availableCards, currentCardIndex]);

  // Reset quiz session
  const resetSession = useCallback(() => {
    setAttempts([]);
    setSessionStats({ correct: 0, total: 0, streak: 0 });
    setCurrentCardIndex(0);
    setShowAnswer(false);
    setError({ hasError: false });

    if (availableCards.length > 0) {
      setCurrentCard(availableCards[0]);
    }
  }, [availableCards]);

  // Get study statistics
  const getStudyStats = useCallback(() => {
    return {
      totalCards: allCards.length,
      dueCards: availableCards.length,
      overdueCards: 0,
      masteredCards: Math.floor(allCards.length * 0.3), // Simulation
      totalReviews: attempts.length,
      averageEaseFactor: 2.5,
      completionRate: allCards.length > 0 ? Math.round((sessionStats.correct / Math.max(sessionStats.total, 1)) * 100) : 0
    };
  }, [allCards, availableCards, attempts, sessionStats]);

  // Load questions on mount
  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  return {
    cards: allCards,
    currentCard,
    attempts,
    loading,
    error,
    showAnswer,
    sessionStats,
    submitAnswer,
    nextCard,
    resetSession,
    loadQuestions,
    getStudyStats,
    // Helper pour la progression
    totalAvailableCards: availableCards.length,
    currentCardNumber: currentCardIndex + 1
  };
};
