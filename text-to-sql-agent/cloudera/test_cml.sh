#!/bin/bash
#
# Test deployed CML Model
#
# Usage:
#   ./test_cml.sh <access-key> [question]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Text-to-SQL Agent - CML Model Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check CML_HOST
if [ -z "$CML_HOST" ]; then
    echo -e "${RED}✗ CML_HOST environment variable not set${NC}"
    exit 1
fi

# Check access key
if [ -z "$1" ]; then
    echo -e "${RED}✗ Access key required${NC}"
    echo ""
    echo "Usage: $0 <access-key> [question]"
    exit 1
fi

ACCESS_KEY="$1"
QUESTION="${2:-What are the top 10 customers by revenue?}"

echo -e "${BLUE}Testing model with:${NC}"
echo "  Host: $CML_HOST"
echo "  Question: $QUESTION"
echo ""

# Run test
python3 cloudera/cml_test_model.py \
    --host "$CML_HOST" \
    --access-key "$ACCESS_KEY" \
    --question "$QUESTION"

echo ""
echo -e "${GREEN}✓ Test complete${NC}"
