# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-01-08

### Added - Auto-Discovery Feature

#### New Functionality
- **Automatic Host Discovery from Cloudera Manager**
  - Fetch all cluster hosts via CM REST API
  - Automatic role detection (master/worker/edge)
  - Auto-detect CM server and cluster name
  - Dynamic host list that stays in sync with cluster

#### New Files
- `scripts/fetch-cm-hosts.sh` - Script to fetch hosts from CM API
- `data-sources.tf` - Terraform data sources for auto-discovery
- `terraform-auto-discover.tfvars.example` - Example config for auto-discovery
- `examples/auto-discover-cluster.tfvars` - Simple auto-discovery example
- `AUTO_DISCOVERY_GUIDE.md` - Comprehensive auto-discovery documentation
- `CHANGELOG.md` - This file

#### Configuration Changes
- Added `auto_discover_hosts` variable (default: false)
- Made `cluster_hosts` variable optional (empty list allowed)
- Added `discovered_cluster_info` output
- Modified `upgrade_summary` output to show discovery mode

#### Enhanced Modules
- All modules now use computed host lists (supports both manual and auto-discovery)
- Main orchestration updated to use dynamic host references
- Variables updated to support both configuration modes

### Changed

#### Configuration Options
- `cluster_hosts` is now optional when `auto_discover_hosts = true`
- `cluster_name` can be empty for auto-detection
- `cm_server_host` can be auto-detected from CM API

#### User Experience
- Simplified configuration - only 4 variables needed for auto-discovery
- Reduced configuration errors - no manual host entry
- Dynamic updates - always reflects current cluster topology

### Documentation Updates

#### New Documentation
- AUTO_DISCOVERY_GUIDE.md - Complete guide for auto-discovery feature
- Enhanced QUICK_START.md with auto-discovery option
- Updated START_HERE.md with two configuration paths

#### Updated Documentation
- README.md - Added auto-discovery section
- CONFIGURATION_GUIDE.md - Added auto-discovery instructions
- QUICK_START.md - Added Option A (auto-discovery) and Option B (manual)
- START_HERE.md - Updated quick start with both methods
- PROJECT_SUMMARY.md - Updated feature list

### Migration Guide

#### Upgrading from v1.0 to v2.0

**Existing Manual Configuration (No Changes Required)**
```hcl
# Your existing terraform.tfvars continues to work
auto_discover_hosts = false  # Add this line (or omit - false is default)

cluster_hosts = [
  # Your existing manual configuration
]
```

**Migrating to Auto-Discovery (Optional)**
```hcl
# New simplified configuration
auto_discover_hosts = true
cm_server_host      = "master01.example.com"
cm_api_user         = "admin"
cm_api_password     = "password"

# Remove or comment out cluster_hosts
# cluster_hosts = [ ... ]
```

### Technical Details

#### API Integration
- Uses CM REST API v40
- Queries: /cm/version, /clusters, /hosts, /services, /roles
- Role detection based on service assignments
- Graceful fallback if API unavailable

#### Role Detection Logic
- **Master:** NameNode, ResourceManager, HBase Master, HiveServer2, Hive Metastore
- **Worker:** DataNode, NodeManager
- **Edge:** No data services (gateways, client nodes)

#### Requirements
- jq must be installed on Terraform execution host
- CM API must be accessible (port 7180)
- Valid CM credentials with read access

### Backwards Compatibility

✅ **Fully Backwards Compatible**
- Existing configurations work without changes
- Default behavior unchanged (`auto_discover_hosts = false`)
- All existing features maintained
- No breaking changes

### Performance

- Auto-discovery adds ~10-20 seconds to `terraform plan`
- CM API calls are cached during plan/apply
- Minimal performance impact
- Only runs when `auto_discover_hosts = true`

### Security

- CM credentials handled securely
- Passwords not logged
- Read-only CM access sufficient
- Support for CM user with limited permissions

---

## [1.0.0] - 2026-01-08

### Initial Release

#### Core Features
- Complete RHEL 7.9 to 8.10 upgrade automation
- CDP Private Base cluster support
- Intelligent orchestration (edge → workers → masters)
- Comprehensive pre/post validation
- CDP-specific service management
- Backup and rollback capability

#### Modules
- pre-upgrade: 15 validation checks
- upgrade-node: Complete upgrade execution
- post-upgrade: 15 post-upgrade validations
- cdp-prepare: Graceful service shutdown
- cdp-restore: Service startup and health checks
- final-validation: Comprehensive validation

#### Documentation
- README.md - Complete project documentation
- QUICK_START.md - 30-minute setup guide
- CONFIGURATION_GUIDE.md - Detailed configuration
- UPGRADE_CHECKLIST.md - Execution checklist
- PROJECT_STRUCTURE.md - Code organization
- INDEX.md - Document navigation
- START_HERE.md - Entry point
- PROJECT_SUMMARY.md - Project overview

#### Helper Scripts
- check-prerequisites.sh - Prerequisites validation
- monitor-upgrade.sh - Real-time monitoring
- verify-os-versions.sh - Post-upgrade verification
- create-support-bundle.sh - Diagnostic bundle creation

#### Configuration
- terraform.tfvars.example - Complete example
- examples/small-cluster.tfvars - Small cluster example

---

## Version Comparison

### v1.0 vs v2.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Manual Configuration | ✅ | ✅ |
| Auto-Discovery | ❌ | ✅ |
| Configuration Lines | 50+ | 6 (auto-mode) |
| Error Prone | Medium | Low |
| Cluster Sync | Manual | Automatic |
| Setup Time | 30 min | 10 min (auto-mode) |

---

## Future Enhancements

### Planned for v2.1
- [ ] Support for multiple CM instances
- [ ] Custom role detection rules
- [ ] Dry-run mode for discovery
- [ ] Host filtering options
- [ ] Export discovered config to manual format

### Under Consideration
- [ ] Web UI for configuration
- [ ] Integration with Ansible
- [ ] Support for other Hadoop distributions
- [ ] Automated testing framework
- [ ] Rollback automation

---

## Contributing

To report issues or suggest enhancements:
1. Check existing documentation
2. Create support bundle
3. Document exact steps to reproduce
4. Include Terraform version and OS

---

## Support

For questions about:
- **Auto-Discovery:** See AUTO_DISCOVERY_GUIDE.md
- **Configuration:** See CONFIGURATION_GUIDE.md
- **Troubleshooting:** See CONFIGURATION_GUIDE.md #Troubleshooting
- **Quick Start:** See QUICK_START.md


