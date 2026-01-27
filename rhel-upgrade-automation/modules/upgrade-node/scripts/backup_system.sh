#!/bin/bash
set -e

# System backup before upgrade
# Usage: backup_system.sh <role>

ROLE=$1
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_BASE="/backup/rhel-upgrade"
BACKUP_DIR="${BACKUP_BASE}/${HOSTNAME}_${TIMESTAMP}"

echo "========================================="
echo "Creating system backup"
echo "Host: $(hostname)"
echo "Role: $ROLE"
echo "========================================="

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Backup directory: $BACKUP_DIR"

# 1. Backup critical system files
echo "Backing up critical system files..."
tar -czf "${BACKUP_DIR}/etc-backup.tar.gz" /etc/ 2>/dev/null || true
tar -czf "${BACKUP_DIR}/var-lib-backup.tar.gz" /var/lib/ 2>/dev/null || true

# 2. Save installed package list
echo "Saving installed packages list..."
rpm -qa | sort > "${BACKUP_DIR}/installed_packages.txt"

# 3. Save repository configuration
echo "Backing up repository configuration..."
cp -r /etc/yum.repos.d "${BACKUP_DIR}/" 2>/dev/null || true

# 4. Save network configuration
echo "Backing up network configuration..."
cp -r /etc/sysconfig/network-scripts "${BACKUP_DIR}/" 2>/dev/null || true
nmcli connection show > "${BACKUP_DIR}/network_connections.txt" 2>/dev/null || true

# 5. Save firewall rules
echo "Backing up firewall configuration..."
iptables-save > "${BACKUP_DIR}/iptables_rules.txt" 2>/dev/null || true
firewall-cmd --list-all > "${BACKUP_DIR}/firewalld_rules.txt" 2>/dev/null || true

# 6. Save SELinux configuration
echo "Backing up SELinux configuration..."
cp /etc/selinux/config "${BACKUP_DIR}/" 2>/dev/null || true
sestatus > "${BACKUP_DIR}/selinux_status.txt" 2>/dev/null || true

# 7. Save crontab entries
echo "Backing up cron jobs..."
crontab -l > "${BACKUP_DIR}/root_crontab.txt" 2>/dev/null || true
cp -r /etc/cron.d "${BACKUP_DIR}/" 2>/dev/null || true

# 8. Save system information
echo "Saving system information..."
cat > "${BACKUP_DIR}/system_info.txt" <<EOF
Hostname: $(hostname)
Role: $ROLE
OS Version: $(cat /etc/redhat-release)
Kernel: $(uname -r)
Uptime: $(uptime)
Memory: $(free -h)
Disk Usage:
$(df -h)
EOF

# 9. CDP specific backups
if systemctl list-unit-files | grep -q cloudera-scm; then
    echo "Backing up CDP configuration..."
    
    # Backup CM agent configuration
    if [ -d /etc/cloudera-scm-agent ]; then
        tar -czf "${BACKUP_DIR}/cloudera-scm-agent-config.tar.gz" /etc/cloudera-scm-agent/
    fi
    
    # Backup CM server configuration (if master)
    if [ "$ROLE" == "master" ] && [ -d /etc/cloudera-scm-server ]; then
        tar -czf "${BACKUP_DIR}/cloudera-scm-server-config.tar.gz" /etc/cloudera-scm-server/
    fi
    
    # Save parcel information
    if [ -d /opt/cloudera/parcels ]; then
        ls -la /opt/cloudera/parcels > "${BACKUP_DIR}/parcels_list.txt"
    fi
fi

# 10. Calculate backup size
echo "Calculating backup size..."
du -sh "$BACKUP_DIR" > "${BACKUP_DIR}/backup_size.txt"

# 11. Create backup manifest
cat > "${BACKUP_DIR}/backup_manifest.json" <<EOF
{
  "hostname": "$(hostname)",
  "role": "$ROLE",
  "timestamp": "$TIMESTAMP",
  "backup_directory": "$BACKUP_DIR",
  "os_version": "$(cat /etc/redhat-release)",
  "kernel_version": "$(uname -r)",
  "backup_size": "$(du -sh $BACKUP_DIR | awk '{print $1}')",
  "backup_completed": "$(date -Iseconds)"
}
EOF

echo "========================================="
echo "Backup completed successfully"
echo "Location: $BACKUP_DIR"
echo "Size: $(du -sh $BACKUP_DIR | awk '{print $1}')"
echo "========================================="

# Create symlink to latest backup
ln -sfn "$BACKUP_DIR" "${BACKUP_BASE}/${HOSTNAME}_latest"

exit 0


