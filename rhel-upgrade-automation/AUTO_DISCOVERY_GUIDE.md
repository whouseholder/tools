# Auto-Discovery Guide - Fetch Hosts from Cloudera Manager

This guide explains how to use the automatic host discovery feature to fetch cluster configuration directly from Cloudera Manager.

## Overview

Instead of manually configuring all cluster hosts in `terraform.tfvars`, you can enable auto-discovery to:
- ✅ Automatically fetch all cluster hosts from CM
- ✅ Auto-determine host roles (master/worker/edge)
- ✅ Always stay in sync with current cluster topology
- ✅ Reduce configuration errors

## Quick Start

### 1. Enable Auto-Discovery

Create or edit `terraform.tfvars`:

```hcl
# Enable auto-discovery
auto_discover_hosts = true

# CM connection details
cm_server_host  = "master01.example.com"
cm_api_user     = "admin"
cm_api_password = "your-password"
cluster_name    = "Production-Cluster"  # Optional - auto-detects if omitted

# SSH configuration
ssh_user        = "root"
ssh_private_key = "~/.ssh/id_rsa"

# Other settings
target_rhel_version = "8.10"
worker_batch_size   = 3
```

### 2. Test Discovery

```bash
# Initialize Terraform
terraform init

# Preview what will be discovered
terraform plan

# You'll see output like:
# discovered_cluster_info = {
#   cluster_name   = "Production-Cluster"
#   cm_server_host = "master01.example.com"
#   total_hosts    = 15
#   master_nodes   = 3
#   worker_nodes   = 10
#   edge_nodes     = 2
# }
```

### 3. Validate Discovery

```bash
# Show discovered hosts
terraform plan | grep -A 100 "discovered_cluster_info"

# Or after apply
terraform output discovered_cluster_info
```

## How It Works

### Host Role Detection

The automation determines roles based on services running on each host:

#### Master Nodes
Hosts running any of:
- NameNode (HDFS)
- ResourceManager (YARN)
- HBase Master
- HiveServer2
- Hive Metastore
- CM Server itself

#### Worker Nodes
Hosts running:
- DataNode (HDFS)
- NodeManager (YARN)

#### Edge Nodes
Hosts not matching master or worker criteria:
- Gateway nodes
- HUE servers
- Client-only nodes

### API Calls Made

1. **GET /api/v40/cm/version** - Verify CM connectivity
2. **GET /api/v40/clusters** - Get cluster list
3. **GET /api/v40/hosts** - Get all hosts
4. **GET /api/v40/clusters/{name}/services** - Get cluster services
5. **GET /api/v40/clusters/{name}/services/{service}/roles** - Get role assignments

## Configuration Options

### Minimal Configuration

```hcl
auto_discover_hosts = true
cm_server_host      = "master01.example.com"
cm_api_user         = "admin"
cm_api_password     = "password"
ssh_private_key     = "~/.ssh/id_rsa"
```

This will:
- Auto-detect cluster name (uses first cluster found)
- Discover all hosts automatically
- Determine roles automatically

### Full Configuration

```hcl
auto_discover_hosts = true

# CM Connection
cm_server_host  = "master01.example.com"
cm_api_user     = "admin"
cm_api_password = "password"
cluster_name    = "Production-Cluster"  # Specify exact cluster

# SSH
ssh_user        = "root"
ssh_private_key = "~/.ssh/id_rsa"

# Upgrade Settings
target_rhel_version = "8.10"
backup_path         = "/backup/rhel-upgrade"
worker_batch_size   = 3
enable_rollback     = true
```

### Mixed Mode (Not Recommended)

You can combine auto-discovery with manual overrides, but this is not recommended:

```hcl
auto_discover_hosts = true  # Discovers hosts

# Manual hosts will be ignored when auto_discover_hosts = true
cluster_hosts = [
  # These will be ignored
]
```

## Testing Auto-Discovery

### Test the Discovery Script Directly

```bash
# Run the discovery script manually
./scripts/fetch-cm-hosts.sh \
  master01.example.com \
  admin \
  password \
  Production-Cluster

# Output will be JSON:
{
  "cluster_name": "Production-Cluster",
  "cm_server_host": "master01.example.com",
  "hosts": [
    {
      "hostname": "master01.example.com",
      "ip_address": "10.0.1.10",
      "role": "master",
      "services": ["NAMENODE", "RESOURCEMANAGER"],
      "description": "NAMENODE, RESOURCEMANAGER"
    },
    ...
  ]
}
```

### Validate Without Executing

```bash
# Generate plan to see what will be discovered
terraform plan -out=test.plan

# Review the plan
terraform show test.plan | less

# Look for:
# - discovered_cluster_info output
# - Number of hosts in each role
# - Hostnames and IP addresses
```

## Troubleshooting

### Issue: Cannot connect to CM

**Error:**
```
Error: Cannot connect to Cloudera Manager at master01.example.com
```

**Solutions:**
```bash
# 1. Test CM connectivity
curl -u admin:password http://master01.example.com:7180/api/v40/cm/version

# 2. Check firewall
telnet master01.example.com 7180

# 3. Verify credentials
# Try logging into CM UI with same credentials

# 4. Check CM service
ssh root@master01.example.com "systemctl status cloudera-scm-server"
```

### Issue: jq not found

**Error:**
```
Error: jq: command not found
```

**Solution:**
```bash
# Install jq
# RHEL/CentOS
yum install -y jq

# Ubuntu/Debian
apt-get install -y jq

# macOS
brew install jq
```

### Issue: Incorrect role detection

**Symptom:** A host is classified as the wrong role

**Investigation:**
```bash
# Check what services CM thinks are on the host
curl -u admin:password \
  "http://master01.example.com:7180/api/v40/hosts" | \
  jq '.items[] | select(.hostname == "worker01.example.com")'

# Check role assignments
curl -u admin:password \
  "http://master01.example.com:7180/api/v40/clusters/Production-Cluster/services" | \
  jq -r '.items[].name' | \
  while read service; do
    echo "=== $service ==="
    curl -s -u admin:password \
      "http://master01.example.com:7180/api/v40/clusters/Production-Cluster/services/$service/roles" | \
      jq -r '.items[] | select(.hostRef.hostname == "worker01.example.com") | .type'
  done
```

**Manual Override:**
If auto-detection doesn't work for your cluster, disable auto-discovery:
```hcl
auto_discover_hosts = false
cluster_hosts = [
  # Manually specify hosts
]
```

### Issue: Multiple clusters found

**Error:**
```
Error: Multiple clusters found, please specify cluster_name
```

**Solution:**
```bash
# List all clusters
curl -u admin:password \
  "http://master01.example.com:7180/api/v40/clusters" | \
  jq -r '.items[] | .name'

# Specify the cluster you want
# In terraform.tfvars:
cluster_name = "Production-Cluster"
```

## Comparison: Manual vs Auto-Discovery

### Manual Configuration

**Pros:**
- ✅ Full control over host roles
- ✅ No dependency on CM API
- ✅ Works offline

**Cons:**
- ❌ Must manually maintain host list
- ❌ Can become outdated
- ❌ More error-prone
- ❌ Time-consuming for large clusters

**Example terraform.tfvars:**
```hcl
auto_discover_hosts = false

cluster_hosts = [
  {
    hostname    = "master01.example.com"
    ip_address  = "10.0.1.10"
    role        = "master"
    description = "CM Server, NameNode"
  },
  # ... 50 more hosts to configure manually
]
```

### Auto-Discovery

**Pros:**
- ✅ No manual host configuration needed
- ✅ Always current with cluster topology
- ✅ Automatic role detection
- ✅ Less error-prone
- ✅ Faster setup

**Cons:**
- ❌ Requires CM API access
- ❌ Depends on CM being up
- ❌ Requires jq installed

**Example terraform.tfvars:**
```hcl
auto_discover_hosts = true
cm_server_host      = "master01.example.com"
cm_api_user         = "admin"
cm_api_password     = "password"
```

## Best Practices

### 1. Validate Discovery Before Upgrade

```bash
# Always check discovered hosts before executing
terraform plan > plan-output.txt
grep -A 100 "discovered_cluster_info" plan-output.txt

# Verify:
# - Correct number of hosts
# - Proper role assignments
# - All expected hosts present
```

### 2. Use Strong CM Credentials

```hcl
# Use environment variables for sensitive data
# Don't commit passwords to git!

# Set in shell:
export TF_VAR_cm_api_password="secure-password"

# In terraform.tfvars:
auto_discover_hosts = true
cm_server_host      = "master01.example.com"
cm_api_user         = "admin"
# cm_api_password comes from environment variable
```

### 3. Test in Dev First

```bash
# Test auto-discovery in dev environment
cd dev-environment/
terraform plan

# Verify results
# Then apply in staging
# Then production
```

### 4. Keep Manual Config as Backup

```bash
# Generate manual config from auto-discovery for backup
terraform plan -out=discovery.plan
terraform show -json discovery.plan | \
  jq '.planned_values.outputs.discovered_cluster_info.value' \
  > cluster-backup.json
```

### 5. Document Your Cluster

```bash
# Save discovery results for documentation
terraform apply
terraform output discovered_cluster_info > cluster-topology.json
```

## Migration from Manual to Auto-Discovery

### Step 1: Backup Current Configuration

```bash
cp terraform.tfvars terraform.tfvars.manual.backup
```

### Step 2: Enable Auto-Discovery

```bash
# Create new tfvars with auto-discovery
cat > terraform.tfvars <<EOF
auto_discover_hosts = true
cm_server_host      = "master01.example.com"
cm_api_user         = "admin"
cm_api_password     = "password"
ssh_user            = "root"
ssh_private_key     = "~/.ssh/id_rsa"
target_rhel_version = "8.10"
worker_batch_size   = 3
EOF
```

### Step 3: Validate

```bash
# Compare discovered vs manual
terraform plan > auto-plan.txt

# Review carefully
# Ensure same number of hosts
# Verify roles match your expectations
```

### Step 4: Test

```bash
# Test in non-production first!
terraform apply -target=module.pre_upgrade_checks

# If successful, proceed with full upgrade
```

## Security Considerations

### CM API Credentials

```bash
# Never commit passwords to git!
# Add to .gitignore:
echo "terraform.tfvars" >> .gitignore

# Use environment variables
export TF_VAR_cm_api_password="password"

# Or use Terraform Cloud/Enterprise secrets
```

### Read-Only CM User

```bash
# Create a read-only CM user for discovery
# In CM UI: Administration → Users & Roles
# Create user: terraform-readonly
# Grant role: Read-Only

# Use in terraform.tfvars:
cm_api_user = "terraform-readonly"
```

### Network Security

```bash
# Ensure CM API port (7180) is accessible
# Only from Terraform execution host
# Use firewall rules to restrict access
```

## Advanced Usage

### Custom Role Detection

If the default role detection doesn't work for your environment, you can modify the script:

```bash
# Edit scripts/fetch-cm-hosts.sh
# Modify the role determination logic around line 70

# Example: Classify based on custom criteria
role: (
  if (.hostname | test("^master")) then "master"
  elif (.hostname | test("^worker")) then "worker"
  else "edge"
  end
)
```

### Multiple Clusters

```bash
# Create separate tfvars for each cluster
# cluster1.tfvars
auto_discover_hosts = true
cluster_name        = "Cluster1"

# cluster2.tfvars
auto_discover_hosts = true
cluster_name        = "Cluster2"

# Apply to specific cluster
terraform apply -var-file=cluster1.tfvars
```

### Filtered Discovery

To exclude certain hosts from discovery, modify the script or use Terraform filters:

```hcl
locals {
  # Filter out specific hosts after discovery
  cluster_hosts_final = [
    for host in local.discovered_hosts :
    host if !contains(["excluded-host.example.com"], host.hostname)
  ]
}
```

## Summary

Auto-discovery simplifies configuration and reduces errors. Use it when:
- ✅ CM API is accessible
- ✅ You want dynamic configuration
- ✅ Your cluster topology changes
- ✅ You have many hosts

Use manual configuration when:
- ✅ CM API is not accessible
- ✅ You need specific role assignments
- ✅ You need to override detection logic
- ✅ Working offline

**Recommendation:** Use auto-discovery for production clusters to ensure accuracy and ease of maintenance.


