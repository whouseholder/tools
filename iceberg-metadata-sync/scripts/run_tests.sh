#!/bin/bash
# Run all tests for iceberg-metadata-sync

set -e

echo "=================================================="
echo "Running Iceberg Metadata Sync Tests"
echo "=================================================="
echo ""

cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "=================================================="
echo "Running Unit Tests"
echo "=================================================="
echo ""

# Run unit tests
python -m pytest tests/unit/ -v --tb=short

echo ""
echo "=================================================="
echo "Running Integration Tests"
echo "=================================================="
echo ""

# Run integration tests (these use PySpark and take longer)
python -m pytest tests/integration/ -v --tb=short -s

echo ""
echo "=================================================="
echo "Test Summary"
echo "=================================================="
echo ""
echo "✅ All tests completed successfully!"
echo ""

