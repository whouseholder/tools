# RHEL Upgrade Checklist for CDP Private Base

Use this checklist to ensure a smooth upgrade process.

## Pre-Upgrade Phase (1-2 weeks before)

### Environment Preparation
- [ ] Verify all nodes are running RHEL 7.9
- [ ] Confirm Red Hat subscription is active with RHEL 8 entitlements
- [ ] Verify SSH key-based authentication works on all nodes
- [ ] Test Cloudera Manager API access
- [ ] Review current cluster health in CM UI
- [ ] Document current cluster configuration
- [ ] Note any custom configurations or modifications

### Testing and Validation
- [ ] Test upgrade process in dev environment
- [ ] Test upgrade process in staging environment
- [ ] Document any issues encountered in testing
- [ ] Verify rollback procedures work in test environment
- [ ] Run baseline performance tests for comparison

### Capacity Planning
- [ ] Verify disk space requirements on all nodes:
  - [ ] `/boot` >= 500MB free
  - [ ] `/` >= 5GB free
  - [ ] `/var` >= 10GB free
  - [ ] `/backup` >= 50GB free (for backups)
- [ ] Verify sufficient network bandwidth
- [ ] Check backup storage capacity

### Backup Strategy
- [ ] Confirm backup solution is working
- [ ] Take full cluster backup (HDFS, databases, configurations)
- [ ] Take VM snapshots if possible
- [ ] Document backup locations and procedures
- [ ] Test backup restoration procedure

### Communication
- [ ] Schedule maintenance window (recommend 8-12 hours)
- [ ] Notify all stakeholders
- [ ] Inform users of expected downtime
- [ ] Prepare communication templates for updates
- [ ] Set up communication channel for upgrade team

### Documentation
- [ ] Print/save this checklist
- [ ] Print/save rollback procedures
- [ ] Document emergency contacts
- [ ] Prepare incident response plan
- [ ] Create runbook for common issues

## Day Before Upgrade

### Final Verification
- [ ] Confirm maintenance window with stakeholders
- [ ] Verify all team members are available
- [ ] Review upgrade plan with team
- [ ] Confirm rollback procedures are understood
- [ ] Test emergency communication channels

### System Preparation
- [ ] Update all nodes to latest RHEL 7.9 patches
- [ ] Clear old log files to free space
- [ ] Remove unnecessary packages
- [ ] Disable unnecessary cron jobs
- [ ] Review and address any CM alerts

### Configuration Files
- [ ] Update `terraform.tfvars` with correct values
- [ ] Verify SSH keys are in place
- [ ] Test Terraform connection to CM API
- [ ] Run `terraform plan` and review output

### Final Backups
- [ ] Take final HDFS snapshot
- [ ] Export CM configuration
- [ ] Backup CM database
- [ ] Backup important data
- [ ] Verify all backups are accessible

## Day of Upgrade

### Pre-Execution (T-minus 1 hour)
- [ ] Final team briefing
- [ ] Confirm go/no-go with stakeholders
- [ ] Start maintenance window
- [ ] Send initial notification to users
- [ ] Stop all non-critical jobs
- [ ] Drain YARN queues if possible

### Execution Phase
- [ ] Start screen/tmux session (in case of disconnection)
- [ ] Enable Terraform logging: `export TF_LOG=DEBUG`
- [ ] Initialize Terraform: `terraform init`
- [ ] Create execution plan: `terraform plan -out=upgrade.plan`
- [ ] Review plan output carefully
- [ ] Execute upgrade: `terraform apply upgrade.plan`
- [ ] Monitor Terraform output continuously
- [ ] Keep CM UI open for visual monitoring
- [ ] Document start time and any issues

### During Upgrade
- [ ] Monitor pre-upgrade checks (expected: 15-30 min)
- [ ] Monitor CDP service shutdown (expected: 15-30 min)
- [ ] Monitor edge node upgrades (expected: 30-60 min)
- [ ] Monitor worker node upgrades (expected: 2-4 hours)
- [ ] Monitor master node upgrades (expected: 2-3 hours)
- [ ] Monitor post-upgrade validation (expected: 15-30 min)
- [ ] Monitor CDP service startup (expected: 30-60 min)

### Communication During Upgrade
- [ ] Send hourly status updates
- [ ] Document any issues immediately
- [ ] Notify team of phase completions
- [ ] Keep stakeholders informed

## Post-Upgrade Phase

### Immediate Validation (within 1 hour)
- [ ] Verify all nodes show RHEL 8 in CM UI
- [ ] Check all services are started in CM
- [ ] Review CM health checks - all should be green
- [ ] Verify no critical alerts in CM
- [ ] Check cluster health summary
- [ ] Review final Terraform output

### System Verification (within 2 hours)
- [ ] SSH to each node and verify OS version
- [ ] Check running kernel version on all nodes
- [ ] Verify network connectivity between nodes
- [ ] Check DNS resolution
- [ ] Verify NTP/time synchronization
- [ ] Check firewall rules are intact
- [ ] Verify SELinux status

### Service Validation (within 4 hours)
- [ ] Run HDFS health check: `hdfs dfsadmin -report`
- [ ] Check HDFS safe mode: `hdfs dfsadmin -safemode get`
- [ ] Run YARN queue check: `yarn node -list`
- [ ] Test Impala: `impala-shell -q "SELECT 1"`
- [ ] Test Hive: `hive -e "SHOW DATABASES"`
- [ ] Test HBase: `echo "status" | hbase shell`
- [ ] Verify ZooKeeper quorum

### Data Validation
- [ ] Run test MapReduce job
- [ ] Run test Spark job
- [ ] Execute sample Impala queries
- [ ] Verify data accessibility in HDFS
- [ ] Check HBase table accessibility
- [ ] Verify Hive table metadata

### Performance Baseline
- [ ] Run performance tests
- [ ] Compare with pre-upgrade baseline
- [ ] Check resource utilization
- [ ] Monitor response times
- [ ] Review query performance

### Documentation
- [ ] Document actual upgrade duration
- [ ] Record any issues encountered and solutions
- [ ] Update runbooks with lessons learned
- [ ] Save all logs and reports
- [ ] Document final cluster state

### Communication
- [ ] Send upgrade completion notification
- [ ] Inform users system is available
- [ ] Share any known issues or limitations
- [ ] Provide support contact information
- [ ] Close maintenance window

## Post-Upgrade Monitoring (24-48 hours)

### Continuous Monitoring
- [ ] Monitor cluster health in CM UI
- [ ] Watch for any service degradation
- [ ] Check for unusual log messages
- [ ] Monitor resource utilization
- [ ] Track user-reported issues

### Daily Checks
- [ ] Review CM alerts each morning
- [ ] Check service health
- [ ] Monitor job success rates
- [ ] Review system logs
- [ ] Check backup jobs are running

### Application Testing
- [ ] Run full application test suite
- [ ] Verify all integrations work
- [ ] Test data pipelines
- [ ] Verify scheduled jobs run successfully
- [ ] Check reporting systems

## Cleanup Phase (1 week after)

### System Cleanup
- [ ] Remove old RHEL 7 packages: `dnf remove $(rpm -qa | grep 'el7')`
- [ ] Remove rescue kernels: `rm -f /boot/*rescue*`
- [ ] Update GRUB configuration
- [ ] Clean up old log files
- [ ] Remove temporary files

### Configuration Updates
- [ ] Update monitoring configurations
- [ ] Update backup scripts if needed
- [ ] Update documentation
- [ ] Update CM host templates if changed
- [ ] Update automation scripts

### Performance Tuning
- [ ] Review and optimize kernel parameters for RHEL 8
- [ ] Tune CDP services if needed
- [ ] Optimize memory settings
- [ ] Review and update cgroups configuration
- [ ] Update system limits if needed

## Long-term Follow-up (1 month after)

### Final Review
- [ ] Conduct post-upgrade review meeting
- [ ] Document lessons learned
- [ ] Update procedures for future upgrades
- [ ] Share knowledge with team
- [ ] Update disaster recovery plans

### Security Hardening
- [ ] Apply RHEL 8 security best practices
- [ ] Review and update SELinux policies
- [ ] Update firewall rules
- [ ] Review user access controls
- [ ] Perform security audit

### Optimization
- [ ] Performance tuning based on observations
- [ ] Optimize configurations
- [ ] Review capacity planning
- [ ] Update monitoring thresholds
- [ ] Implement improvements

## Rollback Procedures (If Needed)

### Decision Criteria for Rollback
- [ ] Pre-upgrade checks show critical blockers
- [ ] Upgrade fails on master nodes
- [ ] Post-upgrade validation shows critical issues
- [ ] Services won't start after upgrade
- [ ] Data corruption detected
- [ ] Unacceptable performance degradation

### Rollback Steps
- [ ] STOP the Terraform execution (Ctrl+C)
- [ ] Document the failure point and errors
- [ ] Notify team and stakeholders
- [ ] Assess which nodes successfully upgraded
- [ ] For successfully upgraded nodes:
  - [ ] Restore from VM snapshots if available
  - [ ] OR restore from backups
  - [ ] OR boot into old RHEL 7 kernel from GRUB
- [ ] For non-upgraded nodes:
  - [ ] Verify they're still on RHEL 7
  - [ ] Restart CM agents
- [ ] Restore CM database from backup if needed
- [ ] Start CDP services
- [ ] Verify cluster health
- [ ] Conduct root cause analysis
- [ ] Plan corrective actions

## Notes and Observations

Use this section to record important information during the upgrade:

**Pre-Upgrade Notes:**
```




```

**Issues Encountered:**
```




```

**Resolutions Applied:**
```




```

**Performance Observations:**
```




```

**Lessons Learned:**
```




```


