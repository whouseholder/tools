"""Full agent test with LLM-powered query generation for SQLite telco database."""

import sys
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional

# Set up path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Setup logging
logger.remove()
logger.add(sys.stderr, level="INFO")

console = Console()


class SimpleLLMManager:
    """Simplified LLM manager for query generation."""
    
    def __init__(self, api_key: str):
        """Initialize with OpenAI API key."""
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        logger.info("LLM Manager initialized")
    
    def generate_sql(
        self,
        question: str,
        table_metadata: List[Dict[str, Any]],
        dialect: str = "sqlite"
    ) -> str:
        """Generate SQL query from natural language question."""
        
        # Build prompt
        prompt = self._build_prompt(question, table_metadata, dialect)
        
        logger.info(f"Generating SQL for: {question[:50]}...")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are an expert {dialect.upper()} SQL query generator. Generate ONLY the SQL query, no explanations or markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500
            )
            
            sql = response.choices[0].message.content.strip()
            
            # Clean up the response
            sql = self._clean_sql(sql)
            
            logger.info("SQL generated successfully")
            return sql
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    def _build_prompt(
        self,
        question: str,
        table_metadata: List[Dict[str, Any]],
        dialect: str
    ) -> str:
        """Build prompt for SQL generation."""
        parts = [
            f"Generate a {dialect.upper()} SQL query to answer this question:",
            f"\nQuestion: {question}",
            "\nAvailable tables and columns:",
        ]
        
        for table in table_metadata:
            parts.append(f"\nTable: {table['name']}")
            if table.get('description'):
                parts.append(f"Description: {table['description']}")
            parts.append("Columns:")
            for col in table['columns']:
                parts.append(f"  - {col}")
        
        parts.append("\nGenerate ONLY the SQL query, no explanations:")
        
        return "\n".join(parts)
    
    def _clean_sql(self, sql: str) -> str:
        """Clean SQL from LLM response."""
        # Remove markdown code blocks
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        # Remove common prefixes
        prefixes = ["SQL:", "Query:", "sql:", "query:"]
        for prefix in prefixes:
            if sql.startswith(prefix):
                sql = sql[len(prefix):].strip()
        
        # Remove semicolons
        sql = sql.rstrip(';').strip()
        
        return sql


class TelcoAgent:
    """Simplified agent for telco database queries."""
    
    def __init__(self, db_path: str, llm_manager: SimpleLLMManager):
        """Initialize agent."""
        self.db_path = db_path
        self.llm_manager = llm_manager
        self.table_metadata = self._load_metadata()
        logger.info("Telco Agent initialized")
    
    def _load_metadata(self) -> List[Dict[str, Any]]:
        """Load table metadata from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        metadata = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [f"{row[1]} ({row[2]})" for row in cursor.fetchall()]
            
            metadata.append({
                'name': table,
                'columns': columns,
                'description': self._get_table_description(table)
            })
        
        conn.close()
        return metadata
    
    def _get_table_description(self, table: str) -> str:
        """Get table description."""
        descriptions = {
            'customers': 'Customer account information including demographics, status, and value metrics',
            'plans': 'Service plans with pricing and limits',
            'devices': 'Customer devices with manufacturer and model info',
            'network_activity': 'Network usage including calls, SMS, data, roaming',
            'transactions': 'Financial transactions including charges, payments, and overages'
        }
        return descriptions.get(table, '')
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """Process question through full agent pipeline."""
        result = {
            'question': question,
            'success': False,
            'sql': None,
            'data': None,
            'error': None
        }
        
        try:
            # Step 1: Generate SQL
            logger.info(f"Step 1: Generating SQL query")
            sql = self.llm_manager.generate_sql(
                question=question,
                table_metadata=self.table_metadata,
                dialect="sqlite"
            )
            result['sql'] = sql
            
            # Step 2: Execute query
            logger.info(f"Step 2: Executing query")
            data = self._execute_query(sql)
            result['data'] = data
            result['success'] = True
            
            logger.info(f"✓ Query successful: {data['row_count']} rows")
            
        except Exception as e:
            logger.error(f"✗ Query failed: {e}")
            result['error'] = str(e)
        
        return result
    
    def _execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        
        conn.close()
        
        return {
            'columns': columns,
            'rows': rows,
            'row_count': len(rows)
        }


# Test questions
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "What are the top 10 customers by lifetime value?",
        "category": "Marketing"
    },
    {
        "id": 2,
        "question": "Show me the total monthly revenue from all active customers",
        "category": "Business Operations"
    },
    {
        "id": 3,
        "question": "Which device manufacturers are most popular among our customers?",
        "category": "Marketing"
    },
    {
        "id": 4,
        "question": "List customers with high churn risk score above 0.7 who are on premium plans costing more than $80 per month",
        "category": "Business Operations"
    },
    {
        "id": 5,
        "question": "What is the average data usage in megabytes per customer in the last 30 days?",
        "category": "Network Operations"
    }
]


def display_result(question: Dict, result: Dict):
    """Display question and result."""
    console.print(f"\n[bold cyan]Question {question['id']}:[/bold cyan] {question['question']}")
    console.print(f"[dim]Category: {question['category']}[/dim]\n")
    
    if result['success']:
        # Show SQL
        console.print(Panel(
            result['sql'],
            title="[green]LLM-Generated SQL Query[/green]",
            border_style="green"
        ))
        
        # Show results
        data = result['data']
        if data['rows']:
            table = Table(show_header=True, header_style="bold magenta")
            
            for col in data['columns']:
                table.add_column(col)
            
            # Show first 10 rows
            for row in data['rows'][:10]:
                table.add_row(*[str(val) for val in row])
            
            if data['row_count'] > 10:
                console.print(f"\n[dim]Showing 10 of {data['row_count']} rows[/dim]")
            
            console.print(table)
            console.print(f"\n[green]✓ Success[/green] - {data['row_count']} rows returned")
        else:
            console.print("[yellow]No rows returned[/yellow]")
    else:
        console.print(Panel(
            result['error'],
            title="[red]Error[/red]",
            border_style="red"
        ))


def main():
    """Main test function."""
    console.print(Panel.fit(
        "[bold cyan]Text-to-SQL Agent - Full LLM Test[/bold cyan]\n"
        "[dim]Using GPT-3.5-turbo for query generation[/dim]",
        border_style="cyan"
    ))
    
    # Check for API key - try both env var and command line
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        console.print("[red]✗ OPENAI_API_KEY not provided![/red]")
        console.print("\nProvide it either way:")
        console.print("  1. export OPENAI_API_KEY='your-key'")
        console.print("  2. python script.py 'your-key'")
        return
    
    console.print(f"\n[green]✓ API key found (length: {len(api_key)})[/green]")
    
    # Check database
    db_path = 'data/telco_sample.db'
    if not Path(db_path).exists():
        console.print(f"[red]✗ Database not found: {db_path}[/red]")
        console.print("\nPlease run: python3 scripts/create_telco_db.py")
        return
    
    console.print(f"[green]✓ Database found: {db_path}[/green]\n")
    
    # Initialize agent
    console.print("[bold]Initializing Agent...[/bold]")
    llm_manager = SimpleLLMManager(api_key)
    agent = TelcoAgent(db_path, llm_manager)
    
    console.print(f"[green]✓ Agent initialized with {len(agent.table_metadata)} tables[/green]")
    
    # Run tests
    console.print(f"\n[bold]Running {len(TEST_QUESTIONS)} Questions with LLM Generation[/bold]\n")
    
    results_summary = {
        'total': len(TEST_QUESTIONS),
        'success': 0,
        'failed': 0
    }
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        console.print("=" * 80)
        
        with console.status(f"[bold green]Processing question {i}...") as status:
            result = agent.process_question(question['question'])
        
        display_result(question, result)
        
        if result['success']:
            results_summary['success'] += 1
        else:
            results_summary['failed'] += 1
        
        if i < len(TEST_QUESTIONS):
            input("\n[dim]Press Enter to continue...[/dim]")
    
    # Summary
    console.print("\n" + "=" * 80)
    console.print(Panel.fit(
        f"""[bold]Test Summary[/bold]

Total Questions: [cyan]{results_summary['total']}[/cyan]
Successful: [green]{results_summary['success']}[/green]
Failed: [red]{results_summary['failed']}[/red]

Success Rate: [cyan]{(results_summary['success'] / results_summary['total'] * 100):.1f}%[/cyan]

[dim]All queries were generated by GPT-3.5-turbo[/dim]""",
        title="[bold green]Results[/bold green]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
