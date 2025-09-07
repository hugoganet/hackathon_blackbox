"""
Spaced Repetition Algorithm Implementation for Dev Mentor AI
Based on SM-2 algorithm with adaptations for programming learning
"""

from datetime import date, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import math


class CardState(Enum):
    """Flashcard learning states"""
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    MATURE = "mature"


@dataclass
class ReviewResult:
    """Result of a flashcard review calculation"""
    next_review_date: date
    interval_days: int
    difficulty_factor: float
    review_count: int
    card_state: CardState


@dataclass
class InitialParameters:
    """Initial parameters for a new flashcard"""
    next_review_date: date
    interval_days: int
    difficulty_factor: float
    card_state: CardState


class SpacedRepetitionEngine:
    """
    SM-2 based spaced repetition algorithm for flashcard scheduling
    
    Adapted for programming learning with:
    - Confidence score integration from curator analysis
    - Performance-based difficulty adjustment
    - Card state progression tracking
    """
    
    # SM-2 Algorithm Constants
    MIN_EASE_FACTOR = 1.3
    DEFAULT_EASE_FACTOR = 2.5
    MAX_EASE_FACTOR = 4.0
    
    # Learning intervals (days)
    LEARNING_INTERVALS = [1, 6]  # First review: 1 day, Second: 6 days
    MIN_MATURE_INTERVAL = 21     # Cards with interval ≥21 days are "mature"
    
    def __init__(self):
        """Initialize the spaced repetition engine"""
        pass
    
    def get_initial_parameters(self, confidence_score: float = 0.5) -> InitialParameters:
        """
        Calculate initial parameters for a new flashcard
        
        Args:
            confidence_score: Curator confidence (0.0-1.0), affects initial scheduling
            
        Returns:
            InitialParameters with first review date and settings
        """
        # Convert confidence to initial ease factor
        # Higher confidence = longer initial interval
        ease_factor = self.DEFAULT_EASE_FACTOR + (confidence_score - 0.5) * 0.5
        ease_factor = max(self.MIN_EASE_FACTOR, min(self.MAX_EASE_FACTOR, ease_factor))
        
        # Initial interval: 1 day for new cards
        initial_interval = 1
        next_review_date = date.today() + timedelta(days=initial_interval)
        
        return InitialParameters(
            next_review_date=next_review_date,
            interval_days=initial_interval,
            difficulty_factor=ease_factor,
            card_state=CardState.NEW
        )
    
    def calculate_next_review(
        self,
        current_interval: int,
        difficulty_factor: float,
        success_score: int,
        review_count: int
    ) -> ReviewResult:
        """
        Calculate next review date using SM-2 algorithm
        
        Args:
            current_interval: Current interval in days
            difficulty_factor: Current ease factor (difficulty)
            success_score: Review performance (0-5 scale)
            review_count: Number of previous reviews
            
        Returns:
            ReviewResult with updated scheduling parameters
        """
        # Validate inputs
        success_score = max(0, min(5, success_score))
        difficulty_factor = max(self.MIN_EASE_FACTOR, min(self.MAX_EASE_FACTOR, difficulty_factor))
        
        # SM-2 Algorithm Implementation
        if success_score < 3:
            # Failed review - reset to learning state
            new_interval = 1
            new_ease_factor = max(self.MIN_EASE_FACTOR, difficulty_factor - 0.2)
            new_review_count = 0
            card_state = CardState.LEARNING
            
        else:
            # Successful review - calculate next interval
            new_review_count = review_count + 1
            
            if new_review_count == 1:
                # First successful review
                new_interval = self.LEARNING_INTERVALS[0]  # 1 day
                card_state = CardState.LEARNING
                
            elif new_review_count == 2:
                # Second successful review
                new_interval = self.LEARNING_INTERVALS[1]  # 6 days
                card_state = CardState.LEARNING
                
            else:
                # Subsequent reviews - use SM-2 formula
                new_interval = math.ceil(current_interval * difficulty_factor)
                card_state = CardState.MATURE if new_interval >= self.MIN_MATURE_INTERVAL else CardState.REVIEW
            
            # Update ease factor based on performance
            new_ease_factor = self._calculate_ease_factor(difficulty_factor, success_score)
        
        # Calculate next review date
        next_review_date = date.today() + timedelta(days=new_interval)
        
        return ReviewResult(
            next_review_date=next_review_date,
            interval_days=new_interval,
            difficulty_factor=new_ease_factor,
            review_count=new_review_count,
            card_state=card_state
        )
    
    def _calculate_ease_factor(self, current_ease: float, success_score: int) -> float:
        """
        Calculate new ease factor using SM-2 formula
        
        Args:
            current_ease: Current ease factor
            success_score: Performance score (0-5)
            
        Returns:
            Updated ease factor
        """
        # SM-2 ease factor adjustment formula
        # EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
        # where q is the success score (0-5)
        
        q = success_score
        adjustment = 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
        new_ease = current_ease + adjustment
        
        # Clamp to valid range
        return max(self.MIN_EASE_FACTOR, min(self.MAX_EASE_FACTOR, new_ease))
    
    def get_retention_probability(self, days_since_review: int, difficulty_factor: float) -> float:
        """
        Estimate retention probability using forgetting curve
        
        Args:
            days_since_review: Days since last review
            difficulty_factor: Card's ease factor
            
        Returns:
            Estimated retention probability (0.0-1.0)
        """
        # Simplified forgetting curve based on ease factor
        # Higher ease factor = slower forgetting
        decay_rate = 1.0 / difficulty_factor
        retention = math.exp(-decay_rate * days_since_review)
        
        return max(0.0, min(1.0, retention))
    
    def is_overdue(self, card_next_review_date: date, urgency_days: int = 1) -> bool:
        """
        Check if a flashcard is overdue for review
        
        Args:
            card_next_review_date: Scheduled review date
            urgency_days: Additional days before considering overdue
            
        Returns:
            True if card is overdue
        """
        today = date.today()
        due_date = card_next_review_date + timedelta(days=urgency_days)
        return today >= due_date
    
    def get_card_priority(
        self,
        next_review_date: date,
        difficulty_factor: float,
        review_count: int
    ) -> float:
        """
        Calculate card priority for review scheduling
        
        Args:
            next_review_date: Scheduled review date
            difficulty_factor: Card's ease factor
            review_count: Number of reviews completed
            
        Returns:
            Priority score (higher = more urgent)
        """
        today = date.today()
        days_overdue = max(0, (today - next_review_date).days)
        
        # Priority factors:
        # 1. Overdue cards get higher priority
        # 2. Lower ease factor (harder cards) get higher priority  
        # 3. Cards with fewer reviews get higher priority
        
        overdue_weight = days_overdue * 2.0
        difficulty_weight = (self.MAX_EASE_FACTOR - difficulty_factor) * 0.5
        newness_weight = max(0, 10 - review_count) * 0.1
        
        return overdue_weight + difficulty_weight + newness_weight


# Development testing
if __name__ == "__main__":
    print("Testing Spaced Repetition Engine...")
    
    engine = SpacedRepetitionEngine()
    
    # Test 1: Initial parameters
    initial = engine.get_initial_parameters(confidence_score=0.7)
    print(f"Initial: {initial}")
    
    # Test 2: Successful reviews
    result1 = engine.calculate_next_review(1, 2.5, 4, 0)
    print(f"First review (score 4): {result1}")
    
    result2 = engine.calculate_next_review(1, 2.5, 5, 1)  
    print(f"Second review (score 5): {result2}")
    
    result3 = engine.calculate_next_review(6, 2.6, 4, 2)
    print(f"Third review (score 4): {result3}")
    
    # Test 3: Failed review
    failed = engine.calculate_next_review(15, 2.6, 2, 3)
    print(f"Failed review (score 2): {failed}")
    
    # Test 4: Retention probability
    retention = engine.get_retention_probability(7, 2.5)
    print(f"Retention after 7 days: {retention:.2%}")
    
    print("✅ Spaced repetition engine tested successfully!")
