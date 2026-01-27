#!/bin/bash
set -e

# Wait for all CM agents to connect
# Usage: wait_for_agents.sh <cm_host> <cm_user> <cm_password> <expected_count>

CM_HOST=$1
CM_USER=$2
CM_PASSWORD=$3
EXPECTED_COUNT=$4
CM_API="http://${CM_HOST}:7180/api/v40"
MAX_WAIT=600  # 10 minutes
ELAPSED=0

echo "========================================="
echo "Waiting for CM agents to connect"
echo "Expected agents: $EXPECTED_COUNT"
echo "========================================="

while [ $ELAPSED -lt $MAX_WAIT ]; do
    CONNECTED=$(curl -s -u "${CM_USER}:${CM_PASSWORD}" "${CM_API}/hosts" | jq '[.items[] | select(.commissionState == "COMMISSIONED")] | length')
    
    echo "Connected agents: $CONNECTED / $EXPECTED_COUNT"
    
    if [ "$CONNECTED" -ge "$EXPECTED_COUNT" ]; then
        echo ""
        echo "========================================="
        echo "All agents connected successfully"
        echo "Time taken: ${ELAPSED}s"
        echo "========================================="
        exit 0
    fi
    
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

echo "WARNING: Not all agents connected within ${MAX_WAIT}s"
echo "Connected: $CONNECTED / $EXPECTED_COUNT"
echo "Proceeding anyway..."
exit 0


