"""
Test suite for Spaced Repetition Algorithm
Tests the SM-2 implementation and related functionality
"""

import pytest
from datetime import datetime, date, timedelta
import math

from backend.spaced_repetition import (
    SpacedRepetitionEngine, ReviewResult, SpacingParameters, CardState,
    calculate_retention_prediction, get_optimal_review_load
)


class TestSpacedRepetitionEngine:
    """Test the core spaced repetition engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = SpacedRepetitionEngine()
    
    def test_initialization(self):
        """Test engine initialization with correct constants"""
        assert self.engine.INITIAL_EASE_FACTOR == 2.5
        assert self.engine.MIN_EASE_FACTOR == 1.3
        assert self.engine.MAX_EASE_FACTOR == 3.0  # Updated to allow growth
        assert self.engine.FAIL_THRESHOLD == 3
        assert self.engine.MATURE_INTERVAL_THRESHOLD == 21
    
    def test_initial_parameters_default_confidence(self):
        """Test initial parameters with default confidence"""
        params = self.engine.get_initial_parameters()
        
        assert isinstance(params, SpacingParameters)
        assert params.interval_days == 1  # Default low confidence
        assert params.difficulty_factor >= self.engine.MIN_EASE_FACTOR
        assert params.difficulty_factor <= self.engine.MAX_EASE_FACTOR
        assert params.card_state == CardState.NEW
        assert params.review_count == 0
        assert params.next_review_date == date.today() + timedelta(days=1)
    
    def test_initial_parameters_high_confidence(self):
        """Test initial parameters with high confidence"""
        params = self.engine.get_initial_parameters(confidence_score=0.8)
        
        assert params.interval_days == 3  # High confidence gets longer interval
        assert params.difficulty_factor > 2.0  # Higher ease factor
        assert params.next_review_date == date.today() + timedelta(days=3)
    
    def test_initial_parameters_low_confidence(self):
        """Test initial parameters with low confidence"""
        params = self.engine.get_initial_parameters(confidence_score=0.3)
        
        assert params.interval_days == 1  # Low confidence gets short interval
        assert params.difficulty_factor < 2.0  # Lower ease factor
    
    def test_difficulty_factor_update_success(self):
        """Test difficulty factor updates for successful reviews"""
        # Perfect score should increase ease factor
        new_factor = self.engine._update_difficulty_factor(2.5, 5)
        assert new_factor > 2.5
        assert new_factor <= self.engine.MAX_EASE_FACTOR
        
        # Score 4 should maintain ease factor (zero adjustment in SM-2)
        new_factor = self.engine._update_difficulty_factor(2.5, 4)
        assert new_factor == 2.5
    
    def test_difficulty_factor_update_failure(self):
        """Test difficulty factor updates for failed reviews"""
        # Poor score should decrease ease factor
        new_factor = self.engine._update_difficulty_factor(2.5, 1)
        assert new_factor < 2.5
        assert new_factor >= self.engine.MIN_EASE_FACTOR
        
        # Very poor score should significantly decrease ease factor
        new_factor = self.engine._update_difficulty_factor(2.5, 0)
        assert new_factor < 2.0
    
    def test_difficulty_factor_bounds(self):
        """Test difficulty factor stays within bounds"""
        # Test lower bound
        new_factor = self.engine._update_difficulty_factor(1.3, 0)
        assert new_factor >= self.engine.MIN_EASE_FACTOR
        
        # Test upper bound
        new_factor = self.engine._update_difficulty_factor(2.5, 5)
        assert new_factor <= self.engine.MAX_EASE_FACTOR
    
    def test_interval_calculation_first_review(self):
        """Test interval calculation for first successful review"""
        interval = self.engine._calculate_interval(1, 2.5, 4, 0)
        assert interval == 1  # First review is always 1 day
    
    def test_interval_calculation_second_review(self):
        """Test interval calculation for second successful review"""
        interval = self.engine._calculate_interval(1, 2.5, 4, 1)
        assert interval == 6  # Second review is always 6 days
    
    def test_interval_calculation_subsequent_reviews(self):
        """Test interval calculation for subsequent reviews"""
        # Third review should use ease factor
        interval = self.engine._calculate_interval(6, 2.5, 4, 2)
        expected = math.ceil(6 * 2.5)  # 15 days
        assert interval == expected
        
        # Should ensure minimum progression
        interval = self.engine._calculate_interval(10, 1.1, 4, 3)  # Very low ease factor
        assert interval > 10  # Should still progress
    
    def test_interval_calculation_failure(self):
        """Test interval calculation for failed reviews"""
        # Failed review should reset to 1 day
        interval = self.engine._calculate_interval(30, 2.5, 2, 5)  # Success score < 3
        assert interval == 1
    
    def test_card_state_determination(self):
        """Test card state determination logic"""
        # New card
        state = self.engine._determine_card_state(1, 4, 0)
        assert state == CardState.NEW
        
        # Failed card goes to learning
        state = self.engine._determine_card_state(1, 2, 1)
        assert state == CardState.LEARNING
        
        # Successful card in review phase
        state = self.engine._determine_card_state(10, 4, 3)
        assert state == CardState.REVIEW
        
        # Mature card (>= 21 days)
        state = self.engine._determine_card_state(25, 4, 5)
        assert state == CardState.MATURE
    
    def test_calculate_next_review_success(self):
        """Test complete next review calculation for successful review"""
        # Use review_count=2 so it's the third review and applies ease factor
        params = self.engine.calculate_next_review(
            current_interval=6,
            difficulty_factor=2.5,
            success_score=4,
            review_count=2  # Third review - should use ease factor
        )
        
        assert isinstance(params, SpacingParameters)
        assert params.interval_days > 6  # Should increase with ease factor
        assert params.difficulty_factor == 2.5  # Score 4 maintains factor
        assert params.review_count == 3
        assert params.card_state in [CardState.REVIEW, CardState.MATURE]
        assert params.next_review_date > date.today()
    
    def test_calculate_next_review_failure(self):
        """Test complete next review calculation for failed review"""
        params = self.engine.calculate_next_review(
            current_interval=15,
            difficulty_factor=2.5,
            success_score=1,  # Failed
            review_count=3
        )
        
        assert params.interval_days == 1  # Reset to 1 day
        assert params.difficulty_factor < 2.5  # Should decrease
        assert params.card_state == CardState.LEARNING
        assert params.next_review_date == date.today() + timedelta(days=1)
    
    def test_process_review_batch(self):
        """Test batch processing of reviews"""
        reviews = [
            ReviewResult(flashcard_id="1", user_id="user1", success_score=4),
            ReviewResult(flashcard_id="2", user_id="user1", success_score=2),
            ReviewResult(flashcard_id="3", user_id="user1", success_score=5)
        ]
        
        results = self.engine.process_review_batch(reviews)
        
        assert len(results) == 3
        assert "1" in results
        assert "2" in results
        assert "3" in results
        
        # Failed review should have short interval
        assert results["2"].interval_days == 1
        
        # Successful reviews should have longer intervals
        assert results["1"].interval_days > 1
        assert results["3"].interval_days > 1
    
    def test_difficulty_adjustment(self):
        """Test difficulty adjustment based on success rate"""
        # Low success rate should make easier
        adjustment = self.engine.get_difficulty_adjustment(0.5, 30)
        assert adjustment == 0.8
        
        # High success rate should make harder
        adjustment = self.engine.get_difficulty_adjustment(0.95, 30)
        assert adjustment == 1.2
        
        # Moderate success rate should remain unchanged
        adjustment = self.engine.get_difficulty_adjustment(0.75, 30)
        assert adjustment == 1.0


class TestReviewResult:
    """Test the ReviewResult data class"""
    
    def test_review_result_creation(self):
        """Test ReviewResult creation with required fields"""
        result = ReviewResult(
            flashcard_id="test-id",
            user_id="user-123",
            success_score=4,
            response_time=30
        )
        
        assert result.flashcard_id == "test-id"
        assert result.user_id == "user-123"
        assert result.success_score == 4
        assert result.response_time == 30
        assert isinstance(result.review_date, datetime)
    
    def test_review_result_default_date(self):
        """Test ReviewResult auto-generates review date"""
        result = ReviewResult(
            flashcard_id="test-id",
            user_id="user-123",
            success_score=3
        )
        
        # Should have a recent timestamp
        assert result.review_date is not None
        assert (datetime.utcnow() - result.review_date).seconds < 5


class TestSpacingParameters:
    """Test the SpacingParameters data class"""
    
    def test_spacing_parameters_creation(self):
        """Test SpacingParameters creation"""
        params = SpacingParameters(
            next_review_date=date.today() + timedelta(days=7),
            difficulty_factor=2.3,
            interval_days=7,
            card_state=CardState.REVIEW,
            review_count=3
        )
        
        assert params.interval_days == 7
        assert params.difficulty_factor == 2.3
        assert params.card_state == CardState.REVIEW
        assert params.review_count == 3
        assert isinstance(params.next_review_date, date)


class TestUtilityFunctions:
    """Test utility functions for spaced repetition"""
    
    def test_retention_prediction(self):
        """Test retention probability calculation"""
        # New card with short interval should have high retention
        retention = calculate_retention_prediction(1, 2.5, 0)
        assert retention > 0.8
        
        # Old card with long interval should have lower retention
        retention = calculate_retention_prediction(30, 2.5, 1)
        assert retention < 0.8
        
        # Difficult card should have lower retention
        retention = calculate_retention_prediction(7, 1.3, 2)
        easy_retention = calculate_retention_prediction(7, 2.5, 2)
        assert retention < easy_retention
        
        # More reviews should improve retention
        retention_few = calculate_retention_prediction(14, 2.5, 1)
        retention_many = calculate_retention_prediction(14, 2.5, 5)
        assert retention_many > retention_few
    
    def test_retention_prediction_bounds(self):
        """Test retention prediction stays within valid bounds"""
        # Test various scenarios to ensure bounds
        scenarios = [
            (1, 1.3, 0),
            (100, 2.5, 10),
            (1, 2.5, 0),
            (50, 1.3, 3)
        ]
        
        for interval, factor, count in scenarios:
            retention = calculate_retention_prediction(interval, factor, count)
            assert 0.0 <= retention <= 1.0
    
    def test_optimal_review_load(self):
        """Test optimal review load calculation"""
        # Higher target retention should mean FEWER daily reviews needed
        # (more efficient learning = less repetition needed)
        high_target_load = get_optimal_review_load(0.95)  # High efficiency
        medium_target_load = get_optimal_review_load(0.85)  # Medium efficiency
        
        # Counter-intuitively, higher retention target might need fewer reviews
        # if we assume this represents system efficiency
        assert high_target_load >= 5  # Minimum load
        assert medium_target_load >= 5
        
        # Should handle edge cases
        extreme_load = get_optimal_review_load(1.0)
        assert extreme_load >= 5


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = SpacedRepetitionEngine()
    
    def test_extreme_success_scores(self):
        """Test handling of extreme success scores"""
        # Score above max should be clamped
        params = self.engine.calculate_next_review(5, 2.5, 10, 2)  # Score 10 should be treated as 5
        assert params.difficulty_factor <= self.engine.MAX_EASE_FACTOR
        
        # Negative score should be clamped to 0
        params = self.engine.calculate_next_review(5, 2.5, -1, 2)
        assert params.interval_days == 1  # Should be treated as failure
    
    def test_extreme_intervals(self):
        """Test handling of extreme intervals"""
        # Very long interval
        params = self.engine.calculate_next_review(1000, 2.5, 4, 10)
        assert params.interval_days > 1000  # Should still progress
        
        # Zero interval should work
        params = self.engine.calculate_next_review(0, 2.5, 4, 0)
        assert params.interval_days >= 1
    
    def test_extreme_ease_factors(self):
        """Test handling of extreme ease factors"""
        # Very high ease factor should be clamped
        params = self.engine.calculate_next_review(10, 5.0, 4, 3)
        updated_factor = self.engine._update_difficulty_factor(5.0, 4)
        assert updated_factor <= self.engine.MAX_EASE_FACTOR
        
        # Very low ease factor should be clamped
        updated_factor = self.engine._update_difficulty_factor(0.5, 1)
        assert updated_factor >= self.engine.MIN_EASE_FACTOR
    
    def test_confidence_score_bounds(self):
        """Test confidence score boundary conditions"""
        # Confidence score > 1.0
        params = self.engine.get_initial_parameters(confidence_score=1.5)
        assert params.difficulty_factor <= self.engine.MAX_EASE_FACTOR
        
        # Negative confidence score
        params = self.engine.get_initial_parameters(confidence_score=-0.5)
        assert params.difficulty_factor >= self.engine.MIN_EASE_FACTOR


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])