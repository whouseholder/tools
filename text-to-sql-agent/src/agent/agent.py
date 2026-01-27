"""Main Text-to-SQL Agent orchestrator."""

import uuid
from typing import Any, Dict, List, Optional
from enum import Enum

from loguru import logger

from ..vector_store.vector_store import VectorStore
from ..llm.llm_manager import LLMManager
from ..metadata.metadata_manager import MetadataManager
from ..query.query_generator import QueryGenerator
from ..query.query_executor import QueryExecutor
from ..visualization.visualization_engine import VisualizationEngine
from .validator import QuestionValidator
from .memory import MemoryManager
from .feedback import FeedbackManager, FeedbackType, FeedbackSource
from ..utils.config import Config


class ResponseType(str, Enum):
    """Type of response."""
    TABLE = "table"
    CHART = "chart"
    ERROR = "error"
    SIMILAR_QUESTION = "similar_question"


class TextToSQLAgent:
    """Main orchestrator for text-to-SQL agent."""
    
    def __init__(self, config: Config):
        """Initialize the agent."""
        self.config = config
        
        # Initialize components
        from ..vector_store import create_vector_store
        
        self.vector_store = create_vector_store(config.vector_store)
        self.llm_manager = LLMManager(config.llm)
        self.metadata_manager = MetadataManager(self.vector_store, config.metadata)
        self.query_generator = QueryGenerator(self.llm_manager, config.query)
        self.query_executor = QueryExecutor(config.metadata, config.query)
        self.visualization_engine = VisualizationEngine(self.llm_manager, config.visualization)
        self.validator = QuestionValidator(self.llm_manager, config.validation)
        self.feedback_manager = FeedbackManager(config.feedback)
        
        # Session-specific memory (will be created per session)
        self._sessions: Dict[str, MemoryManager] = {}
        
        logger.info("Text-to-SQL Agent initialized")
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new conversation session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self._sessions[session_id] = MemoryManager(self.config.memory, session_id)
        logger.info(f"Created session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[MemoryManager]:
        """Get session memory manager."""
        return self._sessions.get(session_id)
    
    def process_question(
        self,
        question: str,
        session_id: Optional[str] = None,
        visualization_type: Optional[str] = None,
        skip_similar_check: bool = False
    ) -> Dict[str, Any]:
        """
        Process a natural language question through the full pipeline.
        
        Args:
            question: Natural language question
            session_id: Session ID for conversation context
            visualization_type: Specific visualization type (table, bar, line, etc.)
            skip_similar_check: Skip checking for similar questions
        
        Returns:
            Dict with processing results and visualization
        """
        # Create session if not provided
        if session_id is None:
            session_id = self.create_session()
        
        # Get or create session memory
        memory = self.get_session(session_id)
        if memory is None:
            memory = MemoryManager(self.config.memory, session_id)
            self._sessions[session_id] = memory
        
        # Add user question to memory
        memory.add_message('user', question)
        
        logger.info(f"Processing question (session: {session_id}): {question[:100]}...")
        
        result = {
            'session_id': session_id,
            'question': question,
            'success': False,
            'response_type': None,
            'data': None,
            'visualization': None,
            'metadata': {}
        }
        
        try:
            # Step 1: Validate question
            logger.info("Step 1: Validating question")
            validation = self.validator.validate(question)
            result['metadata']['validation'] = validation
            
            if not validation['valid']:
                result['response_type'] = ResponseType.ERROR
                result['data'] = {
                    'error': validation['reason'],
                    'type': 'validation_error'
                }
                memory.add_message('assistant', f"Validation failed: {validation['reason']}")
                return result
            
            # Step 2: Check for similar questions
            similar_qa = []
            if self.config.validation.check_similar_questions and not skip_similar_check:
                logger.info("Step 2: Checking for similar questions")
                similar_qa = self.vector_store.search_similar_questions(question)
                result['metadata']['similar_questions'] = len(similar_qa)
                
                # If very similar question found, prompt user
                if similar_qa and self.config.validation.prompt_on_similar:
                    best_match = similar_qa[0]
                    if best_match['similarity'] > self.config.vector_store.similarity_threshold:
                        result['response_type'] = ResponseType.SIMILAR_QUESTION
                        result['data'] = {
                            'similar_question': best_match['question'],
                            'similarity': best_match['similarity'],
                            'answer': best_match['metadata'].get('answer'),
                            'sql_query': best_match['metadata'].get('sql_query'),
                            'message': 'A very similar question was found. Would you like to use this answer or generate a new one?'
                        }
                        return result
            
            # Step 3: Fetch relevant metadata
            logger.info("Step 3: Fetching relevant table metadata")
            relevant_tables = self.metadata_manager.get_relevant_tables(question)
            result['metadata']['relevant_tables'] = [t['table_name'] for t in relevant_tables]
            
            if not relevant_tables:
                result['response_type'] = ResponseType.ERROR
                result['data'] = {
                    'error': 'No relevant tables found for this question',
                    'type': 'metadata_error'
                }
                memory.add_message('assistant', "No relevant tables found")
                return result
            
            # Step 4: Generate SQL query
            logger.info("Step 4: Generating SQL query")
            query_result = self.query_generator.generate_query(
                question=question,
                relevant_tables=relevant_tables,
                similar_qa=similar_qa if similar_qa else None
            )
            
            result['metadata']['query_generation'] = {
                'model_used': query_result['model_used'],
                'attempts': query_result['attempts'],
                'validation_passed': query_result['validation_passed']
            }
            
            sql_query = query_result['query']
            result['metadata']['sql_query'] = sql_query
            
            if not query_result['validation_passed']:
                result['response_type'] = ResponseType.ERROR
                result['data'] = {
                    'error': 'Generated query failed validation',
                    'validation_errors': query_result['validation_errors'],
                    'sql_query': sql_query,
                    'type': 'query_validation_error'
                }
                memory.add_message('assistant', "Query generation failed validation")
                return result
            
            # Step 5: Execute query
            logger.info("Step 5: Executing SQL query")
            execution_result = self.query_executor.execute_query(sql_query)
            
            result['metadata']['execution'] = {
                'success': execution_result['success'],
                'row_count': execution_result['row_count'],
                'execution_time': execution_result['execution_time']
            }
            
            if not execution_result['success']:
                result['response_type'] = ResponseType.ERROR
                result['data'] = {
                    'error': execution_result.get('error', 'Query execution failed'),
                    'sql_query': sql_query,
                    'type': 'execution_error'
                }
                memory.add_message('assistant', f"Query execution failed: {execution_result.get('error')}")
                return result
            
            # Step 6: Create visualization
            logger.info("Step 6: Creating visualization")
            if visualization_type is None:
                visualization_type = self.config.visualization.default_format
            
            if visualization_type == 'table' or not self.config.visualization.auto_suggest_charts:
                visualization = self.visualization_engine.create_table(
                    execution_result['columns'],
                    execution_result['rows']
                )
            else:
                visualization = self.visualization_engine.create_chart(
                    execution_result['columns'],
                    execution_result['rows'],
                    chart_type=visualization_type if visualization_type != 'auto' else None,
                    sql_query=sql_query
                )
            
            result['success'] = True
            result['response_type'] = ResponseType.TABLE if visualization['type'] == 'table' else ResponseType.CHART
            result['data'] = execution_result
            result['visualization'] = visualization
            
            # Add to memory
            memory.add_message(
                'assistant',
                f"Query executed successfully: {execution_result['row_count']} rows returned",
                metadata={'sql_query': sql_query}
            )
            
            # Step 7: Handle feedback (eval mode)
            if self.config.feedback.enabled and self.config.feedback.eval_mode:
                # Calculate confidence score with LLM confidence
                confidence = self._calculate_confidence(
                    validation, 
                    query_result, 
                    execution_result,
                    user_feedback=None  # No user feedback at this point
                )
                result['metadata']['confidence'] = confidence
                
                if self.feedback_manager.should_auto_store(confidence):
                    logger.info("Auto-storing Q&A due to high confidence")
                    self.store_qa_pair(
                        question=question,
                        sql_query=sql_query,
                        answer=execution_result,
                        confidence=confidence,
                        session_id=session_id
                    )
            
            logger.info(f"Question processed successfully: {execution_result['row_count']} rows")
            return result
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            result['response_type'] = ResponseType.ERROR
            result['data'] = {
                'error': str(e),
                'type': 'unexpected_error'
            }
            memory.add_message('assistant', f"Error: {str(e)}")
            return result
    
    def store_qa_pair(
        self,
        question: str,
        sql_query: str,
        answer: Any,
        confidence: float = 1.0,
        session_id: Optional[str] = None
    ):
        """Store Q&A pair in vector store and feedback."""
        try:
            # Store in vector store
            self.vector_store.add_qa_pair(
                question=question,
                answer=str(answer),
                sql_query=sql_query,
                metadata={'confidence': confidence}
            )
            
            # Store in feedback database
            self.feedback_manager.add_feedback(
                question=question,
                sql_query=sql_query,
                answer=answer,
                feedback_type=FeedbackType.POSITIVE,
                feedback_source=FeedbackSource.EVAL_AUTO,
                confidence_score=confidence,
                session_id=session_id
            )
            
            logger.info("Q&A pair stored successfully")
            
        except Exception as e:
            logger.error(f"Failed to store Q&A pair: {e}")
    
    def add_user_feedback(
        self,
        question: str,
        sql_query: str,
        answer: Any,
        feedback_type: FeedbackType,
        comment: Optional[str] = None,
        session_id: Optional[str] = None,
        llm_confidence: Optional[float] = None
    ):
        """
        Add manual user feedback.
        
        Args:
            question: Original question
            sql_query: Generated SQL query
            answer: Query results
            feedback_type: Type of feedback (positive, negative, neutral)
            comment: Optional comment
            session_id: Optional session ID
            llm_confidence: Optional LLM confidence score for recalculation
        """
        try:
            # Calculate confidence with user feedback if in eval mode
            if self.config.feedback.eval_mode and llm_confidence is not None:
                # Recalculate confidence with user feedback
                query_result = {'llm_confidence': llm_confidence}
                validation = {'valid': True}
                execution_result = {'success': True}
                
                confidence = self._calculate_confidence(
                    validation,
                    query_result,
                    execution_result,
                    user_feedback=feedback_type.value
                )
            else:
                confidence = llm_confidence
            
            self.feedback_manager.add_feedback(
                question=question,
                sql_query=sql_query,
                answer=answer,
                feedback_type=feedback_type,
                feedback_source=FeedbackSource.USER_MANUAL,
                user_comment=comment,
                session_id=session_id,
                confidence_score=confidence
            )
            
            # If positive feedback, also store in vector store
            if feedback_type == FeedbackType.POSITIVE:
                self.vector_store.add_qa_pair(
                    question=question,
                    answer=str(answer),
                    sql_query=sql_query,
                    metadata={'user_feedback': 'positive', 'confidence': confidence}
                )
            
            logger.info(f"User feedback added: {feedback_type.value} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to add user feedback: {e}")
    
    def _calculate_confidence(
        self,
        validation: Dict[str, Any],
        query_result: Dict[str, Any],
        execution_result: Dict[str, Any],
        user_feedback: Optional[str] = None
    ) -> float:
        """
        Calculate confidence score for Q&A pair.
        
        Uses LLM-provided confidence score as base.
        In eval mode with user feedback: thumbs_up = (2 + llm_confidence/3)
        
        Args:
            validation: Validation results
            query_result: Query generation results (includes llm_confidence)
            execution_result: Query execution results
            user_feedback: Optional user feedback ('positive', 'negative', 'neutral')
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Get LLM confidence score (default to 0.8 if not provided)
        llm_confidence = query_result.get('llm_confidence', 0.8)
        
        # Check if query failed execution - override to 0
        if not execution_result['success']:
            return 0.0
        
        # In eval mode with user feedback
        if self.config.feedback.eval_mode and user_feedback:
            if user_feedback == 'positive':
                # thumbs up = 2 + llm_confidence/3
                confidence = (2.0 + llm_confidence) / 3.0
                logger.debug(f"Eval mode positive feedback: {confidence:.2f} (from LLM: {llm_confidence:.2f})")
                return max(0.0, min(1.0, confidence))
            elif user_feedback == 'negative':
                # For negative feedback, use a low score
                confidence = llm_confidence * 0.3
                logger.debug(f"Eval mode negative feedback: {confidence:.2f}")
                return max(0.0, min(1.0, confidence))
        
        # Default: use LLM confidence score directly
        logger.debug(f"Using LLM confidence: {llm_confidence:.2f}")
        return max(0.0, min(1.0, llm_confidence))
    
    def initialize_metadata_index(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Initialize or refresh metadata index."""
        logger.info("Initializing metadata index")
        return self.metadata_manager.index_all_tables(force_refresh)
    
    def close(self):
        """Clean up resources."""
        self.query_executor.close()
        self.metadata_manager.close()
        logger.info("Agent closed")
