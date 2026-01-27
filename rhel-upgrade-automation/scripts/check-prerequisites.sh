#!/bin/bash

# Prerequisites checker for RHEL upgrade automation
# Run this before starting the upgrade process

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0

echo "========================================="
echo "RHEL Upgrade Prerequisites Check"
echo "========================================="
echo ""

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check 1: Terraform
echo "Checking Terraform..."
if command -v terraform &> /dev/null; then
    VERSION=$(terraform version | head -1)
    check_pass "Terraform installed: $VERSION"
else
    check_fail "Terraform not found. Install from: https://www.terraform.io/downloads"
fi

# Check 2: jq
echo "Checking jq..."
if command -v jq &> /dev/null; then
    VERSION=$(jq --version)
    check_pass "jq installed: $VERSION"
else
    check_fail "jq not found. Install with: yum install jq"
fi

# Check 3: curl
echo "Checking curl..."
if command -v curl &> /dev/null; then
    VERSION=$(curl --version | head -1)
    check_pass "curl installed"
else
    check_fail "curl not found. Install with: yum install curl"
fi

# Check 4: SSH
echo "Checking SSH..."
if command -v ssh &> /dev/null; then
    check_pass "SSH client installed"
else
    check_fail "SSH not found. Install openssh-clients"
fi

# Check 5: Configuration file
echo "Checking configuration..."
if [ -f "terraform.tfvars" ]; then
    check_pass "terraform.tfvars found"
    
    # Check if it's been customized
    if grep -q "your-password\|CHANGE THIS\|example.com" terraform.tfvars; then
        check_warn "terraform.tfvars appears to use example values. Please customize!"
    fi
else
    check_warn "terraform.tfvars not found. Copy from terraform.tfvars.example"
fi

# Check 6: SSH key
echo "Checking SSH key..."
if [ -f terraform.tfvars ]; then
    SSH_KEY=$(grep ssh_private_key terraform.tfvars | cut -d '"' -f2)
    SSH_KEY_EXPANDED="${SSH_KEY/#\~/$HOME}"
    
    if [ -f "$SSH_KEY_EXPANDED" ]; then
        check_pass "SSH key found: $SSH_KEY"
    else
        check_fail "SSH key not found: $SSH_KEY"
    fi
else
    check_warn "Cannot check SSH key without terraform.tfvars"
fi

# Check 7: Terraform initialization
echo "Checking Terraform initialization..."
if [ -d ".terraform" ]; then
    check_pass "Terraform initialized"
else
    check_warn "Terraform not initialized. Run: terraform init"
fi

# Check 8: Disk space
echo "Checking disk space..."
AVAILABLE=$(df -h . | tail -1 | awk '{print $4}')
check_pass "Available disk space: $AVAILABLE"

# Check 9: CM connectivity (if config exists)
if [ -f terraform.tfvars ]; then
    echo "Checking Cloudera Manager connectivity..."
    
    CM_SERVER=$(grep cm_server_host terraform.tfvars | cut -d '"' -f2)
    CM_USER=$(grep cm_api_user terraform.tfvars | cut -d '"' -f2)
    CM_PASS=$(grep cm_api_password terraform.tfvars | cut -d '"' -f2)
    
    if [ ! -z "$CM_SERVER" ] && [ ! -z "$CM_USER" ] && [ ! -z "$CM_PASS" ]; then
        if curl -s -u "${CM_USER}:${CM_PASS}" "http://${CM_SERVER}:7180/api/v40/cm/version" &> /dev/null; then
            check_pass "Cloudera Manager API accessible at $CM_SERVER"
        else
            check_fail "Cannot reach Cloudera Manager API at $CM_SERVER"
            echo "  Check: firewall, credentials, CM service status"
        fi
    else
        check_warn "CM credentials not configured yet"
    fi
fi

# Summary
echo ""
echo "========================================="
echo "Prerequisites Check Summary"
echo "========================================="
echo -e "${GREEN}Passed:${NC} $CHECKS_PASSED"
echo -e "${RED}Failed:${NC} $CHECKS_FAILED"
echo ""

if [ $CHECKS_FAILED -gt 0 ]; then
    echo -e "${RED}Please resolve the failed checks before proceeding.${NC}"
    exit 1
else
    echo -e "${GREEN}All critical prerequisites met!${NC}"
    echo "You can proceed with: terraform init && terraform plan"
    exit 0
fi


