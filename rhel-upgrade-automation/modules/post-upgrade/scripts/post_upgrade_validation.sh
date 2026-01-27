#!/bin/bash
set -e

# Post-upgrade validation script
# Usage: post_upgrade_validation.sh <role> <expected_version>

ROLE=$1
EXPECTED_VERSION=$2
REPORT_FILE="/tmp/post_upgrade_report.json"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0
ISSUES=()
WARNINGS=()

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS+=("$1")
    ((CHECKS_WARNING++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ISSUES+=("$1")
    ((CHECKS_FAILED++))
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((CHECKS_PASSED++))
}

init_report() {
    cat > $REPORT_FILE <<EOF
{
  "hostname": "$(hostname)",
  "timestamp": "$(date -Iseconds)",
  "role": "$ROLE",
  "expected_version": "$EXPECTED_VERSION",
  "checks": {
EOF
}

add_check_result() {
    local check_name=$1
    local status=$2
    local message=$3
    
    cat >> $REPORT_FILE <<EOF
    "$check_name": {
      "status": "$status",
      "message": "$message"
    },
EOF
}

finalize_report() {
    sed -i '$ s/,$//' $REPORT_FILE
    cat >> $REPORT_FILE <<EOF
  },
  "summary": {
    "passed": $CHECKS_PASSED,
    "failed": $CHECKS_FAILED,
    "warnings": $CHECKS_WARNING,
    "issues": $(printf '%s\n' "${ISSUES[@]}" | jq -R . | jq -s .),
    "warnings_list": $(printf '%s\n' "${WARNINGS[@]}" | jq -R . | jq -s .)
  }
}
EOF
}

# Check 1: OS Version
check_os_version() {
    log_info "Checking OS version..."
    
    if [ -f /etc/redhat-release ]; then
        VERSION=$(cat /etc/redhat-release)
        if echo "$VERSION" | grep -q "release 8"; then
            log_pass "Successfully upgraded to RHEL 8: $VERSION"
            add_check_result "os_version" "pass" "$VERSION"
        else
            log_error "Not running RHEL 8: $VERSION"
            add_check_result "os_version" "fail" "$VERSION"
        fi
    else
        log_error "/etc/redhat-release not found"
        add_check_result "os_version" "fail" "Release file not found"
    fi
}

# Check 2: Kernel Version
check_kernel_version() {
    log_info "Checking kernel version..."
    
    KERNEL=$(uname -r)
    if echo "$KERNEL" | grep -q "el8"; then
        log_pass "Running RHEL 8 kernel: $KERNEL"
        add_check_result "kernel_version" "pass" "$KERNEL"
    else
        log_error "Not running RHEL 8 kernel: $KERNEL"
        add_check_result "kernel_version" "fail" "$KERNEL"
    fi
}

# Check 3: System Status
check_system_status() {
    log_info "Checking system status..."
    
    SYS_STATUS=$(systemctl is-system-running 2>/dev/null || echo "unknown")
    if [ "$SYS_STATUS" == "running" ] || [ "$SYS_STATUS" == "degraded" ]; then
        log_pass "System is $SYS_STATUS"
        add_check_result "system_status" "pass" "$SYS_STATUS"
    else
        log_warn "System status: $SYS_STATUS"
        add_check_result "system_status" "warning" "$SYS_STATUS"
    fi
}

# Check 4: Failed Services
check_failed_services() {
    log_info "Checking for failed services..."
    
    FAILED_COUNT=$(systemctl list-units --failed --no-pager --no-legend | wc -l)
    if [ $FAILED_COUNT -eq 0 ]; then
        log_pass "No failed services"
        add_check_result "failed_services" "pass" "None"
    else
        FAILED_SERVICES=$(systemctl list-units --failed --no-pager --no-legend | awk '{print $1}')
        log_warn "$FAILED_COUNT service(s) failed: $FAILED_SERVICES"
        add_check_result "failed_services" "warning" "$FAILED_SERVICES"
    fi
}

# Check 5: Network Connectivity
check_network() {
    log_info "Checking network connectivity..."
    
    # Check if network is up
    if ip link show | grep -q "state UP"; then
        log_pass "Network interfaces are up"
        add_check_result "network_interfaces" "pass" "UP"
    else
        log_error "No network interfaces are up"
        add_check_result "network_interfaces" "fail" "DOWN"
    fi
    
    # Check DNS
    if nslookup redhat.com &> /dev/null; then
        log_pass "DNS resolution working"
        add_check_result "network_dns" "pass" "OK"
    else
        log_error "DNS resolution not working"
        add_check_result "network_dns" "fail" "Failed"
    fi
}

# Check 6: Disk Space
check_disk_space() {
    log_info "Checking disk space..."
    
    # Check /boot
    BOOT_USAGE=$(df -h /boot | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $BOOT_USAGE -lt 90 ]; then
        log_pass "/boot usage: ${BOOT_USAGE}%"
        add_check_result "disk_boot" "pass" "${BOOT_USAGE}% used"
    else
        log_warn "/boot usage high: ${BOOT_USAGE}%"
        add_check_result "disk_boot" "warning" "${BOOT_USAGE}% used"
    fi
    
    # Check /
    ROOT_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $ROOT_USAGE -lt 90 ]; then
        log_pass "/ usage: ${ROOT_USAGE}%"
        add_check_result "disk_root" "pass" "${ROOT_USAGE}% used"
    else
        log_warn "/ usage high: ${ROOT_USAGE}%"
        add_check_result "disk_root" "warning" "${ROOT_USAGE}% used"
    fi
}

# Check 7: SELinux Status
check_selinux() {
    log_info "Checking SELinux status..."
    
    if command -v getenforce &> /dev/null; then
        SELINUX_STATUS=$(getenforce)
        log_pass "SELinux status: $SELINUX_STATUS"
        add_check_result "selinux" "pass" "$SELINUX_STATUS"
        
        # Check for denials
        if [ -f /var/log/audit/audit.log ]; then
            DENIALS=$(grep "avc.*denied" /var/log/audit/audit.log | wc -l)
            if [ $DENIALS -gt 100 ]; then
                log_warn "High number of SELinux denials: $DENIALS"
                add_check_result "selinux_denials" "warning" "$DENIALS denials"
            else
                log_pass "SELinux denials: $DENIALS"
                add_check_result "selinux_denials" "pass" "$DENIALS denials"
            fi
        fi
    else
        log_warn "SELinux tools not found"
        add_check_result "selinux" "warning" "Not available"
    fi
}

# Check 8: Firewall
check_firewall() {
    log_info "Checking firewall status..."
    
    if systemctl is-active --quiet firewalld; then
        log_pass "Firewalld is active"
        add_check_result "firewall" "pass" "Active"
    elif systemctl is-active --quiet iptables; then
        log_pass "iptables is active"
        add_check_result "firewall" "pass" "Active (iptables)"
    else
        log_warn "No firewall service active"
        add_check_result "firewall" "warning" "Not active"
    fi
}

# Check 9: Package Manager
check_package_manager() {
    log_info "Checking package manager..."
    
    # Test dnf
    if command -v dnf &> /dev/null; then
        if dnf check-update &> /dev/null; then
            log_pass "DNF is working"
            add_check_result "package_manager" "pass" "DNF OK"
        else
            # check-update returns 100 if updates available, which is OK
            if [ $? -eq 100 ]; then
                log_pass "DNF is working (updates available)"
                add_check_result "package_manager" "pass" "DNF OK"
            else
                log_warn "DNF may have issues"
                add_check_result "package_manager" "warning" "DNF issues"
            fi
        fi
    else
        log_error "DNF not found"
        add_check_result "package_manager" "fail" "DNF not found"
    fi
}

# Check 10: Subscription Status
check_subscription() {
    log_info "Checking subscription status..."
    
    if command -v subscription-manager &> /dev/null; then
        if subscription-manager status | grep -q "Overall Status: Current"; then
            log_pass "Valid subscription"
            add_check_result "subscription" "pass" "Active"
        else
            log_warn "Subscription may need attention"
            add_check_result "subscription" "warning" "Check status"
        fi
    else
        log_info "subscription-manager not found"
        add_check_result "subscription" "info" "Not available"
    fi
}

# Check 11: CDP Agent Status (if applicable)
check_cdp_agent() {
    log_info "Checking CDP agent status..."
    
    if systemctl list-unit-files | grep -q cloudera-scm-agent; then
        # Agent should still be stopped at this point
        if systemctl is-active --quiet cloudera-scm-agent; then
            log_warn "CDP agent is running (should be stopped during upgrade)"
            add_check_result "cdp_agent" "warning" "Running"
        else
            log_pass "CDP agent is stopped (as expected)"
            add_check_result "cdp_agent" "pass" "Stopped"
        fi
        
        # Check agent installation
        if [ -d /opt/cloudera/cm-agent ]; then
            log_pass "CDP agent files present"
            add_check_result "cdp_agent_files" "pass" "Present"
        else
            log_error "CDP agent files missing"
            add_check_result "cdp_agent_files" "fail" "Missing"
        fi
    else
        log_info "CDP agent not installed on this host"
        add_check_result "cdp_agent" "info" "Not installed"
    fi
}

# Check 12: CDP Parcels (if applicable)
check_cdp_parcels() {
    log_info "Checking CDP parcels..."
    
    if [ -d /opt/cloudera/parcels ]; then
        PARCEL_COUNT=$(ls -1 /opt/cloudera/parcels | grep -v "\.parcel" | wc -l)
        if [ $PARCEL_COUNT -gt 0 ]; then
            log_pass "CDP parcels present: $PARCEL_COUNT"
            add_check_result "cdp_parcels" "pass" "$PARCEL_COUNT parcels"
        else
            log_warn "No CDP parcels found"
            add_check_result "cdp_parcels" "warning" "None found"
        fi
    else
        log_info "No CDP parcel directory"
        add_check_result "cdp_parcels" "info" "Not applicable"
    fi
}

# Check 13: Java (CDP requirement)
check_java() {
    log_info "Checking Java..."
    
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -1)
        log_pass "Java available: $JAVA_VERSION"
        add_check_result "java" "pass" "$JAVA_VERSION"
    else
        log_warn "Java not in PATH (may be in parcels)"
        add_check_result "java" "warning" "Not in PATH"
    fi
}

# Check 14: Python Version
check_python() {
    log_info "Checking Python..."
    
    # RHEL 8 uses Python 3 by default
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log_pass "Python 3 available: $PYTHON_VERSION"
        add_check_result "python" "pass" "$PYTHON_VERSION"
    else
        log_error "Python 3 not found"
        add_check_result "python" "fail" "Not found"
    fi
}

# Check 15: Upgrade Artifacts
check_upgrade_artifacts() {
    log_info "Checking upgrade artifacts..."
    
    # Check for upgrade completion marker
    if [ -f /root/upgrade-in-progress.marker ]; then
        log_pass "Upgrade marker found"
        add_check_result "upgrade_marker" "pass" "Found"
    fi
    
    # Check Leapp logs
    if [ -f /var/log/leapp/leapp-upgrade.log ]; then
        LOG_SIZE=$(du -h /var/log/leapp/leapp-upgrade.log | awk '{print $1}')
        log_pass "Upgrade logs present: $LOG_SIZE"
        add_check_result "upgrade_logs" "pass" "Present"
        
        # Check for upgrade errors
        if grep -qi "error" /var/log/leapp/leapp-upgrade.log; then
            ERROR_COUNT=$(grep -ci "error" /var/log/leapp/leapp-upgrade.log)
            log_warn "Found $ERROR_COUNT error entries in upgrade log"
            add_check_result "upgrade_errors" "warning" "$ERROR_COUNT errors"
        fi
    fi
}

# Main execution
main() {
    log_info "========================================="
    log_info "Post-Upgrade Validation"
    log_info "Host: $(hostname)"
    log_info "Role: $ROLE"
    log_info "Expected Version: RHEL $EXPECTED_VERSION"
    log_info "========================================="
    
    init_report
    
    check_os_version
    check_kernel_version
    check_system_status
    check_failed_services
    check_network
    check_disk_space
    check_selinux
    check_firewall
    check_package_manager
    check_subscription
    check_cdp_agent
    check_cdp_parcels
    check_java
    check_python
    check_upgrade_artifacts
    
    finalize_report
    
    log_info "========================================="
    log_info "Post-upgrade validation completed"
    log_info "Passed: $CHECKS_PASSED | Failed: $CHECKS_FAILED | Warnings: $CHECKS_WARNING"
    log_info "Report saved to: $REPORT_FILE"
    log_info "========================================="
    
    if [ $CHECKS_FAILED -gt 0 ]; then
        log_error "Post-upgrade validation FAILED"
        exit 1
    fi
    
    if [ $CHECKS_WARNING -gt 0 ]; then
        log_warn "Post-upgrade validation completed with warnings"
    fi
    
    log_info "System is ready for CDP service startup"
    exit 0
}

main


