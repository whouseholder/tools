#!/bin/bash
set -e

# Start CDP cluster services via CM API
# Usage: start_cluster.sh <cm_host> <cm_user> <cm_password> <cluster_name>

CM_HOST=$1
CM_USER=$2
CM_PASSWORD=$3
CLUSTER_NAME=$4
CM_API="http://${CM_HOST}:7180/api/v40"

echo "========================================="
echo "Starting CDP Cluster Services"
echo "CM Server: $CM_HOST"
echo "Cluster: $CLUSTER_NAME"
echo "========================================="

call_cm_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -z "$data" ]; then
        curl -s -u "${CM_USER}:${CM_PASSWORD}" -X "$method" "${CM_API}${endpoint}"
    else
        curl -s -u "${CM_USER}:${CM_PASSWORD}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${CM_API}${endpoint}"
    fi
}

wait_for_command() {
    local command_id=$1
    local max_wait=1800
    local elapsed=0
    
    echo "Waiting for command $command_id to complete..."
    
    while [ $elapsed -lt $max_wait ]; do
        STATUS=$(call_cm_api "GET" "/commands/${command_id}" | jq -r '.active')
        
        if [ "$STATUS" == "false" ]; then
            SUCCESS=$(call_cm_api "GET" "/commands/${command_id}" | jq -r '.success')
            if [ "$SUCCESS" == "true" ]; then
                echo "Command completed successfully"
                return 0
            else
                echo "Command failed"
                return 1
            fi
        fi
        
        sleep 10
        elapsed=$((elapsed + 10))
        
        if [ $((elapsed % 60)) -eq 0 ]; then
            echo "Still waiting... (${elapsed}s elapsed)"
        fi
    done
    
    echo "ERROR: Command timed out"
    return 1
}

# Get cluster services
SERVICES=$(call_cm_api "GET" "/clusters/${CLUSTER_NAME}/services" | jq -r '.items[].name')

echo "Found services:"
echo "$SERVICES"

# Start services in proper order
# Order matters: Start dependencies before dependent services

# 1. Start ZooKeeper first (many services depend on it)
if echo "$SERVICES" | grep -q "ZOOKEEPER"; then
    echo ""
    echo "Starting ZooKeeper..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/ZOOKEEPER/commands/start")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 2. Start HDFS
if echo "$SERVICES" | grep -q "HDFS"; then
    echo ""
    echo "Starting HDFS..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/HDFS/commands/start")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 3. Start YARN
if echo "$SERVICES" | grep -q "YARN"; then
    echo ""
    echo "Starting YARN..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/YARN/commands/start")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 4. Start HBase
if echo "$SERVICES" | grep -q "HBASE"; then
    echo ""
    echo "Starting HBase..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/HBASE/commands/start")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 5. Start Hive
if echo "$SERVICES" | grep -q "HIVE"; then
    echo ""
    echo "Starting Hive..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/HIVE/commands/start")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 6. Start Impala
if echo "$SERVICES" | grep -q "IMPALA"; then
    echo ""
    echo "Starting Impala..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/IMPALA/commands/start")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 7. Start HUE (last - user-facing)
if echo "$SERVICES" | grep -q "HUE"; then
    echo ""
    echo "Starting HUE..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/HUE/commands/start")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# Start any remaining services
echo ""
echo "Starting any remaining services..."
for SERVICE in $SERVICES; do
    STATE=$(call_cm_api "GET" "/clusters/${CLUSTER_NAME}/services/${SERVICE}" | jq -r '.serviceState')
    
    if [ "$STATE" == "STOPPED" ]; then
        echo "Starting $SERVICE..."
        RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/${SERVICE}/commands/start")
        CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
        if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
            wait_for_command "$CMD_ID" || true
        fi
    fi
done

echo ""
echo "========================================="
echo "All CDP services started"
echo "========================================="
exit 0


