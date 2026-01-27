#!/bin/bash

# Quick commands for Telco Test Suite

echo "=========================================="
echo "Telco Test Suite - Quick Commands"
echo "=========================================="
echo ""

# Check if database exists
if [ -f "data/telco_sample.db" ]; then
    echo "✓ Database exists: data/telco_sample.db"
    size=$(du -h data/telco_sample.db | cut -f1)
    echo "  Size: $size"
    echo ""
else
    echo "✗ Database not found!"
    echo ""
    echo "Create it with:"
    echo "  python3 scripts/create_telco_db.py"
    echo ""
    exit 1
fi

# Show menu
echo "Available commands:"
echo ""
echo "1. Show database statistics"
echo "2. View sample customers"
echo "3. View sample plans"
echo "4. View sample devices"
echo "5. View network activity summary"
echo "6. View revenue summary"
echo "7. Run all test questions"
echo "8. Open database in SQLite CLI"
echo "9. Exit"
echo ""
read -p "Enter choice (1-9): " choice

case $choice in
    1)
        echo ""
        echo "Database Statistics:"
        sqlite3 data/telco_sample.db << 'EOF'
.mode column
SELECT 'customers' as table_name, COUNT(*) as record_count FROM customers
UNION ALL
SELECT 'plans', COUNT(*) FROM plans
UNION ALL
SELECT 'devices', COUNT(*) FROM devices
UNION ALL
SELECT 'network_activity', COUNT(*) FROM network_activity
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions;
EOF
        ;;
    
    2)
        echo ""
        echo "Sample Customers (Top 10 by Lifetime Value):"
        sqlite3 data/telco_sample.db << 'EOF'
.mode column
.headers on
SELECT customer_id, first_name, last_name, city, account_status, 
       printf('$%.2f', lifetime_value) as lifetime_value
FROM customers 
ORDER BY lifetime_value DESC 
LIMIT 10;
EOF
        ;;
    
    3)
        echo ""
        echo "Available Plans:"
        sqlite3 data/telco_sample.db << 'EOF'
.mode column
.headers on
SELECT plan_id, plan_name, plan_type, 
       printf('$%.2f', monthly_rate) as monthly_rate
FROM plans 
ORDER BY monthly_rate DESC;
EOF
        ;;
    
    4)
        echo ""
        echo "Sample Devices:"
        sqlite3 data/telco_sample.db << 'EOF'
.mode column
.headers on
SELECT device_id, manufacturer, model, device_status, 
       printf('$%.2f', purchase_price) as purchase_price
FROM devices 
LIMIT 10;
EOF
        ;;
    
    5)
        echo ""
        echo "Network Activity Summary (Last 30 Days):"
        sqlite3 data/telco_sample.db << 'EOF'
.mode column
.headers on
SELECT 
    activity_type,
    COUNT(*) as count,
    printf('%.2f', AVG(CASE WHEN duration_minutes IS NOT NULL THEN duration_minutes END)) as avg_duration_min,
    printf('%.2f', AVG(CASE WHEN data_usage_mb IS NOT NULL THEN data_usage_mb END)) as avg_data_mb
FROM network_activity
WHERE activity_date >= date('now', '-30 days')
GROUP BY activity_type
ORDER BY count DESC;
EOF
        ;;
    
    6)
        echo ""
        echo "Revenue Summary:"
        sqlite3 data/telco_sample.db << 'EOF'
.mode column
.headers on
SELECT 
    'Total Active Customers' as metric,
    COUNT(*) as value
FROM customers 
WHERE account_status = 'active'
UNION ALL
SELECT 
    'Monthly Recurring Revenue',
    printf('$%.2f', SUM(p.monthly_rate))
FROM customers c
JOIN plans p ON c.plan_id = p.plan_id
WHERE c.account_status = 'active'
UNION ALL
SELECT
    'Avg Customer Lifetime Value',
    printf('$%.2f', AVG(lifetime_value))
FROM customers
WHERE account_status = 'active';
EOF
        ;;
    
    7)
        echo ""
        echo "Running all test questions..."
        python3 scripts/test_telco_questions.py
        ;;
    
    8)
        echo ""
        echo "Opening SQLite CLI..."
        echo "Type .quit to exit"
        echo ""
        sqlite3 data/telco_sample.db
        ;;
    
    9)
        echo "Goodbye!"
        exit 0
        ;;
    
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac

echo ""
echo "Done!"
