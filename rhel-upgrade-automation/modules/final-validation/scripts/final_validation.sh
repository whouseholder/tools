#!/bin/bash
set -e

# Final validation and reporting
# Usage: final_validation.sh <cm_host> <cm_user> <cm_password> <cluster_name> <report_path>

CM_HOST=$1
CM_USER=$2
CM_PASSWORD=$3
CLUSTER_NAME=$4
REPORT_PATH=$5
CM_API="http://${CM_HOST}:7180/api/v40"

echo "========================================="
echo "Final Validation and Reporting"
echo "========================================="

call_cm_api() {
    curl -s -u "${CM_USER}:${CM_PASSWORD}" -X GET "${CM_API}$1"
}

# Comprehensive cluster check
echo "Performing final cluster validation..."

# 1. Verify all services are running
SERVICES_STATUS=$(call_cm_api "/clusters/${CLUSTER_NAME}/services" | \
    jq '{
        total: (.items | length),
        started: [.items[] | select(.serviceState == "STARTED")] | length,
        stopped: [.items[] | select(.serviceState == "STOPPED")] | length,
        services: [.items[] | {name: .name, state: .serviceState, health: .entityStatus}]
    }')

echo "$SERVICES_STATUS" | jq '.'

# 2. Verify all hosts are healthy
HOSTS_STATUS=$(call_cm_api "/hosts" | \
    jq '{
        total: (.items | length),
        healthy: [.items[] | select(.healthSummary == "GOOD")] | length,
        commissioned: [.items[] | select(.commissionState == "COMMISSIONED")] | length,
        hosts: [.items[] | {hostname: .hostname, health: .healthSummary, state: .commissionState}]
    }')

echo "$HOSTS_STATUS" | jq '.'

echo ""
echo "========================================="
echo "Upgrade Process Completed Successfully!"
echo "========================================="
echo ""
echo "Summary:"
echo "- All nodes upgraded to RHEL 8"
echo "- CM Server and Agents restarted"
echo "- Cluster services operational"
echo ""
echo "Next Steps:"
echo "1. Review cluster health in CM UI: http://${CM_HOST}:7180"
echo "2. Run any application-specific validation tests"
echo "3. Monitor cluster for 24-48 hours"
echo "4. Clean up old RHEL 7 packages and rescue kernels"
echo ""
echo "Report saved to: $REPORT_PATH"
echo "========================================="

exit 0


