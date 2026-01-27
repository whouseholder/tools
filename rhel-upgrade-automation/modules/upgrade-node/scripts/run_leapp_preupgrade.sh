#!/bin/bash
set -e

# Run Leapp preupgrade assessment and handle common issues
# Usage: run_leapp_preupgrade.sh <role>

ROLE=$1
LEAPP_REPORT="/var/log/leapp/leapp-report.txt"
LEAPP_LOG="/var/log/leapp/leapp-preupgrade.log"

echo "========================================="
echo "Running Leapp Pre-Upgrade Assessment"
echo "========================================="

# Clean up old leapp data
rm -rf /var/log/leapp/*
rm -rf /root/tmp_leapp_py3

# Disable third-party repositories temporarily
echo "Disabling third-party repositories..."
for repo in $(yum repolist | grep -v "rhel-" | grep -v "repo id" | awk '{print $1}'); do
    if [ ! -z "$repo" ] && [ "$repo" != "repo" ] && [ "$repo" != "repolist:" ]; then
        echo "Disabling: $repo"
        yum-config-manager --disable "$repo" 2>/dev/null || true
    fi
done

# Handle common blockers before running leapp
echo "Addressing common upgrade blockers..."

# Remove problematic packages
echo "Removing problematic packages..."
yum remove -y pam_pkcs11 redhat-upgrade-tool 2>/dev/null || true

# Update kernel to latest
echo "Updating kernel..."
yum update -y kernel
RUNNING_KERNEL=$(uname -r)
LATEST_KERNEL=$(rpm -q kernel | sort -V | tail -1 | sed 's/kernel-//')
if [ "$RUNNING_KERNEL" != "$LATEST_KERNEL" ]; then
    echo "WARNING: Kernel update requires reboot"
    echo "Running: $RUNNING_KERNEL"
    echo "Latest: $LATEST_KERNEL"
fi

# Ensure system is fully updated
echo "Ensuring system is fully updated..."
yum update -y

# Handle container-executor for CDP (if present)
if [ -f /opt/cloudera/parcels/CDH*/lib/hadoop-yarn/bin/container-executor ]; then
    echo "Found YARN container-executor - will need special handling"
    # We'll need to preserve setuid permissions
fi

# Run leapp preupgrade
echo "Running leapp preupgrade..."
leapp preupgrade --no-rhsm 2>&1 | tee /tmp/leapp-preupgrade-output.txt || {
    LEAPP_EXIT=$?
    echo "Leapp preupgrade exited with code: $LEAPP_EXIT"
}

# Check results
if [ -f "$LEAPP_REPORT" ]; then
    echo ""
    echo "========================================="
    echo "Leapp Pre-Upgrade Report Summary"
    echo "========================================="
    
    # Count issues by severity
    HIGH_ISSUES=$(grep -c "Risk Factor: high (inhibitor)" "$LEAPP_REPORT" || echo "0")
    MEDIUM_ISSUES=$(grep -c "Risk Factor: medium" "$LEAPP_REPORT" || echo "0")
    
    echo "High severity issues (inhibitors): $HIGH_ISSUES"
    echo "Medium severity issues: $MEDIUM_ISSUES"
    
    if [ "$HIGH_ISSUES" -gt 0 ]; then
        echo ""
        echo "High severity issues found:"
        grep -A 5 "Risk Factor: high (inhibitor)" "$LEAPP_REPORT" || true
        echo ""
        
        # Try to auto-remediate common issues
        echo "Attempting automatic remediation..."
        
        # Issue: Missing required answers
        if grep -q "missing required answers" "$LEAPP_REPORT"; then
            echo "Configuring required answers..."
            leapp answer --section remove_pam_pkcs11_module_check.confirm=True 2>/dev/null || true
        fi
        
        # Issue: Multiple kernel versions
        KERNEL_COUNT=$(rpm -q kernel | wc -l)
        if [ "$KERNEL_COUNT" -gt 2 ]; then
            echo "Removing old kernels..."
            package-cleanup -y --oldkernels --count=2 2>/dev/null || \
            yum install -y yum-utils && package-cleanup -y --oldkernels --count=2
        fi
        
        # Re-run preupgrade after remediation
        echo "Re-running preupgrade after remediation..."
        leapp preupgrade --no-rhsm 2>&1 | tee /tmp/leapp-preupgrade-output-retry.txt || true
        
        # Check if issues were resolved
        HIGH_ISSUES_AFTER=$(grep -c "Risk Factor: high (inhibitor)" "$LEAPP_REPORT" || echo "0")
        if [ "$HIGH_ISSUES_AFTER" -gt 0 ]; then
            echo ""
            echo "ERROR: Unable to auto-remediate all high severity issues"
            echo "Manual intervention required. See: $LEAPP_REPORT"
            exit 1
        fi
    fi
    
    echo ""
    echo "========================================="
    echo "Pre-upgrade assessment PASSED"
    echo "System is ready for upgrade"
    echo "========================================="
    
    # Save report for reference
    cp "$LEAPP_REPORT" /tmp/leapp-report-preupgrade.txt
    
else
    echo "ERROR: Leapp report not generated"
    echo "Check logs: $LEAPP_LOG"
    exit 1
fi

exit 0


