"""Unit tests for memory manager."""

import pytest
from src.agent.memory import MemoryManager, ConversationMessage
from src.utils.config import MemoryConfig


@pytest.fixture
def memory_config():
    """Create test memory configuration."""
    return MemoryConfig(
        max_context_messages=5,
        max_context_tokens=1000,
        cache_enabled=False
    )


@pytest.fixture
def memory_manager(memory_config):
    """Create memory manager."""
    return MemoryManager(memory_config, "test-session")


def test_add_message(memory_manager):
    """Test adding messages."""
    memory_manager.add_message("user", "Hello")
    memory_manager.add_message("assistant", "Hi there!")
    
    assert len(memory_manager.messages) == 2


def test_message_limit(memory_manager):
    """Test message limit enforcement."""
    # Add more than max messages
    for i in range(10):
        memory_manager.add_message("user", f"Message {i}")
    
    # Should only keep last 5 (max_context_messages)
    assert len(memory_manager.messages) == 5
    assert memory_manager.messages[-1].content == "Message 9"


def test_get_context(memory_manager):
    """Test getting conversation context."""
    memory_manager.add_message("user", "Question 1")
    memory_manager.add_message("assistant", "Answer 1")
    memory_manager.add_message("user", "Question 2")
    memory_manager.add_message("assistant", "Answer 2")
    
    context = memory_manager.get_context()
    
    assert len(context) == 4
    assert context[0]['role'] == 'user'
    assert context[0]['content'] == "Question 1"


def test_get_context_with_token_limit(memory_manager):
    """Test context with token limit."""
    # Add messages
    for i in range(5):
        memory_manager.add_message("user", f"Question {i}" * 100)  # Long messages
    
    # Get context with small token limit
    context = memory_manager.get_context(max_tokens=200)
    
    # Should return fewer messages due to token limit
    assert len(context) < 5


def test_clear(memory_manager):
    """Test clearing memory."""
    memory_manager.add_message("user", "Hello")
    memory_manager.add_message("assistant", "Hi!")
    
    memory_manager.clear()
    
    assert len(memory_manager.messages) == 0


def test_conversation_message():
    """Test ConversationMessage class."""
    msg = ConversationMessage(
        role="user",
        content="Test message",
        metadata={"key": "value"}
    )
    
    assert msg.role == "user"
    assert msg.content == "Test message"
    assert msg.metadata['key'] == "value"
    
    # Test serialization
    msg_dict = msg.to_dict()
    assert msg_dict['role'] == "user"
    
    # Test deserialization
    msg2 = ConversationMessage.from_dict(msg_dict)
    assert msg2.role == msg.role
    assert msg2.content == msg.content
