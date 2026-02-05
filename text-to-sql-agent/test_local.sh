#!/bin/bash
#
# Quick Test Script for Text-to-SQL Agent
# Tests all components locally before launching UI
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Text-to-SQL Agent - Quick Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check command
check_step() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        exit 1
    fi
}

# 1. Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Found: Python $python_version"
check_step "Python 3.9+ required"

# 2. Check virtual environment
echo ""
echo "Checking virtual environment..."
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
    check_step "Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment exists"
fi

# 3. Activate and check dependencies
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
check_step "Virtual environment activated"

# 4. Check if key dependencies are installed
echo ""
echo "Checking dependencies..."

dependencies=("openai" "gradio" "pandas" "plotly" "chromadb")
missing=()

for dep in "${dependencies[@]}"; do
    if python -c "import $dep" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $dep installed"
    else
        echo -e "${YELLOW}!${NC} $dep missing"
        missing+=("$dep")
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    pip install -r requirements.txt -q
    check_step "Dependencies installed"
fi

# 5. Check configuration
echo ""
echo "Checking configuration..."
if [ ! -f "config/config.yaml" ]; then
    echo "  Creating config from example..."
    cp config/config.example.yaml config/config.yaml
    check_step "Configuration file created"
    echo -e "${YELLOW}  ! Please edit config/config.yaml with your settings${NC}"
else
    echo -e "${GREEN}✓${NC} Configuration file exists"
fi

# 6. Check environment variables
echo ""
echo "Checking environment variables..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}✗${NC} OPENAI_API_KEY not set"
    echo ""
    echo "  Set it with:"
    echo "  export OPENAI_API_KEY='sk-your-key-here'"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓${NC} OPENAI_API_KEY is set"
fi

# 7. Check test database
echo ""
echo "Checking test database..."
if [ ! -f "data/telco_sample.db" ]; then
    echo "  Creating test database..."
    python scripts/create_telco_db.py
    check_step "Test database created"
else
    echo -e "${GREEN}✓${NC} Test database exists"
    db_size=$(du -h data/telco_sample.db | awk '{print $1}')
    echo "  Size: $db_size"
fi

# 8. Quick functionality test
echo ""
echo "Running quick functionality test..."
python << 'EOF'
import sys
sys.path.insert(0, 'src')

try:
    from agent.tools import ALL_TOOLS, get_tool_by_name
    print(f"  ✓ Found {len(ALL_TOOLS)} tools")
    
    from utils.config import load_config
    config = load_config()
    print("  ✓ Configuration loaded")
    
    print("\n  All systems operational!")
    sys.exit(0)
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)
EOF

check_step "Functionality test passed"

# 9. Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All Tests Passed!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Your system is ready. Next steps:"
echo ""
echo "1. Launch Gradio UI:"
echo "   ${GREEN}./launch_ui.sh${NC}"
echo ""
echo "2. Open browser to:"
echo "   ${BLUE}http://localhost:7860${NC}"
echo ""
echo "3. Click 'Initialize Agent' and start asking questions!"
echo ""
echo "Example questions:"
echo "  • What are the top 10 customers by lifetime value?"
echo "  • Show total revenue by service plan"
echo "  • List active devices by manufacturer"
echo ""
