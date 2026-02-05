# Tool Documentation

Complete reference for all tools available in the Text-to-SQL Agent.

---

## Overview

The Text-to-SQL Agent is built as a **tool-based agentic system**. Each major function is defined as a tool with:

- **Clear purpose** - What the tool does
- **Input schema** - Expected parameters with types
- **Output schema** - Return value structure
- **Usage examples** - Sample inputs and outputs
- **Category** - Tool classification

This architecture makes the agent:
- **Transparent** - Easy to understand what each step does
- **Modular** - Tools can be used independently
- **Extensible** - New tools can be added easily
- **Testable** - Each tool can be tested in isolation

---

## Tool Categories

| Category | Description | Tool Count |
|----------|-------------|------------|
| **Validation** | Question validation and similarity checking | 2 |
| **Metadata** | Database schema and table information | 2 |
| **Query Generation** | SQL query generation and validation | 2 |
| **Query Execution** | SQL execution and result handling | 1 |
| **Visualization** | Data visualization and chart generation | 1 |
| **Feedback** | User feedback and learning | 1 |
| **Memory** | Conversation memory management | 1 |

**Total:** 10 tools

---

## Validation Tools

### 1. validate_question

**Purpose:** Validates if a question is relevant and answerable with SQL.

**Category:** `validation`

**Description:**
This tool checks:
- Is the question data-related?
- Can it be answered with SQL?
- Is it clear and specific enough?

Use this as the **FIRST step** before any query generation.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "question": {
      "type": "string",
      "description": "Natural language question from user"
    }
  },
  "required": ["question"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "valid": {"type": "boolean"},
    "reason": {"type": "string"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
  }
}
```

**Example Usage:**

*Input:*
```json
{
  "question": "What are the top 10 customers by revenue?"
}
```

*Output:*
```json
{
  "valid": true,
  "reason": "Clear data question that can be answered with SQL",
  "confidence": 0.95
}
```

*Input:*
```json
{
  "question": "What is the meaning of life?"
}
```

*Output:*
```json
{
  "valid": false,
  "reason": "Not a data-related question",
  "confidence": 0.98
}
```

---

### 2. check_similar_questions

**Purpose:** Searches for previously answered similar questions.

**Category:** `validation`

**Description:**
This tool:
- Finds semantically similar questions using vector search
- Returns cached answers if found (above threshold)
- Reduces latency and LLM costs by reusing previous work

Use this **AFTER validation** to check for cached answers.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "question": {"type": "string"},
    "threshold": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "default": 0.85,
      "description": "Similarity threshold (0-1)"
    }
  },
  "required": ["question"]
}
```

**Output Schema:**
```json
{
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
}
```

**Example Usage:**

*Input:*
```json
{
  "question": "Show top customers",
  "threshold": 0.85
}
```

*Output:*
```json
{
  "found": true,
  "similar_questions": [
    {
      "question": "What are the top customers?",
      "sql_query": "SELECT * FROM customers ORDER BY revenue DESC LIMIT 10",
      "similarity": 0.92
    }
  ]
}
```

---

## Metadata Tools

### 3. get_relevant_tables

**Purpose:** Identifies and retrieves metadata for tables relevant to the question.

**Category:** `metadata`

**Description:**
This tool:
- Uses semantic search to find relevant tables from the metastore
- Returns table schemas, column descriptions, and relationships
- Essential for accurate query generation

Use this **AFTER validation** to gather context for query generation.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "question": {"type": "string"},
    "max_tables": {
      "type": "integer",
      "default": 5,
      "description": "Maximum number of tables to return"
    }
  },
  "required": ["question"]
}
```

**Output Schema:**
```json
{
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
}
```

**Example Usage:**

*Input:*
```json
{
  "question": "Show customer revenue",
  "max_tables": 5
}
```

*Output:*
```json
{
  "tables": [
    {
      "table_name": "customers",
      "description": "Customer information and metrics",
      "columns": [
        {
          "name": "customer_id",
          "type": "int",
          "description": "Unique customer identifier"
        },
        {
          "name": "revenue",
          "type": "decimal",
          "description": "Total customer revenue"
        }
      ],
      "relevance_score": 0.95
    }
  ]
}
```

---

### 4. get_table_descriptions

**Purpose:** Retrieves detailed descriptions for specific tables.

**Category:** `metadata`

**Description:**
This tool:
- Fetches complete schema information for named tables
- Includes column types, constraints, and descriptions
- Provides sample data patterns when available

Use this when you need **detailed information** about specific tables.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "table_names": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of table names to describe"
    }
  },
  "required": ["table_names"]
}
```

**Output Schema:**
```json
{
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
}
```

**Example Usage:**

*Input:*
```json
{
  "table_names": ["customers", "orders"]
}
```

*Output:*
```json
{
  "tables": {
    "customers": {
      "description": "Customer master data",
      "columns": [
        {"name": "id", "type": "int", "description": "Primary key"}
      ],
      "row_count": 10000
    },
    "orders": {
      "description": "Order transactions",
      "columns": [
        {"name": "order_id", "type": "int"},
        {"name": "customer_id", "type": "int"}
      ],
      "row_count": 50000
    }
  }
}
```

---

## Query Generation Tools

### 5. generate_sql_query

**Purpose:** Generates SQL query from natural language using LLM.

**Category:** `query_generation`

**Description:**
This tool:
- Uses table metadata and similar questions as context
- Employs fallback strategy (small model → large model)
- Returns query with LLM confidence score
- Includes automatic syntax validation

Use this **AFTER gathering metadata** to generate the SQL query.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "question": {"type": "string"},
    "relevant_tables": {
      "type": "array",
      "description": "Tables relevant to the question"
    },
    "similar_qa": {
      "type": "array",
      "optional": true,
      "description": "Similar Q&A pairs for context"
    }
  },
  "required": ["question", "relevant_tables"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string"},
    "llm_confidence": {
      "type": "number",
      "description": "LLM's confidence in the query (0-1)"
    },
    "model_used": {
      "type": "string",
      "description": "Which model generated the query"
    },
    "validation_passed": {"type": "boolean"},
    "validation_errors": {"type": "array"}
  }
}
```

**Example Usage:**

*Input:*
```json
{
  "question": "Top 10 customers by revenue",
  "relevant_tables": [
    {
      "table_name": "customers",
      "columns": [
        {"name": "customer_id", "type": "int"},
        {"name": "name", "type": "string"},
        {"name": "revenue", "type": "decimal"}
      ]
    }
  ]
}
```

*Output:*
```json
{
  "query": "SELECT customer_id, name, SUM(revenue) as total FROM customers GROUP BY customer_id, name ORDER BY total DESC LIMIT 10",
  "llm_confidence": 0.92,
  "model_used": "gpt-3.5-turbo",
  "validation_passed": true,
  "validation_errors": []
}
```

---

### 6. validate_sql_syntax

**Purpose:** Validates SQL query syntax without executing it.

**Category:** `query_generation`

**Description:**
This tool:
- Checks for SQL syntax errors
- Validates table and column name references
- Ensures query is safe to execute

Use this to **verify generated queries** before execution.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "SQL query to validate"
    }
  },
  "required": ["query"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "valid": {"type": "boolean"},
    "errors": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

**Example Usage:**

*Valid Query:*
```json
{
  "query": "SELECT * FROM customers WHERE id = 1"
}
```
→
```json
{
  "valid": true,
  "errors": []
}
```

*Invalid Query:*
```json
{
  "query": "SELCT * FROM customers"
}
```
→
```json
{
  "valid": false,
  "errors": ["Syntax error: SELCT is not a valid keyword"]
}
```

---

## Query Execution Tools

### 7. execute_sql_query

**Purpose:** Executes validated SQL query against the database.

**Category:** `query_execution`

**Description:**
This tool:
- Runs the query safely with timeout protection
- Returns results with execution metadata
- Handles errors gracefully
- Limits result size to prevent memory issues

Use this **AFTER query generation and validation**.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string"},
    "limit": {
      "type": "integer",
      "default": 1000,
      "description": "Maximum rows to return"
    }
  },
  "required": ["query"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "data": {
      "type": "array",
      "description": "Query results as array of rows"
    },
    "columns": {
      "type": "array",
      "items": {"type": "string"}
    },
    "row_count": {"type": "integer"},
    "execution_time": {
      "type": "number",
      "description": "Query execution time in seconds"
    },
    "error": {
      "type": "string",
      "optional": true
    }
  }
}
```

**Example Usage:**

*Input:*
```json
{
  "query": "SELECT * FROM customers LIMIT 10",
  "limit": 1000
}
```

*Output:*
```json
{
  "success": true,
  "data": [
    [1, "John Doe", 5000.00],
    [2, "Jane Smith", 3000.00]
  ],
  "columns": ["id", "name", "revenue"],
  "row_count": 2,
  "execution_time": 0.15
}
```

---

## Visualization Tools

### 8. create_visualization

**Purpose:** Creates appropriate visualization for query results.

**Category:** `visualization`

**Description:**
This tool:
- Analyzes result structure to suggest best visualization
- Generates interactive charts/tables
- Supports multiple formats (table, bar, line, pie, scatter)
- Returns HTML and JSON representations

Use this **AFTER query execution** to present results.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "data": {
      "type": "array",
      "description": "Query results"
    },
    "columns": {
      "type": "array",
      "items": {"type": "string"}
    },
    "visualization_type": {
      "type": "string",
      "optional": true,
      "enum": ["table", "bar", "line", "pie", "scatter"],
      "description": "Specific type, or auto-suggest if not provided"
    }
  },
  "required": ["data", "columns"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "type": {
      "type": "string",
      "description": "Visualization type used"
    },
    "html": {
      "type": "string",
      "description": "HTML representation"
    },
    "json": {
      "type": "object",
      "description": "Plotly JSON spec"
    },
    "suggested_type": {
      "type": "string",
      "description": "AI-suggested visualization type"
    }
  }
}
```

**Example Usage:**

*Input:*
```json
{
  "data": [[1, 5000], [2, 3000]],
  "columns": ["customer_id", "revenue"],
  "visualization_type": "bar"
}
```

*Output:*
```json
{
  "type": "bar",
  "html": "<div>...</div>",
  "suggested_type": "bar"
}
```

---

## Feedback Tools

### 9. submit_feedback

**Purpose:** Submits user feedback on query results.

**Category:** `feedback`

**Description:**
This tool:
- Records user satisfaction (positive/negative/neutral)
- Updates confidence scores based on feedback
- Stores successful Q&A pairs for future use
- Enables continuous learning

Use this to **collect user feedback** for system improvement.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "question": {"type": "string"},
    "sql_query": {"type": "string"},
    "answer": {"type": "object"},
    "feedback_type": {
      "type": "string",
      "enum": ["positive", "negative", "neutral"]
    },
    "comment": {
      "type": "string",
      "optional": true
    }
  },
  "required": ["question", "sql_query", "answer", "feedback_type"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "message": {"type": "string"}
  }
}
```

**Example Usage:**

*Input:*
```json
{
  "question": "Top customers",
  "sql_query": "SELECT ...",
  "answer": {...},
  "feedback_type": "positive",
  "comment": "Perfect results!"
}
```

*Output:*
```json
{
  "success": true,
  "message": "Feedback recorded successfully"
}
```

---

## Memory Tools

### 10. add_to_memory

**Purpose:** Adds message to conversation memory.

**Category:** `memory`

**Description:**
This tool:
- Maintains conversation context across interactions
- Tracks user and assistant messages
- Manages memory limits automatically
- Enables context-aware responses

Use this to **maintain conversation state**.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "session_id": {"type": "string"},
    "role": {
      "type": "string",
      "enum": ["user", "assistant"]
    },
    "content": {"type": "string"}
  },
  "required": ["session_id", "role", "content"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"}
  }
}
```

**Example Usage:**

*Input:*
```json
{
  "session_id": "abc123",
  "role": "user",
  "content": "Show customers"
}
```

*Output:*
```json
{
  "success": true
}
```

---

## Tool Execution Workflow

### Standard Query Flow

```
1. validate_question
   ↓
2. check_similar_questions
   ↓ (if not found)
3. get_relevant_tables
   ↓
4. generate_sql_query
   ↓
5. validate_sql_syntax
   ↓
6. execute_sql_query
   ↓
7. create_visualization
   ↓
8. submit_feedback (optional)
```

### With Caching

```
1. validate_question
   ↓
2. check_similar_questions
   → (if found) Return cached answer
   ↓ (if not found)
3. Continue with standard flow...
```

---

## Programmatic Usage

### Execute Individual Tool

```python
from src.agent.tool_agent import ToolBasedAgent
from src.utils.config import load_config

# Initialize
config = load_config()
agent = ToolBasedAgent(config)

# Execute a tool
result = agent.execute_tool(
    tool_name="validate_question",
    parameters={"question": "What are the top customers?"}
)

print(result)
# {'valid': True, 'reason': '...', 'confidence': 0.95}
```

### Get Available Tools

```python
# List all tools
tools = agent.get_available_tools()

for tool in tools:
    print(f"{tool['name']} ({tool['category']})")
    print(f"  {tool['description']}")
```

### Get Tools by Category

```python
# Get all validation tools
validation_tools = agent.get_tools_by_category("validation")

for tool in validation_tools:
    print(tool['name'])
```

---

## Testing Tools

Each tool can be tested independently:

```python
import pytest
from src.agent.tool_agent import ToolBasedAgent

def test_validate_question_tool():
    agent = ToolBasedAgent(config)
    
    # Test valid question
    result = agent.execute_tool(
        "validate_question",
        {"question": "Show top 10 customers"}
    )
    assert result['valid'] == True
    
    # Test invalid question
    result = agent.execute_tool(
        "validate_question",
        {"question": "What is love?"}
    )
    assert result['valid'] == False
```

---

## Tool Categories Summary

| Category | Tools | Purpose |
|----------|-------|---------|
| **Validation** | 2 | Ensure questions are answerable |
| **Metadata** | 2 | Fetch database schema information |
| **Query Generation** | 2 | Generate and validate SQL |
| **Query Execution** | 1 | Execute queries safely |
| **Visualization** | 1 | Create charts and tables |
| **Feedback** | 1 | Learn from user feedback |
| **Memory** | 1 | Maintain conversation context |

---

## Benefits of Tool-Based Architecture

1. **Transparency** - Clear what each step does
2. **Modularity** - Tools can be used independently
3. **Testability** - Each tool tested in isolation
4. **Extensibility** - Easy to add new tools
5. **Observability** - Track which tools are called
6. **Documentation** - Self-documenting with schemas
7. **Reusability** - Tools can be combined in different ways

---

## Next Steps

- See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [API.md](API.md) for REST API usage
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common tasks

---

**Version**: 1.0.0  
**Last Updated**: January 2026
