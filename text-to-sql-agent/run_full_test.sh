#!/bin/bash

# Helper script to run full agent test

echo "============================================"
echo "Text-to-SQL Full Agent Test Runner"
echo "============================================"
echo ""

# Check if API key is provided as argument
if [ -n "$1" ]; then
    API_KEY="$1"
    echo "✓ Using API key from command line argument"
elif [ -n "$OPENAI_API_KEY" ]; then
    API_KEY="$OPENAI_API_KEY"
    echo "✓ Using API key from environment variable"
else
    echo "✗ No API key found!"
    echo ""
    echo "Please provide your OpenAI API key:"
    echo "  Option 1: ./run_full_test.sh 'sk-your-key-here'"
    echo "  Option 2: export OPENAI_API_KEY='sk-your-key-here' && ./run_full_test.sh"
    echo ""
    exit 1
fi

# Check if database exists
if [ ! -f "data/telco_sample.db" ]; then
    echo "✗ Database not found!"
    echo "Please run: python3 scripts/create_telco_db.py"
    exit 1
fi

echo "✓ Database found"
echo ""
echo "Starting full agent test with LLM generation..."
echo ""

# Run the test
./venv/bin/python scripts/test_full_agent.py "$API_KEY"
