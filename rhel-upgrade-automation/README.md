# RHEL 7.9 to 8.10 Automated Upgrade for CDP Private Base

Terraform-based automation for upgrading Red Hat Enterprise Linux from version 7.9 to 8.10 on Cloudera CDP Private Base clusters. This solution provides comprehensive pre-upgrade validation, automated upgrade execution, post-upgrade validation, and CDP-specific handling with proper orchestration for master, edge, and worker nodes.

## Features

- ✅ **Comprehensive Pre-Upgrade Checks** - Validates system readiness before any changes
- ✅ **Automated Backup** - Creates system and CDP configuration backups
- ✅ **CDP-Aware Orchestration** - Stops/starts services in the correct order
- ✅ **Parallel Execution** - Upgrades edge and worker nodes in parallel batches
- ✅ **Sequential Master Upgrades** - Upgrades master nodes one at a time for safety
- ✅ **Post-Upgrade Validation** - Verifies system health after upgrade
- ✅ **Health Checks** - Ensures CDP cluster is healthy after restart
- ✅ **Rollback Support** - Can detect failures and prevent further damage

## Architecture

### Upgrade Flow

```
1. Pre-Upgrade Checks (Parallel on all nodes)
   ├── OS version validation
   ├── Disk space checks
   ├── Network connectivity
   ├── Package compatibility
   └── CDP-specific checks

2. CDP Cluster Preparation
   ├── Stop cluster services (via CM API)
   ├── Stop CM agents
   ├── Stop CM server
   └── Backup cluster state

3. Upgrade Edge Nodes (Parallel - lowest risk)
   ├── System backup
   ├── Install Leapp
   ├── Run preupgrade
   ├── Execute upgrade
   └── Wait for reboot

4. Upgrade Worker Nodes (Batched - maintain capacity)
   ├── Same steps as edge nodes
   └── Process in configurable batches

5. Upgrade Master Nodes (Sequential - highest risk)
   ├── Same steps as edge nodes
   └── One at a time with validation

6. Post-Upgrade Validation (Parallel)
   ├── OS version verification
   ├── Service health checks
   ├── Network validation
   └── CDP component checks

7. CDP Cluster Restoration
   ├── Start CM server
   ├── Start CM agents
   ├── Start cluster services
   └── Perform health check

8. Final Validation and Reporting
```

## Prerequisites

### Infrastructure Requirements

- Red Hat Enterprise Linux 7.9 on all nodes
- Valid Red Hat subscription with RHEL 8 entitlements
- SSH key-based authentication configured
- At least 500MB free space in `/boot`
- At least 5GB free space in `/`
- At least 10GB free space in `/var`

### Software Requirements

- Terraform >= 1.0
- `jq` (for JSON processing)
- `curl` (for CM API calls)
- SSH access to all cluster nodes
- Cloudera Manager API access

### Network Requirements

- All nodes can reach Red Hat CDN
- All nodes can reach Cloudera Manager
- Terraform execution host can reach all nodes via SSH

## Project Structure

```
rhel-upgrade-automation/
├── main.tf                          # Main orchestration
├── variables.tf                     # Variable definitions
├── outputs.tf                       # Output definitions
├── terraform.tfvars.example         # Example configuration
├── README.md                        # This file
│
├── modules/
│   ├── pre-upgrade/                 # Pre-upgrade validation
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── scripts/
│   │       ├── pre_upgrade_check.sh
│   │       └── check_blockers.sh
│   │
│   ├── upgrade-node/                # Node upgrade execution
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── scripts/
│   │       ├── backup_system.sh
│   │       ├── install_leapp.sh
│   │       ├── run_leapp_preupgrade.sh
│   │       ├── run_upgrade.sh
│   │       └── wait_for_host.sh
│   │
│   ├── post-upgrade/                # Post-upgrade validation
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── scripts/
│   │       ├── post_upgrade_validation.sh
│   │       └── aggregate_validation.sh
│   │
│   ├── cdp-prepare/                 # CDP cluster preparation
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── scripts/
│   │       ├── stop_cluster.sh
│   │       └── backup_cluster_state.sh
│   │
│   ├── cdp-restore/                 # CDP cluster restoration
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── scripts/
│   │       ├── wait_for_cm.sh
│   │       ├── wait_for_agents.sh
│   │       ├── start_cluster.sh
│   │       └── health_check.sh
│   │
│   └── final-validation/            # Final validation & reporting
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── scripts/
│           └── final_validation.sh
│
└── examples/
    ├── small-cluster.tfvars         # Small cluster example
    ├── medium-cluster.tfvars        # Medium cluster example
    └── large-cluster.tfvars         # Large cluster example
```

## Quick Start

### 1. Clone and Setup

```bash
cd /path/to/rhel-upgrade-automation
cp terraform.tfvars.example terraform.tfvars
```

### 2. Configure Your Environment

Edit `terraform.tfvars`:

```hcl
# Cluster hosts
cluster_hosts = [
  {
    hostname    = "master01.example.com"
    ip_address  = "10.0.1.10"
    role        = "master"
    description = "CM Server and Master Services"
  },
  {
    hostname    = "worker01.example.com"
    ip_address  = "10.0.1.20"
    role        = "worker"
    description = "Data Node"
  },
  # ... add all hosts
]

# Cloudera Manager
cm_server_host  = "master01.example.com"
cm_api_user     = "admin"
cm_api_password = "your-password"
cluster_name    = "CDP-Cluster"

# SSH Configuration
ssh_user        = "root"
ssh_private_key = "~/.ssh/id_rsa"

# Upgrade Settings
target_rhel_version = "8.10"
worker_batch_size   = 3
enable_rollback     = true
```

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Plan the Upgrade

```bash
terraform plan -out=upgrade.plan
```

Review the plan carefully. Terraform will show all the resources it will create and actions it will take.

### 5. Execute the Upgrade

```bash
terraform apply upgrade.plan
```

The upgrade process will take 2-4 hours depending on cluster size.

### 6. Monitor Progress

Watch the Terraform output for progress. You can also:

```bash
# Check pre-upgrade reports
ls -la /backup/rhel-upgrade/pre-upgrade-reports/

# Check upgrade logs on individual hosts
ssh root@host01 "tail -f /var/log/leapp/leapp-upgrade.log"

# Monitor CM UI
http://your-cm-server:7180
```

## Configuration Options

### Variable Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `cluster_hosts` | list(object) | Required | List of all cluster hosts with role designation |
| `cm_server_host` | string | Required | Cloudera Manager server hostname |
| `cm_api_user` | string | "admin" | CM API username |
| `cm_api_password` | string | Required | CM API password |
| `cluster_name` | string | Required | CDP cluster name |
| `ssh_user` | string | "root" | SSH user for node access |
| `ssh_private_key` | string | "~/.ssh/id_rsa" | Path to SSH private key |
| `target_rhel_version` | string | "8.10" | Target RHEL version |
| `backup_path` | string | "/backup/rhel-upgrade" | Backup directory path |
| `worker_batch_size` | number | 3 | Number of workers to upgrade in parallel |
| `enable_rollback` | bool | true | Enable automatic rollback on failure |
| `max_upgrade_time` | number | 120 | Max upgrade time per node (minutes) |

## CDP-Specific Considerations

### Service Shutdown Order

The automation stops services in this order:
1. HUE (user-facing)
2. Impala (query engine)
3. Hive (metastore/query)
4. HBase (NoSQL database)
5. YARN (resource manager)
6. HDFS (storage layer)
7. ZooKeeper (coordination - last)

### Service Startup Order

Services start in reverse order:
1. ZooKeeper (coordination - first)
2. HDFS (storage layer)
3. YARN (resource manager)
4. HBase (NoSQL database)
5. Hive (metastore/query)
6. Impala (query engine)
7. HUE (user-facing - last)

### Master Node Handling

Master nodes are upgraded **sequentially** (one at a time) to minimize risk:
- NameNode availability is preserved
- ResourceManager failover is handled
- HBase Master transitions gracefully

### Worker Node Handling

Worker nodes are upgraded in **configurable batches**:
- Default batch size: 3 nodes
- Maintains HDFS replication factor
- Preserves YARN capacity
- Minimizes data unavailability

### Edge Node Handling

Edge nodes are upgraded **in parallel**:
- Lowest risk (no data storage)
- Fastest completion
- No impact on cluster operations

## Rollback and Recovery

### Automatic Detection

The automation will stop if:
- Pre-upgrade checks fail
- Leapp preupgrade finds blockers
- Upgrade fails on any node
- Post-upgrade validation fails

### Manual Rollback

If you need to rollback after upgrade:

```bash
# On each upgraded node
# Boot into old kernel from GRUB menu
# OR restore from backup

# Restore from backup
cd /backup/rhel-upgrade/<hostname>_<timestamp>
tar -xzf etc-backup.tar.gz -C /
reboot
```

### Partial Upgrade Recovery

If only some nodes upgrade successfully:

```bash
# Continue with remaining nodes
terraform apply -target=module.upgrade_worker_nodes

# Or rollback upgraded nodes
# (requires manual intervention)
```

## Troubleshooting

### Common Issues

#### Issue: Leapp preupgrade fails

```bash
# Check Leapp report
ssh root@host01 "cat /var/log/leapp/leapp-report.txt"

# Common fixes:
# 1. Remove problematic packages
yum remove -y pam_pkcs11

# 2. Update kernel
yum update -y kernel && reboot

# 3. Disable third-party repos
yum-config-manager --disable epel
```

#### Issue: CM Agent won't start after upgrade

```bash
# Check logs
tail -f /var/log/cloudera-scm-agent/cloudera-scm-agent.log

# Reinstall agent if needed
yum reinstall -y cloudera-manager-agent
systemctl restart cloudera-scm-agent
```

#### Issue: Services won't start

```bash
# Check service logs in CM UI
# Common issues:
# 1. Java version mismatch
alternatives --set java /usr/java/jdk1.8.0_XXX/bin/java

# 2. Python version issues
alternatives --set python /usr/bin/python3

# 3. Permission issues after upgrade
ls -laZ /opt/cloudera/parcels/
restorecon -R /opt/cloudera/
```

### Debug Mode

Enable verbose logging:

```bash
# Set TF_LOG before running terraform
export TF_LOG=DEBUG
terraform apply
```

## Post-Upgrade Tasks

### Immediate (within 24 hours)

1. **Verify Cluster Health**
   - Check CM UI for any alerts
   - Run test jobs (MapReduce, Spark, Impala queries)
   - Verify data accessibility

2. **Monitor Performance**
   - Watch resource utilization
   - Check for any degraded services
   - Review logs for errors

3. **Update Documentation**
   - Record actual upgrade times
   - Document any issues encountered
   - Update runbooks

### Short-term (within 1 week)

1. **Clean Up Old Packages**
   ```bash
   # Remove RHEL 7 packages
   dnf remove $(rpm -qa | grep 'el7')
   
   # Clean up rescue kernels
   rm -f /boot/vmlinuz-*rescue*
   rm -f /boot/initramfs-*rescue*
   grub2-mkconfig -o /boot/grub2/grub.cfg
   ```

2. **Update Monitoring**
   - Verify monitoring agents work with RHEL 8
   - Update alert thresholds if needed

3. **Application Testing**
   - Run full regression tests
   - Verify all integrations
   - Test disaster recovery procedures

### Long-term (within 1 month)

1. **Performance Tuning**
   - Optimize for RHEL 8 improvements
   - Review and update kernel parameters
   - Tune CDP services for new OS

2. **Security Hardening**
   - Apply RHEL 8 security best practices
   - Update SELinux policies
   - Review firewall configurations

## Best Practices

### Before Running

- [ ] Test in dev/staging environment first
- [ ] Schedule maintenance window (4-8 hours)
- [ ] Notify all stakeholders
- [ ] Take VM snapshots if possible
- [ ] Backup all critical data
- [ ] Review CM alerts/warnings
- [ ] Document current cluster state

### During Execution

- [ ] Monitor Terraform output continuously
- [ ] Keep CM UI open for visual monitoring
- [ ] Have rollback plan ready
- [ ] Keep communication channel open with team
- [ ] Don't interrupt Terraform unless critical

### After Completion

- [ ] Run validation tests
- [ ] Monitor for 24-48 hours
- [ ] Document lessons learned
- [ ] Update procedures for next time

## Performance Expectations

### Time Estimates (per node)

- Pre-upgrade checks: 5-10 minutes
- System backup: 10-20 minutes
- Leapp preupgrade: 10-15 minutes
- Upgrade execution: 30-60 minutes
- Post-upgrade validation: 5-10 minutes

**Total per node: 60-115 minutes**

### Cluster Downtime

- CDP services stopped: Entire upgrade duration
- Typical 10-node cluster: 4-6 hours total
- Larger clusters scale proportionally

## Support and Contributions

### Getting Help

- Check logs in `/var/log/leapp/`
- Review Terraform output
- Check CM logs
- Consult Red Hat documentation

### Known Limitations

- Requires Red Hat subscription
- Cannot upgrade across multiple major versions
- Some third-party packages may need reinstallation
- Custom kernel modules require recompilation

## License

This automation is provided as-is for use with Cloudera CDP Private Base clusters.

## Changelog

### Version 1.0.0 (Initial Release)
- Complete RHEL 7.9 to 8.10 upgrade automation
- CDP Private Base integration
- Parallel and sequential upgrade modes
- Comprehensive validation and health checks
- Backup and rollback support


