"""Unit tests for feedback manager."""

import pytest
from pathlib import Path
from src.agent.feedback import FeedbackManager, FeedbackType, FeedbackSource
from src.utils.config import FeedbackConfig


@pytest.fixture
def feedback_config():
    """Create test feedback configuration."""
    return FeedbackConfig(
        enabled=True,
        storage_path="./tests/data/test_feedback.db",
        eval_mode=True,
        auto_store_threshold=0.9
    )


@pytest.fixture
def feedback_manager(feedback_config):
    """Create feedback manager."""
    # Clean up any existing test database
    db_path = Path(feedback_config.storage_path)
    if db_path.exists():
        db_path.unlink()
    
    return FeedbackManager(feedback_config)


def test_add_feedback(feedback_manager):
    """Test adding feedback."""
    feedback_id = feedback_manager.add_feedback(
        question="What is the total revenue?",
        sql_query="SELECT SUM(revenue) FROM sales",
        answer={"result": 10000},
        feedback_type=FeedbackType.POSITIVE,
        feedback_source=FeedbackSource.USER_MANUAL,
        confidence_score=0.95
    )
    
    assert feedback_id is not None
    assert feedback_id > 0


def test_should_auto_store(feedback_manager):
    """Test auto-store decision logic."""
    # High confidence - should store
    assert feedback_manager.should_auto_store(0.95) is True
    
    # Low confidence - should not store
    assert feedback_manager.should_auto_store(0.85) is False
    
    # Disable eval mode
    feedback_manager.config.eval_mode = False
    assert feedback_manager.should_auto_store(0.95) is False


def test_get_positive_feedback(feedback_manager):
    """Test retrieving positive feedback."""
    # Add some feedback
    feedback_manager.add_feedback(
        question="Question 1",
        sql_query="SELECT * FROM t1",
        answer="Answer 1",
        feedback_type=FeedbackType.POSITIVE,
        feedback_source=FeedbackSource.USER_MANUAL
    )
    
    feedback_manager.add_feedback(
        question="Question 2",
        sql_query="SELECT * FROM t2",
        answer="Answer 2",
        feedback_type=FeedbackType.NEGATIVE,
        feedback_source=FeedbackSource.USER_MANUAL
    )
    
    # Get positive feedback
    positive = feedback_manager.get_positive_feedback()
    
    assert len(positive) == 1
    assert positive[0]['question'] == "Question 1"


def test_get_feedback_stats(feedback_manager):
    """Test getting feedback statistics."""
    # Add various feedback
    feedback_manager.add_feedback(
        question="Q1", sql_query="S1", answer="A1",
        feedback_type=FeedbackType.POSITIVE,
        feedback_source=FeedbackSource.USER_MANUAL,
        confidence_score=0.95
    )
    
    feedback_manager.add_feedback(
        question="Q2", sql_query="S2", answer="A2",
        feedback_type=FeedbackType.NEGATIVE,
        feedback_source=FeedbackSource.USER_MANUAL
    )
    
    stats = feedback_manager.get_feedback_stats()
    
    assert stats['total'] == 2
    assert stats['by_type']['positive'] == 1
    assert stats['by_type']['negative'] == 1
    assert stats['average_confidence'] == 0.95
