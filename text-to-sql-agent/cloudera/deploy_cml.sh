#!/bin/bash
#
# Deploy Text-to-SQL Agent to Cloudera Machine Learning
#
# Usage:
#   ./deploy_cml.sh <project-id> [options]
#
# Requirements:
#   - CML_API_KEY environment variable
#   - CML_HOST environment variable
#   - Python 3.9+ with cmlapi package

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Text-to-SQL Agent - CML Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check required environment variables
if [ -z "$CML_API_KEY" ]; then
    echo -e "${RED}✗ CML_API_KEY environment variable not set${NC}"
    echo ""
    echo "Get your API key from: CML UI -> User Settings -> API Keys"
    echo "Then run: export CML_API_KEY='your-key-here'"
    exit 1
fi

if [ -z "$CML_HOST" ]; then
    echo -e "${RED}✗ CML_HOST environment variable not set${NC}"
    echo ""
    echo "Set your CML workspace host:"
    echo "Example: export CML_HOST='ml-xxxxx.cml.company.com'"
    exit 1
fi

echo -e "${GREEN}✓${NC} CML_API_KEY is set"
echo -e "${GREEN}✓${NC} CML_HOST is set: $CML_HOST"
echo ""

# Check for project ID argument
if [ -z "$1" ]; then
    echo -e "${RED}✗ Project ID required${NC}"
    echo ""
    echo "Usage: $0 <project-id> [options]"
    echo ""
    echo "Get your Project ID from the CML UI:"
    echo "  Project -> Settings -> Project ID"
    exit 1
fi

PROJECT_ID="$1"
shift

echo -e "${BLUE}Project ID:${NC} $PROJECT_ID"
echo ""

# Parse optional arguments
MODEL_NAME="text-to-sql-agent"
CPU="2.0"
MEMORY="4"
REPLICAS="1"

while [[ $# -gt 0 ]]; do
    case $1 in
        --model-name)
            MODEL_NAME="$2"
            shift 2
            ;;
        --cpu)
            CPU="$2"
            shift 2
            ;;
        --memory)
            MEMORY="$2"
            shift 2
            ;;
        --replicas)
            REPLICAS="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}Deployment Configuration:${NC}"
echo "  Model Name: $MODEL_NAME"
echo "  CPU: $CPU cores"
echo "  Memory: ${MEMORY}GB"
echo "  Replicas: $REPLICAS"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found"

# Check if cmlapi is installed
if ! python3 -c "import cmlapi" &> /dev/null; then
    echo -e "${YELLOW}! cmlapi not installed${NC}"
    echo "  Installing cmlapi..."
    pip install cmlapi
fi

echo -e "${GREEN}✓${NC} cmlapi is available"
echo ""

# Verify configuration files exist
if [ ! -f "cloudera/cml_model.py" ]; then
    echo -e "${RED}✗ cloudera/cml_model.py not found${NC}"
    exit 1
fi

if [ ! -f "cloudera/cml_requirements.txt" ]; then
    echo -e "${RED}✗ cloudera/cml_requirements.txt not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Deployment files verified"
echo ""

# Run deployment script
echo -e "${BLUE}Starting deployment...${NC}"
echo ""

python3 cloudera/cml_deploy.py \
    --project-id "$PROJECT_ID" \
    --model-name "$MODEL_NAME" \
    --cpu "$CPU" \
    --memory "$MEMORY" \
    --replicas "$REPLICAS"

DEPLOY_EXIT_CODE=$?

echo ""
if [ $DEPLOY_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Deployment Successful!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test your deployment:"
    echo "     ./cloudera/test_cml.sh"
    echo ""
    echo "  2. View in CML UI:"
    echo "     https://$CML_HOST"
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Deployment Failed${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Check the logs above for error details."
    exit 1
fi
