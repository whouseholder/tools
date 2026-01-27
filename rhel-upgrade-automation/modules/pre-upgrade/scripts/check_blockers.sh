#!/bin/bash
set -e

# Aggregate pre-upgrade check results and fail if any blockers found
# Usage: check_blockers.sh <reports_directory>

REPORTS_DIR=$1
SUMMARY_FILE="${REPORTS_DIR}/summary.json"

if [ ! -d "$REPORTS_DIR" ]; then
    echo "Reports directory not found: $REPORTS_DIR"
    exit 1
fi

echo "Analyzing pre-upgrade reports from: $REPORTS_DIR"

# Initialize summary
cat > $SUMMARY_FILE <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "total_hosts": 0,
  "hosts_passed": 0,
  "hosts_failed": 0,
  "hosts_with_warnings": 0,
  "blockers": [],
  "host_details": {}
}
EOF

TOTAL_HOSTS=0
HOSTS_PASSED=0
HOSTS_FAILED=0
HOSTS_WITH_WARNINGS=0
GLOBAL_BLOCKERS=()

# Process each report
for report in "$REPORTS_DIR"/*.json; do
    if [ "$report" == "$SUMMARY_FILE" ]; then
        continue
    fi
    
    if [ ! -f "$report" ]; then
        continue
    fi
    
    ((TOTAL_HOSTS++))
    
    HOSTNAME=$(jq -r '.hostname' "$report")
    FAILED=$(jq -r '.summary.failed' "$report")
    WARNINGS=$(jq -r '.summary.warnings' "$report")
    
    echo "Processing: $HOSTNAME (Failed: $FAILED, Warnings: $WARNINGS)"
    
    if [ "$FAILED" -gt 0 ]; then
        ((HOSTS_FAILED++))
        BLOCKERS=$(jq -r '.summary.blockers[]' "$report")
        while IFS= read -r blocker; do
            GLOBAL_BLOCKERS+=("$HOSTNAME: $blocker")
        done <<< "$BLOCKERS"
    elif [ "$WARNINGS" -gt 0 ]; then
        ((HOSTS_WITH_WARNINGS++))
    else
        ((HOSTS_PASSED++))
    fi
done

# Update summary
jq --arg total "$TOTAL_HOSTS" \
   --arg passed "$HOSTS_PASSED" \
   --arg failed "$HOSTS_FAILED" \
   --arg warnings "$HOSTS_WITH_WARNINGS" \
   '.total_hosts = ($total | tonumber) |
    .hosts_passed = ($passed | tonumber) |
    .hosts_failed = ($failed | tonumber) |
    .hosts_with_warnings = ($warnings | tonumber)' \
    "$SUMMARY_FILE" > "${SUMMARY_FILE}.tmp" && mv "${SUMMARY_FILE}.tmp" "$SUMMARY_FILE"

# Add global blockers
if [ ${#GLOBAL_BLOCKERS[@]} -gt 0 ]; then
    printf '%s\n' "${GLOBAL_BLOCKERS[@]}" | jq -R . | jq -s . | \
        jq --argjson summary "$(cat $SUMMARY_FILE)" \
        '$summary | .blockers = .' > "${SUMMARY_FILE}.tmp" && mv "${SUMMARY_FILE}.tmp" "$SUMMARY_FILE"
fi

echo ""
echo "========================================="
echo "Pre-Upgrade Check Summary"
echo "========================================="
echo "Total hosts: $TOTAL_HOSTS"
echo "Passed: $HOSTS_PASSED"
echo "Failed: $HOSTS_FAILED"
echo "With warnings: $HOSTS_WITH_WARNINGS"
echo "========================================="

if [ $HOSTS_FAILED -gt 0 ]; then
    echo "ERROR: $HOSTS_FAILED host(s) failed pre-upgrade checks"
    echo ""
    echo "Blockers:"
    printf '%s\n' "${GLOBAL_BLOCKERS[@]}"
    echo ""
    echo "Review individual reports in: $REPORTS_DIR"
    exit 1
fi

if [ $HOSTS_WITH_WARNINGS -gt 0 ]; then
    echo "WARNING: $HOSTS_WITH_WARNINGS host(s) have warnings"
    echo "Review reports before proceeding: $REPORTS_DIR"
fi

echo ""
echo "All pre-upgrade checks PASSED"
echo "Summary saved to: $SUMMARY_FILE"
exit 0


