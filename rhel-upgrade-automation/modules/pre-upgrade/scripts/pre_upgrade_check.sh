#!/bin/bash
set -e

# Pre-upgrade validation script for RHEL 7.9 to 8.10 upgrade
# Usage: pre_upgrade_check.sh <role> <backup_path>

ROLE=$1
BACKUP_PATH=$2
REPORT_FILE="/tmp/pre_upgrade_report.json"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Results tracking
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0
BLOCKERS=()
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
    BLOCKERS+=("$1")
    ((CHECKS_FAILED++))
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((CHECKS_PASSED++))
}

# Initialize report
init_report() {
    cat > $REPORT_FILE <<EOF
{
  "hostname": "$(hostname)",
  "timestamp": "$(date -Iseconds)",
  "role": "$ROLE",
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
    # Remove trailing comma and close JSON
    sed -i '$ s/,$//' $REPORT_FILE
    cat >> $REPORT_FILE <<EOF
  },
  "summary": {
    "passed": $CHECKS_PASSED,
    "failed": $CHECKS_FAILED,
    "warnings": $CHECKS_WARNING,
    "blockers": $(printf '%s\n' "${BLOCKERS[@]}" | jq -R . | jq -s .),
    "warnings_list": $(printf '%s\n' "${WARNINGS[@]}" | jq -R . | jq -s .)
  }
}
EOF
}

# Check 1: Current OS version
check_os_version() {
    log_info "Checking current OS version..."
    
    if [ -f /etc/redhat-release ]; then
        VERSION=$(cat /etc/redhat-release)
        if echo "$VERSION" | grep -q "release 7.9"; then
            log_pass "Running RHEL 7.9"
            add_check_result "os_version" "pass" "$VERSION"
        else
            log_error "Not running RHEL 7.9: $VERSION"
            add_check_result "os_version" "fail" "$VERSION"
        fi
    else
        log_error "/etc/redhat-release not found"
        add_check_result "os_version" "fail" "Release file not found"
    fi
}

# Check 2: System is fully updated
check_system_updated() {
    log_info "Checking if system is fully updated..."
    
    UPDATES=$(yum check-update | grep -v "^$" | wc -l)
    if [ $UPDATES -eq 0 ]; then
        log_pass "System is fully updated"
        add_check_result "system_updated" "pass" "No pending updates"
    else
        log_error "System has $UPDATES pending updates. Run 'yum update' first"
        add_check_result "system_updated" "fail" "$UPDATES pending updates"
    fi
}

# Check 3: Subscription status
check_subscription() {
    log_info "Checking subscription status..."
    
    if command -v subscription-manager &> /dev/null; then
        if subscription-manager status | grep -q "Overall Status: Current"; then
            log_pass "Valid subscription found"
            add_check_result "subscription" "pass" "Active subscription"
        else
            log_error "No valid subscription. Run 'subscription-manager register'"
            add_check_result "subscription" "fail" "Invalid or missing subscription"
        fi
    else
        log_warn "subscription-manager not found"
        add_check_result "subscription" "warning" "Cannot verify subscription"
    fi
}

# Check 4: Disk space requirements
check_disk_space() {
    log_info "Checking disk space..."
    
    # /boot needs at least 500MB
    BOOT_FREE=$(df -m /boot | tail -1 | awk '{print $4}')
    if [ $BOOT_FREE -ge 500 ]; then
        log_pass "/boot has sufficient space: ${BOOT_FREE}MB"
        add_check_result "disk_boot" "pass" "${BOOT_FREE}MB available"
    else
        log_error "/boot has insufficient space: ${BOOT_FREE}MB (need 500MB)"
        add_check_result "disk_boot" "fail" "Only ${BOOT_FREE}MB available"
    fi
    
    # / needs at least 5GB
    ROOT_FREE=$(df -m / | tail -1 | awk '{print $4}')
    if [ $ROOT_FREE -ge 5120 ]; then
        log_pass "/ has sufficient space: ${ROOT_FREE}MB"
        add_check_result "disk_root" "pass" "${ROOT_FREE}MB available"
    else
        log_error "/ has insufficient space: ${ROOT_FREE}MB (need 5GB)"
        add_check_result "disk_root" "fail" "Only ${ROOT_FREE}MB available"
    fi
    
    # /var needs at least 10GB
    VAR_FREE=$(df -m /var | tail -1 | awk '{print $4}')
    if [ $VAR_FREE -ge 10240 ]; then
        log_pass "/var has sufficient space: ${VAR_FREE}MB"
        add_check_result "disk_var" "pass" "${VAR_FREE}MB available"
    else
        log_warn "/var has limited space: ${VAR_FREE}MB (recommended 10GB)"
        add_check_result "disk_var" "warning" "Only ${VAR_FREE}MB available"
    fi
}

# Check 5: Memory requirements
check_memory() {
    log_info "Checking memory..."
    
    TOTAL_MEM=$(free -m | grep Mem | awk '{print $2}')
    if [ $TOTAL_MEM -ge 1500 ]; then
        log_pass "Sufficient memory: ${TOTAL_MEM}MB"
        add_check_result "memory" "pass" "${TOTAL_MEM}MB available"
    else
        log_warn "Limited memory: ${TOTAL_MEM}MB (recommended 2GB+)"
        add_check_result "memory" "warning" "Only ${TOTAL_MEM}MB available"
    fi
}

# Check 6: Leapp packages
check_leapp_installed() {
    log_info "Checking if leapp is installed..."
    
    if rpm -q leapp-upgrade &> /dev/null; then
        LEAPP_VERSION=$(rpm -q leapp-upgrade)
        log_pass "Leapp is installed: $LEAPP_VERSION"
        add_check_result "leapp_installed" "pass" "$LEAPP_VERSION"
    else
        log_info "Leapp not installed (will be installed during upgrade)"
        add_check_result "leapp_installed" "info" "Not installed yet"
    fi
}

# Check 7: Check for problematic packages
check_problematic_packages() {
    log_info "Checking for problematic packages..."
    
    PROBLEM_PKGS=("pam_pkcs11" "redhat-upgrade-tool" "kernel-devel")
    FOUND_PROBLEMS=()
    
    for pkg in "${PROBLEM_PKGS[@]}"; do
        if rpm -q "$pkg" &> /dev/null; then
            FOUND_PROBLEMS+=("$pkg")
            log_warn "Problematic package found: $pkg (should be removed)"
        fi
    done
    
    if [ ${#FOUND_PROBLEMS[@]} -eq 0 ]; then
        log_pass "No problematic packages found"
        add_check_result "problematic_packages" "pass" "None found"
    else
        log_warn "Found ${#FOUND_PROBLEMS[@]} problematic packages: ${FOUND_PROBLEMS[*]}"
        add_check_result "problematic_packages" "warning" "${FOUND_PROBLEMS[*]}"
    fi
}

# Check 8: SELinux status
check_selinux() {
    log_info "Checking SELinux status..."
    
    if command -v getenforce &> /dev/null; then
        SELINUX_STATUS=$(getenforce)
        log_pass "SELinux status: $SELINUX_STATUS"
        add_check_result "selinux" "pass" "$SELINUX_STATUS"
    else
        log_warn "SELinux tools not found"
        add_check_result "selinux" "warning" "Cannot determine status"
    fi
}

# Check 9: CDP specific checks
check_cdp_services() {
    log_info "Checking CDP services..."
    
    if systemctl list-unit-files | grep -q cloudera-scm; then
        if [ "$ROLE" == "master" ]; then
            if systemctl is-active --quiet cloudera-scm-server; then
                log_pass "Cloudera Manager Server is running (will be stopped)"
                add_check_result "cdp_cm_server" "pass" "Running"
            else
                log_warn "Cloudera Manager Server is not running"
                add_check_result "cdp_cm_server" "warning" "Not running"
            fi
        fi
        
        if systemctl is-active --quiet cloudera-scm-agent; then
            log_pass "Cloudera Manager Agent is running (will be stopped)"
            add_check_result "cdp_cm_agent" "pass" "Running"
        else
            log_warn "Cloudera Manager Agent is not running"
            add_check_result "cdp_cm_agent" "warning" "Not running"
        fi
    else
        log_info "No CDP services found on this host"
        add_check_result "cdp_services" "info" "Not a CDP node"
    fi
}

# Check 10: Network connectivity
check_network() {
    log_info "Checking network connectivity..."
    
    # Check DNS
    if nslookup redhat.com &> /dev/null; then
        log_pass "DNS resolution working"
        add_check_result "network_dns" "pass" "DNS OK"
    else
        log_error "DNS resolution not working"
        add_check_result "network_dns" "fail" "DNS failed"
    fi
    
    # Check internet connectivity (for package downloads)
    if curl -s --connect-timeout 5 https://cdn.redhat.com &> /dev/null; then
        log_pass "Internet connectivity OK"
        add_check_result "network_internet" "pass" "Internet OK"
    else
        log_warn "Cannot reach Red Hat CDN"
        add_check_result "network_internet" "warning" "CDN unreachable"
    fi
}

# Check 11: Running kernel is latest
check_kernel() {
    log_info "Checking kernel version..."
    
    RUNNING_KERNEL=$(uname -r)
    LATEST_KERNEL=$(rpm -q kernel | sort -V | tail -1 | sed 's/kernel-//')
    
    if [ "$RUNNING_KERNEL" == "$LATEST_KERNEL" ]; then
        log_pass "Running latest kernel: $RUNNING_KERNEL"
        add_check_result "kernel" "pass" "$RUNNING_KERNEL"
    else
        log_warn "Not running latest kernel. Running: $RUNNING_KERNEL, Latest: $LATEST_KERNEL"
        add_check_result "kernel" "warning" "Reboot required"
    fi
}

# Check 12: Third-party repositories
check_third_party_repos() {
    log_info "Checking for third-party repositories..."
    
    THIRD_PARTY=$(yum repolist | grep -v "rhel-" | grep -v "repo id" | grep -v "repolist:" | wc -l)
    
    if [ $THIRD_PARTY -gt 0 ]; then
        log_warn "Found $THIRD_PARTY third-party repositories (should be disabled during upgrade)"
        add_check_result "third_party_repos" "warning" "$THIRD_PARTY repos found"
    else
        log_pass "No third-party repositories found"
        add_check_result "third_party_repos" "pass" "None found"
    fi
}

# Check 13: Create backup directory
check_backup_directory() {
    log_info "Checking backup directory..."
    
    mkdir -p $BACKUP_PATH
    
    if [ -d "$BACKUP_PATH" ] && [ -w "$BACKUP_PATH" ]; then
        log_pass "Backup directory accessible: $BACKUP_PATH"
        add_check_result "backup_directory" "pass" "$BACKUP_PATH"
    else
        log_error "Cannot create/access backup directory: $BACKUP_PATH"
        add_check_result "backup_directory" "fail" "Not accessible"
    fi
}

# Check 14: Fstab mount options (CDP specific)
check_fstab_mount_options() {
    log_info "Checking fstab mount options..."
    
    # Check if /opt is mounted with nosuid
    if mount | grep " /opt " | grep -q "nosuid"; then
        log_error "/opt mounted with nosuid - will cause issues with CDP"
        add_check_result "fstab_opt_nosuid" "fail" "/opt has nosuid"
    else
        log_pass "/opt mount options OK"
        add_check_result "fstab_opt_nosuid" "pass" "No issues"
    fi
    
    # Check for noexec on /tmp
    if mount | grep " /tmp " | grep -q "noexec"; then
        log_warn "/tmp mounted with noexec - may cause issues"
        add_check_result "fstab_tmp_noexec" "warning" "/tmp has noexec"
    else
        log_pass "/tmp mount options OK"
        add_check_result "fstab_tmp_noexec" "pass" "No issues"
    fi
}

# Check 15: Java version (CDP specific)
check_java() {
    log_info "Checking Java version..."
    
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -1)
        log_pass "Java installed: $JAVA_VERSION"
        add_check_result "java_version" "pass" "$JAVA_VERSION"
    else
        log_warn "Java not found (may be installed via parcels)"
        add_check_result "java_version" "warning" "Not in PATH"
    fi
}

# Main execution
main() {
    log_info "========================================="
    log_info "RHEL 7.9 to 8.10 Pre-Upgrade Checks"
    log_info "Host: $(hostname)"
    log_info "Role: $ROLE"
    log_info "========================================="
    
    init_report
    
    check_os_version
    check_system_updated
    check_subscription
    check_disk_space
    check_memory
    check_leapp_installed
    check_problematic_packages
    check_selinux
    check_cdp_services
    check_network
    check_kernel
    check_third_party_repos
    check_backup_directory
    check_fstab_mount_options
    check_java
    
    finalize_report
    
    log_info "========================================="
    log_info "Pre-upgrade checks completed"
    log_info "Passed: $CHECKS_PASSED | Failed: $CHECKS_FAILED | Warnings: $CHECKS_WARNING"
    log_info "Report saved to: $REPORT_FILE"
    log_info "========================================="
    
    # Exit with error if there are blockers
    if [ $CHECKS_FAILED -gt 0 ]; then
        log_error "Pre-upgrade checks FAILED. Address blockers before proceeding."
        exit 1
    fi
    
    if [ $CHECKS_WARNING -gt 0 ]; then
        log_warn "Pre-upgrade checks completed with warnings. Review before proceeding."
    fi
    
    exit 0
}

main


