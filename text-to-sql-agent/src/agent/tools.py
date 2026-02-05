"""
Tool definitions for the Text-to-SQL Agent.

Each function in the agent workflow is defined as a tool with clear:
- Description
- Input parameters
- Output format
- Usage context
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ToolCategory(str, Enum):
    """Categories of tools available."""
    VALIDATION = "validation"
    METADATA = "metadata"
    QUERY_GENERATION = "query_generation"
    QUERY_EXECUTION = "query_execution"
    VISUALIZATION = "visualization"
    FEEDBACK = "feedback"
    MEMORY = "memory"


@dataclass
class Tool:
    """Definition of a tool available to the agent."""
    name: str
    description: str
    category: ToolCategory
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    function: Callable
    examples: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "examples": self.examples
        }


# ============================================================================
# VALIDATION TOOLS
# ============================================================================

VALIDATE_QUESTION_TOOL = Tool(
    name="validate_question",
    description="""
    Validates if a question is relevant and answerable for text-to-SQL.
    
    This tool checks:
    - Is the question data-related?
    - Can it be answered with SQL?
    - Is it clear and specific enough?
    
    Use this as the FIRST step before any query generation.
    """,
    category=ToolCategory.VALIDATION,
    input_schema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Natural language question from user"
            }
        },
        "required": ["question"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "reason": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        }
    },
    function=None,  # Will be set at runtime
    examples=[
        {
            "input": {"question": "What are the top 10 customers by revenue?"},
            "output": {"valid": True, "reason": "Clear data question", "confidence": 0.95}
        },
        {
            "input": {"question": "What is the meaning of life?"},
            "output": {"valid": False, "reason": "Not a data question", "confidence": 0.98}
        }
    ]
)


CHECK_SIMILAR_QUESTIONS_TOOL = Tool(
    name="check_similar_questions",
    description="""
    Searches for previously answered similar questions in vector store.
    
    This tool:
    - Finds semantically similar questions
    - Returns cached answers if found
    - Reduces latency and LLM costs
    
    Use this AFTER validation to check for cached answers.
    """,
    category=ToolCategory.VALIDATION,
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "threshold": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.85}
        },
        "required": ["question"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "found": {"type": "boolean"},
            "similar_questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {"type": "string"},
                        "sql_query": {"type": "string"},
                        "similarity": {"type": "number"}
                    }
                }
            }
        }
    },
    function=None,
    examples=[
        {
            "input": {"question": "Show top customers", "threshold": 0.85},
            "output": {
                "found": True,
                "similar_questions": [{
                    "question": "What are the top customers?",
                    "sql_query": "SELECT * FROM customers ORDER BY revenue DESC LIMIT 10",
                    "similarity": 0.92
                }]
            }
        }
    ]
)


# ============================================================================
# METADATA TOOLS
# ============================================================================

GET_RELEVANT_TABLES_TOOL = Tool(
    name="get_relevant_tables",
    description="""
    Identifies and retrieves metadata for tables relevant to the question.
    
    This tool:
    - Uses semantic search to find relevant tables
    - Returns table schemas, column descriptions, and relationships
    - Essential for accurate query generation
    
    Use this AFTER validation to gather context for query generation.
    """,
    category=ToolCategory.METADATA,
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "max_tables": {"type": "integer", "default": 5}
        },
        "required": ["question"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "tables": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string"},
                        "description": {"type": "string"},
                        "columns": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "description": {"type": "string"}
                                }
                            }
                        },
                        "relevance_score": {"type": "number"}
                    }
                }
            }
        }
    },
    function=None,
    examples=[
        {
            "input": {"question": "Show customer revenue", "max_tables": 5},
            "output": {
                "tables": [{
                    "table_name": "customers",
                    "description": "Customer information",
                    "columns": [
                        {"name": "customer_id", "type": "int", "description": "Unique ID"},
                        {"name": "revenue", "type": "decimal", "description": "Total revenue"}
                    ],
                    "relevance_score": 0.95
                }]
            }
        }
    ]
)


GET_TABLE_DESCRIPTIONS_TOOL = Tool(
    name="get_table_descriptions",
    description="""
    Retrieves detailed descriptions and metadata for specific tables.
    
    This tool:
    - Fetches complete schema information
    - Includes column types, constraints, and descriptions
    - Provides sample data patterns
    
    Use this when you need detailed information about specific tables.
    """,
    category=ToolCategory.METADATA,
    input_schema={
        "type": "object",
        "properties": {
            "table_names": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["table_names"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "tables": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "columns": {"type": "array"},
                        "row_count": {"type": "integer"},
                        "sample_data": {"type": "array"}
                    }
                }
            }
        }
    },
    function=None,
    examples=[
        {
            "input": {"table_names": ["customers", "orders"]},
            "output": {
                "tables": {
                    "customers": {
                        "description": "Customer master data",
                        "columns": [{"name": "id", "type": "int"}],
                        "row_count": 10000
                    }
                }
            }
        }
    ]
)


# ============================================================================
# QUERY GENERATION TOOLS
# ============================================================================

GENERATE_SQL_QUERY_TOOL = Tool(
    name="generate_sql_query",
    description="""
    Generates SQL query from natural language question using LLM.
    
    This tool:
    - Uses table metadata and similar questions as context
    - Employs fallback strategy (small → large model)
    - Returns query with confidence score
    - Includes syntax validation
    
    Use this AFTER gathering metadata to generate the SQL query.
    """,
    category=ToolCategory.QUERY_GENERATION,
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "relevant_tables": {"type": "array"},
            "similar_qa": {"type": "array", "optional": True}
        },
        "required": ["question", "relevant_tables"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "llm_confidence": {"type": "number"},
            "model_used": {"type": "string"},
            "validation_passed": {"type": "boolean"},
            "validation_errors": {"type": "array"}
        }
    },
    function=None,
    examples=[
        {
            "input": {
                "question": "Top 10 customers by revenue",
                "relevant_tables": [{"table_name": "customers", "columns": [...]}]
            },
            "output": {
                "query": "SELECT customer_id, name, SUM(revenue) as total FROM customers GROUP BY customer_id ORDER BY total DESC LIMIT 10",
                "llm_confidence": 0.92,
                "model_used": "gpt-3.5-turbo",
                "validation_passed": True
            }
        }
    ]
)


VALIDATE_SQL_SYNTAX_TOOL = Tool(
    name="validate_sql_syntax",
    description="""
    Validates SQL query syntax without executing it.
    
    This tool:
    - Checks for syntax errors
    - Validates table and column names
    - Ensures query is safe to execute
    
    Use this to verify generated queries before execution.
    """,
    category=ToolCategory.QUERY_GENERATION,
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "errors": {"type": "array", "items": {"type": "string"}}
        }
    },
    function=None,
    examples=[
        {
            "input": {"query": "SELECT * FROM customers WHERE id = 1"},
            "output": {"valid": True, "errors": []}
        },
        {
            "input": {"query": "SELCT * FROM customers"},
            "output": {"valid": False, "errors": ["Syntax error: SELCT"]}
        }
    ]
)


# ============================================================================
# QUERY EXECUTION TOOLS
# ============================================================================

EXECUTE_SQL_QUERY_TOOL = Tool(
    name="execute_sql_query",
    description="""
    Executes validated SQL query against the database.
    
    This tool:
    - Runs the query safely
    - Returns results with metadata
    - Handles errors gracefully
    - Limits result size
    
    Use this AFTER query generation and validation.
    """,
    category=ToolCategory.QUERY_EXECUTION,
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 1000}
        },
        "required": ["query"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {"type": "array"},
            "columns": {"type": "array", "items": {"type": "string"}},
            "row_count": {"type": "integer"},
            "execution_time": {"type": "number"},
            "error": {"type": "string", "optional": True}
        }
    },
    function=None,
    examples=[
        {
            "input": {"query": "SELECT * FROM customers LIMIT 10", "limit": 1000},
            "output": {
                "success": True,
                "data": [[1, "John", 5000], [2, "Jane", 3000]],
                "columns": ["id", "name", "revenue"],
                "row_count": 2,
                "execution_time": 0.15
            }
        }
    ]
)


# ============================================================================
# VISUALIZATION TOOLS
# ============================================================================

CREATE_VISUALIZATION_TOOL = Tool(
    name="create_visualization",
    description="""
    Creates appropriate visualization for query results.
    
    This tool:
    - Analyzes result structure
    - Suggests best visualization type
    - Generates interactive charts/tables
    - Supports multiple formats (table, bar, line, pie, scatter)
    
    Use this AFTER query execution to present results.
    """,
    category=ToolCategory.VISUALIZATION,
    input_schema={
        "type": "object",
        "properties": {
            "data": {"type": "array"},
            "columns": {"type": "array"},
            "visualization_type": {"type": "string", "optional": True}
        },
        "required": ["data", "columns"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "type": {"type": "string"},
            "html": {"type": "string"},
            "json": {"type": "object"},
            "suggested_type": {"type": "string"}
        }
    },
    function=None,
    examples=[
        {
            "input": {
                "data": [[1, 5000], [2, 3000]],
                "columns": ["customer_id", "revenue"],
                "visualization_type": "bar"
            },
            "output": {
                "type": "bar",
                "html": "<div>...</div>",
                "suggested_type": "bar"
            }
        }
    ]
)


# ============================================================================
# FEEDBACK TOOLS
# ============================================================================

SUBMIT_FEEDBACK_TOOL = Tool(
    name="submit_feedback",
    description="""
    Submits user feedback on query results.
    
    This tool:
    - Records user satisfaction (positive/negative/neutral)
    - Updates confidence scores
    - Stores good Q&A pairs
    - Improves future results
    
    Use this to collect user feedback for continuous improvement.
    """,
    category=ToolCategory.FEEDBACK,
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "sql_query": {"type": "string"},
            "answer": {"type": "object"},
            "feedback_type": {"type": "string", "enum": ["positive", "negative", "neutral"]},
            "comment": {"type": "string", "optional": True}
        },
        "required": ["question", "sql_query", "answer", "feedback_type"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"}
        }
    },
    function=None,
    examples=[
        {
            "input": {
                "question": "Top customers",
                "sql_query": "SELECT ...",
                "answer": {...},
                "feedback_type": "positive"
            },
            "output": {"success": True, "message": "Feedback recorded"}
        }
    ]
)


# ============================================================================
# MEMORY TOOLS
# ============================================================================

ADD_TO_MEMORY_TOOL = Tool(
    name="add_to_memory",
    description="""
    Adds message to conversation memory.
    
    This tool:
    - Maintains conversation context
    - Tracks user and assistant messages
    - Manages memory limits
    
    Use this to maintain conversation state across interactions.
    """,
    category=ToolCategory.MEMORY,
    input_schema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "role": {"type": "string", "enum": ["user", "assistant"]},
            "content": {"type": "string"}
        },
        "required": ["session_id", "role", "content"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"}
        }
    },
    function=None,
    examples=[
        {
            "input": {"session_id": "abc123", "role": "user", "content": "Show customers"},
            "output": {"success": True}
        }
    ]
)


# ============================================================================
# TOOL REGISTRY
# ============================================================================

ALL_TOOLS = [
    VALIDATE_QUESTION_TOOL,
    CHECK_SIMILAR_QUESTIONS_TOOL,
    GET_RELEVANT_TABLES_TOOL,
    GET_TABLE_DESCRIPTIONS_TOOL,
    GENERATE_SQL_QUERY_TOOL,
    VALIDATE_SQL_SYNTAX_TOOL,
    EXECUTE_SQL_QUERY_TOOL,
    CREATE_VISUALIZATION_TOOL,
    SUBMIT_FEEDBACK_TOOL,
    ADD_TO_MEMORY_TOOL
]


def get_tool_by_name(name: str) -> Optional[Tool]:
    """Get tool by name."""
    for tool in ALL_TOOLS:
        if tool.name == name:
            return tool
    return None


def get_tools_by_category(category: ToolCategory) -> List[Tool]:
    """Get all tools in a category."""
    return [tool for tool in ALL_TOOLS if tool.category == category]


def get_all_tool_descriptions() -> Dict[str, Any]:
    """Get descriptions of all tools."""
    return {
        tool.name: tool.to_dict()
        for tool in ALL_TOOLS
    }
