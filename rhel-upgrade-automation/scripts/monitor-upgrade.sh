#!/bin/bash

# Real-time upgrade progress monitor
# Run this in a separate terminal while upgrade is running

# Load configuration
if [ ! -f terraform.tfvars ]; then
    echo "Error: terraform.tfvars not found"
    exit 1
fi

CM_SERVER=$(grep cm_server_host terraform.tfvars | cut -d '"' -f2)
CM_USER=$(grep cm_api_user terraform.tfvars | cut -d '"' -f2)
CM_PASS=$(grep cm_api_password terraform.tfvars | cut -d '"' -f2)
SSH_KEY=$(grep ssh_private_key terraform.tfvars | cut -d '"' -f2)
SSH_KEY="${SSH_KEY/#\~/$HOME}"

# Get list of hosts
HOSTS=$(grep -A 1000 'cluster_hosts = \[' terraform.tfvars | grep 'hostname' | cut -d '"' -f2)

START_TIME=$(date +%s)

while true; do
    clear
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║           RHEL 7.9 → 8.10 Upgrade Progress Monitor                ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Calculate elapsed time
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    HOURS=$((ELAPSED / 3600))
    MINUTES=$(((ELAPSED % 3600) / 60))
    SECONDS=$((ELAPSED % 60))
    
    echo "⏱️  Time Elapsed: ${HOURS}h ${MINUTES}m ${SECONDS}s"
    echo "🕐 Current Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📊 HOSTS STATUS"
    echo "═══════════════════════════════════════════════════════════════════"
    
    RHEL7_COUNT=0
    RHEL8_COUNT=0
    UNREACHABLE_COUNT=0
    
    for host in $HOSTS; do
        # Try to get OS version
        VERSION=$(ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
                  root@$host "cat /etc/redhat-release 2>/dev/null" 2>/dev/null || echo "UNREACHABLE")
        
        # Determine status icon
        if echo "$VERSION" | grep -q "release 8"; then
            STATUS="✅ RHEL 8"
            ((RHEL8_COUNT++))
        elif echo "$VERSION" | grep -q "release 7"; then
            STATUS="⏳ RHEL 7"
            ((RHEL7_COUNT++))
        else
            STATUS="❌ UNREACHABLE"
            ((UNREACHABLE_COUNT++))
        fi
        
        printf "%-30s %s\n" "$host" "$STATUS"
    done
    
    echo ""
    echo "Summary: ✅ $RHEL8_COUNT upgraded  |  ⏳ $RHEL7_COUNT pending  |  ❌ $UNREACHABLE_COUNT unreachable"
    echo ""
    
    echo "═══════════════════════════════════════════════════════════════════"
    echo "🔧 CLOUDERA MANAGER STATUS"
    echo "═══════════════════════════════════════════════════════════════════"
    
    # Check if CM is reachable
    if curl -s -u "${CM_USER}:${CM_PASS}" "http://${CM_SERVER}:7180/api/v40/cm/version" &> /dev/null; then
        echo "CM Server: ✅ Online at $CM_SERVER"
        echo ""
        
        # Get cluster services
        CLUSTER_NAME=$(grep cluster_name terraform.tfvars | cut -d '"' -f2)
        SERVICES=$(curl -s -u "${CM_USER}:${CM_PASS}" \
                   "http://${CM_SERVER}:7180/api/v40/clusters/${CLUSTER_NAME}/services" 2>/dev/null)
        
        if [ ! -z "$SERVICES" ]; then
            echo "Services:"
            echo "$SERVICES" | jq -r '.items[] | "  \(.name): \(.serviceState)"' 2>/dev/null || echo "  Unable to parse services"
        else
            echo "  No services data available"
        fi
    else
        echo "CM Server: ⏳ Offline or unreachable (may be upgrading)"
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📁 PROGRESS FILES"
    echo "═══════════════════════════════════════════════════════════════════"
    
    if [ -d "/backup/rhel-upgrade/pre-upgrade-reports" ]; then
        PRE_COUNT=$(ls -1 /backup/rhel-upgrade/pre-upgrade-reports/*.json 2>/dev/null | wc -l)
        echo "Pre-upgrade reports: $PRE_COUNT files"
    fi
    
    if [ -d "/tmp/post-upgrade-reports" ]; then
        POST_COUNT=$(ls -1 /tmp/post-upgrade-reports/*.json 2>/dev/null | wc -l)
        echo "Post-upgrade reports: $POST_COUNT files"
    fi
    
    if [ -f "terraform-output.log" ]; then
        LOG_SIZE=$(du -h terraform-output.log 2>/dev/null | cut -f1)
        LAST_LINE=$(tail -1 terraform-output.log 2>/dev/null | cut -c1-60)
        echo "Terraform log: $LOG_SIZE"
        echo "Last line: $LAST_LINE..."
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "Press Ctrl+C to exit monitoring (upgrade will continue)"
    echo "Refreshing in 30 seconds..."
    echo "═══════════════════════════════════════════════════════════════════"
    
    sleep 30
done


