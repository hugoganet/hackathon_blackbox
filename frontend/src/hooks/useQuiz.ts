import { useState, useCallback, useEffect } from 'react';
import { QuizCard, QuizQuestion, QuizAttempt, LoadingState, ErrorState } from '../types';
import { apiService } from '../services/api';
import { SpacedRepetitionService } from '../services/spacedRepetition';

export const useQuiz = () => {
  const [cards, setCards] = useState<QuizCard[]>([]);
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
    setLoading({ isLoading: true, message: 'Loading quiz questions...' });
    setError({ hasError: false });

    try {
      const questions = await apiService.getQuizQuestions(20);

      // Convert questions to cards with spaced repetition data
      const quizCards: QuizCard[] = questions.map(question => ({
        ...question,
        ...SpacedRepetitionService.initializeCard()
      }));

      setCards(quizCards);

      // Set first due card as current
      const dueCards = SpacedRepetitionService.getDueCards(quizCards);
      const sortedCards = SpacedRepetitionService.sortCardsByPriority(dueCards);

      if (sortedCards.length > 0) {
        setCurrentCard(sortedCards[0]);
      } else if (quizCards.length > 0) {
        // If no cards are due, start with the first card
        setCurrentCard(quizCards[0]);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load quiz questions';
      setError({ hasError: true, message: errorMessage });
    } finally {
      setLoading({ isLoading: false });
    }
  }, []);

  // Submit answer for current card
  const submitAnswer = useCallback(async (selectedAnswer: number) => {
    if (!currentCard) return;

    const startTime = Date.now();
    setLoading({ isLoading: true, message: 'Checking answer...' });

    try {
      const result = await apiService.submitQuizAnswer(currentCard.id, selectedAnswer);
      const timeSpent = Math.round((Date.now() - startTime) / 1000);

      // Record attempt
      const attempt: QuizAttempt = {
        questionId: currentCard.id,
        selectedAnswer,
        isCorrect: result.isCorrect,
        timeSpent,
        timestamp: new Date()
      };

      setAttempts(prev => [...prev, attempt]);

      // Update session stats
      setSessionStats(prev => ({
        correct: prev.correct + (result.isCorrect ? 1 : 0),
        total: prev.total + 1,
        streak: result.isCorrect ? prev.streak + 1 : 0
      }));

      // Calculate quality for spaced repetition
      const quality = SpacedRepetitionService.calculateQuality(
        result.isCorrect,
        timeSpent,
        currentCard.difficulty
      );

      // Update card with new spaced repetition data
      const updatedSRData = SpacedRepetitionService.updateCard(quality, {
        easeFactor: currentCard.easeFactor,
        interval: currentCard.interval,
        repetitions: currentCard.repetitions,
        nextReview: currentCard.nextReview
      });

      const updatedCard: QuizCard = {
        ...currentCard,
        ...updatedSRData,
        lastReviewed: new Date()
      };

      // Update cards array
      setCards(prev => prev.map(card =>
        card.id === currentCard.id ? updatedCard : card
      ));

      setShowAnswer(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit answer';
      setError({ hasError: true, message: errorMessage });
    } finally {
      setLoading({ isLoading: false });
    }
  }, [currentCard]);

  // Move to next card
  const nextCard = useCallback(() => {
    if (!cards.length) return;

    const dueCards = SpacedRepetitionService.getDueCards(cards);
    const sortedCards = SpacedRepetitionService.sortCardsByPriority(dueCards);

    // Find next card (excluding current one)
    const nextCardIndex = sortedCards.findIndex(card =>
      currentCard && card.id !== currentCard.id
    );

    if (nextCardIndex >= 0) {
      setCurrentCard(sortedCards[nextCardIndex]);
    } else if (sortedCards.length > 0) {
      // If we've gone through all due cards, start over
      setCurrentCard(sortedCards[0]);
    } else {
      // No more due cards
      setCurrentCard(null);
    }

    setShowAnswer(false);
    setError({ hasError: false });
  }, [cards, currentCard]);

  // Reset quiz session
  const resetSession = useCallback(() => {
    setAttempts([]);
    setSessionStats({ correct: 0, total: 0, streak: 0 });
    setShowAnswer(false);
    setError({ hasError: false });

    if (cards.length > 0) {
      const dueCards = SpacedRepetitionService.getDueCards(cards);
      const sortedCards = SpacedRepetitionService.sortCardsByPriority(dueCards);
      setCurrentCard(sortedCards.length > 0 ? sortedCards[0] : cards[0]);
    }
  }, [cards]);

  // Get study statistics
  const getStudyStats = useCallback(() => {
    return SpacedRepetitionService.getStudyStats(cards);
  }, [cards]);

  // Get weekly schedule
  const getWeeklySchedule = useCallback(() => {
    return SpacedRepetitionService.getWeeklySchedule(cards);
  }, [cards]);

  // Load questions on mount
  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  return {
    cards,
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
    getWeeklySchedule
  };
};
