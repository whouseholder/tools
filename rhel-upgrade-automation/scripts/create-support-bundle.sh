#!/bin/bash

# Create a support bundle with all logs and diagnostics

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUNDLE_DIR="support-bundle-${TIMESTAMP}"
BUNDLE_FILE="${BUNDLE_DIR}.tar.gz"

echo "Creating support bundle..."
mkdir -p "$BUNDLE_DIR"

# Copy configuration
echo "Collecting configuration..."
cp terraform.tfvars.example "$BUNDLE_DIR/" 2>/dev/null || true
# Don't copy actual tfvars (contains passwords)
grep -v password terraform.tfvars 2>/dev/null > "$BUNDLE_DIR/terraform.tfvars.sanitized" || true

# Copy Terraform files
echo "Collecting Terraform files..."
cp *.tf "$BUNDLE_DIR/" 2>/dev/null || true

# Copy logs
echo "Collecting logs..."
cp terraform-output.log "$BUNDLE_DIR/" 2>/dev/null || true
cp terraform-debug.log "$BUNDLE_DIR/" 2>/dev/null || true
cp *.log "$BUNDLE_DIR/" 2>/dev/null || true

# Copy reports
echo "Collecting reports..."
cp -r /backup/rhel-upgrade/pre-upgrade-reports "$BUNDLE_DIR/" 2>/dev/null || true
cp -r /tmp/post-upgrade-reports "$BUNDLE_DIR/" 2>/dev/null || true

# Collect system information
echo "Collecting system information..."
cat > "$BUNDLE_DIR/system-info.txt" <<EOF
Timestamp: $(date)
Hostname: $(hostname)
User: $(whoami)
Terraform Version: $(terraform version 2>&1 | head -1)
OS: $(cat /etc/redhat-release)

Directory listing:
$(ls -la)

Terraform state summary:
$(terraform state list 2>&1)
EOF

# Create archive
echo "Creating archive..."
tar -czf "$BUNDLE_FILE" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo ""
echo "========================================"
echo "Support bundle created: $BUNDLE_FILE"
echo "Size: $(du -h $BUNDLE_FILE | cut -f1)"
echo "========================================"
echo ""
echo "You can send this file to support for analysis."
echo "Note: Sensitive data (passwords) have been excluded."


