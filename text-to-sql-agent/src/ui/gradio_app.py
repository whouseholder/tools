"""
Gradio UI for Text-to-SQL Agent using full agent deployment.

This version uses the complete TextToSQLAgent with vector store and all features.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add parent directories to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
project_root = src_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

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
    from loguru import logger
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("\nInstall with:")
    print("  pip install gradio pandas plotly loguru")
    sys.exit(1)

# Import the full agent
try:
    from src.agent.agent import TextToSQLAgent
    from src.utils.config import load_config
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Full agent not available: {e}")
    print("Falling back to simple mode")
    AGENT_AVAILABLE = False

print("=" * 60)
print("Text-to-SQL Agent - Gradio UI (Full Agent)")
print("=" * 60)
print()

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

# Initialize the full agent
agent = None
if AGENT_AVAILABLE:
    try:
        config = load_config()
        agent = TextToSQLAgent(config)
        logger.info("✅ Full TextToSQLAgent initialized successfully")
        print("✓ Full agent initialized with vector store")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}")
        print(f"✗ Agent initialization failed: {e}")
        print("  Continuing without agent - UI may have limited functionality")

print()

# Global state for memory and session
import uuid
from datetime import datetime

session_id = str(uuid.uuid4())
user_id = "local_user"  # Can be customized
conversation_history = []
last_query = {"sql": None, "data": None, "columns": None, "sql_display": None, "question": None, "timestamp": None}


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
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            foreign_keys = cursor.fetchall()
            
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
            
            # Build foreign key list
            fk_list = []
            for fk in foreign_keys:
                # fk format: (id, seq, table, from, to, on_update, on_delete, match)
                from_col = fk[3]
                to_table = fk[2]
                to_col = fk[4]
                fk_list.append(f"<li><strong>{from_col}</strong> → <code>{to_table}.{to_col}</code></li>")
            
            # Create table card
            fk_section = ""
            if fk_list:
                fk_section = f"""
    <p class="fk-header">🔗 Foreign Keys:</p>
    <ul class="fk-list">
        {''.join(fk_list)}
    </ul>"""
            
            table_html = f"""
<div class="schema-table">
    <h4>📊 {table}</h4>
    <p class="row-count">{row_count:,} rows</p>
    <ul class="column-list">
        {''.join(col_list)}
    </ul>{fk_section}
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
.fk-header {{
    margin: 12px 0 8px 0;
    color: #90cdf4;
    font-size: 12px;
    font-weight: 600;
}}
.fk-list {{
    list-style: none;
    padding: 0;
    margin: 0;
}}
.fk-list li {{
    padding: 4px 0;
    border-bottom: 1px solid #2d3748;
    color: #cbd5e0;
    font-size: 12px;
}}
.fk-list li:last-child {{
    border-bottom: none;
}}
.fk-list strong {{
    color: #fbbf24;
    font-weight: 600;
}}
.fk-list code {{
    background: #2d3748;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    color: #c084fc;
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
    """Process user question using the full TextToSQLAgent."""
    global last_query, agent
    
    if not question.strip():
        return history if history else [], last_query.get("sql_display", ""), SCHEMA, None
    
    # Ensure history is a list
    if history is None:
        history = []
    
    if agent is None:
        error_msg = "❌ Agent not initialized. Please check configuration."
        new_history = history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": error_msg}
        ]
        return new_history, "", SCHEMA, None
    
    # Check for visualization follow-up requests (matching gradio_simple.py lines 546-759)
    viz_keywords = ['chart', 'graph', 'plot', 'visualize', 'show that', 'display that', 'bar chart', 'pie chart', 'line chart', 'scatter']
    context_keywords = ['these', 'those', 'that', 'this', 'them', 'it', 'same']
    
    is_viz_request = any(keyword in question.lower() for keyword in viz_keywords)
    has_context_reference = any(keyword in question.lower().split() for keyword in context_keywords)
    is_likely_followup = is_viz_request or has_context_reference
    
    print(f"🔍 Follow-up check:", file=sys.stderr)
    print(f"   - is_viz_request: {is_viz_request}", file=sys.stderr)
    print(f"   - has_context_reference: {has_context_reference}", file=sys.stderr)
    print(f"   - last_query['data']: {bool(last_query['data'])}", file=sys.stderr)
    print(f"   - last_query['columns']: {bool(last_query['columns'])}", file=sys.stderr)
    print(f"   - Will handle as follow-up: {is_likely_followup and last_query['data'] and last_query['columns']}", file=sys.stderr)
    
    # If this looks like a follow-up but we don't have data, give helpful error
    if is_likely_followup and (not last_query["data"] or not last_query["columns"]):
        print("⚠️ Follow-up detected but no cached data available", file=sys.stderr)
        new_history = history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": "❌ **No previous data available**\n\nIt looks like you're asking about previous results (using words like 'these', 'that'), but I don't have any cached data.\n\n💡 **Tip:** Please first ask a data question, then follow up with visualization or analysis requests."}
        ]
        return new_history, "", SCHEMA, None
    
    if is_likely_followup and last_query["data"] and last_query["columns"]:
        # This is a follow-up visualization request - use LLM to analyze it
        print("🎨 Detected visualization follow-up request", file=sys.stderr)
        
        rows = last_query["data"]
        columns = last_query["columns"]
        df = pd.DataFrame(rows, columns=columns)
        
        print(f"📊 Available columns in cached data: {', '.join(columns)}", file=sys.stderr)
        
        # Use agent's LLM to interpret the visualization request
        viz_prompt = f"""You are analyzing a visualization request for cached data.

AVAILABLE COLUMNS IN CACHED DATA: {', '.join(columns)}

USER'S VISUALIZATION REQUEST: "{question}"

STEP 1: Parse what the user is asking for
- Extract what they want on X axis
- Extract what they want on Y axis  
- Extract any grouping/categories
- Extract any time dimensions

STEP 2: Check if those concepts exist in the available columns
- Does the X axis concept match an available column?
- Does the Y axis concept match an available column?
- If they ask for time-based data ("per month", "over time"), is there a date/time column?
- If they ask for a metric ("usage", "revenue", "count"), is that metric column available?

CRITICAL EXAMPLES:
❌ Available: [plan_type, monthly_rate]
   Request: "usage per month per plan type"
   Analysis: User wants X=month (NOT available), Y=usage (NOT available), category=plan_type (available)
   → needs_new_query: TRUE

❌ Available: [plan_type, monthly_rate]  
   Request: "show as line chart"
   Analysis: No specific axis mentioned, can use existing columns
   → needs_new_query: FALSE

❌ Available: [customer_id, name, lifetime_value]
   Request: "show their churn risk as pie chart"
   Analysis: User wants churn_risk (NOT available)
   → needs_new_query: TRUE

DECISION RULE:
If ANY concept the user mentions (metric, dimension, time period) does NOT exist in available columns, set needs_new_query=TRUE.

Return JSON:
{{
  "needs_new_query": true or false,
  "reason": "Specific explanation: 'User requested X column but only Y columns available'",
  "chart_type": "bar|pie|line|scatter",
  "x_column": "column name OR empty string if not available",
  "y_column": "column name OR empty string if not available",  
  "title": "descriptive title based on user's request"
}}

BE STRICT: If user mentions data not in available columns, needs_new_query MUST be TRUE."""

        try:
            # Use agent's LLM manager
            viz_response = agent.llm_manager.generate(
                prompt=viz_prompt,
                system_prompt="You are a data visualization expert. Parse user requests and return valid JSON.",
                use_large_model=False,
                response_format={"type": "json_object"}
            )
            
            import json
            viz_content = viz_response.strip()
            print(f"🤖 LLM viz interpretation: {viz_content}", file=sys.stderr)
            viz_spec = json.loads(viz_content)
            
            # Check if we need a new query
            if viz_spec.get('needs_new_query', False):
                print(f"🔄 New query needed: {viz_spec.get('reason', 'columns not available')}", file=sys.stderr)
                
                # Get original context
                original_sql = last_query.get("sql", "")
                original_question = last_query.get("question", "")
                
                print(f"📝 Original question: {original_question}", file=sys.stderr)
                print(f"📝 Original SQL: {original_sql}", file=sys.stderr)
                
                # Generate SQL query that gets the data needed for visualization
                new_sql_prompt = f"""Given this database schema:

{SCHEMA}

CONTEXT:
- Original question: "{original_question}"
- Original SQL query: {original_sql}
- User's NEW visualization request: "{question}"

VISUALIZATION INTENT:
Chart type: {viz_spec.get('chart_type')}
Title: {viz_spec.get('title')}

ANALYZE THE USER'S REQUEST AND GENERATE APPROPRIATE SQL:

Step 1: Parse what the user is asking for
- What metric/measure do they want to see? (usage, revenue, count, etc.)
- What dimension for X axis? (time/month, category, etc.)
- What grouping/categories for multiple lines/bars? (plan_type, region, etc.)

Step 2: Generate SQL that produces the right data structure
- For LINE CHARTS with "per X per Y" (e.g., "usage per month per plan"):
  * X axis = time dimension (SELECT date/month column)
  * Y axis = aggregated metric (SUM, AVG, COUNT of the metric)
  * Group by BOTH time AND category
  * Example: SELECT month, plan_type, SUM(usage) FROM ... GROUP BY month, plan_type ORDER BY month
  
- For PIE/BAR CHARTS with single dimension:
  * X axis = category
  * Y axis = aggregated metric
  * Group by category only

Step 3: Use the database schema to find the right tables and columns
- Look for tables with the metrics they want (usage, activity, transactions, etc.)
- Look for time columns (timestamp, date, month, etc.)
- Use appropriate SQL functions (strftime for dates, SUM/AVG for aggregations)

Return JSON:
{{
  "sql": "Complete SQL query that gets the data for the visualization",
  "confidence": 0.95
}}"""
                
                new_sql_response = agent.llm_manager.generate(
                    prompt=new_sql_prompt,
                    system_prompt="You are an expert SQL query modifier. Modify existing queries to add columns while preserving the original logic. Always respond with valid JSON.",
                    use_large_model=False,
                    response_format={"type": "json_object"}
                )
                
                new_sql_content = new_sql_response.strip()
                print(f"🤖 Modified SQL generated: {new_sql_content}", file=sys.stderr)
                
                new_sql_data = json.loads(new_sql_content)
                new_sql = new_sql_data.get('sql', '').strip().rstrip(';')
                
                if new_sql:
                    # Execute new query using agent
                    execution_result = agent.query_executor.execute_query(new_sql)
                    
                    if execution_result['success'] and execution_result['row_count'] > 0:
                        print(f"✅ New query executed: {execution_result['row_count']} rows", file=sys.stderr)
                        rows = execution_result['rows']
                        columns = execution_result['columns']
                        df = pd.DataFrame(rows, columns=columns)
                        
                        # Update SQL display
                        new_confidence = new_sql_data.get('confidence', 0.9)
                        sql_display = f"**Confidence:** {new_confidence:.2f}\n\n```sql\n{new_sql}\n```"
                        
                        # Update cache
                        last_query["sql"] = new_sql
                        last_query["data"] = rows
                        last_query["columns"] = columns
                        last_query["sql_display"] = sql_display
                        last_query["question"] = question
                        last_query["timestamp"] = datetime.now().isoformat()
                        
                        # Re-analyze with NEW columns to determine proper x/y/color for the chart
                        print(f"🔄 Re-analyzing with new columns: {', '.join(columns)}", file=sys.stderr)
                        reanalyze_prompt = f"""The user requested: "{question}"

Available columns in the new data: {', '.join(columns)}

Parse the user's request and map it to specific columns:

EXTRACTION RULES:
1. X AXIS: 
   - If user says "per month", "over time", "by date" → use date/month/timestamp column
   - If user explicitly says "X as Y axis" → use X column
   - For time-series: always put time on X axis

2. Y AXIS:
   - If user says metric name ("usage", "revenue", "churn risk") → use that metric column
   - If user explicitly says "X as Y axis" → use X column
   - For aggregated data: use the aggregated metric column

3. COLOR/GROUPING (for multiple lines/bars):
   - If user says "per plan type", "by plan", "each region" → use that column for color
   - For line charts, color creates multiple lines (one per category)
   - Example: "usage per month per plan" → color by plan_type creates separate line for each plan

EXAMPLES:
Request: "Show churn risk as bar chart with customer_id as Y axis"
→ x_column: first_name or customer_id (identifier), y_column: churn_risk_score, color_column: null

Request: "Show usage per month per plan type as line chart"  
→ x_column: month, y_column: usage or total_usage, color_column: plan_type

Request: "Show their churn risk as pie chart"
→ x_column: customer name/id, y_column: churn_risk_score, color_column: null

Return JSON:
{{
  "chart_type": "{viz_spec.get('chart_type', 'bar')}",
  "x_column": "exact column name",
  "y_column": "exact column name",
  "color_column": "column name or null",
  "title": "descriptive title matching user's request"
}}"""
                        
                        reanalyze_response = agent.llm_manager.generate(
                            prompt=reanalyze_prompt,
                            system_prompt="You are a data visualization expert. Map user requests to specific column names. Respect explicit axis specifications. Respond with valid JSON.",
                            use_large_model=False,
                            response_format={"type": "json_object"}
                        )
                        
                        viz_spec = json.loads(reanalyze_response.strip())
                        print(f"🎯 Re-analyzed viz spec: {viz_spec}", file=sys.stderr)
                    else:
                        error_msg = execution_result.get('error', 'Query execution failed')
                        print(f"❌ New query failed: {error_msg}", file=sys.stderr)
                        new_history = history + [
                            {"role": "user", "content": question},
                            {"role": "assistant", "content": f"❌ Failed to execute new query for visualization: {error_msg}"}
                        ]
                        return new_history, last_query.get("sql_display", ""), SCHEMA, None
            
            # Extract chart specs (use re-analyzed values if new query was executed)
            chart_type = viz_spec.get('chart_type', 'bar')
            x_col = viz_spec.get('x_column', columns[0] if columns else None)
            y_col = viz_spec.get('y_column', columns[-1] if len(columns) > 1 else columns[0] if columns else None)
            color_col = viz_spec.get('color_column', None)
            title = viz_spec.get('title', f"{y_col} by {x_col}" if x_col and y_col else "Visualization")
            
            # Validate columns exist in dataframe
            if not x_col or x_col not in df.columns:
                if x_col:
                    print(f"⚠️ x_column '{x_col}' not found in data, using fallback", file=sys.stderr)
                x_col = df.columns[0] if len(df.columns) > 0 else None
                
            if not y_col or y_col not in df.columns:
                if y_col:
                    print(f"⚠️ y_column '{y_col}' not found in data, using fallback", file=sys.stderr)
                y_col = df.columns[-1] if len(df.columns) > 1 else df.columns[0] if len(df.columns) > 0 else None
            
            # Validate color column if specified
            if color_col and color_col not in df.columns:
                print(f"⚠️ color_column '{color_col}' not found, ignoring", file=sys.stderr)
                color_col = None
            
            if not x_col or not y_col:
                new_history = history + [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": "❌ Unable to create visualization: insufficient columns in data."}
                ]
                return new_history, last_query.get("sql_display", ""), SCHEMA, None
            
            print(f"📊 Creating {chart_type} chart: X={x_col}, Y={y_col}, Color={color_col}", file=sys.stderr)
            
            # Create visualization based on LLM recommendation
            viz_fig = None
            
            # Sort dataframe by y_col numerically if possible to avoid lexicographic issues
            df_viz = df.head(20).copy()
            try:
                if y_col in df_viz.columns:
                    df_viz[y_col] = pd.to_numeric(df_viz[y_col], errors='ignore')
                if x_col in df_viz.columns:
                    df_viz[x_col] = pd.to_numeric(df_viz[x_col], errors='ignore')
            except:
                pass
            
            if chart_type == 'bar':
                # For bar charts without color grouping, don't use color parameter to avoid stacking
                if color_col and color_col in df_viz.columns:
                    viz_fig = px.bar(df_viz, x=x_col, y=y_col, color=color_col, title=title)
                else:
                    viz_fig = px.bar(df_viz, x=x_col, y=y_col, title=title)
            elif chart_type == 'pie':
                viz_fig = px.pie(df_viz, names=x_col, values=y_col, title=title)
            elif chart_type == 'line':
                # Line charts with color create multiple lines
                viz_fig = px.line(df_viz, x=x_col, y=y_col, color=color_col, title=title)
            elif chart_type == 'scatter':
                viz_fig = px.scatter(df_viz, x=x_col, y=y_col, color=color_col, title=title)
            else:
                if color_col and color_col in df_viz.columns:
                    viz_fig = px.bar(df_viz, x=x_col, y=y_col, color=color_col, title=title)
                else:
                    viz_fig = px.bar(df_viz, x=x_col, y=y_col, title=title)
            
            print(f"✅ Created {chart_type} chart: {title}", file=sys.stderr)
            
            response = f"""✅ **Visualization Created**

Created **{chart_type} chart**: {title}

Using columns: **{y_col}** by **{x_col}**

Check the **Visualization panel** on the right →"""
            
            new_history = history + [
                {"role": "user", "content": question},
                {"role": "assistant", "content": response}
            ]
            
            # Return updated SQL display if query was modified
            return new_history, last_query.get("sql_display", ""), SCHEMA, viz_fig
            
        except Exception as e:
            print(f"❌ Follow-up viz error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
    
    # Use the full agent to process the question
    try:
        result = agent.process_question(
            question=question,
            session_id=session_id,
            visualization_type="auto" if auto_viz_enabled else None
        )
        
        # Extract data from agent response
        print(f"🔍 Agent result keys: {result.keys()}", file=sys.stderr)
        print(f"🔍 Agent result: {str(result)[:500]}", file=sys.stderr)
        
        sql = result.get('metadata', {}).get('sql_query', '')
        confidence = result.get('metadata', {}).get('confidence', 0.0)
        data = result.get('data', {})
        
        print(f"🔍 Data type: {type(data)}", file=sys.stderr)
        print(f"🔍 Data content: {data}", file=sys.stderr)
        print(f"🔍 Data keys: {data.keys() if isinstance(data, dict) else 'NOT A DICT'}", file=sys.stderr)
        
        columns = data.get('columns', []) if isinstance(data, dict) else []
        rows = data.get('rows', []) if isinstance(data, dict) else []
        visualization = result.get('visualization', {})  # Extract agent's visualization
        
        print(f"🔍 Extracted - Rows: {len(rows)}, Columns: {len(columns)}", file=sys.stderr)
        print(f"🔍 Rows truthiness: {bool(rows)}, Columns truthiness: {bool(columns)}", file=sys.stderr)
        print(f"🔍 Visualization: {visualization.get('type') if visualization else 'None'}", file=sys.stderr)
        
        # Create SQL display
        sql_display = f"**Confidence:** {confidence:.2f}\n\n```sql\n{sql}\n```" if sql else ""
        
        # Only update last_query if we have actual data (don't overwrite on errors)
        if rows and columns:
            last_query = {
                "sql": sql,
                "data": rows,
                "columns": columns,
                "sql_display": sql_display,
                "question": question,
                "timestamp": datetime.now().isoformat()
            }
            print(f"✅ Updated last_query cache with {len(rows)} rows", file=sys.stderr)
        else:
            print(f"⚠️ Not updating last_query - no data to cache", file=sys.stderr)
        
        # Create response - MATCH gradio_simple.py approach
        if rows and columns:
            df = pd.DataFrame(rows, columns=columns)
            
            # Build HTML table manually (matching gradio_simple.py lines 816-863)
            display_df = df.head(20)
            
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
            
            # Compact styling (identical to gradio_simple.py)
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
            
            # Response with the actual data table (matching gradio_simple.py lines 868-872)
            response = f"""✅ **Query Results** • *{row_msg}*

{styled_table}

💡 *Try: "show as bar chart" · "make it a pie chart" · "plot as line graph"*"""
            
            # Create automatic visualization if enabled (matching gradio_simple.py lines 875-917)
            viz_fig = None
            if auto_viz_enabled and len(columns) >= 2 and len(rows) > 0:
                try:
                    # Use simple fallback for now (agent should provide recommendations)
                    x_col = columns[0]
                    y_col = columns[-1]
                    title = f"{y_col} by {x_col}"
                    chart_type = 'bar'
                    
                    # Sort dataframe numerically to avoid lexicographic issues
                    df_viz = df.head(20).copy()
                    try:
                        if y_col in df_viz.columns:
                            df_viz[y_col] = pd.to_numeric(df_viz[y_col], errors='ignore')
                        if x_col in df_viz.columns:
                            df_viz[x_col] = pd.to_numeric(df_viz[x_col], errors='ignore')
                    except:
                        pass
                    
                    # Create the chart based on type
                    if chart_type == 'bar':
                        viz_fig = px.bar(df_viz, x=x_col, y=y_col, title=title)
                    elif chart_type == 'pie':
                        viz_fig = px.pie(df_viz, names=x_col, values=y_col, title=title)
                    elif chart_type == 'line':
                        viz_fig = px.line(df_viz, x=x_col, y=y_col, title=title)
                    elif chart_type == 'scatter':
                        viz_fig = px.scatter(df_viz, x=x_col, y=y_col, title=title)
                    else:
                        viz_fig = px.bar(df_viz, x=x_col, y=y_col, title=title)
                    
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
        
        print(f"📤 Returning to UI:", file=sys.stderr)
        print(f"   - History: {len(new_history)} messages", file=sys.stderr)
        print(f"   - SQL: {len(sql_display)} chars", file=sys.stderr)
        print(f"   - Schema: {len(SCHEMA)} chars", file=sys.stderr)
        print(f"   - Viz: {type(viz_fig).__name__ if viz_fig else 'None'}", file=sys.stderr)
        
        return new_history, sql_display, SCHEMA, viz_fig
        
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        error_msg = f"❌ **Error**: {str(e)}"
        new_history = history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": error_msg}
        ]
        return new_history, "", SCHEMA, None
        
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
                
                # Generate SQL query that gets the data needed for visualization
                new_sql_prompt = f"""Given this database schema:

{SCHEMA}

CONTEXT:
- Original question: "{original_question}"
- Original SQL query: {original_sql}
- User's NEW visualization request: "{question}"

VISUALIZATION INTENT:
Chart type: {viz_spec.get('chart_type')}
Title: {viz_spec.get('title')}

ANALYZE THE USER'S REQUEST AND GENERATE APPROPRIATE SQL:

Step 1: Parse what the user is asking for
- What metric/measure do they want to see? (usage, revenue, count, etc.)
- What dimension for X axis? (time/month, category, etc.)
- What grouping/categories for multiple lines/bars? (plan_type, region, etc.)

Step 2: Generate SQL that produces the right data structure
- For LINE CHARTS with "per X per Y" (e.g., "usage per month per plan"):
  * X axis = time dimension (SELECT date/month column)
  * Y axis = aggregated metric (SUM, AVG, COUNT of the metric)
  * Group by BOTH time AND category
  * Example: SELECT month, plan_type, SUM(usage) FROM ... GROUP BY month, plan_type ORDER BY month
  
- For PIE/BAR CHARTS with single dimension:
  * X axis = category
  * Y axis = aggregated metric
  * Group by category only

Step 3: Use the database schema to find the right tables and columns
- Look for tables with the metrics they want (usage, activity, transactions, etc.)
- Look for time columns (timestamp, date, month, etc.)
- Use appropriate SQL functions (strftime for dates, SUM/AVG for aggregations)

Return JSON:
{{
  "sql": "Complete SQL query that gets the data for the visualization",
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
            
            # Sort dataframe numerically to avoid lexicographic issues
            df_viz = df.head(20).copy()
            try:
                if y_col in df_viz.columns:
                    df_viz[y_col] = pd.to_numeric(df_viz[y_col], errors='ignore')
                if x_col in df_viz.columns:
                    df_viz[x_col] = pd.to_numeric(df_viz[x_col], errors='ignore')
            except:
                pass
            
            if chart_type == "bar" and len(columns) >= 2:
                viz_fig = px.bar(df_viz, x=x_col, y=y_col, title=title)
            elif chart_type == "pie" and len(columns) >= 2:
                viz_fig = px.pie(df_viz, names=x_col, values=y_col, title=title)
            elif chart_type == "line" and len(columns) >= 2:
                viz_fig = px.line(df_viz, x=x_col, y=y_col, title=title)
            elif chart_type == "scatter" and len(columns) >= 2:
                viz_fig = px.scatter(df_viz, x=x_col, y=y_col, title=title)
            
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
    
    # Validate question relevance before generating SQL
    print("🔍 Validating question relevance...", file=sys.stderr)
    is_valid_question, validation_msg = validate_question_relevance(question, SCHEMA)
    
    if not is_valid_question:
        print(f"❌ Question validation failed: {validation_msg}", file=sys.stderr)
        new_history = history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f"❌ **Invalid Question**\n\n{validation_msg}\n\n💡 **Tip:** Ask questions about the available data in the database. For example:\n- What are the top customers?\n- Show revenue by plan type\n- How many active users are there?"}
        ]
        return new_history, "", SCHEMA, None
    
    print(f"✅ Question is valid", file=sys.stderr)
    
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
                
                # Sort dataframe numerically to avoid lexicographic issues
                df_viz = df.head(20).copy()
                try:
                    if y_col in df_viz.columns:
                        df_viz[y_col] = pd.to_numeric(df_viz[y_col], errors='ignore')
                    if x_col in df_viz.columns:
                        df_viz[x_col] = pd.to_numeric(df_viz[x_col], errors='ignore')
                except:
                    pass
                
                # Create the chart based on type
                if chart_type == 'bar':
                    viz_fig = px.bar(df_viz, x=x_col, y=y_col, title=title)
                elif chart_type == 'pie':
                    viz_fig = px.pie(df_viz, names=x_col, values=y_col, title=title)
                elif chart_type == 'line':
                    viz_fig = px.line(df_viz, x=x_col, y=y_col, title=title)
                elif chart_type == 'scatter':
                    viz_fig = px.scatter(df_viz, x=x_col, y=y_col, title=title)
                else:
                    viz_fig = px.bar(df_viz, x=x_col, y=y_col, title=title)
                
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


def submit_feedback(rating: str, comment: str) -> str:
    """Submit user feedback for the last query."""
    global agent, last_query
    
    if not agent:
        return "❌ Agent not available"
    
    if not last_query["sql"]:
        return "❌ No query to provide feedback on. Please run a query first."
    
    try:
        from src.agent.feedback import FeedbackType
        
        # Map rating to feedback type
        feedback_type = FeedbackType.POSITIVE if rating == "👍 Good" else FeedbackType.NEGATIVE
        
        # Submit feedback through agent
        agent.feedback_manager.add_feedback(
            question=last_query["question"],
            sql_query=last_query["sql"],
            feedback_type=feedback_type,
            comment=comment if comment else None,
            session_id=session_id,
            user_id=user_id
        )
        
        logger.info(f"✅ Feedback submitted: {rating}")
        return f"✅ Thank you! Feedback recorded: {rating}"
        
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        return f"❌ Error submitting feedback: {str(e)}"


# Create Gradio interface
with gr.Blocks(title="Text-to-SQL Agent") as demo:
    gr.Markdown(f"""
    # 🤖 Text-to-SQL Agent
    
    Ask questions in natural language and get SQL queries with results!
    
    *Session: `{session_id[:8]}...` • User: `{user_id}` • Mode: Full Agent with Vector Store*
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
            
            # Feedback section below SQL
            with gr.Accordion("⭐ Provide Feedback", open=False):
                gr.Markdown("*Rate the quality of this query result*")
                with gr.Row():
                    feedback_thumbs = gr.Radio(
                        label="Rating",
                        choices=["👍 Good", "👎 Bad"],
                        value=None
                    )
                    feedback_comment = gr.Textbox(
                        label="Comment (optional)",
                        placeholder="Any feedback or suggestions...",
                        lines=2
                    )
                feedback_btn = gr.Button("Submit Feedback", size="sm")
                feedback_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    show_label=False
                )
            
            # Example questions below feedback
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
    
    feedback_btn.click(
        submit_feedback,
        inputs=[feedback_thumbs, feedback_comment],
        outputs=feedback_status
    )


def launch_ui(server_name="127.0.0.1", server_port=7860, share=False):
    """Launch the Gradio interface - for compatibility with launch.py."""
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        show_error=True,
        theme=gr.themes.Soft()
    )


print("Launching Gradio UI...")
print("Open browser to: http://localhost:7860")
print()

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
