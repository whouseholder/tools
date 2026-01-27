"""Standalone test script for telco questions - no dependencies needed."""

import sqlite3
from datetime import datetime

# Test questions
QUESTIONS = [
    {
        "id": 1,
        "question": "What are the top 10 customers by lifetime value?",
        "category": "Marketing",
        "sql": """
            SELECT customer_id, first_name, last_name, 
                   printf('$%.2f', lifetime_value) as lifetime_value
            FROM customers 
            ORDER BY lifetime_value DESC 
            LIMIT 10
        """
    },
    {
        "id": 2,
        "question": "Show me the total monthly revenue from all active customers",
        "category": "Business Operations",
        "sql": """
            SELECT printf('$%.2f', SUM(p.monthly_rate)) as total_monthly_revenue 
            FROM customers c 
            JOIN plans p ON c.plan_id = p.plan_id 
            WHERE c.account_status = 'active'
        """
    },
    {
        "id": 3,
        "question": "Which device manufacturers are most popular among our customers?",
        "category": "Marketing",
        "sql": """
            SELECT manufacturer, COUNT(*) as device_count 
            FROM devices 
            GROUP BY manufacturer 
            ORDER BY device_count DESC
        """
    },
    {
        "id": 4,
        "question": "List customers with high churn risk score (above 0.7) who are on premium plans",
        "category": "Business Operations",
        "sql": """
            SELECT c.customer_id, c.first_name, c.last_name, 
                   c.churn_risk_score, p.plan_name, 
                   printf('$%.2f', p.monthly_rate) as monthly_rate
            FROM customers c 
            JOIN plans p ON c.plan_id = p.plan_id 
            WHERE c.churn_risk_score > 0.7 AND p.monthly_rate > 80
            ORDER BY c.churn_risk_score DESC
            LIMIT 10
        """
    },
    {
        "id": 5,
        "question": "What is the average data usage per customer in the last 30 days?",
        "category": "Network Operations",
        "sql": """
            SELECT printf('%.2f MB', AVG(data_usage_mb)) as avg_data_usage
            FROM network_activity 
            WHERE activity_date >= date('now', '-30 days') 
            AND data_usage_mb IS NOT NULL
        """
    },
    {
        "id": 6,
        "question": "Show me the total overage charges collected in the last 6 months",
        "category": "Finance",
        "sql": """
            SELECT printf('$%.2f', SUM(amount)) as total_overage,
                   COUNT(*) as overage_count
            FROM transactions 
            WHERE transaction_type = 'overage' 
            AND transaction_date >= date('now', '-6 months')
        """
    },
    {
        "id": 7,
        "question": "Which cities have the most active customers?",
        "category": "Marketing",
        "sql": """
            SELECT city, COUNT(*) as customer_count 
            FROM customers 
            WHERE account_status = 'active' 
            GROUP BY city 
            ORDER BY customer_count DESC 
            LIMIT 10
        """
    },
    {
        "id": 8,
        "question": "What is the average customer lifetime value by plan type?",
        "category": "Business Operations",
        "sql": """
            SELECT p.plan_type, 
                   COUNT(c.customer_id) as customers,
                   printf('$%.2f', AVG(c.lifetime_value)) as avg_lifetime_value 
            FROM customers c 
            JOIN plans p ON c.plan_id = p.plan_id 
            GROUP BY p.plan_type 
            ORDER BY AVG(c.lifetime_value) DESC
        """
    },
    {
        "id": 9,
        "question": "How many customers have made international calls in the last month?",
        "category": "Network Operations",
        "sql": """
            SELECT COUNT(DISTINCT customer_id) as international_callers 
            FROM network_activity 
            WHERE international = 1 
            AND activity_date >= date('now', '-30 days')
        """
    },
    {
        "id": 10,
        "question": "Show me the monthly recurring revenue trend for the last 12 months",
        "category": "Finance",
        "sql": """
            SELECT strftime('%Y-%m', transaction_date) as month, 
                   printf('$%.2f', SUM(amount)) as monthly_revenue,
                   COUNT(*) as transaction_count
            FROM transactions 
            WHERE transaction_type = 'monthly_charge' 
            AND transaction_date >= date('now', '-12 months') 
            GROUP BY month 
            ORDER BY month DESC
            LIMIT 12
        """
    }
]


def print_header():
    """Print test header."""
    print("=" * 80)
    print("Text-to-SQL Agent - Telco Business Questions Test")
    print("=" * 80)
    print()


def print_question_header(q):
    """Print question header."""
    print("=" * 80)
    print(f"Question {q['id']}: {q['question']}")
    print(f"Category: {q['category']}")
    print("=" * 80)
    print()


def print_sql(sql):
    """Print SQL query."""
    print("Generated SQL Query:")
    print("-" * 80)
    print(sql.strip())
    print("-" * 80)
    print()


def print_results(columns, rows):
    """Print query results as a formatted table."""
    if not rows:
        print("No results returned")
        return
    
    # Calculate column widths
    widths = [len(str(col)) for col in columns]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))
    
    # Print header
    header = " | ".join(str(col).ljust(widths[i]) for i, col in enumerate(columns))
    print(header)
    print("-" * len(header))
    
    # Print rows (limit to 15 for readability)
    for row in rows[:15]:
        print(" | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row)))
    
    if len(rows) > 15:
        print(f"\n... and {len(rows) - 15} more rows")


def run_test(db_path, question):
    """Run a single test question."""
    print_question_header(question)
    print_sql(question['sql'])
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(question['sql'])
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        print(f"Results ({len(rows)} rows):")
        print()
        print_results(columns, rows)
        
        conn.close()
        
        print()
        print(f"✓ Success - {len(rows)} rows returned")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def print_summary(results):
    """Print test summary."""
    print()
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total Questions: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print()


def main():
    """Main test function."""
    db_path = 'data/telco_sample.db'
    
    print_header()
    
    # Check database exists
    import os
    if not os.path.exists(db_path):
        print(f"✗ Database not found: {db_path}")
        print()
        print("Please run: python3 scripts/create_telco_db.py")
        return
    
    print(f"✓ Database found: {db_path}")
    
    # Show database stats
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print()
        print("Database Statistics:")
        tables = ['customers', 'plans', 'devices', 'network_activity', 'transactions']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} records")
        
        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}")
        return
    
    print()
    print("=" * 80)
    print("Running 10 Business Questions")
    print("=" * 80)
    print()
    input("Press Enter to start...")
    print()
    
    # Run all tests
    results = []
    for i, question in enumerate(QUESTIONS, 1):
        result = run_test(db_path, question)
        results.append(result)
        
        if i < len(QUESTIONS):
            print()
            input("Press Enter for next question...")
            print()
    
    # Print summary
    print_summary(results)
    
    print("Test complete!")


if __name__ == "__main__":
    main()
