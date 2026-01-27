#!/bin/bash
set -e

# Perform CDP cluster health check
# Usage: health_check.sh <cm_host> <cm_user> <cm_password> <cluster_name>

CM_HOST=$1
CM_USER=$2
CM_PASSWORD=$3
CLUSTER_NAME=$4
CM_API="http://${CM_HOST}:7180/api/v40"

echo "========================================="
echo "CDP Cluster Health Check"
echo "========================================="

call_cm_api() {
    curl -s -u "${CM_USER}:${CM_PASSWORD}" -X GET "${CM_API}$1"
}

# Check cluster health
echo "Checking cluster health..."
CLUSTER_HEALTH=$(call_cm_api "/clusters/${CLUSTER_NAME}" | jq -r '.entityStatus')
echo "Cluster health: $CLUSTER_HEALTH"

# Check service health
echo ""
echo "Service Status:"
echo "========================================="
call_cm_api "/clusters/${CLUSTER_NAME}/services" | \
    jq -r '.items[] | "\(.name): \(.serviceState) - \(.entityStatus)"'

# Count services
TOTAL_SERVICES=$(call_cm_api "/clusters/${CLUSTER_NAME}/services" | jq '.items | length')
STARTED_SERVICES=$(call_cm_api "/clusters/${CLUSTER_NAME}/services" | \
    jq '[.items[] | select(.serviceState == "STARTED")] | length')

echo "========================================="
echo "Started services: $STARTED_SERVICES / $TOTAL_SERVICES"

# Check hosts
echo ""
echo "Host Status:"
echo "========================================="
call_cm_api "/hosts" | \
    jq -r '.items[] | "\(.hostname): \(.healthSummary) - \(.commissionState)"'

TOTAL_HOSTS=$(call_cm_api "/hosts" | jq '.items | length')
HEALTHY_HOSTS=$(call_cm_api "/hosts" | \
    jq '[.items[] | select(.healthSummary == "GOOD")] | length')

echo "========================================="
echo "Healthy hosts: $HEALTHY_HOSTS / $TOTAL_HOSTS"

echo ""
echo "========================================="
if [ "$CLUSTER_HEALTH" == "GOOD" ] || [ "$CLUSTER_HEALTH" == "CONCERNING" ]; then
    echo "Cluster health check PASSED"
    echo "========================================="
    exit 0
else
    echo "WARNING: Cluster health may need attention"
    echo "Please review via CM UI: http://${CM_HOST}:7180"
    echo "========================================="
    exit 0  # Don't fail the pipeline
fi


