"""End-to-end tests for the API."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from src.api.api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_agent():
    """Mock the global agent."""
    with patch('src.api.api.agent') as mock:
        mock.process_question.return_value = {
            'session_id': 'test-session',
            'question': 'Test question',
            'success': True,
            'response_type': 'table',
            'data': {
                'columns': ['col1', 'col2'],
                'rows': [(1, 2), (3, 4)],
                'row_count': 2,
                'execution_time': 0.5,
                'success': True
            },
            'visualization': {
                'type': 'table',
                'html': '<table>...</table>'
            },
            'metadata': {
                'sql_query': 'SELECT * FROM test',
                'relevant_tables': ['test']
            }
        }
        mock.create_session.return_value = 'test-session-id'
        mock.feedback_manager.get_feedback_stats.return_value = {
            'total': 10,
            'by_type': {'positive': 8, 'negative': 2},
            'average_confidence': 0.92
        }
        yield mock


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Text-to-SQL Agent API" in response.json()['message']


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'


def test_process_query(client, mock_agent):
    """Test query processing endpoint."""
    response = client.post(
        "/api/query",
        json={
            "question": "Show me all customers",
            "visualization_type": "table"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'data' in data
    assert 'visualization' in data


def test_process_query_no_question(client, mock_agent):
    """Test query processing without question."""
    response = client.post(
        "/api/query",
        json={}
    )
    
    assert response.status_code == 422  # Validation error


def test_submit_feedback(client, mock_agent):
    """Test feedback submission."""
    response = client.post(
        "/api/feedback",
        json={
            "question": "Test question",
            "sql_query": "SELECT * FROM test",
            "answer": {"result": "test"},
            "feedback_type": "positive",
            "comment": "Great!"
        }
    )
    
    assert response.status_code == 200
    assert "successfully" in response.json()['message']


def test_submit_invalid_feedback(client, mock_agent):
    """Test submitting invalid feedback type."""
    response = client.post(
        "/api/feedback",
        json={
            "question": "Test",
            "sql_query": "SELECT *",
            "answer": {},
            "feedback_type": "invalid_type"
        }
    )
    
    assert response.status_code == 400


def test_create_session(client, mock_agent):
    """Test session creation."""
    response = client.post("/api/session")
    
    assert response.status_code == 200
    assert 'session_id' in response.json()


def test_get_feedback_stats(client, mock_agent):
    """Test getting feedback statistics."""
    response = client.get("/api/feedback/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert 'total' in data
    assert 'by_type' in data


def test_initialize_metadata(client, mock_agent):
    """Test metadata initialization."""
    mock_agent.initialize_metadata_index.return_value = {
        'refreshed': True,
        'total_tables': 10,
        'indexed': 10,
        'failed': 0
    }
    
    response = client.post(
        "/api/initialize-metadata",
        json={"force_refresh": False}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data['refreshed'] is True
