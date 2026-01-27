"""Feedback system for capturing user feedback and eval mode."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

from loguru import logger

from ..utils.config import FeedbackConfig


class FeedbackType(str, Enum):
    """Types of feedback."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class FeedbackSource(str, Enum):
    """Source of feedback."""
    USER_MANUAL = "user_manual"
    EVAL_AUTO = "eval_auto"


class FeedbackManager:
    """Manages feedback collection and storage."""
    
    def __init__(self, config: FeedbackConfig):
        """Initialize feedback manager."""
        self.config = config
        self._init_database()
        logger.info(f"Feedback manager initialized (eval_mode: {config.eval_mode})")
    
    def _init_database(self):
        """Initialize SQLite database for feedback storage."""
        db_path = Path(self.config.storage_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                sql_query TEXT NOT NULL,
                answer TEXT,
                feedback_type TEXT NOT NULL,
                feedback_source TEXT NOT NULL,
                confidence_score REAL,
                user_comment TEXT,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_type 
            ON feedback(feedback_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON feedback(created_at)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Feedback database initialized at {db_path}")
    
    def add_feedback(
        self,
        question: str,
        sql_query: str,
        answer: Any,
        feedback_type: FeedbackType,
        feedback_source: FeedbackSource,
        confidence_score: Optional[float] = None,
        user_comment: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add feedback entry to database.
        
        Returns feedback ID.
        """
        import json
        
        conn = sqlite3.connect(self.config.storage_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback (
                question, sql_query, answer, feedback_type, feedback_source,
                confidence_score, user_comment, session_id, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question,
            sql_query,
            json.dumps(answer) if not isinstance(answer, str) else answer,
            feedback_type.value,
            feedback_source.value,
            confidence_score,
            user_comment,
            session_id,
            json.dumps(metadata) if metadata else None
        ))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added {feedback_type.value} feedback (ID: {feedback_id})")
        return feedback_id
    
    def should_auto_store(self, confidence_score: float) -> bool:
        """Check if Q&A should be automatically stored based on confidence."""
        if not self.config.eval_mode:
            return False
        
        return confidence_score >= self.config.auto_store_threshold
    
    def get_positive_feedback(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get positive feedback entries for training/improvement."""
        import json
        
        conn = sqlite3.connect(self.config.storage_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, question, sql_query, answer, confidence_score, 
                   user_comment, session_id, created_at, metadata
            FROM feedback
            WHERE feedback_type = ?
            ORDER BY created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor.execute(query, (FeedbackType.POSITIVE.value,))
        rows = cursor.fetchall()
        
        feedback_list = []
        for row in rows:
            feedback_list.append({
                'id': row[0],
                'question': row[1],
                'sql_query': row[2],
                'answer': json.loads(row[3]) if row[3] and row[3].startswith('{') else row[3],
                'confidence_score': row[4],
                'user_comment': row[5],
                'session_id': row[6],
                'created_at': row[7],
                'metadata': json.loads(row[8]) if row[8] else None
            })
        
        conn.close()
        logger.debug(f"Retrieved {len(feedback_list)} positive feedback entries")
        return feedback_list
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        conn = sqlite3.connect(self.config.storage_path)
        cursor = conn.cursor()
        
        # Total counts by type
        cursor.execute("""
            SELECT feedback_type, COUNT(*) 
            FROM feedback 
            GROUP BY feedback_type
        """)
        
        type_counts = dict(cursor.fetchall())
        
        # Total count
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total = cursor.fetchone()[0]
        
        # Average confidence for positive feedback
        cursor.execute("""
            SELECT AVG(confidence_score) 
            FROM feedback 
            WHERE feedback_type = ? AND confidence_score IS NOT NULL
        """, (FeedbackType.POSITIVE.value,))
        
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        stats = {
            'total': total,
            'by_type': type_counts,
            'average_confidence': avg_confidence
        }
        
        logger.debug(f"Feedback stats: {stats}")
        return stats
