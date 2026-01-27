# Project Structure - RHEL Upgrade Automation

## Overview

This document describes the organization and purpose of each file and directory in the RHEL upgrade automation project.

## Directory Tree

```
rhel-upgrade-automation/
│
├── Documentation Files
│   ├── README.md                     # Main project documentation
│   ├── CONFIGURATION_GUIDE.md        # Detailed configuration guide
│   ├── QUICK_START.md                # Quick start guide
│   ├── UPGRADE_CHECKLIST.md          # Step-by-step checklist
│   └── PROJECT_STRUCTURE.md          # This file
│
├── Terraform Configuration
│   ├── main.tf                       # Main orchestration logic
│   ├── variables.tf                  # Variable definitions
│   ├── outputs.tf                    # Output definitions
│   ├── terraform.tfvars.example      # Example configuration
│   └── terraform.tfvars              # Your actual configuration (create this)
│
├── Helper Scripts
│   └── scripts/
│       ├── check-prerequisites.sh    # Prerequisites checker
│       ├── monitor-upgrade.sh        # Real-time progress monitor
│       ├── verify-os-versions.sh     # Post-upgrade verification
│       └── create-support-bundle.sh  # Support bundle creator
│
├── Terraform Modules
│   ├── modules/pre-upgrade/          # Pre-upgrade validation module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── scripts/
│   │       ├── pre_upgrade_check.sh
│   │       └── check_blockers.sh
│   │
│   ├── modules/upgrade-node/         # Node upgrade execution module
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
│   ├── modules/post-upgrade/         # Post-upgrade validation module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── scripts/
│   │       ├── post_upgrade_validation.sh
│   │       └── aggregate_validation.sh
│   │
│   ├── modules/cdp-prepare/          # CDP preparation module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── scripts/
│   │       ├── stop_cluster.sh
│   │       └── backup_cluster_state.sh
│   │
│   ├── modules/cdp-restore/          # CDP restoration module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── scripts/
│   │       ├── wait_for_cm.sh
│   │       ├── wait_for_agents.sh
│   │       ├── start_cluster.sh
│   │       └── health_check.sh
│   │
│   └── modules/final-validation/     # Final validation module
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── scripts/
│           └── final_validation.sh
│
└── Examples
    └── examples/
        └── small-cluster.tfvars      # Example for small cluster
```

## File Descriptions

### Documentation Files

#### README.md
**Purpose:** Main project documentation  
**Contains:**
- Project overview and features
- Architecture description
- Installation instructions
- Usage examples
- Troubleshooting guide

**When to use:** First stop for understanding the project

#### CONFIGURATION_GUIDE.md
**Purpose:** Comprehensive configuration guide  
**Contains:**
- Detailed prerequisites
- Step-by-step configuration
- Advanced settings
- Troubleshooting procedures
- Post-execution tasks

**When to use:** When setting up the automation for the first time

#### QUICK_START.md
**Purpose:** Condensed quick start guide  
**Contains:**
- 30-minute setup guide
- Execution commands
- Common issues
- Emergency procedures

**When to use:** When you need to get started quickly

#### UPGRADE_CHECKLIST.md
**Purpose:** Comprehensive execution checklist  
**Contains:**
- Pre-upgrade tasks
- Day-of execution steps
- Post-upgrade validation
- Rollback procedures

**When to use:** During actual upgrade execution

### Terraform Configuration Files

#### main.tf
**Purpose:** Main orchestration logic  
**Contains:**
- Module declarations
- Execution order (depends_on)
- Phase coordination

**Modify when:** Never (unless customizing workflow)

#### variables.tf
**Purpose:** Variable definitions  
**Contains:**
- All configurable parameters
- Default values
- Validation rules

**Modify when:** Never (define values in terraform.tfvars)

#### outputs.tf
**Purpose:** Output definitions  
**Contains:**
- Upgrade summary
- Status information
- Next steps guidance

**Modify when:** You want different output information

#### terraform.tfvars.example
**Purpose:** Example configuration  
**Contains:**
- Sample cluster configuration
- Commented parameters
- Usage examples

**Modify when:** Never (copy to terraform.tfvars)

#### terraform.tfvars (you create this)
**Purpose:** Your actual configuration  
**Contains:**
- Your cluster hosts
- CM credentials
- SSH settings
- Upgrade parameters

**Modify when:** Initial setup and any configuration changes

### Helper Scripts

#### scripts/check-prerequisites.sh
**Purpose:** Validate prerequisites before execution  
**Checks:**
- Terraform installation
- Required tools (jq, curl, ssh)
- Configuration file
- SSH connectivity
- CM API access

**Run when:** Before starting upgrade

#### scripts/monitor-upgrade.sh
**Purpose:** Real-time progress monitoring  
**Shows:**
- Host OS versions
- Upgrade progress
- CDP service status
- Time elapsed

**Run when:** During upgrade execution (separate terminal)

#### scripts/verify-os-versions.sh
**Purpose:** Verify all hosts upgraded successfully  
**Checks:**
- OS version on each host
- SSH connectivity

**Run when:** After upgrade completion

#### scripts/create-support-bundle.sh
**Purpose:** Create diagnostic bundle for support  
**Collects:**
- Logs
- Configuration (sanitized)
- Reports
- System information

**Run when:** Encountering issues needing support

### Terraform Modules

Each module is self-contained with:
- `main.tf` - Module logic
- `variables.tf` - Module inputs
- `outputs.tf` - Module outputs
- `scripts/` - Bash scripts for execution

#### modules/pre-upgrade/
**Purpose:** Pre-upgrade validation  
**Performs:**
- OS version check
- Disk space validation
- Subscription verification
- CDP service check
- Network connectivity test

**Scripts:**
- `pre_upgrade_check.sh` - Individual host checks
- `check_blockers.sh` - Aggregate results

#### modules/upgrade-node/
**Purpose:** Execute upgrade on nodes  
**Performs:**
- System backup
- Leapp installation
- Pre-upgrade assessment
- Upgrade execution
- Reboot and wait

**Scripts:**
- `backup_system.sh` - System backup
- `install_leapp.sh` - Install Leapp
- `run_leapp_preupgrade.sh` - Pre-upgrade assessment
- `run_upgrade.sh` - Execute upgrade
- `wait_for_host.sh` - Wait for reboot

#### modules/post-upgrade/
**Purpose:** Post-upgrade validation  
**Performs:**
- OS version verification
- Service health check
- Network validation
- CDP component check

**Scripts:**
- `post_upgrade_validation.sh` - Individual checks
- `aggregate_validation.sh` - Combine results

#### modules/cdp-prepare/
**Purpose:** Prepare CDP cluster for upgrade  
**Performs:**
- Stop cluster services
- Stop CM agents
- Stop CM server
- Backup cluster state

**Scripts:**
- `stop_cluster.sh` - Stop services via CM API
- `backup_cluster_state.sh` - Backup CM database

#### modules/cdp-restore/
**Purpose:** Restore CDP cluster after upgrade  
**Performs:**
- Start CM server
- Start CM agents
- Start cluster services
- Health check

**Scripts:**
- `wait_for_cm.sh` - Wait for CM to be ready
- `wait_for_agents.sh` - Wait for agents
- `start_cluster.sh` - Start services
- `health_check.sh` - Verify cluster health

#### modules/final-validation/
**Purpose:** Final validation and reporting  
**Performs:**
- Comprehensive cluster check
- Generate final report
- Provide next steps

**Scripts:**
- `final_validation.sh` - Complete validation

### Examples

#### examples/small-cluster.tfvars
**Purpose:** Configuration example for small cluster  
**Contains:**
- Minimal cluster configuration (5 nodes)
- Basic settings
- Comments explaining choices

**Use when:** Reference for creating your own configuration

## File Locations During Execution

### On Terraform Execution Host

```
/opt/rhel-upgrade-automation/
├── terraform.tfvars           # Your configuration
├── terraform-output.log       # Execution log
├── upgrade.plan              # Terraform plan
└── .terraform/               # Terraform cache
```

### On Target Hosts

```
/backup/rhel-upgrade/
├── <hostname>_<timestamp>/   # System backup
│   ├── etc-backup.tar.gz
│   ├── system_info.txt
│   └── ...
└── pre-upgrade-reports/      # Pre-upgrade reports
    └── <hostname>.json

/tmp/
├── pre_upgrade_check.sh      # Uploaded scripts
├── pre_upgrade_report.json   # Check results
└── upgrade-scripts/          # Upgrade scripts
    ├── backup_system.sh
    ├── run_upgrade.sh
    └── ...

/var/log/leapp/               # Leapp logs
├── leapp-upgrade.log
├── leapp-report.txt
└── ...
```

### On Cloudera Manager Server

```
/backup/rhel-upgrade/
└── cluster-state-<timestamp>/
    ├── cm_database.sql       # CM database backup
    ├── cm-server-config.tar.gz
    └── cm_deployment.json
```

## Generated Files

### During Execution

| File | Location | Purpose |
|------|----------|---------|
| `terraform-output.log` | Project root | Full Terraform output |
| `upgrade.plan` | Project root | Terraform execution plan |
| `.terraform/` | Project root | Terraform cache |
| `pre-upgrade-reports/*.json` | Backup path | Pre-check results |
| `post-upgrade-reports/*.json` | /tmp | Post-check results |
| `support-bundle-*.tar.gz` | Project root | Support bundle |

### On Target Hosts

| File | Location | Purpose |
|------|----------|---------|
| `/backup/rhel-upgrade/<hostname>_<timestamp>/` | Target host | System backup |
| `/var/log/leapp/` | Target host | Leapp upgrade logs |
| `/root/pre-upgrade-state.txt` | Target host | Pre-upgrade marker |
| `/root/upgrade-in-progress.marker` | Target host | Upgrade marker |

## Execution Flow Through Files

```
1. User runs: terraform apply upgrade.plan
   └─> main.tf orchestrates

2. main.tf calls module.pre_upgrade_checks
   └─> modules/pre-upgrade/main.tf
       └─> modules/pre-upgrade/scripts/pre_upgrade_check.sh (on each host)
       └─> modules/pre-upgrade/scripts/check_blockers.sh (locally)

3. main.tf calls module.cdp_prepare
   └─> modules/cdp-prepare/main.tf
       └─> modules/cdp-prepare/scripts/stop_cluster.sh
       └─> modules/cdp-prepare/scripts/backup_cluster_state.sh

4. main.tf calls module.upgrade_edge_nodes
   └─> modules/upgrade-node/main.tf
       └─> modules/upgrade-node/scripts/backup_system.sh (on each edge node)
       └─> modules/upgrade-node/scripts/install_leapp.sh
       └─> modules/upgrade-node/scripts/run_leapp_preupgrade.sh
       └─> modules/upgrade-node/scripts/run_upgrade.sh
       └─> modules/upgrade-node/scripts/wait_for_host.sh (locally)

5. Repeat step 4 for worker nodes (in batches)

6. Repeat step 4 for master nodes (sequentially)

7. main.tf calls module.post_upgrade_validation
   └─> modules/post-upgrade/main.tf
       └─> modules/post-upgrade/scripts/post_upgrade_validation.sh (on each host)
       └─> modules/post-upgrade/scripts/aggregate_validation.sh (locally)

8. main.tf calls module.cdp_restore
   └─> modules/cdp-restore/main.tf
       └─> modules/cdp-restore/scripts/wait_for_cm.sh
       └─> modules/cdp-restore/scripts/wait_for_agents.sh
       └─> modules/cdp-restore/scripts/start_cluster.sh
       └─> modules/cdp-restore/scripts/health_check.sh

9. main.tf calls module.final_validation
   └─> modules/final-validation/main.tf
       └─> modules/final-validation/scripts/final_validation.sh

10. Terraform generates outputs (outputs.tf)
```

## Customization Points

### To customize upgrade behavior:

1. **Change upgrade order:** Edit `main.tf` dependencies
2. **Modify checks:** Edit scripts in `modules/*/scripts/`
3. **Add custom actions:** Add provisioners in module `main.tf` files
4. **Change batch sizes:** Edit `worker_batch_size` in `terraform.tfvars`
5. **Skip services:** Edit `skip_services` in `terraform.tfvars`

### To add new functionality:

1. Create new module in `modules/`
2. Add module call in root `main.tf`
3. Add variables in root `variables.tf`
4. Add outputs in root `outputs.tf`

## Maintenance

### Regular updates needed:

- **terraform.tfvars** - When cluster topology changes
- **Scripts** - For bug fixes or enhancements
- **Documentation** - When procedures change

### Files to version control:

✅ Include:
- All `.tf` files
- `terraform.tfvars.example`
- All documentation
- All scripts
- Module files

❌ Exclude (add to .gitignore):
- `terraform.tfvars` (contains passwords)
- `.terraform/`
- `*.log`
- `*.plan`
- `support-bundle-*.tar.gz`

## Summary

This project is organized for:
- **Clarity:** Each file has a clear purpose
- **Modularity:** Components are independent
- **Reusability:** Modules can be used separately
- **Maintainability:** Easy to update and debug
- **Scalability:** Works for clusters of any size

For questions about specific files, refer to inline comments in each file.


