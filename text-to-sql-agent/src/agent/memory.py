"""Memory manager for conversation context."""

from typing import Any, Dict, List, Optional
from collections import deque
import json
from pathlib import Path

from loguru import logger

from ..utils.config import MemoryConfig


class ConversationMessage:
    """Represents a conversation message."""
    
    def __init__(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'role': self.role,
            'content': self.content,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create from dictionary."""
        return cls(
            role=data['role'],
            content=data['content'],
            metadata=data.get('metadata', {})
        )


class MemoryManager:
    """Manages conversation memory and context."""
    
    def __init__(self, config: MemoryConfig, session_id: str):
        """Initialize memory manager."""
        self.config = config
        self.session_id = session_id
        self.messages: deque = deque(maxlen=config.max_context_messages)
        self._cache_dir = Path(config.cache_path) / session_id
        
        if config.cache_enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Memory manager initialized for session: {session_id}")
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a message to conversation history."""
        message = ConversationMessage(role, content, metadata)
        self.messages.append(message)
        
        # Save to cache if enabled
        if self.config.cache_enabled:
            self._save_to_cache()
        
        logger.debug(f"Added {role} message to memory ({len(self.messages)} total)")
    
    def get_context(
        self,
        max_tokens: Optional[int] = None,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get conversation context within token limit.
        
        Returns list of message dicts in chronological order.
        """
        if max_tokens is None:
            max_tokens = self.config.max_context_tokens
        
        # Simple token estimation (4 chars ≈ 1 token)
        context = []
        total_tokens = 0
        
        # Iterate from most recent to oldest
        for message in reversed(self.messages):
            msg_dict = message.to_dict() if include_metadata else {
                'role': message.role,
                'content': message.content
            }
            
            # Estimate tokens
            msg_tokens = len(json.dumps(msg_dict)) // 4
            
            if total_tokens + msg_tokens > max_tokens:
                break
            
            context.insert(0, msg_dict)  # Insert at beginning to maintain order
            total_tokens += msg_tokens
        
        logger.debug(f"Retrieved context: {len(context)} messages, ~{total_tokens} tokens")
        return context
    
    def clear(self):
        """Clear conversation history."""
        self.messages.clear()
        
        if self.config.cache_enabled:
            cache_file = self._cache_dir / "messages.json"
            if cache_file.exists():
                cache_file.unlink()
        
        logger.info("Memory cleared")
    
    def _save_to_cache(self):
        """Save messages to cache file."""
        cache_file = self._cache_dir / "messages.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(
                    [msg.to_dict() for msg in self.messages],
                    f,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save messages to cache: {e}")
    
    def load_from_cache(self) -> bool:
        """Load messages from cache file."""
        cache_file = self._cache_dir / "messages.json"
        
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'r') as f:
                messages_data = json.load(f)
            
            self.messages.clear()
            for msg_data in messages_data:
                message = ConversationMessage.from_dict(msg_data)
                self.messages.append(message)
            
            logger.info(f"Loaded {len(self.messages)} messages from cache")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load messages from cache: {e}")
            return False
