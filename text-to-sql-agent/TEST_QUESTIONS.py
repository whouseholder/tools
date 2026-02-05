"""
10 Test Questions for Text-to-SQL Agent
Each with a follow-up visualization request
"""

TEST_QUESTIONS = [
    {
        "id": 1,
        "category": "Customer Analytics",
        "question": "What are the top 10 customers by lifetime value?",
        "follow_up": "show that as a bar chart",
        "description": "Tests: ORDER BY DESC, LIMIT, basic SELECT",
        "expected_sql_keywords": ["SELECT", "FROM customers", "ORDER BY", "DESC", "LIMIT 10"]
    },
    {
        "id": 2,
        "category": "Revenue Analysis",
        "question": "Show total revenue by service plan",
        "follow_up": "make it a pie chart",
        "description": "Tests: JOINs, SUM aggregation, GROUP BY",
        "expected_sql_keywords": ["SELECT", "SUM", "FROM", "JOIN", "GROUP BY"]
    },
    {
        "id": 3,
        "category": "Device Analytics",
        "question": "Which device manufacturers are most popular? Show top 5",
        "follow_up": "visualize as a horizontal bar chart",
        "description": "Tests: COUNT, GROUP BY, ORDER BY, LIMIT",
        "expected_sql_keywords": ["SELECT", "COUNT", "FROM devices", "GROUP BY", "LIMIT 5"]
    },
    {
        "id": 4,
        "category": "Churn Analysis",
        "question": "List customers with high churn risk (above 0.7) and their plan types",
        "follow_up": "show distribution by plan type as a pie chart",
        "description": "Tests: WHERE conditions, JOINs, filtering",
        "expected_sql_keywords": ["SELECT", "FROM customers", "JOIN", "WHERE", "churn_risk_score", "> 0.7"]
    },
    {
        "id": 5,
        "category": "Usage Analytics",
        "question": "What is average data usage by plan type?",
        "follow_up": "show as bar chart",
        "description": "Tests: AVG aggregation, multiple JOINs, GROUP BY",
        "expected_sql_keywords": ["SELECT", "AVG", "FROM", "JOIN", "GROUP BY"]
    },
    {
        "id": 6,
        "category": "Financial Analysis",
        "question": "Show total transaction amounts by type",
        "follow_up": "make it a pie chart",
        "description": "Tests: SUM with GROUP BY, transaction types",
        "expected_sql_keywords": ["SELECT", "SUM", "FROM transactions", "GROUP BY", "transaction_type"]
    },
    {
        "id": 7,
        "category": "Geographic Analysis",
        "question": "Which cities have the most active customers? Show top 10",
        "follow_up": "visualize as bar chart",
        "description": "Tests: COUNT, WHERE, GROUP BY, ORDER BY, LIMIT",
        "expected_sql_keywords": ["SELECT", "COUNT", "FROM customers", "WHERE", "active", "GROUP BY city", "LIMIT 10"]
    },
    {
        "id": 8,
        "category": "Plan Performance",
        "question": "What is average lifetime value by plan type?",
        "follow_up": "show as bar chart ordered by value",
        "description": "Tests: AVG, JOIN, GROUP BY, ORDER BY",
        "expected_sql_keywords": ["SELECT", "AVG", "FROM", "JOIN", "GROUP BY", "ORDER BY"]
    },
    {
        "id": 9,
        "category": "Network Analysis",
        "question": "How many customers made international calls last month?",
        "follow_up": "show breakdown by plan type as pie chart",
        "description": "Tests: COUNT DISTINCT, WHERE with date filter",
        "expected_sql_keywords": ["SELECT", "COUNT", "FROM network_activity", "WHERE", "international"]
    },
    {
        "id": 10,
        "category": "Trend Analysis",
        "question": "Show monthly revenue trend for last 6 months",
        "follow_up": "plot as line graph",
        "description": "Tests: Date functions, GROUP BY date, ORDER BY time",
        "expected_sql_keywords": ["SELECT", "FROM transactions", "GROUP BY", "ORDER BY", "date"]
    }
]


# Visual representation for quick reference
QUICK_REFERENCE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    10 Test Questions - Quick Reference                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  1. Top 10 customers by lifetime value → bar chart                          ║
║  2. Total revenue by service plan → pie chart                               ║
║  3. Most popular device manufacturers (top 5) → horizontal bar              ║
║  4. High churn risk customers → distribution pie chart                      ║
║  5. Average data usage by plan type → bar chart                             ║
║  6. Transaction amounts by type → pie chart                                 ║
║  7. Top 10 cities by active customers → bar chart                           ║
║  8. Average lifetime value by plan → ordered bar chart                      ║
║  9. International callers count → plan type breakdown pie                   ║
║ 10. Monthly revenue trend (6 months) → line graph                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


def print_test_summary():
    """Print a formatted summary of all test questions."""
    print(QUICK_REFERENCE)
    print("\nDetailed Test Cases:\n")
    
    for test in TEST_QUESTIONS:
        print(f"{'='*80}")
        print(f"Test {test['id']}: {test['category']}")
        print(f"{'='*80}")
        print(f"Question:   {test['question']}")
        print(f"Follow-up:  {test['follow_up']}")
        print(f"Tests:      {test['description']}")
        print(f"Keywords:   {', '.join(test['expected_sql_keywords'])}")
        print()


if __name__ == "__main__":
    print_test_summary()
