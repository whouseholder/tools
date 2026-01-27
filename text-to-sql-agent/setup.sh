#!/bin/bash

# Text-to-SQL Agent Setup Script

echo "=================================================="
echo "Text-to-SQL Agent - Setup Script"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo "❌ Error: Python 3.9+ is required"
    exit 1
fi

echo "✅ Python version OK"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/vector_db/chroma
mkdir -p data/feedback
mkdir -p data/cache
mkdir -p logs

echo "✅ Directories created"
echo ""

# Copy example config
if [ ! -f config/config.yaml ]; then
    echo "Creating configuration file..."
    cp config/config.example.yaml config/config.yaml
    echo "✅ Configuration file created at config/config.yaml"
    echo "⚠️  IMPORTANT: Edit config/config.yaml and add your API keys and database credentials"
else
    echo "⚠️  config/config.yaml already exists, skipping"
fi

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit config/config.yaml and add your credentials:"
echo "   - OpenAI/Anthropic API key"
echo "   - Hive database connection details"
echo ""
echo "2. Set environment variables (recommended):"
echo "   export OPENAI_API_KEY='your-key'"
echo "   export HIVE_USER='your-username'"
echo "   export HIVE_PASSWORD='your-password'"
echo ""
echo "3. Initialize metadata index:"
echo "   python scripts/init_vector_stores.py"
echo ""
echo "4. Run tests:"
echo "   python scripts/run_tests.py"
echo ""
echo "5. Start the application:"
echo "   python src/main.py"
echo ""
echo "6. Access the web UI:"
echo "   Open http://localhost:8000 in your browser"
echo "   Or open web_ui/frontend/index.html"
echo ""
