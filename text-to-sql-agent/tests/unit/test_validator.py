"""Unit tests for question validator."""

import pytest
from unittest.mock import Mock
from src.agent.validator import QuestionValidator
from src.llm.llm_manager import LLMManager
from src.utils.config import ValidationConfig


@pytest.fixture
def validation_config():
    """Create test validation configuration."""
    return ValidationConfig(
        min_question_length=5,
        max_question_length=500,
        check_relevance=True,
        check_answerability=True
    )


@pytest.fixture
def mock_llm_manager():
    """Create mock LLM manager."""
    manager = Mock(spec=LLMManager)
    manager.generate.return_value = '{"relevant": true, "reason": "Data query", "confidence": 0.95}'
    return manager


@pytest.fixture
def validator(mock_llm_manager, validation_config):
    """Create validator with mock LLM."""
    return QuestionValidator(mock_llm_manager, validation_config)


def test_validate_valid_question(validator):
    """Test validation of a valid question."""
    result = validator.validate("What is the total revenue from sales?")
    
    assert result['valid'] is True
    assert result['reason'] is None


def test_validate_short_question(validator):
    """Test validation of too short question."""
    result = validator.validate("Hi")
    
    assert result['valid'] is False
    assert 'too short' in result['reason'].lower()


def test_validate_long_question(validator):
    """Test validation of too long question."""
    long_question = "a" * 501
    result = validator.validate(long_question)
    
    assert result['valid'] is False
    assert 'too long' in result['reason'].lower()


def test_check_length(validator):
    """Test length checking."""
    is_valid, reason = validator._check_length("Valid question here")
    assert is_valid is True
    assert reason is None
    
    is_valid, reason = validator._check_length("Hi")
    assert is_valid is False
    assert reason is not None
