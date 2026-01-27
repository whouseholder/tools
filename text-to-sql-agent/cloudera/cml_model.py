"""
Cloudera Machine Learning (CML) Model Entry Point

This script serves as the entry point for deploying the Text-to-SQL agent
as a CML Model. It provides prediction endpoints compatible with CML's
model serving infrastructure.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.agent.agent import TextToSQLAgent, ResponseType
from src.agent.feedback import FeedbackType
from src.utils.config import load_config


# Global agent instance
_agent: Optional[TextToSQLAgent] = None


def initialize_model():
    """
    Initialize the Text-to-SQL agent.
    
    This function is called once when the model is loaded.
    CML will call this automatically during model deployment.
    """
    global _agent
    
    try:
        logger.info("Initializing Text-to-SQL Agent for CML Model")
        
        # Load configuration
        config = load_config()
        
        # Initialize agent
        _agent = TextToSQLAgent(config)
        
        logger.info("Agent initialized successfully")
        
        return {"status": "initialized", "message": "Text-to-SQL Agent ready"}
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise


def predict(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main prediction function called by CML Model serving.
    
    Args:
        args: Dictionary containing request parameters
            - question: str - Natural language question (required)
            - session_id: str - Session ID (optional)
            - visualization_type: str - Type of visualization (optional)
            - skip_similar_check: bool - Skip similarity check (optional)
    
    Returns:
        Dictionary containing query results and metadata
    
    Example input:
        {
            "question": "What are the top 10 customers by revenue?",
            "session_id": "user-123",
            "visualization_type": "table"
        }
    
    Example output:
        {
            "success": true,
            "response_type": "answer",
            "data": {...},
            "metadata": {...}
        }
    """
    global _agent
    
    if _agent is None:
        return {
            "success": False,
            "error": "Agent not initialized. Call initialize_model() first.",
            "error_type": "initialization_error"
        }
    
    try:
        # Extract parameters
        question = args.get("question")
        session_id = args.get("session_id")
        visualization_type = args.get("visualization_type")
        skip_similar_check = args.get("skip_similar_check", False)
        
        # Validate required parameters
        if not question:
            return {
                "success": False,
                "error": "Missing required parameter: question",
                "error_type": "validation_error"
            }
        
        logger.info(f"Processing question: {question[:100]}...")
        
        # Process question
        result = _agent.process_question(
            question=question,
            session_id=session_id,
            visualization_type=visualization_type,
            skip_similar_check=skip_similar_check
        )
        
        # Add success flag
        result["success"] = result.get("response_type") != ResponseType.ERROR.value
        
        return result
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": "processing_error"
        }


def batch_predict(args_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batch prediction function for processing multiple questions.
    
    Args:
        args_list: List of dictionaries, each containing request parameters
    
    Returns:
        List of result dictionaries
    
    Example input:
        [
            {"question": "Show total revenue"},
            {"question": "List top customers"}
        ]
    """
    results = []
    
    for args in args_list:
        result = predict(args)
        results.append(result)
    
    return results


def feedback(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit user feedback for a Q&A pair.
    
    Args:
        args: Dictionary containing feedback parameters
            - question: str (required)
            - sql_query: str (required)
            - answer: dict (required)
            - feedback_type: str - 'positive', 'negative', 'neutral' (required)
            - comment: str (optional)
            - session_id: str (optional)
            - llm_confidence: float (optional)
    
    Returns:
        Dictionary with feedback submission status
    """
    global _agent
    
    if _agent is None:
        return {
            "success": False,
            "error": "Agent not initialized"
        }
    
    try:
        # Extract parameters
        question = args.get("question")
        sql_query = args.get("sql_query")
        answer = args.get("answer")
        feedback_type_str = args.get("feedback_type")
        comment = args.get("comment")
        session_id = args.get("session_id")
        llm_confidence = args.get("llm_confidence")
        
        # Validate required parameters
        if not all([question, sql_query, answer, feedback_type_str]):
            return {
                "success": False,
                "error": "Missing required parameters"
            }
        
        # Parse feedback type
        try:
            feedback_type = FeedbackType(feedback_type_str.lower())
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid feedback_type: {feedback_type_str}"
            }
        
        # Submit feedback
        _agent.add_user_feedback(
            question=question,
            sql_query=sql_query,
            answer=answer,
            feedback_type=feedback_type,
            comment=comment,
            session_id=session_id,
            llm_confidence=llm_confidence
        )
        
        return {
            "success": True,
            "message": "Feedback submitted successfully"
        }
        
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def health_check(args: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Dictionary with health status
    """
    global _agent
    
    status = "healthy" if _agent is not None else "uninitialized"
    
    return {
        "status": status,
        "agent_initialized": _agent is not None,
        "version": "1.0.0"
    }


def get_stats(args: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get feedback statistics.
    
    Returns:
        Dictionary with feedback stats
    """
    global _agent
    
    if _agent is None:
        return {
            "success": False,
            "error": "Agent not initialized"
        }
    
    try:
        stats = _agent.feedback_manager.get_feedback_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# CML Model entry point
# When deployed as a CML Model, this will be called automatically
if __name__ == "__main__":
    # Initialize model for testing
    print("Initializing model...")
    init_result = initialize_model()
    print(f"Initialization result: {init_result}")
    
    # Test prediction
    test_args = {
        "question": "Show me the top 5 customers by revenue"
    }
    print(f"\nTesting prediction with: {test_args}")
    result = predict(test_args)
    print(f"Result: {json.dumps(result, indent=2)}")
