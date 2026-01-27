"""Configuration for pytest."""

import pytest
import os
from pathlib import Path

# Set test environment
os.environ['CONFIG_PATH'] = 'tests/data/test_config.yaml'


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration."""
    from src.utils.config import load_config
    return load_config('tests/data/test_config.yaml')


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return "SELECT * FROM customers LIMIT 10"


@pytest.fixture
def sample_question():
    """Sample question for testing."""
    return "Show me the top 10 customers by revenue"


@pytest.fixture
def sample_table_metadata():
    """Sample table metadata for testing."""
    return {
        'table_name': 'customers',
        'description': 'Customer information table',
        'columns': [
            {'name': 'customer_id', 'type': 'INT', 'description': 'Unique customer ID'},
            {'name': 'name', 'type': 'VARCHAR', 'description': 'Customer name'},
            {'name': 'revenue', 'type': 'DECIMAL', 'description': 'Total revenue from customer'}
        ]
    }


@pytest.fixture
def sample_query_result():
    """Sample query execution result."""
    return {
        'columns': ['customer_id', 'name', 'revenue'],
        'rows': [
            (1, 'Customer A', 10000),
            (2, 'Customer B', 8000),
            (3, 'Customer C', 6000)
        ],
        'row_count': 3,
        'execution_time': 0.5,
        'success': True
    }
