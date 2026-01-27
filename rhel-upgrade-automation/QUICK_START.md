# Quick Start Guide - RHEL 7.9 to 8.10 Upgrade

This is a condensed guide to get you started quickly. For detailed information, see [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md).

## 🚀 30-Minute Setup

### Step 1: Prerequisites Check (5 minutes)

```bash
# Run this on your Terraform execution host
./scripts/check-prerequisites.sh
```

This checks for:
- Terraform installed
- jq installed
- SSH connectivity
- CM API access
- Disk space

### Step 2: Configuration (15 minutes)

**Option A: Auto-Discovery (Recommended)**

```bash
# 1. Copy auto-discovery example
cp terraform-auto-discover.tfvars.example terraform.tfvars

# 2. Edit with minimal settings
nano terraform.tfvars

# Required fields (just 4!):
# - auto_discover_hosts = true
# - cm_server_host
# - cm_api_password
# - ssh_private_key
```

**Option B: Manual Configuration**

```bash
# 1. Copy manual configuration example
cp terraform.tfvars.example terraform.tfvars

# 2. Edit with your cluster details
nano terraform.tfvars

# Required fields:
# - cluster_hosts (all your nodes - manually list them)
# - cm_server_host
# - cm_api_password
# - ssh_private_key
```

**Minimum configuration example (Auto-Discovery):**

```hcl
# Let Terraform discover your cluster automatically!
auto_discover_hosts = true
cm_server_host      = "master01.example.com"
cm_api_user         = "admin"
cm_api_password     = "your-password"
ssh_private_key     = "~/.ssh/id_rsa"
target_rhel_version = "8.10"
```

**Manual configuration example:**

```hcl
auto_discover_hosts = false
cluster_hosts = [
  {
    hostname    = "master01.example.com"
    ip_address  = "10.0.1.10"
    role        = "master"
    description = "CM Server"
  },
  {
    hostname    = "worker01.example.com"
    ip_address  = "10.0.2.10"
    role        = "worker"
    description = "Data Node"
  }
  # Add all your nodes here manually
]

cm_server_host  = "master01.example.com"
cm_api_password = "your-password"
cluster_name    = "CDP-Cluster"
ssh_private_key = "~/.ssh/id_rsa"
```

### Step 3: Validation (5 minutes)

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Generate plan
terraform plan -out=upgrade.plan

# Review the plan output
```

### Step 4: Pre-Flight Check (5 minutes)

```bash
# Run pre-flight checks
./scripts/pre-flight-check.sh

# This verifies:
# - SSH connectivity to all hosts
# - Red Hat subscriptions
# - Disk space
# - CM API access
```

---

## ⚡ Execution

### Option A: Interactive Execution (Recommended for First Time)

```bash
# Start in a screen session
screen -S rhel-upgrade

# Enable logging
export TF_LOG=INFO

# Execute
terraform apply upgrade.plan

# Detach with: Ctrl+A, D
# Reattach with: screen -r rhel-upgrade
```

### Option B: Unattended Execution

```bash
# Run with full logging
terraform apply upgrade.plan 2>&1 | tee upgrade-$(date +%Y%m%d-%H%M%S).log
```

---

## 📊 Monitoring Progress

### Real-Time Status

```bash
# In a separate terminal
./scripts/monitor-upgrade.sh
```

This shows:
- Current OS version on each host
- CDP service status
- Upgrade progress
- Time elapsed

### Manual Checks

```bash
# Check specific host
ssh root@worker01 "cat /etc/redhat-release"

# Check CM services
curl -s -u admin:password http://master01:7180/api/v40/clusters/YourCluster/services | jq .

# Check Terraform progress
terraform show | grep -E "(upgrade|status)"
```

---

## ⏱️ Timeline

**Typical medium cluster (15 nodes):**

| Phase | Duration | Status |
|-------|----------|--------|
| Pre-checks | 15 min | ⏳ Running... |
| Stop services | 15 min | ⏱️ Pending |
| Edge nodes | 1 hour | ⏱️ Pending |
| Worker nodes | 3 hours | ⏱️ Pending |
| Master nodes | 3 hours | ⏱️ Pending |
| Validation | 15 min | ⏱️ Pending |
| Start services | 45 min | ⏱️ Pending |

**Total: ~9 hours**

---

## 🚨 Common Issues

### Issue: Pre-check fails on disk space

```bash
# SSH to problematic host
ssh root@hostname

# Clean old kernels
package-cleanup --oldkernels --count=2

# Or manually remove old kernels
yum remove kernel-<old-version>
```

### Issue: CM API not accessible

```bash
# Check CM is running
systemctl status cloudera-scm-server

# Check firewall
firewall-cmd --list-all

# Test connectivity
curl -u admin:password http://cm-server:7180/api/v40/cm/version
```

### Issue: SSH authentication fails

```bash
# Verify SSH key
ssh -i ~/.ssh/id_rsa root@hostname "hostname"

# If fails, copy key again
ssh-copy-id -i ~/.ssh/id_rsa root@hostname
```

### Issue: Host doesn't come back after reboot

**Symptom:** "Waiting for host..." message for > 20 minutes

**Action:**
1. Access host via console (if VM) or IPMI
2. Check network: `ip addr`
3. If network down: `systemctl restart NetworkManager`
4. If SELinux relabeling: Wait (can take 30-60 min)

### Issue: Services won't start

```bash
# Check Java version
alternatives --list | grep java
alternatives --set java /usr/java/jdk1.8.0_XXX/bin/java

# Check logs
tail -f /var/log/cloudera-scm-agent/cloudera-scm-agent.log

# Restart agent
systemctl restart cloudera-scm-agent
```

---

## ✅ Post-Upgrade Checklist

```bash
# 1. Verify OS versions
./scripts/verify-os-versions.sh

# 2. Check service health
curl -s -u admin:password http://cm-server:7180/api/v40/clusters/YourCluster/services \
  | jq -r '.items[] | "\(.name): \(.serviceState)"'

# 3. Run test job
ssh root@master01 "sudo -u hdfs hadoop jar /opt/cloudera/parcels/CDH/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar pi 2 10"

# 4. Check HDFS
ssh root@master01 "sudo -u hdfs hdfs dfsadmin -report"

# 5. Check YARN
ssh root@master01 "sudo -u yarn yarn node -list"

# 6. Test Impala
ssh root@edge01 "impala-shell -q 'SELECT version()'"
```

---

## 🔧 Emergency Procedures

### Stop Upgrade Immediately

```bash
# In Terraform terminal
Ctrl + C

# Assess current state
./scripts/assess-state.sh
```

### Rollback Single Node

```bash
# If node just upgraded but having issues
ssh root@hostname

# Option 1: Boot old kernel (from GRUB menu at next reboot)

# Option 2: Restore from backup
cd /backup/rhel-upgrade/$(hostname)_latest
tar -xzf etc-backup.tar.gz -C /
reboot
```

### Rollback Entire Cluster

```bash
# 1. Stop Terraform
Ctrl + C

# 2. Identify successfully upgraded nodes
./scripts/check-versions.sh

# 3. Rollback each upgraded node
for host in worker01 worker02; do
  ssh root@$host "cd /backup/rhel-upgrade/\$(hostname)_latest && tar -xzf etc-backup.tar.gz -C / && reboot"
done

# 4. Wait for nodes to come back

# 5. Restart CDP services
curl -u admin:password -X POST \
  http://cm-server:7180/api/v40/clusters/YourCluster/commands/start
```

---

## 📞 Getting Help

### Logs to Check

```bash
# Terraform logs
cat terraform-output.log

# Leapp logs (on target host)
ssh root@hostname "cat /var/log/leapp/leapp-report.txt"
ssh root@hostname "tail -100 /var/log/leapp/leapp-upgrade.log"

# CM logs
ssh root@cm-server "tail -100 /var/log/cloudera-scm-server/cloudera-scm-server.log"

# Agent logs
ssh root@hostname "tail -100 /var/log/cloudera-scm-agent/cloudera-scm-agent.log"
```

### Support Contacts

- **Red Hat Support:** For Leapp/RHEL upgrade issues
- **Cloudera Support:** For CDP service issues
- **Your Team:** Check your escalation matrix

### Debug Information to Collect

```bash
# Create support bundle
./scripts/create-support-bundle.sh

# This collects:
# - Terraform logs
# - Configuration files
# - Pre/post upgrade reports
# - Host information
# - Service status
```

---

## 📚 Next Steps After Successful Upgrade

### Immediate (0-24 hours)

- [ ] Monitor cluster health in CM UI
- [ ] Run production workload tests
- [ ] Check for any alerts/warnings
- [ ] Verify data accessibility
- [ ] Monitor performance metrics

### Short-term (1-7 days)

- [ ] Run full regression tests
- [ ] Update monitoring configurations
- [ ] Document any issues encountered
- [ ] Train team on RHEL 8 differences

### Long-term (1-4 weeks)

- [ ] Clean up old RHEL 7 packages
- [ ] Remove rescue kernels
- [ ] Optimize for RHEL 8
- [ ] Update disaster recovery plans
- [ ] Conduct post-mortem review

---

## 🎯 Key Success Factors

1. **Test First:** Always test in dev/staging before production
2. **Schedule Wisely:** Allow 2x estimated time for maintenance window
3. **Communicate:** Keep stakeholders informed throughout
4. **Monitor:** Watch progress actively, don't set and forget
5. **Document:** Record everything for future reference

---

## 📖 Additional Resources

- [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) - Detailed configuration guide
- [README.md](README.md) - Full documentation
- [UPGRADE_CHECKLIST.md](UPGRADE_CHECKLIST.md) - Comprehensive checklist
- [Red Hat Leapp Documentation](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/upgrading_from_rhel_7_to_rhel_8/)
- [Cloudera CDP Documentation](https://docs.cloudera.com/)

---

## 💡 Tips for Success

### Before You Start

✅ **DO:**
- Test in non-production first
- Take complete backups
- Have rollback plan ready
- Schedule adequate time
- Get stakeholder approval

❌ **DON'T:**
- Rush the process
- Skip pre-checks
- Ignore warnings
- Upgrade during business hours
- Go beyond maintenance window

### During Execution

✅ **DO:**
- Monitor continuously
- Document issues
- Stay calm
- Follow the process
- Communicate status

❌ **DON'T:**
- Panic if something looks slow
- Interrupt Terraform unnecessarily
- Skip validation steps
- Make manual changes mid-upgrade
- Forget to save logs

### After Completion

✅ **DO:**
- Validate thoroughly
- Monitor for 24-48 hours
- Update documentation
- Share lessons learned
- Celebrate success! 🎉

❌ **DON'T:**
- Declare success too early
- Skip cleanup
- Forget to thank your team
- Neglect follow-up monitoring

---

## 🏁 You're Ready!

If you've:
- [x] Read this guide
- [x] Completed prerequisites
- [x] Configured terraform.tfvars
- [x] Run pre-flight checks
- [x] Have backups ready
- [x] Scheduled maintenance window
- [x] Notified stakeholders

**You're ready to execute!**

```bash
terraform apply upgrade.plan
```

Good luck! 🚀

