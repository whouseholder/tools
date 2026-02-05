"""SQL query generation and validation."""

import re
from typing import Any, Dict, List, Optional, Tuple

import sqlparse
from loguru import logger

from ..llm.llm_manager import LLMManager
from ..utils.config import QueryConfig


class QueryGenerator:
    """Generates SQL queries from natural language."""
    
    def __init__(self, llm_manager: LLMManager, config: QueryConfig):
        """Initialize query generator."""
        self.llm_manager = llm_manager
        self.config = config
        logger.info(f"Query generator initialized for {config.dialect}")
    
    def generate_query(
        self,
        question: str,
        relevant_tables: List[Dict[str, Any]],
        similar_qa: Optional[List[Dict[str, Any]]] = None,
        max_validation_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate SQL query from question and metadata with validation and self-correction.
        
        Args:
            question: Natural language question
            relevant_tables: Metadata about tables to query
            similar_qa: Optional similar Q&A pairs
            max_validation_retries: Maximum attempts to generate valid SQL (default: 3)
        
        Returns dict with 'query', 'model_used', 'attempts', and 'validation_passed'.
        """
        # Build comprehensive prompt
        prompt = self._build_query_prompt(question, relevant_tables, similar_qa)
        
        # System prompt with version info
        system_prompt = self._build_system_prompt()
        
        previous_query = None
        validation_errors = None
        
        # Retry loop for validation and self-correction
        for attempt in range(max_validation_retries):
            logger.info(f"Query generation attempt {attempt + 1}/{max_validation_retries}")
            
            try:
                # Build correction prompt if this is a retry
                if attempt > 0 and previous_query and validation_errors:
                    correction_prompt = self._build_correction_prompt(
                        question, prompt, previous_query, validation_errors
                    )
                    generation_prompt = correction_prompt
                else:
                    generation_prompt = prompt
                
                # Try generation with fallback
                result = self.llm_manager.generate_with_fallback(
                    prompt=generation_prompt,
                    system_prompt=system_prompt,
                    max_retries_per_model=self.config.max_retries_per_model
                )
                
                # Extract SQL and confidence from response
                query, llm_confidence = self._extract_sql_and_confidence(result['text'])
                
                # Validate syntax
                is_valid, validation_errors = self._validate_syntax(query)
                
                if is_valid:
                    logger.info(f"✅ Valid SQL generated on attempt {attempt + 1}")
                    return {
                        'query': query,
                        'model_used': result['model_used'],
                        'attempts': result['attempts'],
                        'validation_passed': True,
                        'validation_errors': None,
                        'llm_confidence': llm_confidence
                    }
                else:
                    logger.warning(f"❌ Validation failed on attempt {attempt + 1}: {validation_errors}")
                    previous_query = query
                    
                    # If this is the last attempt, return with validation failure
                    if attempt == max_validation_retries - 1:
                        logger.error(f"Failed to generate valid SQL after {max_validation_retries} attempts")
                        return {
                            'query': query,
                            'model_used': result['model_used'],
                            'attempts': result['attempts'],
                            'validation_passed': False,
                            'validation_errors': validation_errors,
                            'llm_confidence': llm_confidence
                        }
                    
            except Exception as e:
                logger.error(f"Query generation attempt {attempt + 1} failed: {e}")
                if attempt == max_validation_retries - 1:
                    raise
                # Continue to next attempt
        
        # Should not reach here, but just in case
        raise Exception("Query generation failed after all retries")
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with version and dialect info."""
        return f"""You are an expert SQL query generator specializing in {self.config.dialect.upper()}.

Your task is to generate syntactically correct {self.config.dialect.upper()} queries based on natural language questions.

IMPORTANT RULES:
1. Generate the SQL query followed by your confidence score
2. Use the exact table and column names provided
3. Follow {self.config.dialect.upper()} syntax strictly
4. Include appropriate JOINs, WHERE clauses, and aggregations as needed
5. Consider performance implications (use appropriate indexes, limit results)

RESPONSE FORMAT:
First line: The SQL query (starting with SELECT, INSERT, UPDATE, or DELETE)
Second line: CONFIDENCE: <score between 0.0 and 1.0>

Version: {self.config.dialect.upper()} (assume latest stable version)
"""
    
    def _build_query_prompt(
        self,
        question: str,
        relevant_tables: List[Dict[str, Any]],
        similar_qa: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build comprehensive prompt for query generation."""
        prompt_parts = [
            f"Question: {question}",
            "",
            "Available Tables and Columns:",
        ]
        
        # Add table metadata
        for table in relevant_tables:
            prompt_parts.append(f"\nTable: {table['table_name']}")
            if table.get('description'):
                prompt_parts.append(f"Description: {table['description']}")
            
            prompt_parts.append("Columns:")
            for col in table.get('columns', []):
                col_info = f"  - {col['name']} ({col['type']})"
                if col.get('description'):
                    col_info += f": {col['description']}"
                prompt_parts.append(col_info)
        
        # Add similar Q&A examples if available
        if similar_qa:
            prompt_parts.append("\nSimilar Questions and Their SQL Queries (for reference):")
            for i, qa in enumerate(similar_qa[:3], 1):  # Limit to top 3
                prompt_parts.append(f"\nExample {i}:")
                prompt_parts.append(f"Question: {qa['question']}")
                prompt_parts.append(f"SQL: {qa['metadata']['sql_query']}")
        
        prompt_parts.append("\nGenerate the SQL query for the given question:")
        
        return "\n".join(prompt_parts)
    
    def _extract_sql_and_confidence(self, text: str) -> tuple:
        """Extract SQL query and confidence score from LLM response."""
        # Remove markdown code blocks if present
        text = re.sub(r'```sql\n?', '', text)
        text = re.sub(r'```\n?', '', text)
        
        # Look for confidence score
        confidence = 0.8  # Default if not found
        confidence_pattern = r'CONFIDENCE:\s*([0-9]*\.?[0-9]+)'
        confidence_match = re.search(confidence_pattern, text, re.IGNORECASE)
        
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
                confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
                # Remove confidence line from text
                text = re.sub(confidence_pattern, '', text, flags=re.IGNORECASE)
            except ValueError:
                logger.warning("Could not parse confidence score, using default 0.8")
        
        # Remove common prefixes
        text = re.sub(r'^(SQL Query:|Query:|Answer:)\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Find SQL query (starts with SELECT, INSERT, UPDATE, DELETE, WITH)
        sql_pattern = r'((?:WITH|SELECT|INSERT|UPDATE|DELETE)\s+.+?)(?:\n\n|CONFIDENCE|\Z)'
        match = re.search(sql_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            query = match.group(1).strip()
        else:
            query = text.strip()
        
        # Remove trailing semicolons and whitespace
        query = query.rstrip(';').strip()
        
        logger.debug(f"Extracted SQL query: {query[:100]}... (confidence: {confidence})")
        return query, confidence
    
    def _extract_sql(self, text: str) -> str:
        """Extract SQL query from LLM response (legacy method)."""
        query, _ = self._extract_sql_and_confidence(text)
        return query
    
    def _validate_syntax(self, query: str) -> Tuple[bool, Optional[List[str]]]:
        """Validate SQL syntax with comprehensive checks."""
        if not self.config.syntax_check_enabled:
            return True, None
        
        errors = []
        query_stripped = query.strip()
        
        # Empty query check
        if not query_stripped:
            errors.append("Query is empty")
            return False, errors
        
        try:
            # Parse the query
            parsed = sqlparse.parse(query)
            
            if not parsed:
                errors.append("Query could not be parsed")
                return False, errors
            
            # Check for common issues
            query_upper = query_stripped.upper()
            
            # Must start with valid SQL command
            valid_starts = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']
            if not any(query_upper.startswith(cmd) for cmd in valid_starts):
                errors.append("Query must start with SELECT, INSERT, UPDATE, DELETE, or WITH")
            
            # Check for SELECT queries specifically
            if query_upper.startswith('SELECT'):
                # Must have FROM clause for SELECT
                if 'FROM' not in query_upper:
                    errors.append("SELECT query missing FROM clause")
                
                # Check for incomplete queries (ends with SQL keywords)
                incomplete_endings = [
                    'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 
                    'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN',
                    'ON', 'AND', 'OR', 'AS', ','
                ]
                for ending in incomplete_endings:
                    if query_upper.rstrip().endswith(ending):
                        errors.append(f"Query appears incomplete - ends with '{ending}'")
                        break
            
            # Check for balanced parentheses
            if query.count('(') != query.count(')'):
                errors.append("Unbalanced parentheses")
            
            # Check for unclosed quotes
            single_quotes = query.count("'") - query.count("\\'")
            if single_quotes % 2 != 0:
                errors.append("Unclosed single quotes")
            
            double_quotes = query.count('"') - query.count('\\"')
            if double_quotes % 2 != 0:
                errors.append("Unclosed double quotes")
            
            # Format check with sqlparse
            try:
                formatted = sqlparse.format(
                    query,
                    reindent=True,
                    keyword_case='upper'
                )
            except Exception as e:
                errors.append(f"Formatting error: {str(e)}")
            
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")
        
        is_valid = len(errors) == 0
        logger.debug(f"Query validation: {'passed' if is_valid else 'failed'}")
        if not is_valid:
            logger.warning(f"Validation errors: {errors}")
        
        return is_valid, errors if not is_valid else None
    
    def _build_correction_prompt(
        self,
        question: str,
        original_prompt: str,
        previous_query: str,
        validation_errors: List[str]
    ) -> str:
        """Build prompt for LLM to correct a failed query."""
        error_list = '\n'.join(f'- {error}' for error in validation_errors)
        
        return f"""{original_prompt}

IMPORTANT: Your previous attempt generated an INVALID query with the following errors:

Previous Query:
{previous_query}

Validation Errors:
{error_list}

Please generate a CORRECTED query that fixes these specific errors. Make sure:
1. The query is COMPLETE (no missing clauses)
2. All parentheses and quotes are balanced
3. SELECT queries include FROM clause
4. The query does not end with a keyword or comma

Return ONLY the corrected SQL query and confidence score."""
    
    def _fix_query(
        self,
        query: str,
        errors: List[str],
        model_size: str
    ) -> Optional[str]:
        """Attempt to fix query syntax errors."""
        logger.info(f"Attempting to fix query using {model_size} model")
        
        fix_prompt = f"""The following SQL query has syntax errors:

Query:
{query}

Errors:
{chr(10).join(f'- {error}' for error in errors)}

Please fix the query and return ONLY the corrected SQL query, nothing else."""
        
        system_prompt = f"You are a {self.config.dialect.upper()} SQL expert. Fix syntax errors in queries."
        
        try:
            # Use the same model that generated the query
            use_large = (model_size == 'large')
            fixed_text = self.llm_manager.generate(
                prompt=fix_prompt,
                system_prompt=system_prompt,
                use_large_model=use_large
            )
            
            fixed_query = self._extract_sql(fixed_text)
            logger.info("Query fix attempted")
            return fixed_query
            
        except Exception as e:
            logger.error(f"Query fix failed: {e}")
            return None
