#!/bin/bash

# Fetch cluster host information from Cloudera Manager
# Usage: fetch-cm-hosts.sh <cm_host> <cm_user> <cm_password> <cluster_name>

set -e

CM_HOST=$1
CM_USER=$2
CM_PASSWORD=$3
CLUSTER_NAME=$4
CM_API="http://${CM_HOST}:7180/api/v40"

if [ -z "$CM_HOST" ] || [ -z "$CM_USER" ] || [ -z "$CM_PASSWORD" ]; then
    echo "Error: Missing required parameters" >&2
    echo "Usage: $0 <cm_host> <cm_user> <cm_password> [cluster_name]" >&2
    exit 1
fi

# Function to call CM API
call_cm_api() {
    local endpoint=$1
    curl -s -u "${CM_USER}:${CM_PASSWORD}" "${CM_API}${endpoint}" 2>/dev/null
}

# Test CM connectivity
if ! call_cm_api "/cm/version" | jq -e . >/dev/null 2>&1; then
    echo "Error: Cannot connect to Cloudera Manager at $CM_HOST" >&2
    exit 1
fi

# Get cluster name if not provided
if [ -z "$CLUSTER_NAME" ]; then
    CLUSTER_NAME=$(call_cm_api "/clusters" | jq -r '.items[0].name')
    if [ -z "$CLUSTER_NAME" ] || [ "$CLUSTER_NAME" == "null" ]; then
        echo "Error: No cluster found" >&2
        exit 1
    fi
fi

# Get all hosts
HOSTS=$(call_cm_api "/hosts")
if [ -z "$HOSTS" ] || [ "$HOSTS" == "null" ]; then
    echo "Error: Failed to fetch hosts from CM" >&2
    exit 1
fi

# Get cluster services to determine roles
SERVICES=$(call_cm_api "/clusters/${CLUSTER_NAME}/services")

# Get roles for each host
ROLES=$(call_cm_api "/clusters/${CLUSTER_NAME}/services" | \
    jq -r '.items[].name' | \
    while read service; do
        call_cm_api "/clusters/${CLUSTER_NAME}/services/${service}/roles"
    done | jq -s 'add')

# Determine CM server host
CM_SERVER_HOST=$(call_cm_api "/cm/deployment" | \
    jq -r '.clusters[0].services[] | select(.name == "MGMT") | .roles[0].hostRef.hostname' 2>/dev/null || \
    echo "$CM_HOST")

# Build JSON output with role determination
echo "$HOSTS" | jq --arg cluster "$CLUSTER_NAME" --argjson roles "$ROLES" --arg cm_server "$CM_SERVER_HOST" '
{
  cluster_name: $cluster,
  cm_server_host: $cm_server,
  hosts: [
    .items[] | 
    {
      hostname: .hostname,
      ip_address: .ipAddress,
      host_id: .hostId,
      rack_id: (.rackId // "default"),
      # Determine role based on services running
      role: (
        if (.hostname == $cm_server) then "master"
        elif (
          # Check if this host has master services
          [$roles.items[] | select(.hostRef.hostId == .hostId) | .type] |
          any(
            . == "NAMENODE" or 
            . == "RESOURCEMANAGER" or 
            . == "HBASE_MASTER" or
            . == "HIVESERVER2" or
            . == "HIVEMETASTORE"
          )
        ) then "master"
        elif (
          # Check if this host has data services
          [$roles.items[] | select(.hostRef.hostId == .hostId) | .type] |
          any(
            . == "DATANODE" or 
            . == "NODEMANAGER"
          )
        ) then "worker"
        else "edge"
        end
      ),
      # Get services running on this host
      services: [
        $roles.items[] | 
        select(.hostRef.hostId == .hostId) | 
        .type
      ],
      description: (
        [
          $roles.items[] | 
          select(.hostRef.hostId == .hostId) | 
          .type
        ] | 
        join(", ")
      )
    }
  ] | sort_by(.role) | reverse
}
'


