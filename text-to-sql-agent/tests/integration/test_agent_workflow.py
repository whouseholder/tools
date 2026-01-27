"""Integration tests for the complete agent workflow."""

import pytest
from unittest.mock import Mock, patch
from src.agent.agent import TextToSQLAgent, ResponseType
from src.utils.config import load_config


@pytest.fixture
def test_config():
    """Load test configuration."""
    return load_config('tests/data/test_config.yaml')


@pytest.fixture
def mock_agent_components():
    """Mock external dependencies."""
    with patch('src.agent.agent.create_vector_store') as mock_vs, \
         patch('src.llm.llm_manager.OpenAI') as mock_openai, \
         patch('src.metadata.metadata_manager.hive') as mock_hive, \
         patch('src.query.query_executor.hive') as mock_hive_exec:
        
        # Setup mock vector store
        mock_vs.return_value = Mock()
        mock_vs.return_value.search_similar_questions.return_value = []
        mock_vs.return_value.search_relevant_metadata.return_value = [
            {
                'table_name': 'customers',
                'description': 'Customer data',
                'columns': [
                    {'name': 'customer_id', 'type': 'INT', 'description': 'ID'},
                    {'name': 'name', 'type': 'VARCHAR', 'description': 'Name'},
                    {'name': 'revenue', 'type': 'DECIMAL', 'description': 'Revenue'}
                ],
                'relevance': 0.9
            }
        ]
        
        yield


def test_create_session(test_config, mock_agent_components):
    """Test session creation."""
    agent = TextToSQLAgent(test_config)
    
    session_id = agent.create_session()
    
    assert session_id is not None
    assert session_id in agent._sessions


def test_process_question_validation_error(test_config, mock_agent_components):
    """Test processing with validation error."""
    agent = TextToSQLAgent(test_config)
    
    # Too short question
    result = agent.process_question("Hi")
    
    assert result['success'] is False
    assert result['response_type'] == ResponseType.ERROR
    assert 'validation' in result['metadata']


def test_store_qa_pair(test_config, mock_agent_components):
    """Test storing Q&A pair."""
    agent = TextToSQLAgent(test_config)
    
    # Should not raise exception
    agent.store_qa_pair(
        question="Test question",
        sql_query="SELECT * FROM test",
        answer={"result": "test"},
        confidence=0.95
    )


def test_add_user_feedback(test_config, mock_agent_components):
    """Test adding user feedback."""
    from src.agent.feedback import FeedbackType
    
    agent = TextToSQLAgent(test_config)
    
    # Should not raise exception
    agent.add_user_feedback(
        question="Test question",
        sql_query="SELECT * FROM test",
        answer={"result": "test"},
        feedback_type=FeedbackType.POSITIVE,
        comment="Great result!"
    )


def test_calculate_confidence(test_config, mock_agent_components):
    """Test confidence calculation."""
    agent = TextToSQLAgent(test_config)
    
    validation = {'valid': True}
    query_result = {
        'model_used': 'small',
        'attempts': [{'model': 'small', 'attempt': 1}]
    }
    execution_result = {
        'success': True,
        'row_count': 10
    }
    
    confidence = agent._calculate_confidence(
        validation, query_result, execution_result
    )
    
    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.9  # Should be high for successful query
    
    # Test with large model (lower confidence)
    query_result['model_used'] = 'large'
    confidence_large = agent._calculate_confidence(
        validation, query_result, execution_result
    )
    
    assert confidence_large < confidence


def test_session_memory_persistence(test_config, mock_agent_components):
    """Test that session memory persists across questions."""
    agent = TextToSQLAgent(test_config)
    
    session_id = agent.create_session()
    memory = agent.get_session(session_id)
    
    # Add some messages
    memory.add_message('user', 'Question 1')
    memory.add_message('assistant', 'Answer 1')
    
    # Retrieve session again
    memory2 = agent.get_session(session_id)
    
    assert len(memory2.messages) == 2
    assert memory2.messages[0].content == 'Question 1'
