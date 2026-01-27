#!/bin/bash
set -e

# Aggregate post-upgrade validation results
# Usage: aggregate_validation.sh <reports_directory>

REPORTS_DIR=$1
SUMMARY_FILE="${REPORTS_DIR}/validation_summary.json"

if [ ! -d "$REPORTS_DIR" ]; then
    echo "Reports directory not found: $REPORTS_DIR"
    exit 0  # Not fatal, might not have reports yet
fi

echo "Analyzing post-upgrade validation reports from: $REPORTS_DIR"

TOTAL_HOSTS=0
HOSTS_PASSED=0
HOSTS_FAILED=0
HOSTS_WITH_WARNINGS=0
GLOBAL_ISSUES=()

# Process each report
for report in "$REPORTS_DIR"/*.json; do
    if [ "$report" == "$SUMMARY_FILE" ]; then
        continue
    fi
    
    if [ ! -f "$report" ]; then
        continue
    fi
    
    ((TOTAL_HOSTS++))
    
    HOSTNAME=$(jq -r '.hostname' "$report" 2>/dev/null || echo "unknown")
    FAILED=$(jq -r '.summary.failed' "$report" 2>/dev/null || echo "0")
    WARNINGS=$(jq -r '.summary.warnings' "$report" 2>/dev/null || echo "0")
    
    echo "Processing: $HOSTNAME (Failed: $FAILED, Warnings: $WARNINGS)"
    
    if [ "$FAILED" -gt 0 ]; then
        ((HOSTS_FAILED++))
        ISSUES=$(jq -r '.summary.issues[]' "$report" 2>/dev/null || echo "")
        while IFS= read -r issue; do
            if [ ! -z "$issue" ]; then
                GLOBAL_ISSUES+=("$HOSTNAME: $issue")
            fi
        done <<< "$ISSUES"
    elif [ "$WARNINGS" -gt 0 ]; then
        ((HOSTS_WITH_WARNINGS++))
    else
        ((HOSTS_PASSED++))
    fi
done

echo ""
echo "========================================="
echo "Post-Upgrade Validation Summary"
echo "========================================="
echo "Total hosts validated: $TOTAL_HOSTS"
echo "Passed: $HOSTS_PASSED"
echo "Failed: $HOSTS_FAILED"
echo "With warnings: $HOSTS_WITH_WARNINGS"
echo "========================================="

if [ $HOSTS_FAILED -gt 0 ]; then
    echo "ERROR: $HOSTS_FAILED host(s) failed post-upgrade validation"
    echo ""
    echo "Issues:"
    printf '%s\n' "${GLOBAL_ISSUES[@]}"
    exit 1
fi

if [ $HOSTS_WITH_WARNINGS -gt 0 ]; then
    echo "WARNING: $HOSTS_WITH_WARNINGS host(s) have warnings"
    echo "Review reports before starting CDP services: $REPORTS_DIR"
fi

echo ""
echo "All post-upgrade validations PASSED"
exit 0


