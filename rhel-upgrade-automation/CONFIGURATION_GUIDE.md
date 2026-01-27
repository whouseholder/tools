# RHEL Upgrade Automation - Configuration Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Execution](#execution)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

### Infrastructure Requirements

#### System Requirements
- **Operating System:** Red Hat Enterprise Linux 7.9 on all nodes
- **Architecture:** x86_64
- **Root Access:** Required on all nodes
- **Python:** Python 2.7 (RHEL 7) and Python 3.6+ (will be installed during upgrade)

#### Network Requirements
```
✓ All nodes must be able to reach:
  - Red Hat CDN (cdn.redhat.com)
  - Cloudera Manager server
  - Each other for internal communication

✓ Firewall ports required:
  - SSH (22) - For Terraform connectivity
  - CM Server (7180, 7182) - For API calls
  - CM Agent (9000) - For agent communication
```

#### Disk Space Requirements
| Mount Point | Minimum Free Space | Recommended | Purpose |
|-------------|-------------------|-------------|---------|
| `/boot` | 500 MB | 1 GB | Kernel files |
| `/` | 5 GB | 10 GB | System files |
| `/var` | 10 GB | 20 GB | Logs and cache |
| `/tmp` | 2 GB | 5 GB | Temporary files |
| `/backup` | 50 GB | 100 GB | Backups |

#### Memory Requirements
- **Minimum:** 2 GB RAM per node
- **Recommended:** 4 GB+ RAM per node
- **For Leapp:** Additional 1 GB RAM during upgrade

### Software Requirements

#### On Terraform Execution Host

```bash
# Required packages
terraform >= 1.0
jq >= 1.6
curl >= 7.29
openssh-clients >= 7.4

# Verify installations
terraform --version
jq --version
curl --version
ssh -V
```

#### Red Hat Subscription

```bash
# Verify subscription status
subscription-manager status

# Expected output:
# Overall Status: Current
# System Purpose Status: Matched

# Verify RHEL 8 entitlements available
subscription-manager list --available | grep "Red Hat Enterprise Linux Server"
```

#### Cloudera Manager Access

```bash
# Test CM API connectivity
curl -u admin:password http://cm-server:7180/api/v40/cm/version

# Expected output: JSON with CM version
# {"version":"7.x.x","buildUser":"jenkins",...}
```

---

## Installation

### Step 1: Download/Clone the Automation

```bash
# If from git repository
git clone <repository-url> /opt/rhel-upgrade-automation
cd /opt/rhel-upgrade-automation

# Or if copying files
mkdir -p /opt/rhel-upgrade-automation
cd /opt/rhel-upgrade-automation
# Copy all files here
```

### Step 2: Verify Directory Structure

```bash
tree -L 2

# Expected output:
# .
# ├── CONFIGURATION_GUIDE.md
# ├── README.md
# ├── UPGRADE_CHECKLIST.md
# ├── main.tf
# ├── variables.tf
# ├── outputs.tf
# ├── terraform.tfvars.example
# ├── examples/
# │   └── small-cluster.tfvars
# └── modules/
#     ├── cdp-prepare/
#     ├── cdp-restore/
#     ├── final-validation/
#     ├── post-upgrade/
#     ├── pre-upgrade/
#     └── upgrade-node/
```

### Step 3: Make Scripts Executable

```bash
find . -type f -name "*.sh" -exec chmod +x {} \;

# Verify
find . -type f -name "*.sh" -ls | head -5
```

### Step 4: Initialize Terraform

```bash
terraform init

# Expected output:
# Initializing modules...
# Initializing the backend...
# Initializing provider plugins...
# Terraform has been successfully initialized!
```

---

## Configuration

### Step 1: Create Configuration File

```bash
# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Open for editing
vi terraform.tfvars  # or nano, emacs, etc.
```

### Step 2: Gather Cluster Information

#### 2.1 List All Cluster Hosts

Create a spreadsheet or document with:

| Hostname | IP Address | Role | Services |
|----------|------------|------|----------|
| master01.example.com | 10.0.1.10 | master | CM Server, NameNode, RM |
| master02.example.com | 10.0.1.11 | master | Standby NN, HBase Master |
| worker01.example.com | 10.0.2.10 | worker | DataNode, NodeManager |
| ... | ... | ... | ... |

**How to get this information:**

```bash
# From Cloudera Manager
# Navigate to: Hosts > All Hosts
# Export the list or copy manually

# Or via CM API
curl -u admin:password http://cm-server:7180/api/v40/hosts | jq -r '.items[] | "\(.hostname)\t\(.ipAddress)"'
```

#### 2.2 Determine Node Roles

**Master Nodes:**
- Hosts running Cloudera Manager Server
- Hosts running HDFS NameNode
- Hosts running YARN ResourceManager
- Hosts running HBase Master
- Hosts running other master services

**Worker Nodes:**
- Hosts running DataNode
- Hosts running NodeManager
- Hosts with data storage

**Edge Nodes:**
- Gateway/client nodes
- Hosts with HUE, Oozie (optional)
- Hosts without DataNode

#### 2.3 Get Cloudera Manager Information

```bash
# CM Server hostname (usually a master node)
CM_SERVER="master01.example.com"

# CM Admin credentials
# Check in: CM UI > Administration > Users & Roles
CM_USER="admin"
CM_PASSWORD="<from_password_manager>"

# Cluster name
# Check in: CM UI > Clusters dropdown
CLUSTER_NAME="Production-CDP-Cluster"
```

### Step 3: Configure terraform.tfvars

#### 3.1 Basic Configuration

```hcl
# =============================================================================
# CLUSTER HOSTS - Configure all your nodes here
# =============================================================================

cluster_hosts = [
  # Master Nodes (will be upgraded ONE AT A TIME)
  {
    hostname    = "master01.example.com"
    ip_address  = "10.0.1.10"
    role        = "master"
    description = "CM Server, Active NameNode, ResourceManager"
  },
  {
    hostname    = "master02.example.com"
    ip_address  = "10.0.1.11"
    role        = "master"
    description = "Standby NameNode, HBase Master"
  },
  {
    hostname    = "master03.example.com"
    ip_address  = "10.0.1.12"
    role        = "master"
    description = "Secondary ResourceManager, Hive Metastore"
  },

  # Worker Nodes (will be upgraded in BATCHES)
  {
    hostname    = "worker01.example.com"
    ip_address  = "10.0.2.10"
    role        = "worker"
    description = "DataNode, NodeManager"
  },
  {
    hostname    = "worker02.example.com"
    ip_address  = "10.0.2.11"
    role        = "worker"
    description = "DataNode, NodeManager"
  },
  # ... add all worker nodes ...

  # Edge Nodes (will be upgraded in PARALLEL)
  {
    hostname    = "edge01.example.com"
    ip_address  = "10.0.3.10"
    role        = "edge"
    description = "Gateway, HUE"
  },
  # ... add all edge nodes ...
]

# =============================================================================
# CLOUDERA MANAGER SETTINGS
# =============================================================================

cm_server_host  = "master01.example.com"  # Must match one of the master nodes
cm_api_user     = "admin"
cm_api_password = "YourSecurePassword123!"  # CHANGE THIS!
cluster_name    = "Production-CDP-Cluster"  # Exact name from CM UI

# =============================================================================
# SSH CONFIGURATION
# =============================================================================

ssh_user        = "root"  # Or sudo-capable user
ssh_private_key = "/root/.ssh/id_rsa"  # Path to SSH key

# =============================================================================
# UPGRADE SETTINGS
# =============================================================================

target_rhel_version = "8.10"
backup_path         = "/backup/rhel-upgrade"
worker_batch_size   = 3  # Adjust based on cluster size
enable_rollback     = true
```

#### 3.2 Determine Worker Batch Size

The batch size determines how many worker nodes upgrade simultaneously.

**Considerations:**
- **HDFS Replication Factor:** Default is 3
- **Cluster Size:** Larger clusters can handle bigger batches
- **Risk Tolerance:** Smaller batches = safer but slower

**Recommendations:**

| Cluster Size | HDFS Replication | Recommended Batch Size | Reasoning |
|--------------|------------------|------------------------|-----------|
| < 10 workers | 3 | 2 | Maintain 70%+ capacity |
| 10-30 workers | 3 | 3-4 | Balance speed and safety |
| 30-50 workers | 3 | 5-7 | Faster with acceptable risk |
| 50+ workers | 3 | 7-10 | Can absorb more simultaneous downtime |

**Formula:**
```
batch_size = floor(total_workers / replication_factor) - 1
```

Example: 15 workers, replication 3 → batch_size = floor(15/3) - 1 = 4

#### 3.3 Advanced Settings (Optional)

```hcl
# Maximum time to wait for each node upgrade (minutes)
max_upgrade_time = 120  # Increase for slow networks

# Create VM snapshots (if your infrastructure supports it)
pre_upgrade_snapshot = false  # Set true for VMware/AWS/Azure

# Skip specific services (leave stopped)
skip_services = []  # Example: ["HUE", "OOZIE"]
```

### Step 4: Validate Configuration

```bash
# Check syntax
terraform validate

# Expected output:
# Success! The configuration is valid.

# Generate plan (don't apply yet)
terraform plan

# Review the output carefully
# Should show all resources to be created
```

### Step 5: Setup SSH Keys

```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096 -f ~/.ssh/rhel_upgrade_key -N ""

# Distribute to all hosts
for host in master01 master02 worker01 worker02 edge01; do
  ssh-copy-id -i ~/.ssh/rhel_upgrade_key.pub root@${host}.example.com
done

# Verify connectivity
for host in master01 master02 worker01; do
  ssh -i ~/.ssh/rhel_upgrade_key root@${host}.example.com "hostname; cat /etc/redhat-release"
done
```

### Step 6: Pre-Flight Verification Checklist

```bash
# Create a verification script
cat > pre-flight-check.sh <<'EOF'
#!/bin/bash
echo "=== Pre-Flight Verification ==="

# 1. Check Terraform
echo -n "Terraform: "
terraform version &>/dev/null && echo "✓" || echo "✗ NOT FOUND"

# 2. Check jq
echo -n "jq: "
jq --version &>/dev/null && echo "✓" || echo "✗ NOT FOUND"

# 3. Check CM connectivity
echo -n "CM API: "
if curl -s -u admin:password http://master01.example.com:7180/api/v40/cm/version &>/dev/null; then
  echo "✓"
else
  echo "✗ UNREACHABLE"
fi

# 4. Check SSH to all hosts
echo "SSH connectivity:"
for host in master01 master02 worker01; do
  echo -n "  $host: "
  if ssh -i ~/.ssh/rhel_upgrade_key -o ConnectTimeout=5 root@${host}.example.com "echo ok" &>/dev/null; then
    echo "✓"
  else
    echo "✗ FAILED"
  fi
done

# 5. Check Red Hat subscription on sample host
echo -n "RH Subscription: "
if ssh -i ~/.ssh/rhel_upgrade_key root@master01.example.com "subscription-manager status | grep -q Current"; then
  echo "✓"
else
  echo "✗ INVALID"
fi

echo "=== Verification Complete ==="
EOF

chmod +x pre-flight-check.sh
./pre-flight-check.sh
```

---

## Execution

### Phase 1: Dry Run

```bash
# Create execution plan
terraform plan -out=upgrade.plan

# Review the plan
# Look for:
# - Correct number of hosts
# - Proper role assignments
# - Correct CM server
# - Expected module executions

# Save the plan output
terraform plan -out=upgrade.plan 2>&1 | tee plan-output.txt
```

### Phase 2: Pre-Execution Checklist

```bash
# Print checklist
cat <<'EOF'
=== PRE-EXECUTION CHECKLIST ===

Infrastructure:
[ ] All nodes are accessible via SSH
[ ] CM API is accessible
[ ] Red Hat subscriptions are valid
[ ] Sufficient disk space on all nodes
[ ] Backups are current

Communication:
[ ] Maintenance window scheduled
[ ] Stakeholders notified
[ ] Users informed of downtime
[ ] Team is on standby

Safety:
[ ] Tested in dev/staging environment
[ ] Rollback procedures documented
[ ] Emergency contacts ready
[ ] Backup restoration tested

Environment:
[ ] No critical jobs running
[ ] YARN queues are drained
[ ] No ongoing maintenance
[ ] Monitoring is active

Documentation:
[ ] This guide is printed/saved
[ ] Cluster state documented
[ ] Configuration backed up
[ ] Runbook is available

Ready to proceed? (yes/no):
EOF

read -p "> " READY
if [ "$READY" != "yes" ]; then
  echo "Aborting. Complete checklist first."
  exit 1
fi
```

### Phase 3: Execute Upgrade

```bash
# Start in a screen/tmux session (recommended)
screen -S rhel-upgrade
# or
tmux new -s rhel-upgrade

# Enable detailed logging
export TF_LOG=INFO
export TF_LOG_PATH=./terraform-execution.log

# Record start time
echo "Upgrade started: $(date)" | tee upgrade-timing.log

# Execute the upgrade
terraform apply upgrade.plan 2>&1 | tee -a terraform-output.log

# If successful, record completion
echo "Upgrade completed: $(date)" | tee -a upgrade-timing.log
```

### Phase 4: Execution Timeline

**Expected Timeline for Medium Cluster (15 nodes):**

```
00:00 - Start
00:00 - 00:15 | Pre-upgrade checks (parallel on all nodes)
00:15 - 00:30 | Stop CDP services
00:30 - 01:30 | Upgrade edge nodes (2 nodes, parallel)
01:30 - 04:30 | Upgrade worker nodes (9 nodes, batch size 3)
04:30 - 07:30 | Upgrade master nodes (3 nodes, sequential)
07:30 - 07:45 | Post-upgrade validation
07:45 - 08:30 | Start CDP services
08:30 - 08:45 | Health checks and validation
08:45 - Done
```

**Total: ~9 hours**

---

## Monitoring

### Real-Time Monitoring

#### Terminal 1: Terraform Output
```bash
# Main execution window
tail -f terraform-output.log
```

#### Terminal 2: CM Server Logs
```bash
# Monitor CM server
ssh root@master01 'tail -f /var/log/cloudera-scm-server/cloudera-scm-server.log'
```

#### Terminal 3: Sample Host Upgrade
```bash
# Watch a worker node upgrade
ssh root@worker01 'tail -f /var/log/leapp/leapp-upgrade.log'
```

#### Terminal 4: Cluster Health
```bash
# Monitor via CM API
while true; do
  curl -s -u admin:password http://master01:7180/api/v40/clusters/Production-CDP-Cluster/services \
    | jq -r '.items[] | "\(.name): \(.serviceState)"'
  sleep 60
done
```

### Web UI Monitoring

```bash
# Open Cloudera Manager UI
http://master01.example.com:7180

# Monitor:
# - Hosts > All Hosts (watch status)
# - Clusters > <your-cluster> (service health)
# - Diagnostics > Logs (errors/warnings)
```

### Progress Tracking

```bash
# Create progress tracker
cat > track-progress.sh <<'EOF'
#!/bin/bash

while true; do
  clear
  echo "=== RHEL Upgrade Progress ==="
  echo "Time: $(date)"
  echo ""
  
  echo "Pre-upgrade Reports:"
  ls -1 /backup/rhel-upgrade/pre-upgrade-reports/*.json 2>/dev/null | wc -l
  
  echo ""
  echo "Hosts Status:"
  for host in master01 master02 worker01 worker02 worker03; do
    VERSION=$(ssh -i ~/.ssh/rhel_upgrade_key root@${host} "cat /etc/redhat-release 2>/dev/null" || echo "UNREACHABLE")
    echo "  $host: $VERSION"
  done
  
  echo ""
  echo "CDP Services:"
  curl -s -u admin:password http://master01:7180/api/v40/clusters/Production-CDP-Cluster/services 2>/dev/null \
    | jq -r '.items[] | "  \(.name): \(.serviceState)"' || echo "  CM UNREACHABLE"
  
  sleep 60
done
EOF

chmod +x track-progress.sh
./track-progress.sh
```

### Check Progress Manually

```bash
# Check which hosts have been upgraded
for host in master01 master02 worker01 worker02; do
  echo -n "$host: "
  ssh root@$host "cat /etc/redhat-release" 2>/dev/null || echo "UNREACHABLE"
done

# Check backup reports
ls -lh /backup/rhel-upgrade/pre-upgrade-reports/

# Check Terraform state
terraform show | grep -A 5 "null_resource.upgrade_node"
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Pre-upgrade Check Fails

**Symptom:**
```
Error: Pre-upgrade checks failed on host worker01
Blocker: Insufficient disk space in /boot
```

**Solution:**
```bash
# SSH to the problematic host
ssh root@worker01

# Check disk space
df -h /boot

# Clean old kernels
package-cleanup --oldkernels --count=2

# Or manually
rpm -q kernel
yum remove kernel-<old-version>

# Verify
df -h /boot
```

#### Issue 2: Leapp Preupgrade Fails

**Symptom:**
```
Error: Leapp preupgrade found high severity issues
Inhibitor: Missing required answers
```

**Solution:**
```bash
# Check Leapp report
ssh root@worker01 "cat /var/log/leapp/leapp-report.txt"

# Common fix: Answer required questions
ssh root@worker01 "leapp answer --section remove_pam_pkcs11_module_check.confirm=True"

# Remove problematic packages
ssh root@worker01 "yum remove -y pam_pkcs11"

# Re-run preupgrade
ssh root@worker01 "leapp preupgrade"
```

#### Issue 3: Node Doesn't Come Back After Reboot

**Symptom:**
```
Waiting for host to come back online...
Still waiting... (600s elapsed, 6600s remaining)
```

**Solution:**
```bash
# Check if accessible via console (if virtualized)
# VM console or IPMI

# Common issues:
# 1. Network configuration lost
# 2. Hung in boot process
# 3. SELinux relabeling in progress

# If you can access console:
# - Check network: ip addr
# - Check boot status: systemctl status
# - Check SELinux: ls -lZ /

# If network issue:
# systemctl restart NetworkManager
# nmcli connection up <connection-name>

# If SELinux relabeling:
# - This can take 30-60 minutes
# - Just wait
```

#### Issue 4: CM Agent Won't Start After Upgrade

**Symptom:**
```
Error: CDP agent failed to start
Status: Failed
```

**Solution:**
```bash
# Check logs
ssh root@worker01 "tail -100 /var/log/cloudera-scm-agent/cloudera-scm-agent.log"

# Common issues:

# 1. Python version mismatch
ssh root@worker01 "alternatives --set python /usr/bin/python3"

# 2. Missing dependencies
ssh root@worker01 "yum install -y python3-psycopg2"

# 3. Permission issues
ssh root@worker01 "chown -R cloudera-scm:cloudera-scm /var/lib/cloudera-scm-agent"

# 4. Reinstall agent
ssh root@worker01 "yum reinstall -y cloudera-manager-agent"

# Restart
ssh root@worker01 "systemctl restart cloudera-scm-agent"
```

#### Issue 5: Services Won't Start

**Symptom:**
```
Error: HDFS service failed to start
Unhealthy: DataNode on worker01
```

**Solution:**
```bash
# Check service-specific logs
ssh root@worker01 "tail -100 /var/log/hadoop-hdfs/hadoop-hdfs-datanode-*.log"

# Common fixes:

# 1. Java version issues
ssh root@worker01 "alternatives --list | grep java"
ssh root@worker01 "alternatives --set java /usr/java/jdk1.8.0_XXX/bin/java"

# 2. Permission issues
ssh root@worker01 "ls -laZ /dfs/dn"
ssh root@worker01 "chown -R hdfs:hdfs /dfs/dn"

# 3. SELinux denials
ssh root@worker01 "grep denied /var/log/audit/audit.log | tail -20"
ssh root@worker01 "setenforce 0"  # Temporary, investigate further

# Restart via CM UI or:
curl -u admin:password -X POST \
  http://master01:7180/api/v40/clusters/Production-CDP-Cluster/services/HDFS/commands/restart
```

### Emergency Rollback

If upgrade fails catastrophically:

```bash
# 1. STOP Terraform immediately
Ctrl+C  (in Terraform terminal)

# 2. Assess situation
./assess-cluster-state.sh

# 3. For nodes that haven't upgraded yet
# - Leave them on RHEL 7
# - Don't proceed with their upgrades

# 4. For nodes that upgraded successfully but services won't start
# - Boot into old kernel from GRUB menu
# - Or restore from backup

# 5. For nodes mid-upgrade
# - Wait for completion
# - Then decide: keep RHEL 8 and fix, or rollback

# 6. Restore from backups if needed
for host in worker01 worker02; do
  ssh root@$host "
    cd /backup/rhel-upgrade/\$(hostname)_latest
    tar -xzf etc-backup.tar.gz -C /
  "
done

# 7. Restart services
curl -u admin:password -X POST \
  http://master01:7180/api/v40/clusters/Production-CDP-Cluster/commands/start
```

### Debug Mode

```bash
# Enable maximum verbosity
export TF_LOG=TRACE
export TF_LOG_PATH=./terraform-debug.log

# Enable script debugging
# Edit any script and add:
set -x  # Enable debug mode
set -v  # Print commands as they're read

# Run specific module only
terraform apply -target=module.pre_upgrade_checks

# Check Terraform state
terraform state list
terraform state show 'module.upgrade_worker_nodes.null_resource.upgrade_node["worker01.example.com"]'
```

---

## Advanced Configuration

### Custom Upgrade Order

If you need a different upgrade order:

```bash
# Edit main.tf
vi main.tf

# Comment out modules you want to skip temporarily
# Or adjust depends_on relationships

# Example: Upgrade only edge nodes
terraform apply -target=module.upgrade_edge_nodes
```

### Partial Cluster Upgrade

Upgrade specific nodes:

```hcl
# In terraform.tfvars, comment out nodes you want to skip
cluster_hosts = [
  {
    hostname    = "worker01.example.com"
    ip_address  = "10.0.2.10"
    role        = "worker"
    description = "DataNode"
  },
  # {
  #   hostname    = "worker02.example.com"
  #   ip_address  = "10.0.2.11"
  #   role        = "worker"
  #   description = "DataNode"
  # },  # SKIP THIS NODE
]
```

### Custom Scripts

Add custom pre/post actions:

```bash
# Create custom script
cat > modules/upgrade-node/scripts/custom_pre_upgrade.sh <<'EOF'
#!/bin/bash
# Custom pre-upgrade actions
echo "Running custom checks..."
# Add your logic here
EOF

# Edit module to call it
vi modules/upgrade-node/main.tf

# Add provisioner:
provisioner "remote-exec" {
  inline = [
    "/tmp/upgrade-scripts/custom_pre_upgrade.sh"
  ]
}
```

### Integration with Monitoring Systems

```bash
# Send notifications to Slack/email
cat > notify.sh <<'EOF'
#!/bin/bash
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
MESSAGE="$1"

curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"RHEL Upgrade: $MESSAGE\"}" \
  $WEBHOOK_URL
EOF

# Call from Terraform
provisioner "local-exec" {
  command = "./notify.sh 'Starting upgrade of ${each.value.hostname}'"
}
```

### Scheduled Execution

```bash
# Create cron job for off-hours execution
# (Not recommended for initial run, but useful for maintenance)

# Create wrapper script
cat > scheduled-upgrade.sh <<'EOF'
#!/bin/bash
cd /opt/rhel-upgrade-automation
terraform apply -auto-approve upgrade.plan > /var/log/upgrade-$(date +%Y%m%d).log 2>&1
EOF

# Add to cron (example: 2 AM Sunday)
# crontab -e
# 0 2 * * 0 /opt/rhel-upgrade-automation/scheduled-upgrade.sh
```

---

## Post-Execution Validation

### Comprehensive Validation Script

```bash
cat > validate-cluster.sh <<'EOF'
#!/bin/bash

echo "=== Post-Upgrade Validation ==="

# 1. OS Version Check
echo "1. Checking OS versions..."
for host in master01 master02 worker01 worker02 worker03 edge01; do
  VERSION=$(ssh root@$host "cat /etc/redhat-release")
  echo "  $host: $VERSION"
done

# 2. Service Health
echo ""
echo "2. Checking service health..."
curl -s -u admin:password http://master01:7180/api/v40/clusters/Production-CDP-Cluster/services \
  | jq -r '.items[] | "  \(.name): \(.serviceState) - \(.healthSummary)"'

# 3. HDFS Health
echo ""
echo "3. Checking HDFS health..."
ssh root@master01 "sudo -u hdfs hdfs dfsadmin -report" | head -20

# 4. YARN Health
echo ""
echo "4. Checking YARN health..."
ssh root@master01 "sudo -u yarn yarn node -list" | head -10

# 5. Run Test Job
echo ""
echo "5. Running test job..."
ssh root@master01 "sudo -u hdfs hadoop jar /opt/cloudera/parcels/CDH/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar pi 2 10"

# 6. Check Impala
echo ""
echo "6. Checking Impala..."
ssh root@edge01 "impala-shell -q 'SELECT version()'"

echo ""
echo "=== Validation Complete ==="
EOF

chmod +x validate-cluster.sh
./validate-cluster.sh
```

---

## Support and Next Steps

### Documentation to Keep

- [ ] Save all log files
- [ ] Save Terraform output
- [ ] Save pre/post upgrade reports
- [ ] Document issues and resolutions
- [ ] Update your runbooks

### Knowledge Transfer

- [ ] Share lessons learned with team
- [ ] Update documentation
- [ ] Create post-mortem if issues occurred
- [ ] Schedule follow-up review

### Cleanup

After 1-2 weeks of stable operation:

```bash
# Clean up old RHEL 7 packages
for host in master01 master02 worker01 worker02 worker03 edge01; do
  ssh root@$host "dnf remove \$(rpm -qa | grep el7)"
done

# Remove rescue kernels
for host in master01 master02 worker01 worker02 worker03 edge01; do
  ssh root@$host "rm -f /boot/*rescue*; grub2-mkconfig -o /boot/grub2/grub.cfg"
done
```

---

## Quick Reference

### Important Commands

```bash
# Check cluster state
./track-progress.sh

# Validate configuration
terraform validate

# Plan upgrade
terraform plan -out=upgrade.plan

# Execute upgrade
terraform apply upgrade.plan

# Check Terraform state
terraform show

# Emergency stop
Ctrl+C (in Terraform terminal)

# Check logs
tail -f /var/log/leapp/leapp-upgrade.log  # On target host
tail -f terraform-output.log               # On Terraform host
```

### Important Files

| File | Location | Purpose |
|------|----------|---------|
| Configuration | `terraform.tfvars` | Your cluster config |
| Execution log | `terraform-output.log` | Full Terraform output |
| Plan file | `upgrade.plan` | Execution plan |
| Pre-upgrade reports | `/backup/rhel-upgrade/pre-upgrade-reports/` | Validation results |
| Post-upgrade reports | `/tmp/post-upgrade-reports/` | Validation results |
| Leapp logs | `/var/log/leapp/` (on each host) | Upgrade details |
| CM logs | `/var/log/cloudera-scm-server/` | CM server logs |

---

## Questions and Issues

If you encounter issues not covered in this guide:

1. Check the detailed logs
2. Review the troubleshooting section
3. Consult Red Hat documentation for Leapp
4. Consult Cloudera documentation for CDP
5. Engage Red Hat support if needed
6. Engage Cloudera support if needed

**Remember:** This is a complex operation. Take your time, follow the checklist, and don't hesitate to stop if something doesn't look right.


