# 🚀 Text-to-SQL Agent - Quick Start

Your Text-to-SQL Agent is ready for local testing with the Gradio UI!

## One-Command Launch

```bash
cd /Users/whouseholder/Projects/text-to-sql-agent

# Set your API key
export OPENAI_API_KEY="sk-your-actual-key-here"

# Launch!
python launch.py
```

**Browser opens to:** http://localhost:7860

---

## What Happens Automatically

The launcher will:
1. ✅ Check your OpenAI API key
2. ✅ Create test database if missing (`data/telco_sample.db`)
3. ✅ Detect Python 3.14 and use simplified mode (without ChromaDB)
4. ✅ Launch Gradio UI with chat interface

---

## Try These Example Questions

Once the UI loads, try:

**Customer Analytics:**
```
What are the top 10 customers by lifetime value?
Which cities have the most active customers?
List customers with high churn risk on premium plans
```

**Revenue & Finance:**
```
Show total revenue by service plan
Calculate average customer lifetime value by plan type
Show monthly recurring revenue trend
```

**Network & Usage:**
```
What is the average data usage per customer?
How many customers made international calls last month?
Show device manufacturers by popularity
```

---

## Python 3.14 Simplified Mode

Your system has Python 3.14, which has compatibility issues with ChromaDB. The launcher automatically uses a **simplified mode**:

**What Works:**
- ✅ Natural language to SQL conversion (via OpenAI)
- ✅ SQLite query execution
- ✅ Interactive data tables
- ✅ Automatic chart generation
- ✅ CSV export
- ✅ Chat interface with history

**Full Agent Features (requires Python 3.12/3.13):**
- Vector store for Q&A examples
- Similarity checking for previous questions
- Advanced confidence scoring with feedback
- Metadata indexing from Hive metastore

---

## Troubleshooting

### API Key Not Found
```bash
export OPENAI_API_KEY="sk-proj-your-key-here"
```
Get your key at: https://platform.openai.com/api-keys

### Database Missing
The launcher auto-creates it, but if needed:
```bash
python scripts/create_telco_db.py
```

### Dependencies Missing
```bash
source venv/bin/activate
pip install gradio pandas plotly openai
```

### Port 7860 Already in Use
Edit line 94 in `launch.py` and change to `server_port=7861`

---

## Project Structure

```
text-to-sql-agent/
├── launch.py              # Main launcher (use this!)
├── src/
│   ├── ui/
│   │   ├── gradio_simple.py    # Simplified UI (Python 3.14)
│   │   └── gradio_app.py       # Full agent UI
│   └── agent/
│       ├── agent.py            # Core agent logic
│       └── tools.py            # Tool definitions
├── data/
│   └── telco_sample.db         # Test database
├── scripts/
│   ├── create_telco_db.py      # Database setup
│   └── test_telco_simple.py    # Standalone tests
└── docs/
    └── README.md               # Full documentation
```

---

## Next Steps

1. **Test the workflow** - Ask different types of questions
2. **Check the SQL** - Expand "Generated SQL Query" to see what was created
3. **Export results** - Use the "Export CSV" button to save data
4. **Review visualizations** - Charts are auto-generated for numeric data

---

## Full Documentation

- **Architecture**: `docs/ARCHITECTURE.md`
- **API Reference**: `docs/API.md`
- **Tools Documentation**: `docs/TOOLS.md`
- **Deployment**: `docs/DEPLOYMENT.md`
- **Telco Test Suite**: `docs/TELCO_TEST_SUITE.md`

---

**That's it! Just run `python launch.py` and start testing** 🚀
