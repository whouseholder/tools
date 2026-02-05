"""
Tool-based Text-to-SQL Agent with agentic tool definitions and LLM-driven workflow.
"""

import uuid
from typing import Any, Dict, List, Optional
from enum import Enum
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
from .feedback import FeedbackManager, FeedbackType, FeedbackSource


class ResponseType(str, Enum):
    """Type of response."""
    TABLE = "table"
    CHART = "chart"
    ERROR = "error"
    SIMILAR_QUESTION = "similar_question"


class TextToSQLAgent:
    """
    Agentic Text-to-SQL system with explicit tool definitions.
    
    Combines:
    - Full feature set (validation, similar Q&A, metadata, query generation, execution, visualization, feedback)
    - Proper tool-based architecture
    - LLM-driven decision making
    - Transparent workflow
    """
    
    def __init__(self, config: Config):
        """Initialize agent with all components and tool bindings."""
        self.config = config
        
        # Initialize components
        from ..vector_store import create_vector_store
        
        self.vector_store = create_vector_store(config.vector_store)
        self.llm_manager = LLMManager(config.llm)
        self.metadata_manager = MetadataManager(self.vector_store, config.metadata, config.query)
        self.query_generator = QueryGenerator(self.llm_manager, config.query)
        self.query_executor = QueryExecutor(config.metadata, config.query)
        self.visualization_engine = VisualizationEngine(self.llm_manager, config.visualization)
        self.validator = QuestionValidator(self.llm_manager, config.validation)
        self.feedback_manager = FeedbackManager(config.feedback)
        
        self._sessions: Dict[str, MemoryManager] = {}
        
        # Bind tools to actual functions
        self._bind_tools()
        
        logger.info(f"Text-to-SQL Agent initialized with {len(ALL_TOOLS)} tools")
    
    def _bind_tools(self):
        """Bind tool definitions to actual implementation functions."""
        tool_bindings = {
            "validate_question": self._tool_validate_question,
            "check_similar_questions": self._tool_check_similar_questions,
            "get_relevant_tables": self._tool_get_relevant_tables,
            "get_table_descriptions": self._tool_get_table_descriptions,
            "generate_sql_query": self._tool_generate_sql_query,
            "validate_sql_syntax": self._tool_validate_sql_syntax,
            "execute_sql_query": self._tool_execute_sql_query,
            "create_visualization": self._tool_create_visualization,
            "submit_feedback": self._tool_submit_feedback,
            "add_to_memory": self._tool_add_to_memory,
        }
        
        for tool_name, function in tool_bindings.items():
            tool = get_tool_by_name(tool_name)
            if tool:
                tool.function = function
        
        logger.info(f"Bound {len(tool_bindings)} tools to implementations")
    
    # ========================================================================
    # Tool Implementations
    # ========================================================================
    
    def _tool_validate_question(
        self, 
        question: str, 
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Tool: Validate if question is answerable, considering conversation context.
        
        Input: {"question": "...", "conversation_history": [...]}
        Output: {"valid": bool, "reason": str, "confidence": float}
        """
        logger.info(f"[TOOL] validate_question: {question[:50]}...")
        if conversation_history:
            logger.info(f"[TOOL] Using conversation context: {len(conversation_history)} messages")
        result = self.validator.validate(question, conversation_history)
        logger.info(f"[TOOL] Result: valid={result['valid']}, confidence={result.get('checks', {}).get('relevance', {}).get('score', 0):.2f}")
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
        
        similar = self.vector_store.search_similar_questions(question, top_k=3)
        
        # Filter by threshold
        similar_filtered = [
            s for s in similar
            if s.get('similarity', 0) >= threshold
        ]
        
        found = len(similar_filtered) > 0
        logger.info(f"[TOOL] Result: found={found}, count={len(similar_filtered)}")
        
        return {
            "found": found,
            "similar_questions": similar_filtered
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
        logger.debug(f"[TOOL] Metadata manager DB type: {self.metadata_manager.db_type}")
        
        tables = self.metadata_manager.get_relevant_tables(question)
        
        # Limit to max_tables
        tables = tables[:max_tables]
        
        logger.info(f"[TOOL] Result: {len(tables)} tables found")
        logger.debug(f"[TOOL] Table names: {[t.get('table_name') for t in tables]}")
        
        if not tables:
            logger.warning(f"[TOOL] No tables found for question: {question}")
        
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
            metadata = self.metadata_manager.get_table_metadata(table_name)
            if metadata:
                tables[table_name] = metadata
        
        logger.info(f"[TOOL] Result: {len(tables)} tables retrieved")
        
        return {"tables": tables}
    
    def _build_validation_generation_prompt(
        self,
        question: str,
        relevant_tables: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict]] = None,
        similar_qa: Optional[List[Dict[str, Any]]] = None,
        db_info: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build the templated prompt for combined validation and SQL generation.
        This template is used consistently for both initial questions and follow-ups.
        """
        # Get database info if not provided
        if db_info is None:
            db_info = self.metadata_manager.get_database_info()
        
        # Build database info section
        db_section = f"""DATABASE TYPE: {db_info['type']}
VERSION: {db_info.get('version', 'unknown')}
DESCRIPTION: {db_info.get('description', '')}
SQL DIALECT: {db_info['dialect']}"""
        
        # Build schema description with enhanced relationship info
        schema_description = ""
        
        # First pass: collect all foreign key relationships to build a relationship map
        all_relationships = []
        table_columns_map = {}
        
        for table in relevant_tables:
            table_name = table['table_name']
            table_columns_map[table_name] = [col['name'] for col in table.get('columns', [])]
            
            if table.get('foreign_keys'):
                for fk in table['foreign_keys']:
                    all_relationships.append({
                        'from_table': table_name,
                        'from_column': fk['column'],
                        'to_table': fk['references_table'],
                        'to_column': fk['references_column']
                    })
        
        # Build detailed schema for each table
        for table in relevant_tables:
            schema_description += f"\n\nTable: {table['table_name']}"
            if table.get('description'):
                schema_description += f"\nDescription: {table['description']}"
            schema_description += "\nColumns:"
            for col in table.get('columns', []):
                col_desc = f"\n  - {col['name']} ({col['type']})"
                if col.get('description'):
                    col_desc += f": {col['description']}"
                if col.get('is_primary_key'):
                    col_desc += " [PRIMARY KEY]"
                schema_description += col_desc
            
            # Add foreign key relationships
            if table.get('foreign_keys'):
                schema_description += "\nForeign Keys:"
                for fk in table['foreign_keys']:
                    schema_description += f"\n  - {fk['column']} REFERENCES {fk['references_table']}({fk['references_column']})"
        
        # Build RELATIONSHIPS section showing common join patterns and analysis possibilities
        relationships_section = ""
        if all_relationships:
            relationships_section = "\n\nTABLE RELATIONSHIPS & JOIN PATTERNS:"
            relationships_section += "\nThese relationships enable cross-table analysis:\n"
            
            # Document each relationship with analysis examples
            for rel in all_relationships:
                from_t = rel['from_table']
                to_t = rel['to_table']
                from_cols = table_columns_map.get(from_t, [])
                to_cols = table_columns_map.get(to_t, [])
                
                relationships_section += f"\n• {from_t}.{rel['from_column']} → {to_t}.{rel['to_column']}"
                relationships_section += f"\n  ↳ Enables: Analyze {to_t} attributes grouped by {from_t} attributes"
                
                # Show concrete column examples if available
                if from_cols and to_cols:
                    # Find interesting columns (non-id columns)
                    from_interesting = [c for c in from_cols if not c.endswith('_id') and c != 'id'][:3]
                    to_interesting = [c for c in to_cols if not c.endswith('_id') and c != 'id'][:3]
                    
                    if from_interesting and to_interesting:
                        relationships_section += f"\n  ↳ Example: {', '.join(to_interesting)} by {', '.join(from_interesting)}"
            
            # Add multi-hop relationship examples if we have them
            if len(all_relationships) > 1:
                relationships_section += "\n\nMULTI-TABLE JOIN EXAMPLES:"
                
                # Check for devices → customers → plans chain
                has_device_customer = any(r['from_table'] == 'devices' and r['to_table'] == 'customers' for r in all_relationships)
                has_customer_plan = any(r['from_table'] == 'customers' and r['to_table'] == 'plans' for r in all_relationships)
                if has_device_customer and has_customer_plan:
                    relationships_section += "\n• devices → customers → plans"
                    relationships_section += "\n  ↳ JOIN devices d JOIN customers c ON d.customer_id=c.customer_id JOIN plans p ON c.plan_id=p.plan_id"
                    if 'manufacturer' in table_columns_map.get('devices', []):
                        if 'churn_risk_score' in table_columns_map.get('customers', []):
                            relationships_section += "\n  ↳ Example Query: Average customer churn_risk_score by device manufacturer"
                        if 'lifetime_value' in table_columns_map.get('customers', []):
                            relationships_section += "\n  ↳ Example Query: Total customer lifetime_value by device manufacturer"
                    if 'plan_type' in table_columns_map.get('plans', []):
                        relationships_section += "\n  ↳ Example Query: Device usage patterns by plan type"
                
                # Check for network_activity → customers → plans chain
                has_activity_customer = any(r['from_table'] == 'network_activity' and r['to_table'] == 'customers' for r in all_relationships)
                if has_activity_customer and has_customer_plan:
                    relationships_section += "\n• network_activity → customers → plans"
                    relationships_section += "\n  ↳ JOIN network_activity n JOIN customers c ON n.customer_id=c.customer_id JOIN plans p ON c.plan_id=p.plan_id"
                    if 'data_usage_mb' in table_columns_map.get('network_activity', []):
                        relationships_section += "\n  ↳ Example Query: Average data usage by plan type"
        
        # Build conversation context
        context_section = ""
        if conversation_history:
            recent_messages = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
            
            context_entries = []
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:200]
                metadata = msg.get('metadata', {})
                
                if role == 'user':
                    context_entries.append(f"User: {content}")
                elif role == 'assistant' and metadata.get('sql_query'):
                    context_entries.append(f"Assistant executed SQL: {metadata['sql_query'][:150]}")
            
            if context_entries:
                context_section = "\n\nCONVERSATION HISTORY:\n" + "\n".join(context_entries)
        
        # Build similar Q&A context
        similar_section = ""
        if similar_qa:
            similar_entries = []
            for qa in similar_qa[:3]:
                entry = f"- Q: {qa['question']}"
                if qa.get('metadata', {}).get('sql_query'):
                    entry += f"\n  SQL: {qa['metadata']['sql_query'][:120]}"
                similar_entries.append(entry)
            
            if similar_entries:
                similar_section = "\n\nSIMILAR QUESTIONS ANSWERED BEFORE:\n" + "\n".join(similar_entries)
        
        # Build the complete prompt using consistent template
        prompt = f"""You are a Text-to-SQL validation and generation agent.

TASK:
1. VALIDATE if the question is answerable given the database schema and conversation context
2. If INVALID, explain why and return {{"valid": false, "reason": "..."}}
3. If VALID, generate the SQL query and return {{"valid": true, "sql": "...", "confidence": 0.0-1.0, "explanation": "..."}}

{db_section}

DATABASE SCHEMA:
{schema_description}
{relationships_section}
{similar_section}
{context_section}

CURRENT QUESTION: {question}

VALIDATION RULES:

**CRITICAL**: Before deciding if a question is valid, ALWAYS review the TABLE RELATIONSHIPS section above to see what cross-table analyses are possible.

✅ Answer "valid: true" if:
- Question asks about data in the available tables/columns (even if it requires JOINs)
- **STEP 1**: Check if ALL required columns exist somewhere in the schema (across any tables)
- **STEP 2**: Check TABLE RELATIONSHIPS to see if those tables can be joined
- **STEP 3**: If columns exist AND tables can be joined → VALID
  Example: "Which manufacturers have highest churn risk?" 
    → devices.manufacturer EXISTS ✓
    → customers.churn_risk_score EXISTS ✓  
    → devices→customers relationship EXISTS ✓
    → VALID (JOIN devices to customers, aggregate churn by manufacturer)
  Example: "What is average usage by plan type?"
    → network_activity.data_usage_mb EXISTS ✓
    → plans.plan_type EXISTS ✓
    → network_activity→customers→plans chain EXISTS ✓
    → VALID (multi-hop JOIN)
- Follow-up question relates to previous conversation topic AND asks for columns that exist in the schema (possibly across tables)
  Example: Previous Q: "top 10 customers by lifetime value", Follow-up Q: "what is their churn risk?" → VALID (churn_risk column exists in customers table)
- Question asks for visualization of data (pie chart, bar chart, etc.) - just generate the SQL to get the data, the visualization engine will create the chart
  Example: "Show me churn risk as a pie chart" → Generate SQL to get churn risk data, don't worry about the chart rendering
- Question is clear and answerable with the database schema
- **USE THE RELATIONSHIPS SECTION**: It explicitly shows what cross-table analyses are possible with example queries

❌ Answer "valid: false" if:
- Question asks about data/entities that DO NOT EXIST in ANY table in the schema (e.g., "pizza preferences" when schema has only telecom/customer data)
- Required columns exist BUT there is NO way to JOIN the tables (no foreign key relationship path)
- Follow-up references previous results ("these", "those", "that") BUT asks about columns/entities NOT in ANY table in the schema
  Example: Previous Q: "top customers", Follow-up Q: "what pizza do they like?" → INVALID (pizza data not in any table)
- Follow-up references previous results ("these", "those", "that") BUT asks about columns/entities NOT in ANY table in the schema
  Example: Previous Q: "top customers", Follow-up Q: "what pizza do they like?" → INVALID (pizza data not in any table)
- Question requires external data not available in any database table
- Question is pure chitchat, greetings, or nonsensical
- **NOTE**: DO NOT reject just because data is in different tables - as long as tables can be joined via Foreign Keys, the question is VALID

SQL GENERATION RULES (if valid):
- Use the EXACT SQL dialect and syntax for {db_info['type']} version {db_info.get('version', 'unknown')}
- Use exact table and column names from the schema
- DO NOT add LIMIT clause unless explicitly requested
- Use proper SQL syntax appropriate for {db_info['dialect']} (SELECT, FROM, WHERE, GROUP BY, ORDER BY, etc.)
- For {db_info['dialect']}-specific features, use the appropriate syntax for version {db_info.get('version', 'unknown')}
- **CRITICAL - USE JOINS WHEN NEEDED**: If columns from multiple tables are needed, you MUST use JOIN:
  - Check the Foreign Keys section for each table to understand relationships
  - Example: To get plan_type for network_activity, JOIN network_activity → customers → plans
  - Use INNER JOIN by default, LEFT JOIN only when explicitly needed
  - Example Query 1: "SELECT p.plan_type, SUM(n.data_usage_mb) FROM network_activity n JOIN customers c ON n.customer_id = c.customer_id JOIN plans p ON c.plan_id = p.plan_id GROUP BY p.plan_type"
  - Example Query 2: "Which manufacturers have highest churn risk?" → "SELECT d.manufacturer, AVG(c.churn_risk_score) as avg_churn FROM devices d JOIN customers c ON d.customer_id = c.customer_id GROUP BY d.manufacturer ORDER BY avg_churn DESC"
- **AGGREGATION ACROSS JOINS**: When aggregating metrics from one table grouped by attributes from another:
  - Identify the metric table and the grouping table
  - JOIN them via their foreign key relationship
  - Use appropriate aggregate functions (AVG, SUM, COUNT, MAX, MIN)
  - Always ORDER BY the aggregated metric to show highest/lowest first
- **IMPORTANT FOR VISUALIZATION REQUESTS**: When someone asks for a chart (pie chart, bar chart, line chart, etc.):
  - ONLY generate the SQL query to retrieve the data
  - DO NOT try to create the chart in SQL
  - The visualization engine will handle rendering the chart
  - Example: "show churn risk as a pie chart" → "SELECT customer_id, first_name, churn_risk FROM customers ORDER BY value DESC LIMIT 10"
- **IMPORTANT FOR FOLLOW-UPS**: When the question references "these", "those", "that" entities from previous conversation:
  - Generate a NEW query that selects the requested columns for the same entity set
  - Maintain context: preserve the same sorting, filtering, and LIMIT from the previous query
  - Example: If previous query was "SELECT name FROM customers ORDER BY value DESC LIMIT 10"
    and follow-up asks for "churn risk for these customers", generate "SELECT name, churn_risk FROM customers ORDER BY value DESC LIMIT 10"
- Return confidence score based on clarity of question and availability of data

RESPONSE FORMAT:

If INVALID:
{{
  "valid": false,
  "reason": "Brief explanation of why question cannot be answered"
}}

If VALID:
{{
  "valid": true,
  "sql": "SELECT column1, column2 FROM table WHERE condition ORDER BY column",
  "confidence": 0.95,
  "explanation": "Brief explanation of what the query does"
}}

Return ONLY valid JSON, no markdown code blocks or additional text."""

        return prompt
    
    def _tool_validate_and_generate_sql(
        self,
        question: str,
        relevant_tables: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict]] = None,
        similar_qa: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Tool: Combined validation and SQL generation in a single LLM call.
        
        Uses a templated prompt that works consistently for both initial questions and follow-ups.
        
        Input: {"question": "...", "relevant_tables": [...], "conversation_history": [...], "similar_qa": [...]}
        Output: {"valid": bool, "reason": str (if invalid), "query": str (if valid), ...}
        """
        logger.info(f"[TOOL] validate_and_generate_sql: {question[:50]}...")
        
        # Build the prompt using consistent template
        prompt = self._build_validation_generation_prompt(
            question=question,
            relevant_tables=relevant_tables,
            conversation_history=conversation_history,
            similar_qa=similar_qa
        )
        
        logger.debug(f"[TOOL] Prompt length: {len(prompt)} chars")
        # Log a snippet of the relationships section if it exists
        if "TABLE RELATIONSHIPS" in prompt:
            rel_start = prompt.find("TABLE RELATIONSHIPS")
            rel_snippet = prompt[rel_start:rel_start+300] if rel_start != -1 else "not found"
            logger.debug(f"[TOOL] Relationships section preview: {rel_snippet}...")
        
        # Call LLM with JSON mode
        try:
            response = self.llm_manager.generate(
                prompt=prompt,
                system_prompt="You are a SQL expert that validates questions against database schemas and generates queries. Always consider conversation context for follow-ups. Respond ONLY with valid JSON.",
                use_large_model=False,
                response_format={"type": "json_object"}
            )
            
            import json
            result_json = json.loads(response.strip())
            
            logger.debug(f"[TOOL] LLM response: {result_json}")
            
            # Check if valid
            if not result_json.get('valid', False):
                logger.info(f"[TOOL] Question invalid: {result_json.get('reason', 'Unknown')}")
                return {
                    'valid': False,
                    'reason': result_json.get('reason', 'Question not answerable with available data'),
                    'model_used': 'small',
                    'attempts': 1,
                    'validation_passed': False
                }
            
            # Valid - extract SQL
            sql_query = result_json.get('sql', '').strip()
            confidence = result_json.get('confidence', 0.8)
            explanation = result_json.get('explanation', '')
            
            logger.info(f"[TOOL] Question valid, SQL generated: {sql_query[:100]}")
            logger.info(f"[TOOL] Confidence: {confidence:.2f}, Explanation: {explanation}")
            
            # Validate SQL syntax
            is_valid, errors = self.query_generator._validate_syntax(sql_query)
            
            if not is_valid:
                logger.warning(f"[TOOL] SQL syntax validation failed: {errors}")
                # Try to fix with LLM using the same context
                fix_prompt = f"""Fix the SQL syntax errors in this query.

ORIGINAL QUERY:
{sql_query}

SYNTAX ERRORS:
{', '.join(errors)}

Return a JSON object with the fixed query:
{{
  "sql": "corrected SQL query here"
}}"""
                
                fixed_response = self.llm_manager.generate(
                    prompt=fix_prompt,
                    system_prompt="You are a SQL expert. Fix syntax errors. Respond ONLY with valid JSON.",
                    use_large_model=False,
                    response_format={"type": "json_object"}
                )
                
                try:
                    fixed_json = json.loads(fixed_response.strip())
                    sql_query = fixed_json.get('sql', sql_query).strip()
                    is_valid, errors = self.query_generator._validate_syntax(sql_query)
                    logger.info(f"[TOOL] SQL fixed, validation: {is_valid}")
                except:
                    logger.warning("[TOOL] Failed to parse fixed SQL response")
            
            return {
                'valid': True,
                'query': sql_query,
                'llm_confidence': confidence,
                'explanation': explanation,
                'model_used': 'small',
                'attempts': 1,
                'validation_passed': is_valid,
                'validation_errors': errors if not is_valid else []
            }
            
        except Exception as e:
            logger.error(f"[TOOL] Combined validation/generation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'valid': False,
                'reason': f'Internal error during validation/generation: {str(e)}',
                'model_used': 'small',
                'attempts': 1,
                'validation_passed': False
            }
    
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
        
        # Use the validator if it has _validate_syntax, otherwise do basic check
        if hasattr(self.query_generator, '_validate_syntax'):
            is_valid, errors = self.query_generator._validate_syntax(query)
        else:
            # Basic validation
            is_valid = query.strip().upper().startswith('SELECT')
            errors = [] if is_valid else ["Query must start with SELECT"]
        
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
        logger.debug(f"[TOOL] Full query: {query}")
        logger.debug(f"[TOOL] Query executor type: {self.query_executor.db_type}")
        
        result = self.query_executor.execute_query(query)
        
        logger.info(f"[TOOL] Result: success={result['success']}, rows={result.get('row_count', 0)}")
        if not result['success']:
            logger.error(f"[TOOL] Execution error: {result.get('error', 'Unknown error')}")
        if result.get('row_count', 0) == 0:
            logger.warning(f"[TOOL] Query returned 0 rows - check if data exists")
        
        return result
    
    def _tool_create_visualization(
        self,
        columns: List[str],
        rows: List[List[Any]],
        visualization_type: Optional[str] = None,
        sql_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool: Create visualization from data.
        
        Input: {"columns": [...], "rows": [[...]], "visualization_type": "bar", "sql_query": "..."}
        Output: {"type": str, "html": str, "json": {...}}
        """
        logger.info(f"[TOOL] create_visualization: {len(rows)} rows, type={visualization_type}")
        
        if visualization_type == 'table' or visualization_type is None:
            result = self.visualization_engine.create_table(columns, rows)
        else:
            result = self.visualization_engine.create_chart(
                columns, rows,
                chart_type=visualization_type if visualization_type != 'auto' else None,
                sql_query=sql_query
            )
        
        logger.info(f"[TOOL] Result: type={result.get('type')}")
        
        return result
    
    def _tool_submit_feedback(
        self,
        question: str,
        sql_query: str,
        answer: Any,
        feedback_type: str,
        comment: Optional[str] = None,
        session_id: Optional[str] = None
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
                feedback_source=FeedbackSource.USER_MANUAL,
                user_comment=comment,
                session_id=session_id
            )
            
            # If positive feedback, store in vector store
            if feedback_enum == FeedbackType.POSITIVE:
                self.vector_store.add_qa_pair(
                    question=question,
                    answer=str(answer),
                    sql_query=sql_query,
                    metadata={'user_feedback': 'positive'}
                )
            
            return {"success": True, "message": "Feedback recorded"}
            
        except Exception as e:
            logger.error(f"[TOOL] Error: {e}")
            return {"success": False, "message": str(e)}
    
    def _tool_add_to_memory(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Tool: Add message to conversation memory.
        
        Input: {"session_id": "...", "role": "user", "content": "...", "metadata": {...}}
        Output: {"success": bool}
        """
        logger.info(f"[TOOL] add_to_memory: session={session_id}, role={role}")
        
        memory = self._sessions.get(session_id)
        if memory:
            memory.add_message(role, content, metadata=metadata)
            return {"success": True}
        
        return {"success": False}
    
    # ========================================================================
    # Main Processing Pipeline
    # ========================================================================
    
    def process_question(
        self,
        question: str,
        session_id: Optional[str] = None,
        visualization_type: Optional[str] = None,
        skip_similar_check: bool = False
    ) -> Dict[str, Any]:
        """
        Process a natural language question through the full agentic pipeline.
        
        WORKFLOW:
        1. Fetch conversation history and relevant metadata from vector store
        2. Check for similar questions (optional)
        3. Fetch relevant table metadata based on question
        4. **Combined Validation & SQL Generation** (single LLM call):
           - Uses templated prompt that works for both initial questions and follow-ups
           - Validates question against schema and conversation context
           - If invalid: returns error with reason
           - If valid: generates SQL query with confidence score
        5. Execute SQL query against database
        6. Create visualization (table/chart) from results
        7. Handle feedback (if in eval mode)
        
        The templated prompt ensures consistent validation and generation for:
        - Initial standalone questions
        - Follow-up questions referencing previous results ("these customers", "that data")
        - Visualization requests building on previous queries
        
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
            # Step 1: Get conversation history and relevant metadata
            logger.info("[STEP 1] Fetching conversation context and relevant metadata")
            
            # Get conversation history from memory for context (with metadata for SQL queries)
            conversation_history = memory.get_context(include_metadata=True)
            
            # Step 2: Check for similar questions
            similar_qa = []
            if self.config.validation.check_similar_questions and not skip_similar_check:
                logger.info("[STEP 2] Checking for similar questions")
                similar_result = self._tool_check_similar_questions(
                    question,
                    threshold=self.config.vector_store.similarity_threshold
                )
                similar_qa = similar_result['similar_questions']
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
            logger.info("[STEP 3] Fetching relevant table metadata")
            tables_result = self._tool_get_relevant_tables(question, max_tables=5)
            relevant_tables = tables_result['tables']
            result['metadata']['relevant_tables'] = [t['table_name'] for t in relevant_tables]
            
            if not relevant_tables:
                result['response_type'] = ResponseType.ERROR
                result['data'] = {
                    'error': 'No relevant tables found for this question',
                    'type': 'metadata_error'
                }
                memory.add_message('assistant', "No relevant tables found")
                return result
            
            # Step 4: Combined validation and SQL generation
            logger.info("[STEP 4] Combined validation and SQL generation")
            logger.debug(f"[STEP 4] Question: {question}")
            logger.debug(f"[STEP 4] Relevant tables: {[t['table_name'] for t in relevant_tables]}")
            
            combined_result = self._tool_validate_and_generate_sql(
                question=question,
                relevant_tables=relevant_tables,
                conversation_history=conversation_history,
                similar_qa=similar_qa if similar_qa else None
            )
            
            # Check if validation failed
            if not combined_result['valid']:
                result['response_type'] = ResponseType.ERROR
                result['data'] = {
                    'error': combined_result['reason'],
                    'type': 'validation_error'
                }
                result['metadata']['validation'] = {
                    'valid': False,
                    'reason': combined_result['reason']
                }
                memory.add_message('assistant', f"Validation failed: {combined_result['reason']}")
                return result
            
            # Validation passed, extract SQL query
            logger.debug(f"[STEP 4] Combined result keys: {combined_result.keys()}")
            logger.debug(f"[STEP 4] Generated query: {combined_result.get('query', 'NO QUERY')}")
            
            result['metadata']['validation'] = {
                'valid': True,
                'reason': None
            }
            result['metadata']['query_generation'] = {
                'model_used': combined_result['model_used'],
                'attempts': combined_result['attempts'],
                'validation_passed': combined_result['validation_passed']
            }
            
            sql_query = combined_result['query']
            result['metadata']['sql_query'] = sql_query
            logger.info(f"[STEP 4] SQL query: {sql_query}")
            
            if not combined_result['validation_passed']:
                logger.error(f"[STEP 4] Query validation failed: {combined_result.get('validation_errors', [])}")
                result['response_type'] = ResponseType.ERROR
                result['data'] = {
                    'error': 'Generated query failed validation',
                    'validation_errors': combined_result['validation_errors'],
                    'sql_query': sql_query,
                    'type': 'query_validation_error'
                }
                memory.add_message('assistant', "Query generation failed validation")
                return result
            
            # Step 5: Execute query
            logger.info("[STEP 5] Executing SQL query")
            logger.debug(f"[STEP 5] About to execute: {sql_query}")
            
            execution_result = self._tool_execute_sql_query(sql_query)
            
            logger.debug(f"[STEP 5] Execution result keys: {execution_result.keys()}")
            logger.debug(f"[STEP 5] Success: {execution_result.get('success')}")
            logger.debug(f"[STEP 5] Row count: {execution_result.get('row_count', 0)}")
            logger.debug(f"[STEP 5] Columns: {execution_result.get('columns', [])}")
            
            result['metadata']['execution'] = {
                'success': execution_result['success'],
                'row_count': execution_result['row_count'],
                'execution_time': execution_result.get('execution_time', 0)
            }
            
            if not execution_result['success']:
                logger.error(f"[STEP 5] Execution failed: {execution_result.get('error', 'Unknown error')}")
                result['response_type'] = ResponseType.ERROR
                result['data'] = {
                    'error': execution_result.get('error', 'Query execution failed'),
                    'sql_query': sql_query,
                    'type': 'execution_error'
                }
                memory.add_message('assistant', f"Query execution failed: {execution_result.get('error')}")
                return result
            
            if execution_result.get('row_count', 0) == 0:
                logger.warning(f"[STEP 5] Query returned 0 rows")
            
            logger.info(f"[STEP 5] Query execution successful: {execution_result['row_count']} rows")
            
            # Step 6: Create visualization
            logger.info("[STEP 6] Creating visualization")
            if visualization_type is None:
                visualization_type = self.config.visualization.default_format
            
            visualization = self._tool_create_visualization(
                columns=execution_result['columns'],
                rows=execution_result['rows'],
                visualization_type=visualization_type,
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
                confidence = self._calculate_confidence(
                    result['metadata']['validation'], 
                    combined_result, 
                    execution_result,
                    user_feedback=None
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
    
    # ========================================================================
    # Feedback & Storage
    # ========================================================================
    
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
        In eval mode with user feedback: thumbs_up = (2 + llm_confidence) / 3
        
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
                # thumbs up = (2 + llm_confidence) / 3
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
    
    # ========================================================================
    # Tool Management API
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
    
    # ========================================================================
    # Session Management
    # ========================================================================
    
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
    
    # ========================================================================
    # Initialization & Cleanup
    # ========================================================================
    
    def initialize_metadata_index(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Initialize or refresh metadata index."""
        logger.info("Initializing metadata index")
        return self.metadata_manager.index_all_tables(force_refresh)
    
    def close(self):
        """Clean up resources."""
        self.query_executor.close()
        self.metadata_manager.close()
        logger.info("Agent closed")
