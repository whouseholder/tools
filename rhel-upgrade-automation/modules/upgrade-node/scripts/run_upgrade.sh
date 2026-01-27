#!/bin/bash
set -e

# Execute RHEL upgrade using Leapp
# Usage: run_upgrade.sh <target_version> <role>

TARGET_VERSION=$1
ROLE=$2
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================="
echo "Starting RHEL Upgrade"
echo "Host: $(hostname)"
echo "Role: $ROLE"
echo "Current: $(cat /etc/redhat-release)"
echo "Target: RHEL $TARGET_VERSION"
echo "Time: $(date)"
echo "========================================="

# Ensure CDP services are stopped
if systemctl list-unit-files | grep -q cloudera-scm; then
    echo "Ensuring CDP services are stopped..."
    
    systemctl stop cloudera-scm-agent 2>/dev/null || true
    
    if [ "$ROLE" == "master" ]; then
        systemctl stop cloudera-scm-server 2>/dev/null || true
    fi
    
    # Verify stopped
    sleep 5
    if systemctl is-active --quiet cloudera-scm-agent; then
        echo "WARNING: cloudera-scm-agent still running"
    fi
fi

# Final system update before upgrade
echo "Performing final system update..."
yum clean all
yum update -y

# Clear any locks
rm -f /var/run/yum.pid 2>/dev/null || true

# Set target version if specified
if [ ! -z "$TARGET_VERSION" ]; then
    echo "Setting target version to RHEL $TARGET_VERSION..."
    # Note: Leapp will upgrade to latest RHEL 8 by default
    # Specific version targeting may require additional configuration
fi

# Create pre-upgrade snapshot marker
cat > /root/pre-upgrade-state.txt <<EOF
Hostname: $(hostname)
Role: $ROLE
Pre-upgrade OS: $(cat /etc/redhat-release)
Pre-upgrade Kernel: $(uname -r)
Upgrade started: $(date -Iseconds)
Target: RHEL $TARGET_VERSION
EOF

# Run the upgrade
echo ""
echo "========================================="
echo "Executing: leapp upgrade"
echo "This will:"
echo "  1. Download RHEL 8 packages"
echo "  2. Prepare upgrade environment"
echo "  3. Configure system for reboot"
echo "  4. Initiate automatic reboot"
echo "========================================="
echo ""

# Execute leapp upgrade
leapp upgrade --no-rhsm 2>&1 | tee /var/log/leapp/leapp-upgrade-execution.log

# Check if upgrade was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "Leapp upgrade preparation completed"
    echo "System will now reboot to complete upgrade"
    echo "========================================="
    
    # Create marker for post-upgrade verification
    cat > /root/upgrade-in-progress.marker <<EOF
{
  "hostname": "$(hostname)",
  "role": "$ROLE",
  "upgrade_started": "$(date -Iseconds)",
  "target_version": "$TARGET_VERSION",
  "status": "rebooting"
}
EOF
    
    # Sync filesystems
    sync
    
    # Log final message
    logger "RHEL upgrade: Rebooting to complete upgrade to RHEL $TARGET_VERSION"
    
    # Reboot to complete upgrade
    echo "Rebooting in 10 seconds..."
    sleep 10
    reboot
    
else
    echo "ERROR: Leapp upgrade failed"
    echo "Check logs: /var/log/leapp/"
    
    # Save failure state
    cat > /root/upgrade-failed.marker <<EOF
{
  "hostname": "$(hostname)",
  "role": "$ROLE",
  "upgrade_failed": "$(date -Iseconds)",
  "target_version": "$TARGET_VERSION",
  "status": "failed"
}
EOF
    
    exit 1
fi


