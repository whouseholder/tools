#!/bin/bash
set -e

echo "========================================="
echo "Installing Leapp Upgrade Framework"
echo "========================================="

# Check if already installed
if rpm -q leapp-upgrade &> /dev/null; then
    echo "Leapp already installed: $(rpm -q leapp-upgrade)"
    exit 0
fi

# Enable required repositories
echo "Enabling required repositories..."
subscription-manager repos \
    --enable rhel-7-server-rpms \
    --enable rhel-7-server-extras-rpms

# Update subscription-manager and related packages
echo "Updating subscription-manager..."
yum update -y subscription-manager

# Install leapp
echo "Installing leapp packages..."
yum install -y leapp-upgrade leapp-data-rhel

# Verify installation
if rpm -q leapp-upgrade &> /dev/null; then
    echo "Leapp successfully installed: $(rpm -q leapp-upgrade)"
    leapp --version
else
    echo "ERROR: Leapp installation failed"
    exit 1
fi

echo "========================================="
echo "Leapp installation completed"
echo "========================================="

exit 0


