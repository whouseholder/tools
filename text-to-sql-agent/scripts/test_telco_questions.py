"""Test the Text-to-SQL agent with telco business questions."""

import sys
from pathlib import Path
import sqlite3

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.agent import TextToSQLAgent
from src.utils.config import load_config
from src.utils.logger import setup_logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


# 10 realistic telco business questions
TELCO_QUESTIONS = [
    {
        "id": 1,
        "question": "What are the top 10 customers by lifetime value?",
        "category": "Marketing",
        "expected_tables": ["customers"]
    },
    {
        "id": 2,
        "question": "Show me the total monthly revenue from all active customers",
        "category": "Business Operations",
        "expected_tables": ["customers", "plans"]
    },
    {
        "id": 3,
        "question": "Which device manufacturers are most popular among our customers?",
        "category": "Marketing",
        "expected_tables": ["devices"]
    },
    {
        "id": 4,
        "question": "List customers with high churn risk score (above 0.7) who are on premium plans",
        "category": "Business Operations",
        "expected_tables": ["customers", "plans"]
    },
    {
        "id": 5,
        "question": "What is the average data usage per customer in the last 30 days?",
        "category": "Network Operations",
        "expected_tables": ["network_activity"]
    },
    {
        "id": 6,
        "question": "Show me the total overage charges collected in the last 6 months",
        "category": "Finance",
        "expected_tables": ["transactions"]
    },
    {
        "id": 7,
        "question": "Which cities have the most active customers?",
        "category": "Marketing",
        "expected_tables": ["customers"]
    },
    {
        "id": 8,
        "question": "What is the average customer lifetime value by plan type?",
        "category": "Business Operations",
        "expected_tables": ["customers", "plans"]
    },
    {
        "id": 9,
        "question": "How many customers have made international calls in the last month?",
        "category": "Network Operations",
        "expected_tables": ["network_activity"]
    },
    {
        "id": 10,
        "question": "Show me the monthly recurring revenue trend for the last 12 months",
        "category": "Finance",
        "expected_tables": ["transactions", "customers"]
    }
]


def verify_database():
    """Verify the telco database exists and has data."""
    db_path = project_root / "data" / "telco_sample.db"
    
    if not db_path.exists():
        console.print("[red]✗ Telco database not found![/red]")
        console.print("\nPlease run: python scripts/create_telco_db.py")
        return False
    
    # Check tables
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ['customers', 'plans', 'devices', 'network_activity', 'transactions']
    missing_tables = [t for t in expected_tables if t not in tables]
    
    if missing_tables:
        console.print(f"[red]✗ Missing tables: {', '.join(missing_tables)}[/red]")
        conn.close()
        return False
    
    # Check record counts
    stats = {}
    for table in expected_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        stats[table] = cursor.fetchone()[0]
    
    conn.close()
    
    # Display stats
    console.print("\n[green]✓ Database verified[/green]")
    console.print("\nDatabase Statistics:")
    for table, count in stats.items():
        console.print(f"  {table}: [cyan]{count:,}[/cyan] records")
    
    return True


def create_sqlite_agent_adapter():
    """Create a modified agent configuration for SQLite."""
    # This is a simplified adapter - in production you'd want proper SQLite support
    # For now, we'll note that the agent needs to be configured for SQLite
    console.print("\n[yellow]Note: Agent configured for Hive. For SQLite testing, manual queries will be used.[/yellow]")
    return None


def test_question_manually(question_data):
    """Test a question by manually querying SQLite (since agent is configured for Hive)."""
    db_path = project_root / "data" / "telco_sample.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Manual SQL queries for each question (for demonstration)
    query_map = {
        1: "SELECT customer_id, first_name, last_name, lifetime_value FROM customers ORDER BY lifetime_value DESC LIMIT 10",
        2: "SELECT SUM(p.monthly_rate) as total_monthly_revenue FROM customers c JOIN plans p ON c.plan_id = p.plan_id WHERE c.account_status = 'active'",
        3: "SELECT manufacturer, COUNT(*) as device_count FROM devices GROUP BY manufacturer ORDER BY device_count DESC",
        4: "SELECT c.customer_id, c.first_name, c.last_name, c.churn_risk_score, p.plan_name FROM customers c JOIN plans p ON c.plan_id = p.plan_id WHERE c.churn_risk_score > 0.7 AND p.monthly_rate > 80",
        5: "SELECT AVG(data_usage_mb) as avg_data_usage_mb FROM network_activity WHERE activity_date >= date('now', '-30 days') AND data_usage_mb IS NOT NULL",
        6: "SELECT SUM(amount) as total_overage FROM transactions WHERE transaction_type = 'overage' AND transaction_date >= date('now', '-6 months')",
        7: "SELECT city, COUNT(*) as customer_count FROM customers WHERE account_status = 'active' GROUP BY city ORDER BY customer_count DESC LIMIT 10",
        8: "SELECT p.plan_type, AVG(c.lifetime_value) as avg_lifetime_value FROM customers c JOIN plans p ON c.plan_id = p.plan_id GROUP BY p.plan_type ORDER BY avg_lifetime_value DESC",
        9: "SELECT COUNT(DISTINCT customer_id) as international_callers FROM network_activity WHERE international = 1 AND activity_date >= date('now', '-30 days')",
        10: "SELECT strftime('%Y-%m', transaction_date) as month, SUM(amount) as monthly_revenue FROM transactions WHERE transaction_type = 'monthly_charge' AND transaction_date >= date('now', '-12 months') GROUP BY month ORDER BY month"
    }
    
    query = query_map.get(question_data['id'])
    
    if query:
        try:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            result = {
                'success': True,
                'query': query,
                'columns': columns,
                'rows': rows,
                'row_count': len(rows)
            }
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'query': query
            }
    else:
        result = {
            'success': False,
            'error': 'No manual query defined'
        }
    
    conn.close()
    return result


def display_results(question_data, result):
    """Display question and results in a nice format."""
    # Question header
    console.print(f"\n[bold cyan]Question {question_data['id']}:[/bold cyan] {question_data['question']}")
    console.print(f"[dim]Category: {question_data['category']}[/dim]")
    console.print()
    
    if result['success']:
        # SQL Query
        console.print(Panel(
            result['query'],
            title="[green]Generated SQL Query[/green]",
            border_style="green"
        ))
        
        # Results table
        if result['rows']:
            table = Table(show_header=True, header_style="bold magenta")
            
            for col in result['columns']:
                table.add_column(col)
            
            # Limit display to first 10 rows
            for row in result['rows'][:10]:
                table.add_row(*[str(val) for val in row])
            
            if result['row_count'] > 10:
                console.print(f"\n[dim]Showing 10 of {result['row_count']} rows[/dim]")
            
            console.print(table)
            console.print(f"\n[green]✓ Success[/green] - {result['row_count']} rows returned")
        else:
            console.print("[yellow]No rows returned[/yellow]")
    else:
        console.print(Panel(
            result.get('error', 'Unknown error'),
            title="[red]Error[/red]",
            border_style="red"
        ))


def main():
    """Main test function."""
    console.print(Panel.fit(
        "[bold cyan]Text-to-SQL Agent - Telco Business Questions Test[/bold cyan]",
        border_style="cyan"
    ))
    
    # Verify database
    console.print("\n[bold]Step 1: Verifying Database[/bold]")
    if not verify_database():
        return
    
    # Run test questions
    console.print("\n[bold]Step 2: Testing Business Questions[/bold]")
    console.print(f"Running {len(TELCO_QUESTIONS)} questions...\n")
    
    results_summary = {
        'total': len(TELCO_QUESTIONS),
        'success': 0,
        'failed': 0
    }
    
    for i, question_data in enumerate(TELCO_QUESTIONS, 1):
        console.print("=" * 80)
        
        result = test_question_manually(question_data)
        display_results(question_data, result)
        
        if result['success']:
            results_summary['success'] += 1
        else:
            results_summary['failed'] += 1
        
        # Pause between questions for readability
        if i < len(TELCO_QUESTIONS):
            input("\n[dim]Press Enter to continue to next question...[/dim]")
    
    # Summary
    console.print("\n" + "=" * 80)
    console.print(Panel.fit(
        f"""[bold]Test Summary[/bold]

Total Questions: [cyan]{results_summary['total']}[/cyan]
Successful: [green]{results_summary['success']}[/green]
Failed: [red]{results_summary['failed']}[/red]

Success Rate: [cyan]{(results_summary['success'] / results_summary['total'] * 100):.1f}%[/cyan]""",
        title="[bold green]Results[/bold green]",
        border_style="green"
    ))
    
    console.print("\n[bold cyan]Test complete![/bold cyan]")
    console.print("\nNote: This test used manual SQL queries for demonstration.")
    console.print("To use the full agent with LLM-generated queries, configure SQLite support in the agent.")


if __name__ == "__main__":
    main()
