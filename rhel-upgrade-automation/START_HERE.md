# 🚀 START HERE - RHEL Upgrade Automation

## Welcome!

This is your automated solution for upgrading Red Hat Enterprise Linux from version 7.9 to 8.10 on Cloudera CDP Private Base clusters.

## ⚡ Quick Navigation

### 👉 I'm New Here
**Start with:** [README.md](README.md)  
**Then read:** [QUICK_START.md](QUICK_START.md)  
**Time needed:** 1 hour to understand, 2 hours to configure

### 👉 I Want to Get Started Now
**Go to:** [QUICK_START.md](QUICK_START.md)  
**Time needed:** 30 minutes to configure, 6-12 hours to execute

### 👉 I Need Detailed Instructions
**Go to:** [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)  
**Time needed:** 2 hours to read, reference during setup

### 👉 I'm Ready to Execute
**Go to:** [UPGRADE_CHECKLIST.md](UPGRADE_CHECKLIST.md)  
**Print this:** Use as your working checklist during upgrade

### 👉 I Need to Understand the Code
**Go to:** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)  
**Time needed:** 30 minutes

### 👉 I Want an Overview of Everything
**Go to:** [INDEX.md](INDEX.md)  
**Time needed:** 10 minutes

## 📋 What This Automation Does

```
1. ✅ Validates all nodes are ready for upgrade
2. 🛑 Stops CDP cluster services gracefully
3. 💾 Creates comprehensive backups
4. 🔄 Upgrades nodes in optimal order:
   - Edge nodes (parallel - fastest)
   - Worker nodes (batches - maintains capacity)
   - Master nodes (sequential - safest)
5. ✅ Validates each upgrade
6. 🚀 Restarts CDP services
7. 📊 Performs health checks
8. 📄 Generates detailed report
```

## ⏱️ Time Commitment

| Phase | Duration |
|-------|----------|
| **Learning & Setup** | 4-8 hours |
| **Testing in Dev** | 1 day |
| **Testing in Staging** | 1 day |
| **Production Execution** | 6-12 hours |
| **Post-Upgrade Monitoring** | 1-2 weeks |

## 🎯 Success Path

### Week 1: Preparation
```bash
Day 1-2: Read documentation
Day 3:   Configure for dev environment
Day 4:   Test in dev
Day 5:   Review and refine
```

### Week 2: Staging
```bash
Day 1:   Configure for staging
Day 2:   Execute in staging
Day 3-5: Validate and monitor
```

### Week 3: Production
```bash
Day 1:   Final preparation
Day 2:   Execute upgrade
Day 3-7: Monitor and validate
```

## 🚦 Prerequisites Checklist

Before you begin, ensure you have:

### Infrastructure
- [ ] RHEL 7.9 on all nodes
- [ ] Valid Red Hat subscription with RHEL 8 entitlements
- [ ] SSH key-based authentication configured
- [ ] Sufficient disk space (see requirements)
- [ ] Network connectivity to Red Hat CDN

### Software
- [ ] Terraform >= 1.0 installed
- [ ] jq installed
- [ ] curl installed
- [ ] SSH client installed

### Access
- [ ] Root or sudo access to all nodes
- [ ] Cloudera Manager admin credentials
- [ ] CM API accessible

### Planning
- [ ] Maintenance window scheduled (8-12 hours)
- [ ] Stakeholders notified
- [ ] Backups current
- [ ] Rollback plan documented
- [ ] Team available

## 🎬 Quick Start (30 Minutes)

**Option A: With Auto-Discovery (Easiest)**

```bash
# 1. Check prerequisites (5 min)
cd /path/to/rhel-upgrade-automation
./scripts/check-prerequisites.sh

# 2. Configure with auto-discovery (5 min)
cp terraform-auto-discover.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit CM connection details only

# 3. Initialize and validate (10 min)
terraform init
terraform validate
terraform plan -out=upgrade.plan
# Terraform will automatically discover all hosts from CM!

# 4. Review plan (10 min)
# Check discovered_cluster_info output
# Verify host roles and counts
```

**Option B: Manual Configuration**

```bash
# 1. Check prerequisites (5 min)
cd /path/to/rhel-upgrade-automation
./scripts/check-prerequisites.sh

# 2. Configure manually (15 min)
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Manually list all hosts

# 3. Initialize and validate (5 min)
terraform init
terraform validate
terraform plan -out=upgrade.plan

# 4. Review plan (5 min)
# Read the plan output carefully!
```

## 📚 Documentation Overview

| Document | Purpose | Size | When to Use |
|----------|---------|------|-------------|
| **START_HERE.md** | This file - orientation | Short | First stop |
| **INDEX.md** | Document index & navigation | Short | Finding documents |
| **README.md** | Complete project documentation | Long | Understanding project |
| **QUICK_START.md** | Fast-track implementation | Medium | Quick setup |
| **CONFIGURATION_GUIDE.md** | Detailed setup & troubleshooting | Very Long | Deep dive |
| **UPGRADE_CHECKLIST.md** | Execution checklist | Long | During upgrade |
| **PROJECT_STRUCTURE.md** | Code organization | Medium | Understanding code |

## 🎓 Recommended Reading Order

### For Beginners
1. START_HERE.md (you are here) ← 5 min
2. README.md ← 30 min
3. CONFIGURATION_GUIDE.md ← 60 min
4. QUICK_START.md ← 15 min
5. UPGRADE_CHECKLIST.md ← Reference during execution

### For Experienced Users
1. START_HERE.md (you are here) ← 5 min
2. QUICK_START.md ← 15 min
3. UPGRADE_CHECKLIST.md ← Reference during execution

## 🛠️ Key Files to Know

### Configuration Files
- **terraform.tfvars.example** - Copy this to terraform.tfvars
- **terraform.tfvars** - Your actual configuration (YOU CREATE THIS)

### Helper Scripts
- **scripts/check-prerequisites.sh** - Run before starting
- **scripts/monitor-upgrade.sh** - Run during execution
- **scripts/verify-os-versions.sh** - Run after completion

### Terraform Files
- **main.tf** - Orchestration logic (don't modify)
- **variables.tf** - Variable definitions (don't modify)
- **outputs.tf** - Output definitions (don't modify)

## 🚨 Important Warnings

### ⚠️ DO NOT
- ❌ Run in production without testing in dev/staging first
- ❌ Start without a maintenance window
- ❌ Skip the pre-upgrade checks
- ❌ Interrupt Terraform during critical phases
- ❌ Modify files during execution

### ✅ DO
- ✅ Test in non-production first
- ✅ Take complete backups
- ✅ Schedule adequate time (2x estimated)
- ✅ Monitor continuously during execution
- ✅ Document everything

## 🎯 Your Next Steps

### Right Now (5 minutes)
1. ✅ You're reading START_HERE.md (good!)
2. → Open [INDEX.md](INDEX.md) for document overview
3. → Decide your path: Quick or Detailed

### Today (2-4 hours)
1. → Read [README.md](README.md) for project understanding
2. → Review [QUICK_START.md](QUICK_START.md) for setup steps
3. → Run `./scripts/check-prerequisites.sh`

### This Week (8-16 hours)
1. → Read [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)
2. → Configure `terraform.tfvars`
3. → Test in dev environment
4. → Document your experience

### Next Week (8-12 hours)
1. → Test in staging environment
2. → Refine configuration
3. → Prepare for production

### Week 3 (8-12 hours)
1. → Execute in production
2. → Follow [UPGRADE_CHECKLIST.md](UPGRADE_CHECKLIST.md)
3. → Monitor and validate

## 💡 Pro Tips

### Before You Start
- 📖 Read all documentation first
- 🧪 Test in dev environment
- 📋 Print the checklist
- 👥 Have your team ready
- ☕ Get coffee - it's a long process!

### During Execution
- 👀 Monitor continuously
- 📝 Document issues immediately
- 🤝 Keep team informed
- 😌 Stay calm
- 🚫 Don't panic if things seem slow

### After Completion
- ✅ Validate thoroughly
- 📊 Monitor for 24-48 hours
- 📄 Update documentation
- 🎉 Celebrate success!
- 📚 Share lessons learned

## 🆘 Need Help?

### Common Issues
→ See [CONFIGURATION_GUIDE.md - Troubleshooting](CONFIGURATION_GUIDE.md#troubleshooting)

### Emergency Procedures
→ See [QUICK_START.md - Emergency Procedures](QUICK_START.md#emergency-procedures)

### Support
- **Red Hat Support:** RHEL/Leapp issues
- **Cloudera Support:** CDP issues
- **Your Team:** Configuration questions

## 📞 Before Contacting Support

1. Check troubleshooting section
2. Review all logs
3. Run `./scripts/create-support-bundle.sh`
4. Document exact error messages

## 🎬 Ready to Begin?

### Choose Your Path:

**Path A: Quick Start (Experienced Users)**
```bash
→ Go to QUICK_START.md
→ Follow 30-minute setup
→ Execute upgrade
```

**Path B: Detailed Path (First-Time Users)**
```bash
→ Read README.md (30 min)
→ Read CONFIGURATION_GUIDE.md (60 min)
→ Follow setup instructions
→ Test in dev environment
→ Execute upgrade
```

**Path C: Just Browsing**
```bash
→ Read INDEX.md for overview
→ Browse documentation
→ Come back when ready
```

## 📊 What Success Looks Like

After successful completion:
- ✅ All nodes running RHEL 8.10
- ✅ All CDP services healthy
- ✅ No data loss
- ✅ Performance maintained or improved
- ✅ Comprehensive documentation
- ✅ Team knowledge transfer complete

## 🏁 Final Checklist Before Starting

- [ ] I've read the documentation
- [ ] I understand the process
- [ ] I've tested in non-production
- [ ] I have a maintenance window
- [ ] I have backups
- [ ] I have a rollback plan
- [ ] My team is ready
- [ ] I'm ready to commit 8-12 hours

## 🚀 Let's Go!

**If you've checked all the boxes above, you're ready!**

**Next Step:** Open [QUICK_START.md](QUICK_START.md) or [README.md](README.md)

---

## 📖 Document Map

```
START_HERE.md (you are here)
    ├── Quick Path → QUICK_START.md
    │                    └── UPGRADE_CHECKLIST.md
    │
    └── Detailed Path → README.md
                           ├── CONFIGURATION_GUIDE.md
                           └── UPGRADE_CHECKLIST.md

Reference Documents:
    ├── INDEX.md (navigation)
    └── PROJECT_STRUCTURE.md (code organization)
```

---

**Questions?** Check [INDEX.md](INDEX.md) for document navigation.

**Ready?** Go to [QUICK_START.md](QUICK_START.md)!

**Need details?** Go to [README.md](README.md)!

Good luck with your upgrade! 🎉

