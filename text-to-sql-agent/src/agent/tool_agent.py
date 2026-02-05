"""
Tool-based Text-to-SQL Agent.

This agent uses explicit tool definitions for each step in the workflow,
making it truly agentic and transparent.
"""

import uuid
from typing import Any, Dict, List, Optional
from loguru import logger

from .tools import (
    ALL_TOOLS,
    get_tool_by_name,
    get_tools_by_category,
    ToolCategory
)
from ..utils.config import Config
from ..vector_store.vector_store import VectorStore
from ..llm.llm_manager import LLMManager
from ..metadata.metadata_manager import MetadataManager
from ..query.query_generator import QueryGenerator
from ..query.query_executor import QueryExecutor
from ..visualization.visualization_engine import VisualizationEngine
from .validator import QuestionValidator
from .memory import MemoryManager
from .feedback import FeedbackManager, FeedbackType


class ToolBasedAgent:
    """
    Tool-based Text-to-SQL Agent with explicit tool definitions.
    
    Each function is defined as a tool with clear:
    - Purpose and description
    - Input/output schemas
    - Usage examples
    """
    
    def __init__(self, config: Config):
        """Initialize agent with tool bindings."""
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
        
        self._sessions: Dict[str, MemoryManager] = {}
        
        # Bind tools to actual functions
        self._bind_tools()
        
        logger.info("Tool-based agent initialized with {} tools", len(ALL_TOOLS))
    
    def _bind_tools(self):
        """Bind tool definitions to actual implementation functions."""
        # Validation tools
        validate_tool = get_tool_by_name("validate_question")
        if validate_tool:
            validate_tool.function = self._tool_validate_question
        
        similar_tool = get_tool_by_name("check_similar_questions")
        if similar_tool:
            similar_tool.function = self._tool_check_similar_questions
        
        # Metadata tools
        relevant_tables_tool = get_tool_by_name("get_relevant_tables")
        if relevant_tables_tool:
            relevant_tables_tool.function = self._tool_get_relevant_tables
        
        table_desc_tool = get_tool_by_name("get_table_descriptions")
        if table_desc_tool:
            table_desc_tool.function = self._tool_get_table_descriptions
        
        # Query generation tools
        generate_tool = get_tool_by_name("generate_sql_query")
        if generate_tool:
            generate_tool.function = self._tool_generate_sql_query
        
        validate_sql_tool = get_tool_by_name("validate_sql_syntax")
        if validate_sql_tool:
            validate_sql_tool.function = self._tool_validate_sql_syntax
        
        # Query execution tools
        execute_tool = get_tool_by_name("execute_sql_query")
        if execute_tool:
            execute_tool.function = self._tool_execute_sql_query
        
        # Visualization tools
        viz_tool = get_tool_by_name("create_visualization")
        if viz_tool:
            viz_tool.function = self._tool_create_visualization
        
        # Feedback tools
        feedback_tool = get_tool_by_name("submit_feedback")
        if feedback_tool:
            feedback_tool.function = self._tool_submit_feedback
        
        # Memory tools
        memory_tool = get_tool_by_name("add_to_memory")
        if memory_tool:
            memory_tool.function = self._tool_add_to_memory
    
    # ========================================================================
    # Tool Implementations
    # ========================================================================
    
    def _tool_validate_question(self, question: str) -> Dict[str, Any]:
        """
        Tool: Validate if question is answerable.
        
        Input: {"question": "..."}
        Output: {"valid": bool, "reason": str, "confidence": float}
        """
        logger.info(f"[TOOL] validate_question: {question[:50]}...")
        result = self.validator.validate_question(question)
        logger.info(f"[TOOL] Result: valid={result['valid']}, confidence={result.get('confidence', 0):.2f}")
        return result
    
    def _tool_check_similar_questions(
        self,
        question: str,
        threshold: float = 0.85
    ) -> Dict[str, Any]:
        """
        Tool: Check for similar previously answered questions.
        
        Input: {"question": "...", "threshold": 0.85}
        Output: {"found": bool, "similar_questions": [...]}
        """
        logger.info(f"[TOOL] check_similar_questions: {question[:50]}...")
        
        similar = self.vector_store.search_similar_questions(
            question=question,
            top_k=3,
            threshold=threshold
        )
        
        found = len(similar) > 0
        logger.info(f"[TOOL] Result: found={found}, count={len(similar)}")
        
        return {
            "found": found,
            "similar_questions": similar
        }
    
    def _tool_get_relevant_tables(
        self,
        question: str,
        max_tables: int = 5
    ) -> Dict[str, Any]:
        """
        Tool: Get relevant tables for the question.
        
        Input: {"question": "...", "max_tables": 5}
        Output: {"tables": [...]}
        """
        logger.info(f"[TOOL] get_relevant_tables: {question[:50]}...")
        
        tables = self.metadata_manager.find_relevant_tables(
            query=question,
            top_k=max_tables
        )
        
        logger.info(f"[TOOL] Result: {len(tables)} tables found")
        
        return {"tables": tables}
    
    def _tool_get_table_descriptions(
        self,
        table_names: List[str]
    ) -> Dict[str, Any]:
        """
        Tool: Get detailed table descriptions.
        
        Input: {"table_names": ["table1", "table2"]}
        Output: {"tables": {...}}
        """
        logger.info(f"[TOOL] get_table_descriptions: {table_names}")
        
        tables = {}
        for table_name in table_names:
            metadata = self.metadata_manager.fetch_table_metadata(table_name)
            if metadata:
                tables[table_name] = metadata
        
        logger.info(f"[TOOL] Result: {len(tables)} tables retrieved")
        
        return {"tables": tables}
    
    def _tool_generate_sql_query(
        self,
        question: str,
        relevant_tables: List[Dict[str, Any]],
        similar_qa: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Tool: Generate SQL query from question.
        
        Input: {"question": "...", "relevant_tables": [...], "similar_qa": [...]}
        Output: {"query": str, "llm_confidence": float, "model_used": str, ...}
        """
        logger.info(f"[TOOL] generate_sql_query: {question[:50]}...")
        
        result = self.query_generator.generate_query(
            question=question,
            relevant_tables=relevant_tables,
            similar_qa=similar_qa
        )
        
        logger.info(f"[TOOL] Result: model={result['model_used']}, confidence={result.get('llm_confidence', 0):.2f}")
        
        return result
    
    def _tool_validate_sql_syntax(self, query: str) -> Dict[str, Any]:
        """
        Tool: Validate SQL syntax.
        
        Input: {"query": "SELECT ..."}
        Output: {"valid": bool, "errors": [...]}
        """
        logger.info(f"[TOOL] validate_sql_syntax: {query[:50]}...")
        
        is_valid, errors = self.query_generator._validate_syntax(query)
        
        logger.info(f"[TOOL] Result: valid={is_valid}")
        
        return {
            "valid": is_valid,
            "errors": errors if not is_valid else []
        }
    
    def _tool_execute_sql_query(
        self,
        query: str,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Tool: Execute SQL query.
        
        Input: {"query": "SELECT ...", "limit": 1000}
        Output: {"success": bool, "data": [...], "columns": [...], ...}
        """
        logger.info(f"[TOOL] execute_sql_query: {query[:50]}...")
        
        result = self.query_executor.execute_query(query, limit=limit)
        
        logger.info(f"[TOOL] Result: success={result['success']}, rows={result.get('row_count', 0)}")
        
        return result
    
    def _tool_create_visualization(
        self,
        data: List[List[Any]],
        columns: List[str],
        visualization_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool: Create visualization from data.
        
        Input: {"data": [[...]], "columns": [...], "visualization_type": "bar"}
        Output: {"type": str, "html": str, "json": {...}}
        """
        logger.info(f"[TOOL] create_visualization: {len(data)} rows, type={visualization_type}")
        
        result = self.visualization_engine.create_visualization(
            data=data,
            columns=columns,
            visualization_type=visualization_type
        )
        
        logger.info(f"[TOOL] Result: type={result.get('type')}")
        
        return result
    
    def _tool_submit_feedback(
        self,
        question: str,
        sql_query: str,
        answer: Any,
        feedback_type: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool: Submit user feedback.
        
        Input: {"question": "...", "sql_query": "...", "feedback_type": "positive", ...}
        Output: {"success": bool, "message": str}
        """
        logger.info(f"[TOOL] submit_feedback: type={feedback_type}")
        
        try:
            feedback_enum = FeedbackType(feedback_type.lower())
            
            self.feedback_manager.add_feedback(
                question=question,
                sql_query=sql_query,
                answer=answer,
                feedback_type=feedback_enum,
                user_comment=comment
            )
            
            return {"success": True, "message": "Feedback recorded"}
            
        except Exception as e:
            logger.error(f"[TOOL] Error: {e}")
            return {"success": False, "message": str(e)}
    
    def _tool_add_to_memory(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Tool: Add message to conversation memory.
        
        Input: {"session_id": "...", "role": "user", "content": "..."}
        Output: {"success": bool}
        """
        logger.info(f"[TOOL] add_to_memory: session={session_id}, role={role}")
        
        memory = self._sessions.get(session_id)
        if memory:
            memory.add_message(role, content)
            return {"success": True}
        
        return {"success": False}
    
    # ========================================================================
    # Public API
    # ========================================================================
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools."""
        return [tool.to_dict() for tool in ALL_TOOLS]
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get tools in a specific category."""
        try:
            cat_enum = ToolCategory(category)
            tools = get_tools_by_category(cat_enum)
            return [tool.to_dict() for tool in tools]
        except ValueError:
            return []
    
    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
        
        Returns:
            Tool execution result
        """
        tool = get_tool_by_name(tool_name)
        
        if not tool:
            return {"error": f"Tool not found: {tool_name}"}
        
        if not tool.function:
            return {"error": f"Tool not bound: {tool_name}"}
        
        try:
            result = tool.function(**parameters)
            return result
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"error": str(e)}
    
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
