# RHEL Upgrade Automation - Document Index

Welcome to the RHEL 7.9 to 8.10 upgrade automation for Cloudera CDP Private Base clusters!

## 🎯 Start Here

**New to this automation?**
1. Read [README.md](README.md) for project overview
2. Follow [QUICK_START.md](QUICK_START.md) for 30-minute setup
3. Use [UPGRADE_CHECKLIST.md](UPGRADE_CHECKLIST.md) during execution

**Need detailed guidance?**
- Read [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for comprehensive setup instructions

## 📚 Documentation Guide

### Getting Started Documents

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [README.md](README.md) | Project overview, features, architecture | Understanding the project |
| [QUICK_START.md](QUICK_START.md) | Fast-track setup and execution | Quick implementation |
| [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) | Detailed configuration and troubleshooting | In-depth setup |
| [UPGRADE_CHECKLIST.md](UPGRADE_CHECKLIST.md) | Step-by-step execution checklist | During upgrade |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | File organization and descriptions | Understanding codebase |

### Quick Navigation

#### 🚀 I want to get started quickly
→ Go to [QUICK_START.md](QUICK_START.md)

#### 📖 I need detailed configuration help
→ Go to [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)

#### ✅ I'm ready to execute the upgrade
→ Go to [UPGRADE_CHECKLIST.md](UPGRADE_CHECKLIST.md)

#### 🔍 I want to understand the architecture
→ Go to [README.md](README.md#architecture)

#### 🛠️ I encountered an issue
→ Go to [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md#troubleshooting)

#### 📁 I need to understand the file structure
→ Go to [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 🔧 Configuration Files

| File | Description | Action Required |
|------|-------------|-----------------|
| `terraform.tfvars.example` | Example configuration | Copy to `terraform.tfvars` |
| `terraform.tfvars` | Your configuration | **Create and customize** |
| `main.tf` | Main orchestration | No changes needed |
| `variables.tf` | Variable definitions | No changes needed |
| `outputs.tf` | Output definitions | No changes needed |

## 🛠️ Helper Scripts

Located in `scripts/` directory:

| Script | Purpose | Usage |
|--------|---------|-------|
| `check-prerequisites.sh` | Validate prerequisites | Run before starting |
| `monitor-upgrade.sh` | Real-time monitoring | Run during execution |
| `verify-os-versions.sh` | Verify upgrade success | Run after completion |
| `create-support-bundle.sh` | Create diagnostic bundle | Run when troubleshooting |

## 📦 Modules

Located in `modules/` directory:

| Module | Purpose | Phase |
|--------|---------|-------|
| `pre-upgrade/` | Validation checks | Before upgrade |
| `cdp-prepare/` | Stop CDP services | Preparation |
| `upgrade-node/` | Execute OS upgrade | Main upgrade |
| `post-upgrade/` | Validation checks | After upgrade |
| `cdp-restore/` | Start CDP services | Restoration |
| `final-validation/` | Final checks and reporting | Completion |

## 📋 Common Tasks

### Initial Setup

```bash
# 1. Check prerequisites
./scripts/check-prerequisites.sh

# 2. Create configuration
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with your settings

# 3. Initialize Terraform
terraform init

# 4. Validate configuration
terraform validate

# 5. Create execution plan
terraform plan -out=upgrade.plan
```

### Execution

```bash
# Start monitoring (in separate terminal)
./scripts/monitor-upgrade.sh

# Execute upgrade
terraform apply upgrade.plan
```

### Post-Execution

```bash
# Verify OS versions
./scripts/verify-os-versions.sh

# Check cluster health
# (see UPGRADE_CHECKLIST.md for detailed steps)
```

## 🎓 Learning Path

### For First-Time Users

1. **Day 1-2:** Read documentation
   - Read [README.md](README.md)
   - Review [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)
   - Understand [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

2. **Day 3:** Set up dev environment
   - Follow [QUICK_START.md](QUICK_START.md)
   - Configure test cluster
   - Run prerequisite checks

3. **Day 4:** Test in dev
   - Execute in dev environment
   - Document issues
   - Refine configuration

4. **Day 5:** Test in staging
   - Execute in staging environment
   - Validate procedures
   - Update runbooks

5. **Week 2:** Production execution
   - Follow [UPGRADE_CHECKLIST.md](UPGRADE_CHECKLIST.md)
   - Execute with team
   - Document lessons learned

### For Experienced Users

1. Review [QUICK_START.md](QUICK_START.md)
2. Customize `terraform.tfvars`
3. Run `./scripts/check-prerequisites.sh`
4. Execute: `terraform apply upgrade.plan`
5. Follow [UPGRADE_CHECKLIST.md](UPGRADE_CHECKLIST.md#post-upgrade-phase)

## 🆘 Troubleshooting Quick Links

| Problem | Solution Document | Section |
|---------|-------------------|---------|
| Prerequisites not met | [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md#prerequisites) | Prerequisites |
| Configuration issues | [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md#configuration) | Configuration |
| Pre-upgrade check fails | [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md#issue-1-pre-upgrade-check-fails) | Troubleshooting |
| Node doesn't reboot | [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md#issue-3-node-doesnt-come-back-after-reboot) | Troubleshooting |
| Services won't start | [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md#issue-5-services-wont-start) | Troubleshooting |
| Need to rollback | [QUICK_START.md](QUICK_START.md#emergency-procedures) | Emergency |

## 📞 Support

### Before Contacting Support

1. Review relevant troubleshooting section
2. Check all logs
3. Run `./scripts/create-support-bundle.sh`
4. Document exact error messages

### Support Channels

- **Red Hat Support:** RHEL/Leapp upgrade issues
- **Cloudera Support:** CDP service issues
- **Internal Team:** Configuration and execution questions

## 🎯 Document Comparison

### README.md vs QUICK_START.md

| README.md | QUICK_START.md |
|-----------|----------------|
| Comprehensive overview | Fast-track guide |
| Full architecture details | Simplified steps |
| All features explained | Key tasks only |
| Complete troubleshooting | Common issues only |
| Read for understanding | Read for action |

### CONFIGURATION_GUIDE.md vs UPGRADE_CHECKLIST.md

| CONFIGURATION_GUIDE.md | UPGRADE_CHECKLIST.md |
|------------------------|----------------------|
| How to configure | What to check |
| Why settings matter | When to do tasks |
| Detailed explanations | Step-by-step actions |
| Troubleshooting guide | Execution checklist |
| Reference document | Working document |

## 📊 Document Size and Reading Time

| Document | Size | Reading Time | Purpose |
|----------|------|--------------|---------|
| [README.md](README.md) | Large | 30-45 min | Comprehensive understanding |
| [QUICK_START.md](QUICK_START.md) | Medium | 15-20 min | Quick implementation |
| [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) | Very Large | 60-90 min | Deep dive |
| [UPGRADE_CHECKLIST.md](UPGRADE_CHECKLIST.md) | Large | Work alongside | Execution guide |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Medium | 20-30 min | Code understanding |

## 🗺️ Upgrade Journey Map

```
┌─────────────────────────────────────────────────────────┐
│                   PREPARATION PHASE                      │
│  Documents: README.md, CONFIGURATION_GUIDE.md           │
│  Scripts: check-prerequisites.sh                        │
│  Duration: 1-2 weeks                                    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  CONFIGURATION PHASE                     │
│  Documents: QUICK_START.md, terraform.tfvars.example    │
│  Actions: Configure, validate, plan                     │
│  Duration: 2-4 hours                                    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    EXECUTION PHASE                       │
│  Documents: UPGRADE_CHECKLIST.md                        │
│  Scripts: monitor-upgrade.sh                            │
│  Duration: 6-12 hours                                   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   VALIDATION PHASE                       │
│  Documents: UPGRADE_CHECKLIST.md (Post-Upgrade)         │
│  Scripts: verify-os-versions.sh                         │
│  Duration: 4-8 hours                                    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    MONITORING PHASE                      │
│  Duration: 1-4 weeks                                    │
│  Activities: Monitor, optimize, document                │
└─────────────────────────────────────────────────────────┘
```

## 📝 Checklist: Before You Start

- [ ] Read [README.md](README.md)
- [ ] Review [QUICK_START.md](QUICK_START.md)
- [ ] Understand [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- [ ] Run `./scripts/check-prerequisites.sh`
- [ ] Create and configure `terraform.tfvars`
- [ ] Test in non-production environment
- [ ] Schedule maintenance window
- [ ] Notify stakeholders
- [ ] Print [UPGRADE_CHECKLIST.md](UPGRADE_CHECKLIST.md)
- [ ] Prepare rollback plan

## 🚀 You're Ready!

Once you've completed the checklist above, you're ready to begin!

**Next Step:** Open [QUICK_START.md](QUICK_START.md) and follow the 30-minute setup guide.

---

**Quick Command Reference:**

```bash
# Check prerequisites
./scripts/check-prerequisites.sh

# Initialize
terraform init

# Plan
terraform plan -out=upgrade.plan

# Execute
terraform apply upgrade.plan

# Monitor (separate terminal)
./scripts/monitor-upgrade.sh

# Verify
./scripts/verify-os-versions.sh
```

Good luck with your upgrade! 🎉


