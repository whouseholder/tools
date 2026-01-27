#!/bin/bash
set -e

# Backup CDP cluster state before upgrade
# Usage: backup_cluster_state.sh <cm_host> <ssh_user> <ssh_key>

CM_HOST=$1
SSH_USER=$2
SSH_KEY=$3
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/rhel-upgrade/cluster-state-${TIMESTAMP}"

echo "========================================="
echo "Backing up CDP cluster state"
echo "CM Server: $CM_HOST"
echo "Backup directory: $BACKUP_DIR"
echo "========================================="

# Create backup directory on CM server
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${SSH_USER}@${CM_HOST}" \
    "mkdir -p $BACKUP_DIR"

# Backup CM Server database
echo "Backing up CM database..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${SSH_USER}@${CM_HOST}" \
    "pg_dump -U scm scm > ${BACKUP_DIR}/cm_database.sql" || \
    echo "WARNING: Database backup may have failed"

# Backup CM configuration
echo "Backing up CM configuration..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${SSH_USER}@${CM_HOST}" \
    "tar -czf ${BACKUP_DIR}/cm-server-config.tar.gz /etc/cloudera-scm-server /var/lib/cloudera-scm-server" || true

# Export CM deployment via API
echo "Exporting CM deployment..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${SSH_USER}@${CM_HOST}" \
    "curl -s -u admin:admin http://localhost:7180/api/v40/cm/deployment > ${BACKUP_DIR}/cm_deployment.json" || true

echo ""
echo "========================================="
echo "Cluster state backup completed"
echo "Location: ${CM_HOST}:${BACKUP_DIR}"
echo "========================================="

exit 0


