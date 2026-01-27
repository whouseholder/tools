#!/bin/bash
set -e

# Wait for host to complete upgrade and come back online
# Usage: wait_for_host.sh <host_ip> <ssh_user> <ssh_key>

HOST_IP=$1
SSH_USER=$2
SSH_KEY=$3

MAX_WAIT=7200  # 2 hours
CHECK_INTERVAL=30
ELAPSED=0

echo "========================================="
echo "Waiting for host to complete upgrade"
echo "Host: $HOST_IP"
echo "Max wait time: ${MAX_WAIT}s ($(($MAX_WAIT / 60)) minutes)"
echo "========================================="

# Wait for host to go down (reboot initiated)
echo "Waiting for reboot to initiate..."
sleep 30

# Wait for SSH to become unavailable (system rebooting)
while ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
    "${SSH_USER}@${HOST_IP}" "echo test" &>/dev/null; do
    echo "Host still responding, waiting for reboot..."
    sleep 10
done

echo "Host is rebooting..."

# Wait for host to come back up
echo "Waiting for host to come back online..."
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        "${SSH_USER}@${HOST_IP}" "echo test" &>/dev/null; then
        echo ""
        echo "Host is back online after ${ELAPSED}s"
        
        # Wait a bit more for services to stabilize
        echo "Waiting for services to stabilize..."
        sleep 60
        
        # Verify system is responsive
        echo "Verifying system responsiveness..."
        if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "${SSH_USER}@${HOST_IP}" "systemctl is-system-running --wait" &>/dev/null; then
            echo "System is fully operational"
        else
            echo "WARNING: System may still be initializing"
        fi
        
        # Check OS version
        NEW_VERSION=$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "${SSH_USER}@${HOST_IP}" "cat /etc/redhat-release" 2>/dev/null || echo "Unknown")
        echo "New OS version: $NEW_VERSION"
        
        if echo "$NEW_VERSION" | grep -q "release 8"; then
            echo ""
            echo "========================================="
            echo "Upgrade completed successfully!"
            echo "Host: $HOST_IP"
            echo "Version: $NEW_VERSION"
            echo "Total time: ${ELAPSED}s ($(($ELAPSED / 60)) minutes)"
            echo "========================================="
            exit 0
        else
            echo "WARNING: OS version doesn't show RHEL 8"
            echo "Current version: $NEW_VERSION"
            # Continue anyway, post-upgrade checks will catch issues
            exit 0
        fi
    fi
    
    # Print progress
    if [ $(($ELAPSED % 300)) -eq 0 ]; then
        echo "Still waiting... (${ELAPSED}s elapsed, $(($MAX_WAIT - $ELAPSED))s remaining)"
    fi
    
    sleep $CHECK_INTERVAL
    ELAPSED=$((ELAPSED + CHECK_INTERVAL))
done

echo ""
echo "ERROR: Host did not come back online within ${MAX_WAIT}s"
echo "Host: $HOST_IP"
echo "Manual intervention required"
exit 1


