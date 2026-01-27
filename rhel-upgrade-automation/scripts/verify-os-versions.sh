#!/bin/bash

# Verify OS versions on all hosts after upgrade

if [ ! -f terraform.tfvars ]; then
    echo "Error: terraform.tfvars not found"
    exit 1
fi

SSH_KEY=$(grep ssh_private_key terraform.tfvars | cut -d '"' -f2)
SSH_KEY="${SSH_KEY/#\~/$HOME}"
HOSTS=$(grep -A 1000 'cluster_hosts = \[' terraform.tfvars | grep 'hostname' | cut -d '"' -f2)

echo "========================================"
echo "OS Version Verification"
echo "========================================"
echo ""

ALL_UPGRADED=true

for host in $HOSTS; do
    echo -n "Checking $host... "
    
    VERSION=$(ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
              root@$host "cat /etc/redhat-release 2>/dev/null" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        if echo "$VERSION" | grep -q "release 8"; then
            echo "✅ $VERSION"
        else
            echo "❌ $VERSION (NOT UPGRADED)"
            ALL_UPGRADED=false
        fi
    else
        echo "❌ UNREACHABLE"
        ALL_UPGRADED=false
    fi
done

echo ""
echo "========================================"
if $ALL_UPGRADED; then
    echo "✅ All hosts successfully upgraded to RHEL 8!"
    exit 0
else
    echo "❌ Some hosts are not on RHEL 8 or unreachable"
    exit 1
fi


