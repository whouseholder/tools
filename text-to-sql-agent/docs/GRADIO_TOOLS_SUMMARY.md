# Gradio UI & Tool-Based Agent Implementation

## Summary

The Text-to-SQL Agent has been enhanced with:

1. **Gradio Chat UI** - Interactive web interface with data viewer
2. **Tool-Based Architecture** - 10 explicit tool definitions
3. **Complete Documentation** - Comprehensive tool reference guide

---

## 🎨 Gradio UI Features

### Interface Components

**Left Panel - Chat Interface:**
- Natural language question input
- Conversation history display
- SQL query viewer (collapsible)
- Feedback submission
- Visualization type selector

**Right Panel - Data Viewer:**
- Real-time query results table
- Interactive visualizations (charts)
- CSV export functionality

### Key Features

✅ **Real-time Chat** - Ask questions, see answers instantly  
✅ **SQL Display** - View generated queries with syntax highlighting  
✅ **Data Tables** - Browse results up to 100 rows  
✅ **Auto Visualization** - Charts generated based on data structure  
✅ **Feedback Loop** - Submit ratings to improve the system  
✅ **Export** - Download results as CSV  
✅ **Session Management** - Maintains conversation context  

### Launch

```bash
# Quick start
./launch_ui.sh

# Opens at http://localhost:7860
```

---

## 🛠️ Tool-Based Architecture

### 10 Agentic Tools

The agent now uses explicit tool definitions for transparency and modularity:

| # | Tool Name | Category | Purpose |
|---|-----------|----------|---------|
| 1 | `validate_question` | Validation | Check if question is answerable |
| 2 | `check_similar_questions` | Validation | Find cached answers |
| 3 | `get_relevant_tables` | Metadata | Find relevant database tables |
| 4 | `get_table_descriptions` | Metadata | Get detailed table schemas |
| 5 | `generate_sql_query` | Query Gen | Generate SQL with LLM |
| 6 | `validate_sql_syntax` | Query Gen | Validate SQL syntax |
| 7 | `execute_sql_query` | Execution | Run query safely |
| 8 | `create_visualization` | Visualization | Generate charts/tables |
| 9 | `submit_feedback` | Feedback | Record user feedback |
| 10 | `add_to_memory` | Memory | Manage conversation context |

### Tool Structure

Each tool has:
- **Name & Description** - Clear purpose statement
- **Category** - Tool classification
- **Input Schema** - Expected parameters with types
- **Output Schema** - Return value structure
- **Examples** - Sample inputs and outputs
- **Function Binding** - Actual implementation

### Example Tool Definition

```python
VALIDATE_QUESTION_TOOL = Tool(
    name="validate_question",
    description="""
    Validates if a question is relevant and answerable for text-to-SQL.
    
    Checks:
    - Is the question data-related?
    - Can it be answered with SQL?
    - Is it clear and specific enough?
    """,
    category=ToolCategory.VALIDATION,
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"}
        },
        "required": ["question"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "reason": {"type": "string"},
            "confidence": {"type": "number"}
        }
    },
    examples=[...],
    function=agent._tool_validate_question
)
```

---

## 📁 New Files Created

### UI Files (2)
```
src/ui/
├── gradio_app.py          # Main Gradio application (580 lines)
└── README.md              # UI documentation (350 lines)
```

### Tool Files (2)
```
src/agent/
├── tools.py               # Tool definitions (700 lines)
└── tool_agent.py          # Tool-based agent implementation (450 lines)
```

### Documentation (1)
```
docs/
└── TOOLS.md               # Complete tool reference guide (1,000+ lines)
```

### Scripts (1)
```
launch_ui.sh               # UI launch script
```

**Total:** 6 new files, ~3,000 lines of code

---

## 🚀 Usage

### Launch Gradio UI

```bash
./launch_ui.sh
```

Access at: `http://localhost:7860`

### Use Tool-Based Agent

```python
from src.agent.tool_agent import ToolBasedAgent
from src.utils.config import load_config

# Initialize
config = load_config()
agent = ToolBasedAgent(config)

# List available tools
tools = agent.get_available_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")

# Execute a tool
result = agent.execute_tool(
    tool_name="validate_question",
    parameters={"question": "Show top customers"}
)
print(result)
# {'valid': True, 'reason': '...', 'confidence': 0.95}

# Get tools by category
validation_tools = agent.get_tools_by_category("validation")
```

---

## 📊 Tool Workflow

### Standard Query Process

```
User Question
    ↓
[1] validate_question
    ↓ (if valid)
[2] check_similar_questions
    ↓ (if not cached)
[3] get_relevant_tables
    ↓
[4] generate_sql_query
    ↓
[5] validate_sql_syntax
    ↓ (if valid)
[6] execute_sql_query
    ↓
[7] create_visualization
    ↓
Return Results
    ↓ (optional)
[8] submit_feedback
```

### With Caching

```
User Question
    ↓
[1] validate_question
    ↓
[2] check_similar_questions
    → Cache Hit? → Return Cached Answer ✓
    ↓ Cache Miss
[3-7] Continue normal flow...
```

---

## 🎯 Benefits

### Tool-Based Architecture

✅ **Transparency** - Clear what each step does  
✅ **Modularity** - Tools work independently  
✅ **Testability** - Each tool tested in isolation  
✅ **Extensibility** - Easy to add new tools  
✅ **Observability** - Log which tools are called  
✅ **Documentation** - Self-documenting with schemas  

### Gradio UI

✅ **User-Friendly** - No coding required  
✅ **Interactive** - Real-time feedback  
✅ **Visual** - See data and charts immediately  
✅ **Exportable** - Download results as CSV  
✅ **Feedback Loop** - Improve system with user input  

---

## 📚 Documentation

### Quick Start
- [UI README](../src/ui/README.md) - Gradio UI guide
- [Tool Documentation](../docs/TOOLS.md) - Complete tool reference
- [Quick Reference](../docs/QUICK_REFERENCE.md) - Common tasks

### Technical
- [Architecture](../docs/ARCHITECTURE.md) - System design
- [API Reference](../docs/API.md) - REST API docs
- [Deployment](../docs/DEPLOYMENT.md) - Deployment options

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."
export HIVE_HOST="hive.company.com"
export HIVE_USER="username"
export HIVE_PASSWORD="password"

# Optional
export HIVE_PORT="10000"
export LOG_LEVEL="INFO"
```

### Dependencies

Added to `requirements.txt`:
```
gradio==4.15.0  # Gradio UI framework
```

---

## 📋 Testing

### Test Individual Tools

```python
from src.agent.tool_agent import ToolBasedAgent

agent = ToolBasedAgent(config)

# Test validation
result = agent.execute_tool(
    "validate_question",
    {"question": "Show revenue"}
)
assert result['valid'] == True

# Test metadata retrieval
result = agent.execute_tool(
    "get_relevant_tables",
    {"question": "Show customer data", "max_tables": 5}
)
assert len(result['tables']) > 0
```

### Test Gradio UI

```bash
# Launch UI
./launch_ui.sh

# Test in browser
# 1. Click "Initialize Agent"
# 2. Enter question: "What are the top 10 customers?"
# 3. Click Submit
# 4. Verify results appear in data viewer
# 5. Submit feedback
```

---

## 🎓 Example Queries

### Marketing
```
- What are the top 10 customers by lifetime value?
- Show customer acquisition trends by month
- Which products have the highest conversion rates?
```

### Operations
```
- Count active users in the last 30 days
- Show average response time by category
- List all failed transactions from yesterday
```

### Finance
```
- Calculate total revenue by region for Q4
- Show monthly recurring revenue growth
- What's the average order value by segment?
```

---

## 🔄 Migration Guide

### From Old Agent to Tool-Based Agent

**Before:**
```python
from src.agent.agent import TextToSQLAgent

agent = TextToSQLAgent(config)
result = agent.process_question("Show customers")
```

**After (with explicit tools):**
```python
from src.agent.tool_agent import ToolBasedAgent

agent = ToolBasedAgent(config)

# Option 1: Use high-level process_question (same as before)
result = agent.process_question("Show customers")

# Option 2: Use tools explicitly
validation = agent.execute_tool("validate_question", {"question": "Show customers"})
if validation['valid']:
    tables = agent.execute_tool("get_relevant_tables", {"question": "Show customers"})
    query_result = agent.execute_tool("generate_sql_query", {
        "question": "Show customers",
        "relevant_tables": tables['tables']
    })
```

Both agents are compatible - use `ToolBasedAgent` for transparency and observability.

---

## 🎉 Result

The Text-to-SQL Agent now has:

✅ **Modern Gradio UI** - Chat interface with data viewer  
✅ **Tool-Based Architecture** - 10 explicit, documented tools  
✅ **Complete Documentation** - 1,000+ lines of tool reference  
✅ **Easy Launch** - One command to start UI  
✅ **Production Ready** - Tested and documented  

### Key Files

- `src/ui/gradio_app.py` - Gradio UI application
- `src/agent/tools.py` - Tool definitions
- `src/agent/tool_agent.py` - Tool-based agent
- `docs/TOOLS.md` - Tool documentation
- `launch_ui.sh` - Launch script

---

**Launch UI:** `./launch_ui.sh`  
**View Tools:** See `docs/TOOLS.md`  
**Status:** ✅ Complete

---

*Version: 1.0.0*  
*Date: January 2026*
