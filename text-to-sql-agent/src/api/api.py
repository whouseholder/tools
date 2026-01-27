"""FastAPI REST API for the Text-to-SQL agent."""

from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from loguru import logger

from ..agent.agent import TextToSQLAgent, ResponseType
from ..agent.feedback import FeedbackType
from ..utils.config import get_config


# Pydantic models for API
class QuestionRequest(BaseModel):
    """Request model for question processing."""
    question: str
    session_id: Optional[str] = None
    visualization_type: Optional[str] = None
    skip_similar_check: bool = False


class FeedbackRequest(BaseModel):
    """Request model for user feedback."""
    question: str
    sql_query: str
    answer: dict
    feedback_type: str  # 'positive', 'negative', 'neutral'
    comment: Optional[str] = None
    session_id: Optional[str] = None


class InitializeRequest(BaseModel):
    """Request model for metadata initialization."""
    force_refresh: bool = False


# Create FastAPI app
config = get_config()
app = FastAPI(
    title="Text-to-SQL Agent API",
    description="API for natural language to SQL query conversion",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent: Optional[TextToSQLAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup."""
    global agent
    logger.info("Starting Text-to-SQL Agent API")
    agent = TextToSQLAgent(config)
    logger.info("API ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    global agent
    if agent:
        agent.close()
    logger.info("API shutdown complete")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Text-to-SQL Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/query")
async def process_query(request: QuestionRequest):
    """
    Process a natural language question.
    
    Returns query results and visualization.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = agent.process_question(
            question=request.question,
            session_id=request.session_id,
            visualization_type=request.visualization_type,
            skip_similar_check=request.skip_similar_check
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/similar-confirm")
async def confirm_similar_question(
    session_id: str,
    use_existing: bool,
    question: Optional[str] = None
):
    """
    Confirm whether to use similar question's answer or generate new.
    
    Args:
        session_id: Session ID
        use_existing: If True, use existing answer; if False, generate new
        question: Original question (required if use_existing=False)
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    if use_existing:
        return {"message": "Using existing answer"}
    else:
        if not question:
            raise HTTPException(status_code=400, detail="Question required for new generation")
        
        # Process with skip_similar_check=True to avoid loop
        result = agent.process_question(
            question=question,
            session_id=session_id,
            skip_similar_check=True
        )
        return result


@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback for a Q&A pair.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Parse feedback type
        feedback_type = FeedbackType(request.feedback_type.lower())
        
        agent.add_user_feedback(
            question=request.question,
            sql_query=request.sql_query,
            answer=request.answer,
            feedback_type=feedback_type,
            comment=request.comment,
            session_id=request.session_id
        )
        
        return {"message": "Feedback submitted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid feedback type")
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/initialize-metadata")
async def initialize_metadata(request: InitializeRequest):
    """
    Initialize or refresh metadata index.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = agent.initialize_metadata_index(request.force_refresh)
        return result
        
    except Exception as e:
        logger.error(f"Metadata initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feedback/stats")
async def get_feedback_stats():
    """Get feedback statistics."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        stats = agent.feedback_manager.get_feedback_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session")
async def create_session():
    """Create a new conversation session."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    session_id = agent.create_session()
    return {"session_id": session_id}


# WebSocket for real-time interactions
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    logger.info(f"WebSocket connected: {session_id}")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            question = data.get('question')
            visualization_type = data.get('visualization_type')
            
            if not question:
                await websocket.send_json({
                    'error': 'No question provided'
                })
                continue
            
            # Process question
            result = agent.process_question(
                question=question,
                session_id=session_id,
                visualization_type=visualization_type
            )
            
            # Send result
            await websocket.send_json(result)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                'error': str(e)
            })
        except:
            pass


def start_api(host: Optional[str] = None, port: Optional[int] = None):
    """Start the API server."""
    if host is None:
        host = config.api.host
    if port is None:
        port = config.api.port
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_api()
