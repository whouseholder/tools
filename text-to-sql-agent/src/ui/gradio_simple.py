"""
Simple launcher for Gradio UI - Works without full dependencies.

This version works with minimal dependencies for local testing.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Check API key first
if not os.environ.get("OPENAI_API_KEY"):
    print("=" * 60)
    print("ERROR: OPENAI_API_KEY not set")
    print("=" * 60)
    print()
    print("Please set your OpenAI API key:")
    print('  export OPENAI_API_KEY="sk-your-key-here"')
    print()
    print("Get your key at: https://platform.openai.com/api-keys")
    print()
    sys.exit(1)

# Check dependencies
try:
    import gradio as gr
    import pandas as pd
    import plotly.express as px
    from openai import OpenAI
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("\nInstall with:")
    print("  pip install gradio pandas plotly openai")
    sys.exit(1)

print("=" * 60)
print("Text-to-SQL Agent - Gradio UI (Lite)")
print("=" * 60)
print()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Database connection
DB_PATH = "data/telco_sample.db"

# Check database exists
if not Path(DB_PATH).exists():
    print(f"Database not found: {DB_PATH}")
    print("\nCreate it with:")
    print("  python scripts/create_telco_db.py")
    sys.exit(1)

print(f"✓ Database found: {DB_PATH}")
print(f"✓ OpenAI API key set")
print()

# Global state for memory and session
import uuid
from datetime import datetime

session_id = str(uuid.uuid4())
user_id = "local_user"  # Can be customized
conversation_history = []
last_query = {"sql": None, "data": None, "columns": None, "sql_display": None, "question": None, "timestamp": None}


def validate_sql_syntax(sql: str) -> tuple:
    """Validate SQL syntax and check for common errors.
    
    Returns: (is_valid, error_message)
    """
    if not sql or not sql.strip():
        return False, "Empty SQL query"
    
    sql_upper = sql.upper()
    
    # Check for SELECT statement
    if not sql_upper.startswith('SELECT'):
        return False, "Query must start with SELECT"
    
    # Check for FROM clause (required for SELECT)
    if 'FROM' not in sql_upper:
        return False, "Missing FROM clause - query is incomplete"
    
    # Check for unclosed quotes
    single_quotes = sql.count("'")
    double_quotes = sql.count('"')
    if single_quotes % 2 != 0:
        return False, "Unclosed single quote in query"
    if double_quotes % 2 != 0:
        return False, "Unclosed double quote in query"
    
    # Check for balanced parentheses
    open_paren = sql.count('(')
    close_paren = sql.count(')')
    if open_paren != close_paren:
        return False, f"Unbalanced parentheses: {open_paren} open, {close_paren} close"
    
    # Check for common incomplete patterns
    if sql_upper.rstrip().endswith(('SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'AND', 'OR', ',')):
        return False, "Query appears incomplete - ends with keyword or comma"
    
    # Try to parse with sqlparse if available
    try:
        import sqlparse
        parsed = sqlparse.parse(sql)
        if not parsed:
            return False, "Failed to parse SQL query"
        
        # Check if parsed query is valid
        stmt = parsed[0]
        if not stmt.tokens:
            return False, "Empty or invalid SQL statement"
            
    except ImportError:
        # sqlparse not available, basic checks are still valuable
        pass
    except Exception as e:
        return False, f"SQL parsing error: {str(e)}"
    
    return True, None


def generate_sql_with_retry(question: str, db_schema: str, max_retries: int = 3, auto_viz_enabled: bool = False) -> tuple:
    """Generate SQL query with validation and self-correction.
    
    Returns: (sql, confidence, error, viz_recommendation)
    """
    
    for attempt in range(max_retries):
        print(f"🔄 Attempt {attempt + 1}/{max_retries} to generate SQL", file=sys.stderr)
        
        # Generate SQL
        if attempt == 0:
            # First attempt - standard prompt
            sql, confidence, error, viz_rec = generate_sql(question, db_schema, auto_viz_enabled)
        else:
            # Retry with error feedback
            sql, confidence, error = generate_sql_with_correction(
                question, db_schema, previous_sql, validation_error
            )
            viz_rec = None  # Don't regenerate viz on retries
        
        if error:
            print(f"❌ LLM error: {error}", file=sys.stderr)
            if attempt == max_retries - 1:
                return None, 0.0, f"Failed to generate SQL after {max_retries} attempts: {error}", None
            continue
        
        # Clean up SQL
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        # Validate syntax
        is_valid, validation_error = validate_sql_syntax(sql)
        
        if is_valid:
            print(f"✅ Valid SQL generated on attempt {attempt + 1}", file=sys.stderr)
            return sql, confidence, None, viz_rec
        else:
            print(f"❌ Validation failed: {validation_error}", file=sys.stderr)
            previous_sql = sql
            
            if attempt == max_retries - 1:
                return None, 0.0, f"SQL validation failed after {max_retries} attempts: {validation_error}", None
    
    return None, 0.0, "Failed to generate valid SQL", None


def generate_sql_with_correction(question: str, db_schema: str, previous_sql: str, error: str) -> tuple:
    """Generate SQL with correction feedback from previous attempt."""
    prompt = f"""Given this database schema:

{db_schema}

Generate a SQLite query for this question: {question}

PREVIOUS ATTEMPT FAILED with this error: {error}

Previous SQL: {previous_sql}

Fix the error and return a COMPLETE, VALID SQLite query.

Return ONLY the SQL query on the first line, then on a new line: CONFIDENCE: <0.0-1.0>

Example:
SELECT * FROM customers LIMIT 10
CONFIDENCE: 0.95"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert SQL query generator. Fix the SQL error and generate a complete, valid SQLite query."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract SQL and confidence
        lines = content.split('\n')
        sql = lines[0].strip().rstrip(';')
        
        confidence = 0.8
        for line in lines[1:]:
            if 'CONFIDENCE' in line.upper():
                try:
                    confidence = float(line.split(':')[1].strip())
                except:
                    pass
        
        return sql, confidence, None
        
    except Exception as e:
        return None, 0.0, str(e)


def generate_sql(question: str, db_schema: str, auto_viz_enabled: bool = False) -> tuple:
    """Generate SQL query using OpenAI (base function for first attempt).
    
    Returns: (sql, confidence, error, viz_recommendation)
    """
    # Build system message
    system_msg = "You are an expert SQL query generator. Generate only valid SQLite queries. Always respond with valid JSON."
    
    # Base prompt for SQL generation
    prompt = f"""Given this database schema:

{db_schema}

Generate a SQLite query for this question: {question}

Return a JSON object with the following structure:"""

    # Define JSON structure based on auto_viz setting
    if auto_viz_enabled:
        prompt += """
{
  "sql": "the complete SQL query on a single line",
  "confidence": 0.95,
  "viz_recommendations": [
    {
      "chart_type": "bar",
      "x_column": "column_name",
      "y_column": "column_name",
      "title": "descriptive title"
    }
  ]
}

Provide 3 visualization recommendations in the array, ordered by relevance."""
    else:
        prompt += """
{
  "sql": "the complete SQL query on a single line",
  "confidence": 0.95
}"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        print(f"🤖 LLM Response:\n{content}", file=sys.stderr)
        
        # Parse JSON response
        import json
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}", file=sys.stderr)
            return None, 0.0, f"Invalid JSON response from LLM: {e}", None
        
        # Extract SQL
        sql = data.get('sql', '').strip().rstrip(';')
        if not sql:
            return None, 0.0, "No SQL query in response", None
        
        print(f"📝 Extracted SQL: {sql}", file=sys.stderr)
        
        # Extract confidence
        confidence = float(data.get('confidence', 0.8))
        
        # Extract viz recommendation (first one if available)
        viz_recommendation = None
        if auto_viz_enabled and 'viz_recommendations' in data:
            recs = data['viz_recommendations']
            if recs and len(recs) > 0:
                first_rec = recs[0]
                viz_recommendation = {
                    'chart_type': first_rec.get('chart_type', 'bar'),
                    'x_column': first_rec.get('x_column', ''),
                    'y_column': first_rec.get('y_column', ''),
                    'title': first_rec.get('title', 'Data Visualization')
                }
                print(f"📊 LLM recommended viz: {viz_recommendation['chart_type']} - {viz_recommendation['title']}", file=sys.stderr)
        
        return sql, confidence, None, viz_recommendation
        
    except Exception as e:
        return None, 0.0, str(e), None


def execute_query(sql: str) -> tuple:
    """Execute SQL query against SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        conn.close()
        
        return rows, columns, None
        
    except Exception as e:
        return None, None, str(e)


def get_schema() -> str:
    """Get database schema as hierarchical markdown with 2-column layout."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Build schema for each table
        table_schemas = []
        
        for table in tables:
            # Get table info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            
            # Build column list
            col_list = []
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_pk = " 🔑" if col[5] else ""
                col_list.append(f"<li><strong>{col_name}</strong> <code>{col_type}</code>{is_pk}</li>")
            
            # Create table card
            table_html = f"""
<div class="schema-table">
    <h4>📊 {table}</h4>
    <p class="row-count">{row_count:,} rows</p>
    <ul class="column-list">
        {''.join(col_list)}
    </ul>
</div>"""
            table_schemas.append(table_html)
        
        conn.close()
        
        # Split tables into 2 columns
        mid = (len(table_schemas) + 1) // 2
        col1_tables = table_schemas[:mid]
        col2_tables = table_schemas[mid:]
        
        # Build 2-column layout with DARK THEME
        schema_html = f"""
<style>
.schema-container {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    font-size: 13px;
}}
.schema-table {{
    background: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
}}
.schema-table h4 {{
    margin: 0 0 8px 0;
    color: #e2e8f0;
    font-size: 15px;
    font-weight: 600;
}}
.row-count {{
    margin: 0 0 10px 0;
    color: #a0aec0;
    font-size: 12px;
    font-style: italic;
}}
.column-list {{
    list-style: none;
    padding: 0;
    margin: 0;
}}
.column-list li {{
    padding: 4px 0;
    border-bottom: 1px solid #2d3748;
    color: #cbd5e0;
}}
.column-list li:last-child {{
    border-bottom: none;
}}
.column-list strong {{
    color: #e2e8f0;
    font-weight: 600;
}}
.column-list code {{
    background: #2d3748;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    color: #90cdf4;
    border: 1px solid #4a5568;
}}
@media (max-width: 768px) {{
    .schema-container {{
        grid-template-columns: 1fr;
    }}
}}
</style>

<div class="schema-container">
    <div class="schema-column-1">
        {''.join(col1_tables)}
    </div>
    <div class="schema-column-2">
        {''.join(col2_tables)}
    </div>
</div>"""
        
        return schema_html
        
    except Exception as e:
        return f"<p style='color:red;'>Error getting schema: {e}</p>"


# Get schema once
SCHEMA = get_schema()


def process_question(question, history, auto_viz_enabled):
    """Process user question with follow-up support."""
    global last_query
    
    if not question.strip():
        return history if history else [], last_query.get("sql_display", ""), SCHEMA, None
    
    # Ensure history is a list
    if history is None:
        history = []
    
    # Check for visualization follow-up requests
    viz_keywords = ['chart', 'graph', 'plot', 'visualize', 'show that', 'display that', 'bar chart', 'pie chart', 'line chart', 'scatter']
    is_viz_request = any(keyword in question.lower() for keyword in viz_keywords)
    
    if is_viz_request and last_query["data"] and last_query["columns"]:
        # This is a follow-up visualization request - use cached data OR generate new query
        print("🎨 Detected visualization follow-up request", file=sys.stderr)
        
        rows = last_query["data"]
        columns = last_query["columns"]
        df = pd.DataFrame(rows, columns=columns)
        
        print(f"📊 Available columns in cached data: {', '.join(columns)}", file=sys.stderr)
        
        # Use LLM to interpret the visualization request
        viz_prompt = f"""The user previously ran a query with these columns: {', '.join(columns)}

User's visualization request: "{question}"

Analyze the request and return JSON:
{{
  "needs_new_query": true/false,
  "reason": "explanation if new query needed",
  "chart_type": "bar|pie|line|scatter",
  "x_column": "column name",
  "y_column": "column name",
  "title": "descriptive title"
}}

Set "needs_new_query" to true if:
- The user requests columns not in the available columns
- The user asks for different data than what's currently available

Set "needs_new_query" to false if:
- The user just wants a different chart type of the same data
- The requested columns are available"""

        try:
            viz_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data visualization expert. Parse user requests and return valid JSON."},
                    {"role": "user", "content": viz_prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            viz_content = viz_response.choices[0].message.content.strip()
            print(f"🤖 LLM viz interpretation: {viz_content}", file=sys.stderr)
            
            import json
            viz_spec = json.loads(viz_content)
            
            # Check if we need a new query
            if viz_spec.get('needs_new_query', False):
                print(f"🔄 New query needed: {viz_spec.get('reason', 'columns not available')}", file=sys.stderr)
                
                # Get original context
                original_sql = last_query.get("sql", "")
                original_question = history[-2]["content"] if len(history) >= 2 and history[-2]["role"] == "user" else ""
                
                print(f"📝 Original question: {original_question}", file=sys.stderr)
                print(f"📝 Original SQL: {original_sql}", file=sys.stderr)
                
                # Generate modified SQL query that maintains original context
                new_sql_prompt = f"""Given this database schema:

{SCHEMA}

CONTEXT:
- Original question: "{original_question}"
- Original SQL query: {original_sql}
- User now wants to visualize: "{question}"

The user wants to add these columns to the visualization: {viz_spec.get('x_column')} and {viz_spec.get('y_column')}

IMPORTANT: 
- Keep the same filtering, sorting, and LIMIT from the original query
- Add the requested columns to the SELECT clause
- Maintain the same WHERE conditions and ORDER BY
- Do NOT completely rewrite the query - modify the original

Return JSON:
{{
  "sql": "modified SQL query with added columns",
  "confidence": 0.95
}}"""
                
                new_sql_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert SQL query modifier. Modify existing queries to add columns while preserving the original logic. Always respond with valid JSON."},
                        {"role": "user", "content": new_sql_prompt}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                
                new_sql_content = new_sql_response.choices[0].message.content.strip()
                print(f"🤖 Modified SQL generated: {new_sql_content}", file=sys.stderr)
                
                new_sql_data = json.loads(new_sql_content)
                new_sql = new_sql_data.get('sql', '').strip().rstrip(';')
                
                if new_sql:
                    # Validate and execute new query
                    is_valid, validation_error = validate_sql_syntax(new_sql)
                    if is_valid:
                        rows, columns, exec_error = execute_query(new_sql)
                        if not exec_error and rows and columns:
                            print(f"✅ New query executed: {len(rows)} rows, columns: {', '.join(columns)}", file=sys.stderr)
                            df = pd.DataFrame(rows, columns=columns)
                            
                            # Create new SQL display
                            new_confidence = new_sql_data.get('confidence', 0.9)
                            new_sql_display = f"**Confidence:** {new_confidence:.2f}\n\n```sql\n{new_sql}\n```"
                            
                            # Update cache with new data AND SQL display
                            last_query["sql"] = new_sql
                            last_query["data"] = rows
                            last_query["columns"] = columns
                            last_query["sql_display"] = new_sql_display
                            last_query["question"] = question
                            last_query["timestamp"] = datetime.now().isoformat()
                        else:
                            print(f"❌ New query failed: {exec_error}", file=sys.stderr)
                            new_history = history + [
                                {"role": "user", "content": question},
                                {"role": "assistant", "content": f"❌ Failed to execute new query for visualization: {exec_error}"}
                            ]
                            return new_history, last_query.get("sql_display", ""), SCHEMA, None
                    else:
                        print(f"❌ New query validation failed: {validation_error}", file=sys.stderr)
            
            chart_type = viz_spec.get('chart_type', 'bar')
            x_col = viz_spec.get('x_column', columns[0] if columns else None)
            y_col = viz_spec.get('y_column', columns[-1] if len(columns) > 1 else columns[0] if columns else None)
            title = viz_spec.get('title', f"{y_col} by {x_col}" if x_col and y_col else "Visualization")
            
            # Validate columns exist in (possibly new) dataframe
            if x_col not in df.columns:
                print(f"⚠️ x_column '{x_col}' not found in data", file=sys.stderr)
                x_col = df.columns[0] if len(df.columns) > 0 else None
            if y_col not in df.columns:
                print(f"⚠️ y_column '{y_col}' not found in data", file=sys.stderr)
                y_col = df.columns[-1] if len(df.columns) > 1 else df.columns[0] if len(df.columns) > 0 else None
            
            if not x_col or not y_col:
                new_history = history + [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": "❌ Unable to create visualization: insufficient columns in data."}
                ]
                return new_history, last_query.get("sql_display", ""), SCHEMA, None
            
            print(f"📈 Chart: {chart_type} - {title} ({y_col} by {x_col})", file=sys.stderr)
            
        except Exception as e:
            print(f"⚠️ Failed to parse viz request with LLM, using defaults: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            chart_type = "bar"
            x_col = columns[0] if columns else None
            y_col = columns[-1] if len(columns) > 1 else columns[0] if columns else None
            title = f"{y_col} by {x_col}" if x_col and y_col else "Visualization"
        
        # Create visualization using Plotly
        viz_fig = None
        try:
            print(f"🎨 Creating {chart_type} chart with x={x_col}, y={y_col}", file=sys.stderr)
            print(f"🎨 Sample data - {x_col}: {df[x_col].head(3).tolist()}", file=sys.stderr)
            print(f"🎨 Sample data - {y_col}: {df[y_col].head(3).tolist()}", file=sys.stderr)
            
            if chart_type == "bar" and len(columns) >= 2:
                viz_fig = px.bar(df.head(20), x=x_col, y=y_col, title=title)
            elif chart_type == "pie" and len(columns) >= 2:
                viz_fig = px.pie(df.head(20), names=x_col, values=y_col, title=title)
            elif chart_type == "line" and len(columns) >= 2:
                viz_fig = px.line(df, x=x_col, y=y_col, title=title)
            elif chart_type == "scatter" and len(columns) >= 2:
                viz_fig = px.scatter(df, x=x_col, y=y_col, title=title)
            
            if viz_fig:
                print(f"✅ Generated {chart_type} chart: {title}", file=sys.stderr)
                # Verify what's actually in the figure
                if hasattr(viz_fig, 'data') and len(viz_fig.data) > 0:
                    trace = viz_fig.data[0]
                    print(f"🔍 Chart trace x: {getattr(trace, 'x', 'N/A')[:3] if hasattr(trace, 'x') else 'N/A'}", file=sys.stderr)
                    print(f"🔍 Chart trace y: {getattr(trace, 'y', 'N/A')[:3] if hasattr(trace, 'y') else 'N/A'}", file=sys.stderr)
            else:
                print("⚠️ Not enough columns for visualization", file=sys.stderr)
                
        except Exception as e:
            print(f"❌ Chart creation error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
        
        response = f"""✅ **Visualization Created**

Created **{chart_type} chart**: {title}

Using columns: **{y_col}** by **{x_col}**

Check the **Visualization panel** on the right →"""
        
        new_history = history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": response}
        ]
        
        # Return the updated SQL display (which may have been modified if new query was run)
        sql_display = last_query.get("sql_display", "")
        
        return new_history, sql_display, SCHEMA, viz_fig
    
    # Not a follow-up - generate new SQL query with validation and retry
    sql, confidence, error, viz_rec = generate_sql_with_retry(question, SCHEMA, max_retries=3, auto_viz_enabled=auto_viz_enabled)
    
    if error:
        # Show error in chat after all retries failed
        new_history = history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f"❌ **Failed to generate valid SQL**\n\n{error}\n\nThe agent attempted 3 times but could not create a valid query. Please try rephrasing your question."}
        ]
        return new_history, "", SCHEMA, None
    
    # Execute query
    rows, columns, exec_error = execute_query(sql)
    
    if exec_error:
        # Show SQL with error in chat
        sql_display = f"**Confidence:** {confidence:.2f}\n\n```sql\n{sql}\n```"
        new_history = history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f"❌ **Error executing query**\n\n{exec_error}"}
        ]
        return new_history, sql_display, SCHEMA, None
    
    # Create SQL display for the accordion
    sql_display = f"**Confidence:** {confidence:.2f}\n\n```sql\n{sql}\n```"
    
    # Store last query for follow-ups (including SQL display, question, timestamp)
    last_query = {
        "sql": sql, 
        "data": rows, 
        "columns": columns, 
        "sql_display": sql_display,
        "question": question,
        "timestamp": datetime.now().isoformat()
    }
    
    # Create data table HTML for chat
    if rows and columns:
        df = pd.DataFrame(rows, columns=columns)
        
        # Create a compact, styled HTML table
        display_df = df.head(20)
        
        # Build clean HTML table manually for better control
        table_rows = []
        
        # Header row
        header_cells = ''.join([f'<th>{col}</th>' for col in columns])
        table_rows.append(f'<tr>{header_cells}</tr>')
        
        # Data rows
        for _, row in display_df.iterrows():
            cells = ''.join([f'<td>{val}</td>' for val in row])
            table_rows.append(f'<tr>{cells}</tr>')
        
        table_html = f"""<div style="overflow-x:auto;margin:10px 0;">
<table class="results-table">
{''.join(table_rows)}
</table>
</div>"""
        
        # Compact styling
        styled_table = f"""<style>
.results-table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
}}
.results-table th {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    border: none;
}}
.results-table td {{
    padding: 8px 12px;
    border-bottom: 1px solid #e2e8f0;
}}
.results-table tr:hover {{
    background-color: #f7fafc;
}}
.results-table tr:last-child td {{
    border-bottom: 2px solid #667eea;
}}
</style>
{table_html}"""
        
        row_msg = f"Showing {min(20, len(rows))} of {len(rows)} rows" if len(rows) > 20 else f"{len(rows)} rows"
        
        # Response with the actual data table
        response = f"""✅ **Query Results** • *{row_msg}*

{styled_table}

💡 *Try: "show as bar chart" · "make it a pie chart" · "plot as line graph"*"""
        
        # Create automatic visualization if enabled using LLM recommendation
        viz_fig = None
        if auto_viz_enabled and len(columns) >= 2 and len(rows) > 0:
            try:
                # Use LLM recommendation if available, otherwise fallback to default
                if viz_rec and viz_rec.get('x_column') and viz_rec.get('y_column'):
                    chart_type = viz_rec['chart_type'].lower()
                    x_col = viz_rec['x_column']
                    y_col = viz_rec['y_column']
                    title = viz_rec['title']
                    
                    # Verify columns exist in results
                    if x_col not in columns or y_col not in columns:
                        print(f"⚠️ LLM recommended columns not in results, using fallback", file=sys.stderr)
                        x_col = columns[0]
                        y_col = columns[-1]
                        title = f"{y_col} by {x_col}"
                        chart_type = 'bar'
                else:
                    # Fallback to default
                    x_col = columns[0]
                    y_col = columns[-1]
                    title = f"{y_col} by {x_col}"
                    chart_type = 'bar'
                    print(f"⚠️ No LLM viz recommendation, using default", file=sys.stderr)
                
                # Create the chart based on type
                if chart_type == 'bar':
                    viz_fig = px.bar(df.head(20), x=x_col, y=y_col, title=title)
                elif chart_type == 'pie':
                    viz_fig = px.pie(df.head(20), names=x_col, values=y_col, title=title)
                elif chart_type == 'line':
                    viz_fig = px.line(df, x=x_col, y=y_col, title=title)
                elif chart_type == 'scatter':
                    viz_fig = px.scatter(df, x=x_col, y=y_col, title=title)
                else:
                    viz_fig = px.bar(df.head(20), x=x_col, y=y_col, title=title)
                
                print(f"✅ Auto-generated {chart_type} chart: {title}", file=sys.stderr)
                
                # Add explanation to response
                response += f"\n\n📊 *Auto-generated visualization: **{title}** ({chart_type} chart)*"
            except Exception as e:
                print(f"⚠️ Auto-visualization error: {e}", file=sys.stderr)
    else:
        response = "✅ **Query executed successfully**\n\nNo data returned."
        viz_fig = None
    
    new_history = history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": response}
    ]
    
    return new_history, sql_display, SCHEMA, viz_fig


def clear_chat():
    """Clear chat history and reset conversation."""
    global last_query, conversation_history, session_id
    
    # Generate new session ID
    session_id = str(uuid.uuid4())
    
    # Clear memory
    conversation_history = []
    last_query = {"sql": None, "data": None, "columns": None, "sql_display": None, "question": None, "timestamp": None}
    
    print(f"🔄 Conversation reset - New session: {session_id[:8]}", file=sys.stderr)
    
    return [], "", SCHEMA, None


def export_data():
    """Export last result as CSV."""
    global last_query
    
    if not last_query["data"] or not last_query["columns"]:
        return None
    
    df = pd.DataFrame(last_query["data"], columns=last_query["columns"])
    csv_path = "exported_data.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


# Create Gradio interface
with gr.Blocks(title="Text-to-SQL Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"""
    # 🤖 Text-to-SQL Agent (Lite)
    
    Ask questions in natural language and get SQL queries with results!
    
    *Session: `{session_id[:8]}...` • User: `{user_id}`*
    """)
    
    with gr.Row():
        # Left column - Chat Interface
        with gr.Column(scale=6):
            with gr.Row():
                gr.Markdown("### 💬 Chat Interface")
                reset_btn = gr.Button("🔄 Reset Conversation", size="sm", scale=0)
            
            chatbot = gr.Chatbot(
                label="Conversation", 
                height=600
            )
            
            question_input = gr.Textbox(
                label="Your Question",
                placeholder="e.g., What are the top 10 customers by lifetime value?",
                lines=2
            )
            
            with gr.Row():
                submit_btn = gr.Button("🔍 Submit", variant="primary")
                clear_btn = gr.Button("🗑️ Clear")
            
            # Auto-viz checkbox
            auto_viz_checkbox = gr.Checkbox(
                label="Auto-Viz: Automatically generate visualizations for query results",
                value=False,
                info="When enabled, charts are created automatically. When disabled, only create charts when explicitly requested."
            )
            
            # Generated SQL section
            with gr.Accordion("📝 Generated SQL & Confidence", open=False):
                sql_output = gr.Markdown(label="SQL Query & Confidence")
            
            # Example questions below SQL
            with gr.Accordion("ℹ️ Example Questions & Follow-ups", open=False):
                gr.Markdown("""
                **Initial Questions:**
                - What are the top 10 customers by lifetime value?
                - Show total revenue by service plan
                - Which device manufacturers are most popular? Show top 5
                - List customers with high churn risk (above 0.7) and their plan types
                - What is average data usage by plan type?
                - Show total transaction amounts by type
                - Which cities have the most active customers? Show top 10
                - What is average lifetime value by plan type?
                - How many customers made international calls last month?
                - Show monthly revenue trend for last 6 months
                
                **Follow-up Visualization Requests:**
                - "Show that as a bar chart"
                - "Make it a pie chart"
                - "Visualize as a line graph"
                - "Plot as horizontal bar chart"
                
                💡 *After any query, ask for different visualizations without re-querying the database!*
                """)
        
        # Right column - Visualization & Schema
        with gr.Column(scale=4):
            gr.Markdown("### 📈 Visualization")
            viz_output = gr.Plot(
                label="Chart"
            )
            
            export_btn = gr.Button("💾 Export Results as CSV", size="sm")
            export_file = gr.File(label="Download")
            
            gr.Markdown("### 🗄️ Database Schema")
            
            # Show database metadata in 2-column layout
            data_viewer = gr.HTML(
                value=SCHEMA,
                label="Tables & Columns"
            )
    
    # Event handlers
    def submit_and_clear_input(question, history, auto_viz):
        """Process question and clear input."""
        print(f"\n🔄 Processing: {question}", file=sys.stderr)
        print(f"   Auto-viz enabled: {auto_viz}", file=sys.stderr)
        
        new_history, sql, schema, viz = process_question(question, history, auto_viz)
        
        print(f"📤 Returning to UI:", file=sys.stderr)
        print(f"   - History: {len(new_history)} messages", file=sys.stderr)
        print(f"   - SQL: {len(sql)} chars", file=sys.stderr)
        print(f"   - Schema: {len(schema)} chars", file=sys.stderr)
        
        # Check viz type (now a Figure object, not HTML string)
        if viz is not None:
            viz_type = type(viz).__name__
            print(f"   - Viz: {viz_type} object", file=sys.stderr)
            print(f"   ✅ VIZ FIGURE PRESENT - should update viz_output", file=sys.stderr)
        else:
            print(f"   ⚠️  VIZ IS NONE", file=sys.stderr)
        
        return new_history, sql, schema, viz, ""  # Clear input
    
    submit_btn.click(
        submit_and_clear_input,
        inputs=[question_input, chatbot, auto_viz_checkbox],
        outputs=[chatbot, sql_output, data_viewer, viz_output, question_input]
    )
    
    question_input.submit(
        submit_and_clear_input,
        inputs=[question_input, chatbot, auto_viz_checkbox],
        outputs=[chatbot, sql_output, data_viewer, viz_output, question_input]
    )
    
    clear_btn.click(
        clear_chat,
        outputs=[chatbot, sql_output, data_viewer, viz_output]
    )
    
    reset_btn.click(
        clear_chat,
        outputs=[chatbot, sql_output, data_viewer, viz_output]
    )
    
    export_btn.click(export_data, outputs=export_file)


print("Launching Gradio UI...")
print("Open browser to: http://localhost:7860")
print()

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
