#!/bin/bash

# Interactive Setup Wizard for RHEL Upgrade Automation
# Minimal configuration required - smart defaults for everything

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║     RHEL Upgrade Automation - Interactive Setup Wizard      ║
║                                                              ║
║  This wizard will configure your upgrade with minimal input ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Function to prompt with default
prompt_with_default() {
    local prompt=$1
    local default=$2
    local var_name=$3
    
    if [ -z "$default" ]; then
        read -p "$(echo -e ${GREEN}$prompt:${NC} )" value
    else
        read -p "$(echo -e ${GREEN}$prompt${NC} [${YELLOW}$default${NC}]: )" value
        value=${value:-$default}
    fi
    
    eval $var_name="'$value'"
}

# Function to prompt yes/no
prompt_yes_no() {
    local prompt=$1
    local default=$2
    local var_name=$3
    
    while true; do
        read -p "$(echo -e ${GREEN}$prompt${NC} [${YELLOW}$default${NC}]: )" yn
        yn=${yn:-$default}
        case $yn in
            [Yy]* ) eval $var_name="true"; break;;
            [Nn]* ) eval $var_name="false"; break;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Step 1: Cloudera Manager Connection (Required)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Detect CM server from current host
CURRENT_HOST=$(hostname -f 2>/dev/null || hostname)
prompt_with_default "Cloudera Manager server hostname" "$CURRENT_HOST" CM_HOST

prompt_with_default "CM API username" "admin" CM_USER

# Password (no default)
while true; do
    read -s -p "$(echo -e ${GREEN}CM API password:${NC} )" CM_PASS
    echo ""
    if [ ! -z "$CM_PASS" ]; then
        break
    fi
    echo "Password cannot be empty"
done

# Test CM connectivity
echo ""
echo -e "${YELLOW}Testing CM connectivity...${NC}"
if curl -s -u "${CM_USER}:${CM_PASS}" "http://${CM_HOST}:7180/api/v40/cm/version" &> /dev/null; then
    echo -e "${GREEN}✓ Connected to Cloudera Manager successfully${NC}"
    CM_VERSION=$(curl -s -u "${CM_USER}:${CM_PASS}" "http://${CM_HOST}:7180/api/v40/cm/version" | jq -r '.version' 2>/dev/null || echo "Unknown")
    echo -e "  CM Version: ${CM_VERSION}"
else
    echo -e "${RED}✗ Cannot connect to Cloudera Manager${NC}"
    echo "  Please check hostname, credentials, and CM service status"
    exit 1
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Step 2: Cluster Selection (Auto-Detected)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Auto-detect clusters
CLUSTERS=$(curl -s -u "${CM_USER}:${CM_PASS}" "http://${CM_HOST}:7180/api/v40/clusters" | jq -r '.items[].name' 2>/dev/null)
CLUSTER_COUNT=$(echo "$CLUSTERS" | grep -v '^$' | wc -l)

if [ "$CLUSTER_COUNT" -eq 0 ]; then
    echo -e "${RED}No clusters found in CM${NC}"
    exit 1
elif [ "$CLUSTER_COUNT" -eq 1 ]; then
    CLUSTER_NAME=$(echo "$CLUSTERS" | head -1)
    echo -e "${GREEN}✓ Found 1 cluster: ${CLUSTER_NAME}${NC}"
else
    echo -e "${YELLOW}Found ${CLUSTER_COUNT} clusters:${NC}"
    echo "$CLUSTERS" | nl
    echo ""
    prompt_with_default "Select cluster name" "$(echo $CLUSTERS | head -1)" CLUSTER_NAME
fi

# Get cluster info
echo ""
echo -e "${YELLOW}Discovering cluster topology...${NC}"
HOST_COUNT=$(curl -s -u "${CM_USER}:${CM_PASS}" "http://${CM_HOST}:7180/api/v40/hosts" | jq '.items | length' 2>/dev/null)
echo -e "${GREEN}✓ Found ${HOST_COUNT} hosts in cluster${NC}"

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Step 3: SSH Configuration (Smart Defaults)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Detect SSH key
DEFAULT_SSH_KEY=""
for key in ~/.ssh/id_rsa ~/.ssh/id_ed25519 ~/.ssh/id_ecdsa; do
    if [ -f "$key" ]; then
        DEFAULT_SSH_KEY="$key"
        break
    fi
done

if [ -z "$DEFAULT_SSH_KEY" ]; then
    echo -e "${YELLOW}No SSH key found in ~/.ssh/${NC}"
    prompt_with_default "Path to SSH private key" "" SSH_KEY
else
    prompt_with_default "Path to SSH private key" "$DEFAULT_SSH_KEY" SSH_KEY
fi

# Test SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found: $SSH_KEY${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SSH key found${NC}"

prompt_with_default "SSH username" "root" SSH_USER

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Step 4: Upgrade Settings (Smart Defaults)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

prompt_with_default "Target RHEL version" "8.10" TARGET_VERSION

# Auto-calculate worker batch size
if [ "$HOST_COUNT" -lt 10 ]; then
    DEFAULT_BATCH=2
elif [ "$HOST_COUNT" -lt 30 ]; then
    DEFAULT_BATCH=3
else
    DEFAULT_BATCH=5
fi

prompt_with_default "Worker batch size (parallel upgrades)" "$DEFAULT_BATCH" WORKER_BATCH

# Detect backup path with sufficient space
BACKUP_PATH="/backup/rhel-upgrade"
if [ -d "/backup" ]; then
    AVAIL_SPACE=$(df -BG /backup | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$AVAIL_SPACE" -gt 50 ]; then
        echo -e "${GREEN}✓ Found /backup with ${AVAIL_SPACE}GB available${NC}"
    else
        echo -e "${YELLOW}⚠ /backup has only ${AVAIL_SPACE}GB (recommend 50GB+)${NC}"
    fi
else
    BACKUP_PATH="/var/backup/rhel-upgrade"
    echo -e "${YELLOW}⚠ /backup not found, using ${BACKUP_PATH}${NC}"
fi
prompt_with_default "Backup path" "$BACKUP_PATH" BACKUP_PATH

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Step 5: Advanced Options (Optional)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

prompt_yes_no "Enable automatic rollback on failure?" "y" ENABLE_ROLLBACK

prompt_yes_no "Create VM snapshots before upgrade (if supported)?" "n" ENABLE_SNAPSHOTS

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Configuration Summary${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

cat << EOF
Configuration Mode:      Auto-Discovery (recommended)
CM Server:              ${CM_HOST}
Cluster:                ${CLUSTER_NAME}
Hosts:                  ${HOST_COUNT} (auto-discovered)
SSH Key:                ${SSH_KEY}
SSH User:               ${SSH_USER}
Target Version:         RHEL ${TARGET_VERSION}
Worker Batch Size:      ${WORKER_BATCH}
Backup Path:            ${BACKUP_PATH}
Rollback:               ${ENABLE_ROLLBACK}
VM Snapshots:           ${ENABLE_SNAPSHOTS}
EOF

echo ""
prompt_yes_no "Save this configuration?" "y" SAVE_CONFIG

if [ "$SAVE_CONFIG" != "true" ]; then
    echo "Configuration cancelled"
    exit 0
fi

# Generate terraform.tfvars
echo ""
echo -e "${YELLOW}Generating terraform.tfvars...${NC}"

cat > terraform.tfvars <<EOF
# Auto-generated by setup wizard on $(date)
# This configuration uses smart defaults and auto-discovery

# =============================================================================
# AUTO-DISCOVERY MODE (Recommended)
# =============================================================================

auto_discover_hosts = true

# =============================================================================
# CLOUDERA MANAGER CONNECTION
# =============================================================================

cm_server_host  = "${CM_HOST}"
cm_api_user     = "${CM_USER}"
cm_api_password = "${CM_PASS}"
cluster_name    = "${CLUSTER_NAME}"

# =============================================================================
# SSH CONFIGURATION
# =============================================================================

ssh_user        = "${SSH_USER}"
ssh_private_key = "${SSH_KEY}"

# =============================================================================
# UPGRADE SETTINGS
# =============================================================================

target_rhel_version = "${TARGET_VERSION}"
backup_path         = "${BACKUP_PATH}"
worker_batch_size   = ${WORKER_BATCH}
enable_rollback     = ${ENABLE_ROLLBACK}
pre_upgrade_snapshot = ${ENABLE_SNAPSHOTS}

# =============================================================================
# ADDITIONAL SETTINGS (Defaults - Uncomment to Customize)
# =============================================================================

# Max time to wait for each node upgrade (minutes)
# max_upgrade_time = 120

# Services to skip during stop/start (if any)
# skip_services = []

# =============================================================================
# CUSTOMIZATION NOTES
# =============================================================================

# This configuration uses auto-discovery to fetch all hosts from CM.
# To see what will be discovered, run: terraform plan
#
# To customize further, you can:
# 1. Add skip_services to exclude specific services
# 2. Adjust worker_batch_size based on your cluster size
# 3. Change max_upgrade_time for slower networks
# 4. Disable auto_discover_hosts and manually specify hosts
#
# See CONFIGURATION_GUIDE.md for all available options.

EOF

echo -e "${GREEN}✓ Configuration saved to terraform.tfvars${NC}"

# Test SSH to a sample host
echo ""
echo -e "${YELLOW}Testing SSH connectivity to cluster...${NC}"

SAMPLE_HOST=$(curl -s -u "${CM_USER}:${CM_PASS}" "http://${CM_HOST}:7180/api/v40/hosts" | \
    jq -r '.items[0].hostname' 2>/dev/null)

if [ ! -z "$SAMPLE_HOST" ]; then
    if ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
        "${SSH_USER}@${SAMPLE_HOST}" "echo test" &>/dev/null; then
        echo -e "${GREEN}✓ SSH connectivity verified (tested: ${SAMPLE_HOST})${NC}"
    else
        echo -e "${YELLOW}⚠ Cannot SSH to ${SAMPLE_HOST}${NC}"
        echo "  Please ensure SSH key is distributed to all hosts"
        echo "  Run: ssh-copy-id -i ${SSH_KEY} ${SSH_USER}@<each-host>"
    fi
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Next Steps${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

cat << EOF
${GREEN}✓ Configuration complete!${NC}

Your next steps:

${YELLOW}1.${NC} Initialize Terraform:
   ${BLUE}terraform init${NC}

${YELLOW}2.${NC} Preview what will be upgraded:
   ${BLUE}terraform plan${NC}
   
   ${GREEN}Look for 'discovered_cluster_info' in the output${NC}

${YELLOW}3.${NC} Create execution plan:
   ${BLUE}terraform plan -out=upgrade.plan${NC}

${YELLOW}4.${NC} Review the plan carefully:
   ${BLUE}terraform show upgrade.plan | less${NC}

${YELLOW}5.${NC} Execute the upgrade:
   ${BLUE}terraform apply upgrade.plan${NC}

${YELLOW}6.${NC} Monitor progress (in separate terminal):
   ${BLUE}./scripts/monitor-upgrade.sh${NC}

${GREEN}Documentation:${NC}
  - Quick Start:    ${BLUE}QUICK_START.md${NC}
  - Full Guide:     ${BLUE}CONFIGURATION_GUIDE.md${NC}
  - Auto-Discovery: ${BLUE}AUTO_DISCOVERY_GUIDE.md${NC}
  - Checklist:      ${BLUE}UPGRADE_CHECKLIST.md${NC}

${GREEN}Tips:${NC}
  - Test in dev/staging first!
  - Schedule maintenance window (8-12 hours)
  - Have rollback plan ready
  - Keep team on standby

${YELLOW}Need help?${NC} Run: ./scripts/check-prerequisites.sh

EOF

echo -e "${GREEN}Good luck with your upgrade! 🚀${NC}"
echo ""


