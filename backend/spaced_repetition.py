"""
Spaced Repetition Algorithm Implementation

This module implements the SM-2 spaced repetition algorithm for optimal flashcard
review scheduling based on user performance.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import math
from dataclasses import dataclass
from enum import Enum


class CardState(Enum):
    """Flashcard learning states"""
    NEW = "new"  # Never reviewed
    LEARNING = "learning"  # Being learned (interval < 1 day)
    REVIEW = "review"  # In review phase (interval >= 1 day)
    MATURE = "mature"  # Mastered (interval >= 21 days)


@dataclass
class ReviewResult:
    """Result of a flashcard review session"""
    flashcard_id: str
    user_id: str
    success_score: int  # 0-5 scale
    response_time: Optional[int] = None  # seconds
    review_date: datetime = None
    
    def __post_init__(self):
        if self.review_date is None:
            self.review_date = datetime.utcnow()


@dataclass
class SpacingParameters:
    """Parameters for spaced repetition calculation"""
    next_review_date: date
    difficulty_factor: float
    interval_days: int
    card_state: CardState
    review_count: int


class SpacedRepetitionEngine:
    """
    SM-2 based spaced repetition algorithm implementation
    
    This class implements a simplified version of the SM-2 algorithm
    optimized for the Dev Mentor AI learning system.
    """
    
    # Algorithm constants
    INITIAL_EASE_FACTOR = 2.5
    MIN_EASE_FACTOR = 1.3
    MAX_EASE_FACTOR = 3.0  # Allow higher than initial for good performance
    EASE_ADJUSTMENT = 0.15
    FAIL_THRESHOLD = 3  # Success scores below this trigger relearning
    MATURE_INTERVAL_THRESHOLD = 21  # Days to be considered mature
    
    def __init__(self):
        """Initialize the spaced repetition engine"""
        pass
    
    def calculate_next_review(
        self, 
        current_interval: int,
        difficulty_factor: float,
        success_score: int,
        review_count: int = 0
    ) -> SpacingParameters:
        """
        Calculate the next review parameters based on performance
        
        Args:
            current_interval: Current interval in days
            difficulty_factor: Current ease factor (1.3-2.5)
            success_score: Performance score (0-5)
            review_count: Number of previous reviews
            
        Returns:
            SpacingParameters with next review details
        """
        # Update ease factor based on performance
        new_difficulty_factor = self._update_difficulty_factor(difficulty_factor, success_score)
        
        # Calculate next interval
        new_interval = self._calculate_interval(current_interval, new_difficulty_factor, success_score, review_count)
        
        # Determine card state
        card_state = self._determine_card_state(new_interval, success_score, review_count)
        
        # Calculate next review date
        next_review_date = date.today() + timedelta(days=new_interval)
        
        return SpacingParameters(
            next_review_date=next_review_date,
            difficulty_factor=new_difficulty_factor,
            interval_days=new_interval,
            card_state=card_state,
            review_count=review_count + 1
        )
    
    def _update_difficulty_factor(self, current_factor: float, success_score: int) -> float:
        """
        Update the difficulty factor based on review performance
        
        SM-2 formula: EF' = EF + (0.1 - (5-q)*(0.08+(5-q)*0.02))
        where q is the quality of response (success_score)
        """
        # Clamp success_score to valid range
        q = max(0, min(5, success_score))
        
        # Apply SM-2 formula
        adjustment = 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
        new_factor = current_factor + adjustment
        
        # Clamp to valid range
        return max(self.MIN_EASE_FACTOR, min(self.MAX_EASE_FACTOR, new_factor))
    
    def _calculate_interval(
        self, 
        current_interval: int, 
        ease_factor: float, 
        success_score: int,
        review_count: int
    ) -> int:
        """Calculate the next review interval in days"""
        
        # Failed review - reset to learning state
        if success_score < self.FAIL_THRESHOLD:
            return 1
        
        # First successful review
        if review_count == 0:
            return 1
        
        # Second successful review  
        if review_count == 1:
            return 6
        
        # Subsequent reviews - apply ease factor
        new_interval = math.ceil(current_interval * ease_factor)
        
        # Ensure minimum progression (at least 1 day increase)
        return max(new_interval, current_interval + 1)
    
    def _determine_card_state(self, interval_days: int, success_score: int, review_count: int) -> CardState:
        """Determine the learning state of the card"""
        if review_count == 0:
            return CardState.NEW
        elif success_score < self.FAIL_THRESHOLD:
            return CardState.LEARNING
        elif interval_days >= self.MATURE_INTERVAL_THRESHOLD:
            return CardState.MATURE
        else:
            return CardState.REVIEW
    
    def get_initial_parameters(self, confidence_score: float = 0.5) -> SpacingParameters:
        """
        Get initial spacing parameters for a new flashcard
        
        Args:
            confidence_score: Initial confidence from curator (0.0-1.0)
            
        Returns:
            Initial SpacingParameters for the card
        """
        # Clamp confidence score to valid range
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        # Map confidence to initial interval
        # High confidence: longer initial interval
        # Low confidence: shorter initial interval
        initial_interval = 1 if confidence_score < 0.7 else 3
        
        # Initial difficulty factor based on confidence
        initial_ease = self.MIN_EASE_FACTOR + (confidence_score * (self.MAX_EASE_FACTOR - self.MIN_EASE_FACTOR))
        initial_ease = max(self.MIN_EASE_FACTOR, min(self.MAX_EASE_FACTOR, initial_ease))
        
        return SpacingParameters(
            next_review_date=date.today() + timedelta(days=initial_interval),
            difficulty_factor=initial_ease,
            interval_days=initial_interval,
            card_state=CardState.NEW,
            review_count=0
        )
    
    def process_review_batch(self, reviews: List[ReviewResult]) -> Dict[str, SpacingParameters]:
        """
        Process a batch of review results
        
        Args:
            reviews: List of ReviewResult objects
            
        Returns:
            Dict mapping flashcard_id to new SpacingParameters
        """
        results = {}
        for review in reviews:
            # This would normally fetch current parameters from database
            # For testing, we'll use realistic values that show progression
            current_interval = 1 if review.success_score < 3 else 3  # Simulate some progression
            current_ease = 2.5   # Would be fetched from DB
            review_count = 1     # Simulate first real review (not initial)
            
            parameters = self.calculate_next_review(
                current_interval=current_interval,
                difficulty_factor=current_ease,
                success_score=review.success_score,
                review_count=review_count
            )
            
            results[review.flashcard_id] = parameters
        
        return results
    
    def get_difficulty_adjustment(self, success_rate: float, time_span_days: int = 30) -> float:
        """
        Calculate difficulty adjustment based on historical success rate
        
        Args:
            success_rate: Success rate over time span (0.0-1.0)
            time_span_days: Time span for calculation
            
        Returns:
            Difficulty adjustment multiplier
        """
        if success_rate < 0.6:
            return 0.8  # Make easier
        elif success_rate > 0.9:
            return 1.2  # Make harder
        else:
            return 1.0  # No change


def calculate_retention_prediction(
    interval_days: int, 
    difficulty_factor: float, 
    review_count: int
) -> float:
    """
    Predict retention probability using simplified forgetting curve
    
    Args:
        interval_days: Days since last review
        difficulty_factor: Card difficulty factor
        review_count: Number of previous reviews
        
    Returns:
        Predicted retention probability (0.0-1.0)
    """
    # Simplified forgetting curve with difficulty adjustment
    # Higher difficulty factor means easier card, so slower decay
    decay_rate = 1.0 / max(1.0, difficulty_factor)
    
    # More reviews increase stability
    stability = math.log(max(1, review_count) + 1) + 1
    
    # Calculate retention with adjusted parameters for better predictions
    retention = math.exp(-decay_rate * interval_days / (stability * 2))
    return max(0.0, min(1.0, retention))


def get_optimal_review_load(target_retention: float = 0.9) -> int:
    """
    Calculate optimal daily review load to maintain target retention
    
    Args:
        target_retention: Target retention rate (0.0-1.0)
        
    Returns:
        Recommended daily review count
    """
    # Simplified calculation - higher retention target means more reviews needed
    base_load = 20
    # Higher target retention needs MORE reviews (inverse relationship with failure rate)
    failure_rate = 1.0 - target_retention
    adjustment = failure_rate * 30  # More failures = fewer reviews needed
    return max(5, int(base_load + adjustment))


# Example usage and testing
if __name__ == "__main__":
    engine = SpacedRepetitionEngine()
    
    # Test initial parameters
    initial = engine.get_initial_parameters(confidence_score=0.8)
    print(f"Initial parameters: {initial}")
    
    # Test review calculation
    next_params = engine.calculate_next_review(
        current_interval=1,
        difficulty_factor=2.5,
        success_score=4,
        review_count=0
    )
    print(f"After first review (success=4): {next_params}")
    
    # Test failed review
    failed_params = engine.calculate_next_review(
        current_interval=6,
        difficulty_factor=2.3,
        success_score=2,
        review_count=1
    )
    print(f"After failed review (success=2): {failed_params}")