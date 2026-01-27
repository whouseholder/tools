"""Unit tests for query generator."""

import pytest
from unittest.mock import Mock, MagicMock
from src.query.query_generator import QueryGenerator
from src.llm.llm_manager import LLMManager
from src.utils.config import QueryConfig, LLMConfig, LLMModelConfig


@pytest.fixture
def query_config():
    """Create test query configuration."""
    return QueryConfig(
        dialect="hive",
        syntax_check_enabled=True,
        max_retries_per_model=2
    )


@pytest.fixture
def mock_llm_manager():
    """Create mock LLM manager."""
    manager = Mock(spec=LLMManager)
    manager.generate_with_fallback.return_value = {
        'text': 'SELECT customer_id, name, SUM(revenue) as total_revenue FROM customers GROUP BY customer_id, name ORDER BY total_revenue DESC LIMIT 10',
        'model_used': 'small',
        'attempts': [{'model': 'small', 'attempt': 1, 'success': True}]
    }
    return manager


@pytest.fixture
def query_generator(mock_llm_manager, query_config):
    """Create query generator with mock LLM."""
    return QueryGenerator(mock_llm_manager, query_config)


def test_generate_query(query_generator, sample_question, sample_table_metadata):
    """Test query generation."""
    result = query_generator.generate_query(
        question=sample_question,
        relevant_tables=[sample_table_metadata]
    )
    
    assert result is not None
    assert 'query' in result
    assert 'model_used' in result
    assert result['validation_passed'] is True


def test_extract_sql(query_generator):
    """Test SQL extraction from LLM response."""
    # Test with markdown
    text = "```sql\nSELECT * FROM customers\n```"
    sql = query_generator._extract_sql(text)
    assert sql == "SELECT * FROM customers"
    
    # Test plain SQL
    text = "SELECT * FROM customers"
    sql = query_generator._extract_sql(text)
    assert sql == "SELECT * FROM customers"
    
    # Test with prefix
    text = "SQL Query: SELECT * FROM customers"
    sql = query_generator._extract_sql(text)
    assert sql == "SELECT * FROM customers"


def test_validate_syntax(query_generator):
    """Test SQL syntax validation."""
    # Valid query
    is_valid, errors = query_generator._validate_syntax(
        "SELECT * FROM customers WHERE id = 1"
    )
    assert is_valid is True
    assert errors is None
    
    # Invalid query (unbalanced parentheses)
    is_valid, errors = query_generator._validate_syntax(
        "SELECT * FROM customers WHERE (id = 1"
    )
    assert is_valid is False
    assert len(errors) > 0


def test_build_query_prompt(query_generator, sample_question, sample_table_metadata):
    """Test query prompt building."""
    prompt = query_generator._build_query_prompt(
        question=sample_question,
        relevant_tables=[sample_table_metadata],
        similar_qa=None
    )
    
    assert sample_question in prompt
    assert "customers" in prompt
    assert "customer_id" in prompt
