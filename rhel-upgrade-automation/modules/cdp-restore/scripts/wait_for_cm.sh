#!/bin/bash
set -e

# Wait for Cloudera Manager to be ready
# Usage: wait_for_cm.sh <cm_host> <cm_user> <cm_password>

CM_HOST=$1
CM_USER=$2
CM_PASSWORD=$3
CM_API="http://${CM_HOST}:7180/api/v40"
MAX_WAIT=600  # 10 minutes
ELAPSED=0

echo "========================================="
echo "Waiting for Cloudera Manager to be ready"
echo "CM Server: $CM_HOST"
echo "========================================="

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -s -u "${CM_USER}:${CM_PASSWORD}" "${CM_API}/cm/version" &> /dev/null; then
        VERSION=$(curl -s -u "${CM_USER}:${CM_PASSWORD}" "${CM_API}/cm/version" | jq -r '.version')
        echo ""
        echo "========================================="
        echo "Cloudera Manager is ready"
        echo "Version: $VERSION"
        echo "Time taken: ${ELAPSED}s"
        echo "========================================="
        exit 0
    fi
    
    if [ $((ELAPSED % 30)) -eq 0 ]; then
        echo "Still waiting for CM... (${ELAPSED}s elapsed)"
    fi
    
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

echo "ERROR: Cloudera Manager did not become ready within ${MAX_WAIT}s"
exit 1


