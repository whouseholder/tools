"""Unit tests for vector store."""

import pytest
from src.vector_store.vector_store import ChromaDBVectorStore
from src.utils.config import VectorStoreConfig


@pytest.fixture
def vector_store_config():
    """Create test vector store configuration."""
    return VectorStoreConfig(
        provider="chromadb",
        embedding_model="all-MiniLM-L6-v2",
        similarity_threshold=0.85,
        chromadb={
            "persist_directory": "./tests/data/test_vector_db",
            "collection_name": "test"
        }
    )


@pytest.fixture
def vector_store(vector_store_config):
    """Create test vector store."""
    return ChromaDBVectorStore(vector_store_config)


def test_add_qa_pair(vector_store):
    """Test adding Q&A pair to vector store."""
    doc_id = vector_store.add_qa_pair(
        question="What is the total revenue?",
        answer="10000",
        sql_query="SELECT SUM(revenue) FROM sales"
    )
    
    assert doc_id is not None
    assert isinstance(doc_id, str)


def test_search_similar_questions(vector_store):
    """Test searching for similar questions."""
    # Add some Q&A pairs
    vector_store.add_qa_pair(
        question="What is the total revenue?",
        answer="10000",
        sql_query="SELECT SUM(revenue) FROM sales"
    )
    
    vector_store.add_qa_pair(
        question="Show me all customers",
        answer="[...]",
        sql_query="SELECT * FROM customers"
    )
    
    # Search for similar question
    results = vector_store.search_similar_questions(
        "What is the total sales revenue?",
        top_k=5
    )
    
    assert len(results) > 0
    assert results[0]['similarity'] > 0.7  # Should be similar


def test_add_metadata(vector_store):
    """Test adding table metadata."""
    doc_id = vector_store.add_metadata(
        table_name="customers",
        columns=[
            {"name": "customer_id", "type": "INT"},
            {"name": "name", "type": "VARCHAR"}
        ],
        description="Customer information"
    )
    
    assert doc_id is not None
    assert isinstance(doc_id, str)


def test_search_relevant_metadata(vector_store):
    """Test searching for relevant metadata."""
    # Add metadata
    vector_store.add_metadata(
        table_name="customers",
        columns=[
            {"name": "customer_id", "type": "INT"},
            {"name": "name", "type": "VARCHAR"},
            {"name": "revenue", "type": "DECIMAL"}
        ],
        description="Customer information with revenue"
    )
    
    # Search
    results = vector_store.search_relevant_metadata(
        "Show me customer revenue",
        top_k=5
    )
    
    assert len(results) > 0
    assert results[0]['table_name'] == "customers"
