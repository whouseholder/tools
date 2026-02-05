# Gradio UI for Text-to-SQL Agent

Interactive chat interface with data visualization for the Text-to-SQL Agent.

## Features

- 💬 **Chat Interface** - Natural language question input with conversation history
- 📊 **Data Viewer** - Real-time display of query results in tabular format
- 📈 **Visualizations** - Auto-generated charts (bar, line, pie, scatter)
- 🔍 **SQL Display** - View generated SQL queries with syntax highlighting
- 👍 **Feedback** - Submit feedback (positive/negative/neutral) for continuous improvement
- 💾 **Export** - Download query results as CSV
- 🎨 **Modern UI** - Clean, responsive interface built with Gradio

## Quick Start

### Launch the UI

```bash
# Make script executable (first time only)
chmod +x launch_ui.sh

# Launch
./launch_ui.sh
```

The UI will be available at `http://localhost:7860`

### Manual Launch

```bash
# Activate virtual environment
source venv/bin/activate

# Launch Gradio
python src/ui/gradio_app.py
```

## Interface Layout

```
┌─────────────────────────────────────────────────────────┐
│                 Text-to-SQL Agent                       │
│  [Initialize Agent]                                     │
├──────────────────────┬──────────────────────────────────┤
│                      │                                  │
│  Chat Interface      │    Data Viewer                   │
│                      │                                  │
│  ┌────────────────┐ │  ┌────────────────────────────┐ │
│  │ Conversation   │ │  │ Query Results              │ │
│  │ History        │ │  │ (Table View)               │ │
│  │                │ │  │                            │ │
│  └────────────────┘ │  └────────────────────────────┘ │
│                      │                                  │
│  [Your Question]     │  [Export CSV]                    │
│  [Visualization ▼]   │                                  │
│  [Submit] [Clear]    │  Visualization                   │
│                      │  ┌────────────────────────────┐ │
│  SQL Query           │  │ Charts/Graphs              │ │
│  Feedback            │  │                            │ │
│                      │  └────────────────────────────┘ │
└──────────────────────┴──────────────────────────────────┘
```

## Usage

### 1. Initialize

Click **"Initialize Agent"** to load the model and connect to the database.

### 2. Ask Questions

Type natural language questions in the input box:

**Examples:**
- "What are the top 10 customers by revenue?"
- "Show monthly revenue trends"
- "List active users from last month"
- "Count transactions by category"

### 3. View Results

**Chat Panel (Left):**
- See conversation history
- View SQL queries in formatted code blocks
- See confidence scores

**Data Viewer (Right):**
- Browse query results in table format
- See up to 100 rows at a time
- Export data as CSV

**Visualization Panel (Right):**
- Auto-generated charts based on data
- Choose specific visualization types (bar, line, pie, scatter)
- Interactive Plotly visualizations

### 4. Provide Feedback

1. Click "Provide Feedback" accordion
2. Select 👍 Positive, 👎 Negative, or 😐 Neutral
3. Add optional comment
4. Click "Submit Feedback"

Feedback helps improve the system over time!

### 5. Export Data

Click **"Export as CSV"** to download query results for further analysis.

## Configuration

### Server Settings

Edit `src/ui/gradio_app.py` to customize:

```python
# Launch settings
interface.launch(
    server_name="127.0.0.1",  # Host
    server_port=7860,          # Port
    share=False                # Set True for public URL
)
```

### Share Publicly

To share your UI publicly via Gradio's sharing feature:

```python
interface.launch(share=True)
```

This creates a temporary public URL (valid for 72 hours).

## Environment Variables

Required:
```bash
export OPENAI_API_KEY="sk-..."      # OpenAI API key
export HIVE_HOST="hive.company.com" # Hive metastore
export HIVE_USER="username"
export HIVE_PASSWORD="password"
```

Optional:
```bash
export HIVE_PORT="10000"
export HIVE_DATABASE="default"
export LOG_LEVEL="INFO"
```

## Features in Detail

### Chat Interface

- **Conversation History**: See all Q&A in the chat
- **SQL Display**: Collapsible SQL query viewer with syntax highlighting
- **Status Updates**: Real-time feedback on query execution
- **Clear Chat**: Reset conversation and start fresh

### Data Viewer

- **Responsive Tables**: Auto-formatted HTML tables
- **Row Count**: See how many rows returned
- **Large Result Handling**: Displays up to 100 rows
- **Export**: Download full results as CSV

### Visualizations

The agent automatically chooses the best visualization based on:
- Number of columns
- Data types (numeric vs categorical)
- Row count

**Supported Types:**
- **Table**: Default for all queries
- **Bar Chart**: Categorical comparisons
- **Line Chart**: Time series trends
- **Pie Chart**: Proportions and percentages
- **Scatter Plot**: Correlations and distributions

### Feedback System

**Why provide feedback?**
- Improves query generation accuracy
- Stores good Q&A pairs for future use
- Adjusts confidence scores
- Enables continuous learning

**Feedback Types:**
- **👍 Positive**: Query was perfect
- **👎 Negative**: Query had issues
- **😐 Neutral**: Query was okay but not great

## Troubleshooting

### UI Won't Start

```bash
# Check if gradio is installed
pip install gradio==4.15.0

# Check if agent dependencies are installed
pip install -r requirements.txt
```

### Agent Not Initializing

```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $HIVE_HOST

# Test Hive connection
python -c "from pyhive import hive; conn = hive.Connection(host='your-host')"
```

### Slow Response Times

- First query may be slow (loading models)
- Subsequent queries should be faster
- Large result sets take longer to visualize

### Visualization Not Showing

- Check browser console for errors
- Ensure data has at least 1 row
- Try different visualization types

## Keyboard Shortcuts

- **Enter**: Submit question (when input box is focused)
- **Ctrl+R**: Refresh page
- **Esc**: Close accordions

## Advanced Usage

### Custom Styling

Edit the `custom_css` variable in `gradio_app.py`:

```python
custom_css = """
.container {max-width: 1600px;}
.dataframe {font-size: 14px;}
...
```

### Programmatic Access

```python
from src.ui.gradio_app import create_gradio_interface

# Create custom interface
interface = create_gradio_interface()

# Launch with custom settings
interface.launch(
    server_name="0.0.0.0",
    server_port=8080,
    auth=("username", "password")  # Add authentication
)
```

### Embedding in Apps

Gradio interfaces can be embedded in other applications:

```python
import gradio as gr
from src.ui.gradio_app import create_gradio_interface

# Mount in FastAPI
from fastapi import FastAPI
app = FastAPI()

gradio_app = create_gradio_interface()
app = gr.mount_gradio_app(app, gradio_app, path="/ui")
```

## API Reference

### Functions

**`initialize_agent()`**
- Initializes the Text-to-SQL agent
- Returns: Status message

**`process_question_ui(question, chat_history, visualization_type)`**
- Processes user question
- Returns: Updated chat, SQL, data HTML, visualization, status

**`submit_feedback_ui(feedback_type, comment)`**
- Submits user feedback
- Returns: Feedback status message

**`clear_chat()`**
- Clears conversation history
- Returns: Empty chat state

**`export_data_ui()`**
- Exports last result as CSV
- Returns: File path for download

## Performance Tips

1. **Use specific questions** - Clearer questions = faster, better results
2. **Limit result size** - Use LIMIT in questions for large datasets
3. **Choose visualization type** - Manual selection faster than auto-suggest
4. **Reuse sessions** - Don't clear chat unnecessarily (context helps!)

## Examples

### Marketing Analytics
```
Q: What are the top 10 customers by lifetime value?
Q: Show customer acquisition trends by month for 2023
Q: Which products have the highest conversion rates?
```

### Operations
```
Q: Count active users in the last 30 days
Q: Show average response time by service category
Q: List all failed transactions from yesterday
```

### Finance
```
Q: Calculate total revenue by region for Q4
Q: Show monthly recurring revenue growth
Q: What's the average order value by customer segment?
```

## Screenshots

*(Screenshots would go here showing the interface in action)*

## Support

- **Documentation**: [docs/README.md](../../docs/README.md)
- **Tool Reference**: [docs/TOOLS.md](../../docs/TOOLS.md)
- **API Docs**: [docs/API.md](../../docs/API.md)
- **Issues**: Contact project team

## Changelog

### v1.0.0 (Initial Release)
- Chat interface with conversation history
- Data viewer with export functionality
- Auto visualization generation
- Feedback system integration
- SQL query display
- Responsive design

---

**Launch the UI:** `./launch_ui.sh`  
**Port:** 7860  
**Status:** Production Ready ✅
