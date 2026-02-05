"""
Gradio UI for Text-to-SQL Agent.

Provides a chat interface with:
- Natural language question input
- SQL query display
- Interactive data visualization
- Data viewer panel
- Feedback mechanism
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import json

# Add parent directories to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
project_root = src_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

import gradio as gr
import pandas as pd
from loguru import logger

from agent.agent import TextToSQLAgent
from agent.feedback import FeedbackType
from utils.config import load_config


# Global agent instance
agent: Optional[TextToSQLAgent] = None
current_session_id: Optional[str] = None
last_result: Optional[Dict[str, Any]] = None


def initialize_agent():
    """Initialize the Text-to-SQL agent."""
    global agent
    if agent is None:
        try:
            config = load_config()
            agent = TextToSQLAgent(config)
            logger.info("Agent initialized successfully")
            return "✅ Agent initialized successfully"
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            return f"❌ Failed to initialize: {str(e)}"
    return "✅ Agent already initialized"


def process_question_ui(
    question: str,
    chat_history: List[Tuple[str, str]],
    visualization_type: str
) -> Tuple[List[Tuple[str, str]], str, str, str, str]:
    """
    Process user question and return results for UI.
    
    Returns:
        - Updated chat history
        - SQL query
        - Result data (HTML table)
        - Visualization (HTML)
        - Status message
    """
    global agent, current_session_id, last_result
    
    if agent is None:
        error_msg = "Agent not initialized. Please initialize first."
        chat_history.append((question, f"❌ {error_msg}"))
        return chat_history, "", "", "", error_msg
    
    if not question.strip():
        return chat_history, "", "", "", "Please enter a question"
    
    try:
        # Create session if needed
        if current_session_id is None:
            current_session_id = agent.create_session()
        
        # Process question
        viz_type = None if visualization_type == "auto" else visualization_type
        result = agent.process_question(
            question=question,
            session_id=current_session_id,
            visualization_type=viz_type
        )
        
        last_result = result
        
        # Extract response
        response_type = result.get('response_type')
        
        if response_type == 'error':
            error_msg = result.get('data', {}).get('error', 'Unknown error')
            chat_history.append((question, f"❌ Error: {error_msg}"))
            return chat_history, "", "", "", f"Error: {error_msg}"
        
        # Get SQL query
        sql_query = result.get('metadata', {}).get('sql_query', '')
        
        # Get data
        data = result.get('data', {})
        columns = data.get('columns', [])
        rows = data.get('data', [])
        row_count = data.get('row_count', 0)
        
        # Create data table HTML
        if rows and columns:
            df = pd.DataFrame(rows, columns=columns)
            data_html = df.to_html(
                index=False,
                classes='dataframe',
                border=0,
                max_rows=100
            )
        else:
            data_html = "<p>No data returned</p>"
        
        # Get visualization
        visualization_html = data.get('visualization', '')
        if not visualization_html:
            visualization_html = "<p>No visualization available</p>"
        
        # Build response message
        response_msg = f"""
✅ **Query executed successfully**

**Rows returned:** {row_count}

**SQL Query:**
```sql
{sql_query}
```

**Confidence:** {result.get('metadata', {}).get('confidence', 0):.2f}
"""
        
        chat_history.append((question, response_msg))
        
        status = f"✅ Success | {row_count} rows | Confidence: {result.get('metadata', {}).get('confidence', 0):.2f}"
        
        return chat_history, sql_query, data_html, visualization_html, status
        
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        error_msg = f"❌ Error: {str(e)}"
        chat_history.append((question, error_msg))
        return chat_history, "", "", "", error_msg


def submit_feedback_ui(feedback_type: str, comment: str) -> str:
    """Submit user feedback."""
    global agent, last_result
    
    if agent is None or last_result is None:
        return "No query to provide feedback on"
    
    try:
        feedback_map = {
            "👍 Positive": FeedbackType.POSITIVE,
            "👎 Negative": FeedbackType.NEGATIVE,
            "😐 Neutral": FeedbackType.NEUTRAL
        }
        
        feedback_enum = feedback_map.get(feedback_type, FeedbackType.NEUTRAL)
        
        # Extract info from last result
        question = last_result.get('metadata', {}).get('question', '')
        sql_query = last_result.get('metadata', {}).get('sql_query', '')
        answer = last_result.get('data', {})
        llm_confidence = last_result.get('metadata', {}).get('query_generation', {}).get('llm_confidence', 0.8)
        
        agent.add_user_feedback(
            question=question,
            sql_query=sql_query,
            answer=answer,
            feedback_type=feedback_enum,
            comment=comment if comment else None,
            llm_confidence=llm_confidence
        )
        
        return f"✅ Feedback submitted: {feedback_type}"
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return f"❌ Error: {str(e)}"


def clear_chat() -> Tuple[List, str, str, str, str]:
    """Clear chat history and reset session."""
    global current_session_id, last_result
    current_session_id = None
    last_result = None
    return [], "", "", "", "Chat cleared"


def export_data_ui() -> str:
    """Export last result data as CSV."""
    global last_result
    
    if last_result is None:
        return None
    
    try:
        data = last_result.get('data', {})
        columns = data.get('columns', [])
        rows = data.get('data', [])
        
        if not rows:
            return None
        
        df = pd.DataFrame(rows, columns=columns)
        csv_path = "exported_data.csv"
        df.to_csv(csv_path, index=False)
        
        return csv_path
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return None


# ============================================================================
# Gradio Interface
# ============================================================================

def create_gradio_interface():
    """Create and configure Gradio interface."""
    
    # Custom CSS for better styling
    custom_css = """
    .container {max-width: 1400px; margin: auto;}
    .dataframe {font-size: 12px; width: 100%;}
    .dataframe th {background-color: #f0f0f0; padding: 8px;}
    .dataframe td {padding: 6px;}
    .status-box {padding: 10px; border-radius: 5px; margin: 10px 0;}
    .success {background-color: #d4edda; border: 1px solid #c3e6cb;}
    .error {background-color: #f8d7da; border: 1px solid #f5c6cb;}
    """
    
    with gr.Blocks(
        title="Text-to-SQL Agent",
        theme=gr.themes.Soft(),
        css=custom_css
    ) as interface:
        
        gr.Markdown("""
        # 🤖 Text-to-SQL Agent
        
        Ask questions in natural language and get SQL queries and visualizations!
        """)
        
        # Initialization
        with gr.Row():
            init_btn = gr.Button("🚀 Initialize Agent", variant="primary")
            init_status = gr.Textbox(
                label="Status",
                value="Click 'Initialize Agent' to start",
                interactive=False
            )
        
        init_btn.click(fn=initialize_agent, outputs=init_status)
        
        gr.Markdown("---")
        
        # Main layout: Chat on left, Data viewer on right
        with gr.Row():
            # Left column: Chat interface
            with gr.Column(scale=6):
                gr.Markdown("### 💬 Chat Interface")
                
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=400,
                    show_label=True
                )
                
                with gr.Row():
                    question_input = gr.Textbox(
                        label="Your Question",
                        placeholder="e.g., What are the top 10 customers by revenue?",
                        lines=2,
                        scale=4
                    )
                    viz_type = gr.Dropdown(
                        label="Visualization",
                        choices=["auto", "table", "bar", "line", "pie", "scatter"],
                        value="auto",
                        scale=1
                    )
                
                with gr.Row():
                    submit_btn = gr.Button("🔍 Submit", variant="primary")
                    clear_btn = gr.Button("🗑️ Clear Chat")
                
                status_box = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=1
                )
                
                # SQL Query display
                with gr.Accordion("📝 Generated SQL Query", open=False):
                    sql_output = gr.Code(
                        label="SQL",
                        language="sql",
                        interactive=False
                    )
                
                # Feedback section
                with gr.Accordion("📊 Provide Feedback", open=False):
                    with gr.Row():
                        feedback_type = gr.Radio(
                            label="Feedback",
                            choices=["👍 Positive", "👎 Negative", "😐 Neutral"],
                            value="👍 Positive"
                        )
                        feedback_comment = gr.Textbox(
                            label="Comment (optional)",
                            placeholder="Any additional comments...",
                            lines=2
                        )
                    
                    feedback_btn = gr.Button("Submit Feedback")
                    feedback_status = gr.Textbox(
                        label="Feedback Status",
                        interactive=False
                    )
            
            # Right column: Data viewer
            with gr.Column(scale=4):
                gr.Markdown("### 📊 Data Viewer")
                
                data_viewer = gr.HTML(
                    label="Query Results",
                    value="<p style='text-align: center; color: #666;'>Results will appear here...</p>"
                )
                
                export_btn = gr.Button("💾 Export as CSV")
                export_file = gr.File(label="Download CSV")
                
                gr.Markdown("---")
                
                gr.Markdown("### 📈 Visualization")
                
                visualization_output = gr.HTML(
                    label="Chart",
                    value="<p style='text-align: center; color: #666;'>Visualization will appear here...</p>"
                )
        
        gr.Markdown("---")
        
        # Instructions
        with gr.Accordion("ℹ️ How to Use", open=False):
            gr.Markdown("""
            ### Quick Start
            
            1. **Initialize**: Click "Initialize Agent" first
            2. **Ask**: Type your question in natural language
            3. **Review**: See the SQL query, data table, and visualization
            4. **Feedback**: Rate the results to improve the system
            
            ### Example Questions
            
            - What are the top 10 customers by revenue?
            - Show monthly revenue trends
            - List active users from last month
            - Count transactions by category
            - Which products have the highest sales?
            
            ### Tips
            
            - Be specific in your questions
            - Mention table names if known
            - Specify aggregations (sum, average, count)
            - Use the visualization dropdown for specific chart types
            """)
        
        # Event handlers
        submit_btn.click(
            fn=process_question_ui,
            inputs=[question_input, chatbot, viz_type],
            outputs=[chatbot, sql_output, data_viewer, visualization_output, status_box]
        )
        
        question_input.submit(
            fn=process_question_ui,
            inputs=[question_input, chatbot, viz_type],
            outputs=[chatbot, sql_output, data_viewer, visualization_output, status_box]
        )
        
        clear_btn.click(
            fn=clear_chat,
            outputs=[chatbot, sql_output, data_viewer, visualization_output, status_box]
        )
        
        feedback_btn.click(
            fn=submit_feedback_ui,
            inputs=[feedback_type, feedback_comment],
            outputs=feedback_status
        )
        
        export_btn.click(
            fn=export_data_ui,
            outputs=export_file
        )
    
    return interface


def launch_ui(server_name="127.0.0.1", server_port=7860, share=False):
    """Launch the Gradio interface."""
    interface = create_gradio_interface()
    interface.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        show_error=True
    )


if __name__ == "__main__":
    # Setup logging
    logger.info("Starting Gradio UI...")
    
    # Launch with default settings
    launch_ui(share=False)
