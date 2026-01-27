#!/bin/bash
# Quick demonstration of the Iceberg Metadata Sync tool

echo "=========================================="
echo "Iceberg Metadata Sync - Quick Demo"
echo "=========================================="
echo ""

cd "$(dirname "$0")/.."

echo "Project Statistics:"
echo "-------------------"
echo "Source Code Files: $(find src -name '*.py' | wc -l | xargs)"
echo "Test Files: $(find tests -name 'test_*.py' | wc -l | xargs)"
echo "Lines of Code: $(find src -name '*.py' -exec wc -l {} + | tail -1 | awk '{print $1}')"
echo ""

echo "Running Tests..."
echo "-------------------"
venv/bin/python -m pytest tests/unit/ tests/integration/test_simple_workflow.py -v --tb=short

echo ""
echo "=========================================="
echo "✅ Demo Complete!"
echo "=========================================="
echo ""
echo "To use the tool:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Run sync:"
echo "     python -m src.sync_manager \\"
echo "       --replicated-path /path/to/replicated/warehouse \\"
echo "       --catalog dr_catalog \\"
echo "       --database mydb \\"
echo "       --table mytable \\"
echo "       --warehouse /path/to/warehouse"
echo ""
echo "For more info:"
echo "  - README.md - Project overview"
echo "  - FINAL_SUMMARY.md - Complete summary"
echo "  - docs/USAGE.md - Detailed usage guide"
echo "  - examples/ - Code examples"
echo ""

