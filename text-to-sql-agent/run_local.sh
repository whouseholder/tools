#!/bin/bash
# Quick launcher with prompts for easy local testing

set -e

echo "=========================================="
echo "Text-to-SQL Agent - Local Test Launcher"
echo "=========================================="
echo ""

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OpenAI API key not set"
    echo ""
    echo "You need an OpenAI API key to use this agent."
    echo ""
    echo "To set it:"
    echo "  export OPENAI_API_KEY='sk-your-actual-key-here'"
    echo ""
    echo "Get your key at: https://platform.openai.com/api-keys"
    echo ""
    exit 1
elif [[ "$OPENAI_API_KEY" == *"test"* ]] || [[ "$OPENAI_API_KEY" != "sk-"* ]]; then
    echo "⚠️  Invalid or test API key detected"
    echo ""
    echo "Current key: ${OPENAI_API_KEY:0:10}..."
    echo ""
    echo "Please set a real OpenAI API key:"
    echo "  export OPENAI_API_KEY='sk-your-actual-key-here'"
    echo ""
    exit 1
else
    echo "✓ OpenAI API key found: ${OPENAI_API_KEY:0:10}..."
fi

# Check database
if [ ! -f "data/telco_sample.db" ]; then
    echo ""
    echo "⚠️  Creating test database..."
    python scripts/create_telco_db.py
    if [ $? -eq 0 ]; then
        echo "✓ Database created"
    else
        echo "✗ Failed to create database"
        exit 1
    fi
else
    echo "✓ Database found"
fi

echo ""
echo "=========================================="
echo "Launching Gradio UI (Updated Agent)..."
echo "=========================================="
echo ""
echo "✓ Using consolidated TextToSQLAgent from src/agent/agent.py"
echo "✓ Agent auto-initializes on launch (no manual init required)"
echo ""
echo "The UI will open at: http://localhost:7860"
echo ""
echo "Example questions to try:"
echo "  • What are the top 10 customers by lifetime value?"
echo "  • Show total revenue by service plan"
echo "  • Which device manufacturers are most popular?"
echo "  • List customers with high churn risk (above 0.7)"
echo ""
echo "📊 Auto-Viz Feature:"
echo "  • Toggle the 'Auto-Viz' checkbox in the UI to enable/disable"
echo "  • When ENABLED: Charts auto-generated using LLM recommendations"
echo "  • When DISABLED: Request charts manually (e.g., 'show as bar chart')"
echo ""
echo "🔄 Follow-up Visualizations:"
echo "  1. Ask any question (with Auto-Viz OFF)"
echo "  2. Then ask: 'show that as a pie chart'"
echo "  3. Then ask: 'make it a bar chart'"
echo "  4. Charts update without re-querying the database!"
echo ""
echo "🔄 Reset Conversation:"
echo "  • Click 'Reset Conversation' button to start fresh"
echo "  • Generates new session ID and clears memory"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Launch
python launch.py
