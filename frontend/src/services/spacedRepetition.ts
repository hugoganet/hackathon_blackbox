import { SpacedRepetitionData, QuizCard } from '../types';

/**
 * SM-2 Algorithm Implementation for Spaced Repetition
 * Based on the SuperMemo SM-2 algorithm
 */

export class SpacedRepetitionService {
  /**
   * Calculate next review date and update spaced repetition data
   * @param quality - Quality of response (0-5, where 3+ is passing)
   * @param currentData - Current spaced repetition data
   * @returns Updated spaced repetition data
   */
  static updateCard(quality: number, currentData: SpacedRepetitionData): SpacedRepetitionData {
    let { easeFactor, interval, repetitions } = currentData;

    // Ensure quality is within valid range
    quality = Math.max(0, Math.min(5, quality));

    if (quality >= 3) {
      // Correct response
      if (repetitions === 0) {
        interval = 1;
      } else if (repetitions === 1) {
        interval = 6;
      } else {
        interval = Math.round(interval * easeFactor);
      }
      repetitions += 1;
    } else {
      // Incorrect response - reset repetitions and set short interval
      repetitions = 0;
      interval = 1;
    }

    // Update ease factor
    easeFactor = easeFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));

    // Ensure ease factor doesn't go below 1.3
    easeFactor = Math.max(1.3, easeFactor);

    // Calculate next review date
    const nextReview = new Date();
    nextReview.setDate(nextReview.getDate() + interval);

    return {
      easeFactor,
      interval,
      repetitions,
      nextReview
    };
  }

  /**
   * Convert quiz performance to SM-2 quality score
   * @param isCorrect - Whether the answer was correct
   * @param timeSpent - Time spent on question (in seconds)
   * @param difficulty - Question difficulty level
   * @returns Quality score (0-5)
   */
  static calculateQuality(
    isCorrect: boolean,
    timeSpent: number,
    difficulty: 'beginner' | 'intermediate' | 'advanced'
  ): number {
    if (!isCorrect) {
      return Math.random() < 0.5 ? 0 : 1; // Failed responses
    }

    // Base quality for correct answers
    let quality = 4;

    // Adjust based on time spent (assuming optimal times)
    const optimalTimes = {
      beginner: 30,     // 30 seconds
      intermediate: 45, // 45 seconds
      advanced: 60      // 60 seconds
    };

    const optimalTime = optimalTimes[difficulty];
    const timeRatio = timeSpent / optimalTime;

    if (timeRatio <= 0.5) {
      // Very fast - excellent understanding
      quality = 5;
    } else if (timeRatio <= 1.0) {
      // Within optimal time - good understanding
      quality = 4;
    } else if (timeRatio <= 2.0) {
      // Slower but still reasonable
      quality = 3;
    } else {
      // Very slow - barely passing
      quality = 3;
    }

    return quality;
  }

  /**
   * Get cards that are due for review
   * @param cards - Array of quiz cards
   * @returns Cards that need to be reviewed
   */
  static getDueCards(cards: QuizCard[]): QuizCard[] {
    const now = new Date();
    return cards.filter(card => card.nextReview <= now);
  }

  /**
   * Sort cards by priority (most urgent first)
   * @param cards - Array of quiz cards
   * @returns Sorted cards
   */
  static sortCardsByPriority(cards: QuizCard[]): QuizCard[] {
    return [...cards].sort((a, b) => {
      // First, prioritize overdue cards
      const now = new Date();
      const aOverdue = a.nextReview < now;
      const bOverdue = b.nextReview < now;

      if (aOverdue && !bOverdue) return -1;
      if (!aOverdue && bOverdue) return 1;

      // Then sort by next review date
      return a.nextReview.getTime() - b.nextReview.getTime();
    });
  }

  /**
   * Initialize spaced repetition data for a new card
   * @returns Initial spaced repetition data
   */
  static initializeCard(): SpacedRepetitionData {
    const nextReview = new Date();
    nextReview.setDate(nextReview.getDate() + 1); // Review tomorrow

    return {
      easeFactor: 2.5,  // Default ease factor
      interval: 1,      // Review in 1 day
      repetitions: 0,   // No repetitions yet
      nextReview
    };
  }

  /**
   * Get study statistics for a user
   * @param cards - User's quiz cards
   * @returns Study statistics
   */
  static getStudyStats(cards: QuizCard[]) {
    const now = new Date();
    const dueCards = cards.filter(card => card.nextReview <= now);
    const overdueCards = cards.filter(card => card.nextReview < now);
    const masteredCards = cards.filter(card => card.repetitions >= 3 && card.easeFactor >= 2.5);

    const totalReviews = cards.reduce((sum, card) => sum + card.repetitions, 0);
    const averageEaseFactor = cards.length > 0
      ? cards.reduce((sum, card) => sum + card.easeFactor, 0) / cards.length
      : 0;

    return {
      totalCards: cards.length,
      dueCards: dueCards.length,
      overdueCards: overdueCards.length,
      masteredCards: masteredCards.length,
      totalReviews,
      averageEaseFactor: Math.round(averageEaseFactor * 100) / 100,
      completionRate: cards.length > 0 ? Math.round((masteredCards.length / cards.length) * 100) : 0
    };
  }

  /**
   * Generate study schedule for the next week
   * @param cards - User's quiz cards
   * @returns Daily review counts for the next 7 days
   */
  static getWeeklySchedule(cards: QuizCard[]): { date: string; count: number }[] {
    const schedule = [];
    const today = new Date();

    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);

      const count = cards.filter(card => {
        const reviewDate = new Date(card.nextReview);
        return reviewDate.toDateString() === date.toDateString();
      }).length;

      schedule.push({
        date: date.toISOString().split('T')[0],
        count
      });
    }

    return schedule;
  }
}
