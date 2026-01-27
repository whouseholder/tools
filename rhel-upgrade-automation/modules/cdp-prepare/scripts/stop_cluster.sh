#!/bin/bash
set -e

# Stop CDP cluster services via CM API
# Usage: stop_cluster.sh <cm_host> <cm_user> <cm_password> <cluster_name>

CM_HOST=$1
CM_USER=$2
CM_PASSWORD=$3
CLUSTER_NAME=$4
CM_API="http://${CM_HOST}:7180/api/v40"

echo "========================================="
echo "Stopping CDP Cluster Services"
echo "CM Server: $CM_HOST"
echo "Cluster: $CLUSTER_NAME"
echo "========================================="

# Function to call CM API
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

# Wait for command to complete
wait_for_command() {
    local command_id=$1
    local max_wait=1800  # 30 minutes
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
    
    echo "ERROR: Command timed out after ${max_wait}s"
    return 1
}

# Check CM is accessible
echo "Checking Cloudera Manager accessibility..."
if ! call_cm_api "GET" "/clusters" &> /dev/null; then
    echo "ERROR: Cannot connect to Cloudera Manager at $CM_HOST"
    echo "Please ensure CM is running and accessible"
    exit 1
fi

echo "CM is accessible"

# Get cluster services
echo "Getting cluster services..."
SERVICES=$(call_cm_api "GET" "/clusters/${CLUSTER_NAME}/services" | jq -r '.items[].name')

if [ -z "$SERVICES" ]; then
    echo "WARNING: No services found in cluster $CLUSTER_NAME"
    echo "Cluster may already be stopped or cluster name is incorrect"
    exit 0
fi

echo "Found services:"
echo "$SERVICES"

# Stop services in proper order
# Order matters: Stop dependent services before their dependencies

# 1. Stop HUE (user-facing)
if echo "$SERVICES" | grep -q "HUE"; then
    echo ""
    echo "Stopping HUE..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/HUE/commands/stop")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 2. Stop Impala
if echo "$SERVICES" | grep -q "IMPALA"; then
    echo ""
    echo "Stopping Impala..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/IMPALA/commands/stop")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 3. Stop Hive
if echo "$SERVICES" | grep -q "HIVE"; then
    echo ""
    echo "Stopping Hive..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/HIVE/commands/stop")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 4. Stop HBase
if echo "$SERVICES" | grep -q "HBASE"; then
    echo ""
    echo "Stopping HBase..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/HBASE/commands/stop")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 5. Stop YARN
if echo "$SERVICES" | grep -q "YARN"; then
    echo ""
    echo "Stopping YARN..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/YARN/commands/stop")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 6. Stop HDFS
if echo "$SERVICES" | grep -q "HDFS"; then
    echo ""
    echo "Stopping HDFS..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/HDFS/commands/stop")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# 7. Stop ZooKeeper (last - many services depend on it)
if echo "$SERVICES" | grep -q "ZOOKEEPER"; then
    echo ""
    echo "Stopping ZooKeeper..."
    RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/ZOOKEEPER/commands/stop")
    CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
        wait_for_command "$CMD_ID"
    fi
fi

# Stop any remaining services
echo ""
echo "Stopping any remaining services..."
for SERVICE in $SERVICES; do
    STATE=$(call_cm_api "GET" "/clusters/${CLUSTER_NAME}/services/${SERVICE}" | jq -r '.serviceState')
    
    if [ "$STATE" == "STARTED" ]; then
        echo "Stopping $SERVICE..."
        RESPONSE=$(call_cm_api "POST" "/clusters/${CLUSTER_NAME}/services/${SERVICE}/commands/stop")
        CMD_ID=$(echo "$RESPONSE" | jq -r '.id')
        if [ ! -z "$CMD_ID" ] && [ "$CMD_ID" != "null" ]; then
            wait_for_command "$CMD_ID" || true
        fi
    fi
done

# Final verification
echo ""
echo "Verifying all services are stopped..."
sleep 10

ALL_STOPPED=true
for SERVICE in $SERVICES; do
    STATE=$(call_cm_api "GET" "/clusters/${CLUSTER_NAME}/services/${SERVICE}" | jq -r '.serviceState')
    echo "$SERVICE: $STATE"
    
    if [ "$STATE" != "STOPPED" ] && [ "$STATE" != "NA" ]; then
        ALL_STOPPED=false
    fi
done

echo ""
echo "========================================="
if [ "$ALL_STOPPED" == "true" ]; then
    echo "All CDP services stopped successfully"
    echo "========================================="
    exit 0
else
    echo "WARNING: Some services may not be fully stopped"
    echo "Please verify manually via CM UI"
    echo "========================================="
    exit 0  # Don't fail the pipeline
fi


