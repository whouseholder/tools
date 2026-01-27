"""
Cloudera AI Inference Service Model Entry Point

This script serves as the entry point for deploying the Text-to-SQL agent
to Cloudera AI Inference (CAI) - the next-generation AI serving platform.

CAI provides:
- Model versioning
- A/B testing
- Auto-scaling
- Advanced monitoring
- Multi-model serving
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.agent.agent import TextToSQLAgent, ResponseType
from src.agent.feedback import FeedbackType
from src.utils.config import load_config


class TextToSQLInferenceModel:
    """
    Cloudera AI Inference Model wrapper for Text-to-SQL agent.
    
    This class implements the CAI model interface with:
    - Model initialization
    - Inference endpoints
    - Health checks
    - Metadata
    """
    
    def __init__(self):
        """Initialize the model."""
        self.agent: Optional[TextToSQLAgent] = None
        self.config = None
        self.version = "1.0.0"
        self.model_name = "text-to-sql-agent"
    
    def load(self, model_path: str = None):
        """
        Load the model.
        
        This method is called by CAI during model deployment.
        
        Args:
            model_path: Path to model artifacts (optional)
        """
        try:
            logger.info(f"Loading {self.model_name} v{self.version}")
            
            # Load configuration
            self.config = load_config()
            
            # Initialize agent
            self.agent = TextToSQLAgent(self.config)
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def predict(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main inference endpoint.
        
        Args:
            request: Inference request with structure:
                {
                    "inputs": {
                        "question": "What are the top customers?",
                        "session_id": "optional-session-id",
                        "visualization_type": "table",
                        "skip_similar_check": false
                    }
                }
        
        Returns:
            Inference response with structure:
                {
                    "outputs": {
                        "success": true,
                        "response_type": "answer",
                        "data": {...},
                        "metadata": {...}
                    }
                }
        """
        if self.agent is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        
        try:
            # Extract inputs
            inputs = request.get("inputs", {})
            
            question = inputs.get("question")
            session_id = inputs.get("session_id")
            visualization_type = inputs.get("visualization_type")
            skip_similar_check = inputs.get("skip_similar_check", False)
            
            # Validate required inputs
            if not question:
                return {
                    "outputs": {
                        "success": False,
                        "error": "Missing required input: question",
                        "error_type": "validation_error"
                    }
                }
            
            logger.info(f"Processing question: {question[:100]}...")
            
            # Process question
            result = self.agent.process_question(
                question=question,
                session_id=session_id,
                visualization_type=visualization_type,
                skip_similar_check=skip_similar_check
            )
            
            # Add success flag
            result["success"] = result.get("response_type") != ResponseType.ERROR.value
            
            # Wrap in outputs
            return {"outputs": result}
            
        except Exception as e:
            logger.error(f"Inference failed: {e}", exc_info=True)
            return {
                "outputs": {
                    "success": False,
                    "error": str(e),
                    "error_type": "processing_error"
                }
            }
    
    def batch_predict(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch inference endpoint.
        
        Args:
            requests: List of inference requests
        
        Returns:
            List of inference responses
        """
        results = []
        
        for request in requests:
            result = self.predict(request)
            results.append(result)
        
        return results
    
    def feedback(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Feedback endpoint.
        
        Args:
            request: Feedback request with structure:
                {
                    "inputs": {
                        "question": "...",
                        "sql_query": "...",
                        "answer": {...},
                        "feedback_type": "positive",
                        "comment": "optional",
                        "session_id": "optional",
                        "llm_confidence": 0.95
                    }
                }
        
        Returns:
            Feedback response
        """
        if self.agent is None:
            raise RuntimeError("Model not loaded")
        
        try:
            inputs = request.get("inputs", {})
            
            question = inputs.get("question")
            sql_query = inputs.get("sql_query")
            answer = inputs.get("answer")
            feedback_type_str = inputs.get("feedback_type")
            comment = inputs.get("comment")
            session_id = inputs.get("session_id")
            llm_confidence = inputs.get("llm_confidence")
            
            # Validate required inputs
            if not all([question, sql_query, answer, feedback_type_str]):
                return {
                    "outputs": {
                        "success": False,
                        "error": "Missing required inputs"
                    }
                }
            
            # Parse feedback type
            try:
                feedback_type = FeedbackType(feedback_type_str.lower())
            except ValueError:
                return {
                    "outputs": {
                        "success": False,
                        "error": f"Invalid feedback_type: {feedback_type_str}"
                    }
                }
            
            # Submit feedback
            self.agent.add_user_feedback(
                question=question,
                sql_query=sql_query,
                answer=answer,
                feedback_type=feedback_type,
                comment=comment,
                session_id=session_id,
                llm_confidence=llm_confidence
            )
            
            return {
                "outputs": {
                    "success": True,
                    "message": "Feedback submitted successfully"
                }
            }
            
        except Exception as e:
            logger.error(f"Feedback submission failed: {e}")
            return {
                "outputs": {
                    "success": False,
                    "error": str(e)
                }
            }
    
    def health(self) -> Dict[str, Any]:
        """
        Health check endpoint.
        
        Returns:
            Health status
        """
        status = "healthy" if self.agent is not None else "uninitialized"
        
        return {
            "status": status,
            "model_name": self.model_name,
            "version": self.version,
            "agent_initialized": self.agent is not None
        }
    
    def metadata(self) -> Dict[str, Any]:
        """
        Model metadata endpoint.
        
        Returns:
            Model metadata including:
            - Model name and version
            - Input/output schema
            - Supported operations
        """
        return {
            "model_name": self.model_name,
            "version": self.version,
            "description": "Text-to-SQL Agent for natural language query generation",
            "input_schema": {
                "question": {
                    "type": "string",
                    "required": True,
                    "description": "Natural language question"
                },
                "session_id": {
                    "type": "string",
                    "required": False,
                    "description": "Optional session ID for conversation context"
                },
                "visualization_type": {
                    "type": "string",
                    "required": False,
                    "description": "Visualization type (table, bar, line, pie, etc.)"
                },
                "skip_similar_check": {
                    "type": "boolean",
                    "required": False,
                    "description": "Skip similarity check for cached answers"
                }
            },
            "output_schema": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the request was successful"
                },
                "response_type": {
                    "type": "string",
                    "description": "Type of response (answer, similar, error)"
                },
                "data": {
                    "type": "object",
                    "description": "Query results and visualization"
                },
                "metadata": {
                    "type": "object",
                    "description": "Request metadata including SQL query and confidence"
                }
            },
            "operations": [
                "predict",
                "batch_predict",
                "feedback",
                "health",
                "metadata"
            ]
        }


# Global model instance
_model = None


def get_model() -> TextToSQLInferenceModel:
    """
    Get or create the global model instance.
    
    Returns:
        Model instance
    """
    global _model
    
    if _model is None:
        _model = TextToSQLInferenceModel()
        _model.load()
    
    return _model


# CAI entry points
def predict(request: Dict[str, Any]) -> Dict[str, Any]:
    """CAI predict endpoint."""
    model = get_model()
    return model.predict(request)


def batch_predict(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """CAI batch predict endpoint."""
    model = get_model()
    return model.batch_predict(requests)


def feedback(request: Dict[str, Any]) -> Dict[str, Any]:
    """CAI feedback endpoint."""
    model = get_model()
    return model.feedback(request)


def health() -> Dict[str, Any]:
    """CAI health endpoint."""
    model = get_model()
    return model.health()


def metadata() -> Dict[str, Any]:
    """CAI metadata endpoint."""
    model = get_model()
    return model.metadata()


# Test the model locally
if __name__ == "__main__":
    print("Testing CAI Inference Model...")
    
    # Create model
    model = TextToSQLInferenceModel()
    model.load()
    
    # Test health
    print("\n=== Health Check ===")
    health_result = model.health()
    print(json.dumps(health_result, indent=2))
    
    # Test metadata
    print("\n=== Metadata ===")
    metadata_result = model.metadata()
    print(json.dumps(metadata_result, indent=2))
    
    # Test prediction
    print("\n=== Prediction Test ===")
    test_request = {
        "inputs": {
            "question": "What are the top 10 customers by revenue?"
        }
    }
    result = model.predict(test_request)
    print(json.dumps(result, indent=2))
    
    print("\n✓ Model test complete!")
