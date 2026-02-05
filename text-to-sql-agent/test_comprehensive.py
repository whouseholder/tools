#!/usr/bin/env python3
"""
Comprehensive Test Suite for Text-to-SQL Agent
Tests 10 diverse questions with follow-up visualizations
"""

import os
import sys
import time
from pathlib import Path

# Test Questions with Follow-ups
TEST_CASES = [
    {
        "id": 1,
        "category": "Customer Analytics",
        "question": "What are the top 10 customers by lifetime value?",
        "follow_up": "show that as a bar chart",
        "expected_columns": ["customer_id", "first_name", "last_name", "lifetime_value"],
        "expected_rows": 10
    },
    {
        "id": 2,
        "category": "Revenue Analysis",
        "question": "Show total revenue by service plan",
        "follow_up": "make it a pie chart",
        "expected_columns": ["plan_name", "total_revenue"],
        "expected_visualization": "pie"
    },
    {
        "id": 3,
        "category": "Device Analytics",
        "question": "Which device manufacturers are most popular? Show top 5",
        "follow_up": "visualize as a horizontal bar chart",
        "expected_columns": ["manufacturer", "device_count"],
        "expected_rows": 5
    },
    {
        "id": 4,
        "category": "Churn Analysis",
        "question": "List customers with high churn risk (above 0.7) and their plan types",
        "follow_up": "show distribution by plan type as a pie chart",
        "expected_columns": ["customer_id", "churn_risk_score", "plan_name"]
    },
    {
        "id": 5,
        "category": "Usage Analytics",
        "question": "What is average data usage by plan type?",
        "follow_up": "show as bar chart",
        "expected_columns": ["plan_type", "avg_data_usage"],
        "expected_visualization": "bar"
    },
    {
        "id": 6,
        "category": "Financial Analysis",
        "question": "Show total transaction amounts by type",
        "follow_up": "make it a pie chart",
        "expected_columns": ["transaction_type", "total_amount"],
        "expected_visualization": "pie"
    },
    {
        "id": 7,
        "category": "Geographic Analysis",
        "question": "Which cities have the most active customers? Show top 10",
        "follow_up": "visualize as bar chart",
        "expected_columns": ["city", "customer_count"],
        "expected_rows": 10
    },
    {
        "id": 8,
        "category": "Plan Performance",
        "question": "What is average lifetime value by plan type?",
        "follow_up": "show as bar chart ordered by value",
        "expected_columns": ["plan_type", "avg_lifetime_value"],
        "expected_visualization": "bar"
    },
    {
        "id": 9,
        "category": "Network Analysis",
        "question": "How many customers made international calls last month?",
        "follow_up": "show breakdown by plan type as pie chart",
        "expected_columns": ["international_callers"]
    },
    {
        "id": 10,
        "category": "Trend Analysis",
        "question": "Show monthly revenue trend for last 6 months",
        "follow_up": "plot as line graph",
        "expected_columns": ["month", "revenue"],
        "expected_visualization": "line"
    }
]


def print_header(text, char="="):
    """Print a formatted header."""
    print(f"\n{char * 80}")
    print(f"{text:^80}")
    print(f"{char * 80}\n")


def print_test_case(test_case):
    """Print test case details."""
    print(f"📋 Test {test_case['id']}: {test_case['category']}")
    print(f"   Question: \"{test_case['question']}\"")
    print(f"   Follow-up: \"{test_case['follow_up']}\"")
    print()


def test_with_gradio_ui():
    """
    Interactive test instructions for Gradio UI.
    """
    print_header("Text-to-SQL Agent - Comprehensive Test Suite")
    
    print("This test suite includes 10 diverse questions covering:")
    print("  • Customer analytics")
    print("  • Revenue analysis")
    print("  • Device & usage patterns")
    print("  • Churn risk assessment")
    print("  • Geographic distribution")
    print("  • Trend analysis")
    print()
    print("Each test includes a follow-up visualization request.")
    print()
    
    # Check for API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set!")
        print()
        print("Please run:")
        print('  export OPENAI_API_KEY="sk-your-key-here"')
        print()
        return False
    
    print("✅ OpenAI API key found")
    print()
    
    # Check for database
    db_path = Path(__file__).parent / "data" / "telco_sample.db"
    if not db_path.exists():
        print(f"❌ ERROR: Database not found at {db_path}")
        print()
        print("Please run:")
        print("  python scripts/create_telco_db.py")
        print()
        return False
    
    print(f"✅ Database found: {db_path}")
    print()
    
    print_header("Test Cases", "-")
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"{i:2d}. {test_case['category']}")
        print(f"    Q: {test_case['question']}")
        print(f"    F: {test_case['follow_up']}")
        print()
    
    print_header("Starting Interactive Test", "-")
    
    print("To run these tests:")
    print()
    print("1. Launch the Gradio UI:")
    print("   python launch.py")
    print()
    print("2. Open your browser to http://localhost:7860")
    print()
    print("3. Test each question in order:")
    print()
    
    for test_case in TEST_CASES:
        print(f"   Test {test_case['id']}:")
        print(f"   ├─ Ask: \"{test_case['question']}\"")
        print(f"   │  └─ ✓ Verify SQL is valid and complete")
        print(f"   │  └─ ✓ Check results table is properly formatted")
        print(f"   │  └─ ✓ Verify correct data is returned")
        print(f"   └─ Then: \"{test_case['follow_up']}\"")
        print(f"      └─ ✓ Verify visualization appears in right panel")
        print(f"      └─ ✓ Check chart type matches request")
        print()
    
    print_header("Expected Behavior", "-")
    
    print("✅ SQL Validation:")
    print("   • All queries should be complete (no missing FROM clause)")
    print("   • Queries should pass syntax validation")
    print("   • If invalid, agent retries up to 3 times")
    print()
    
    print("✅ Table Formatting:")
    print("   • Tables should be compact (no blank rows)")
    print("   • Clean styling with gradient header")
    print("   • Hover effects on rows")
    print("   • Responsive layout")
    print()
    
    print("✅ Visualizations:")
    print("   • Follow-up requests should reuse previous data")
    print("   • Charts should match the requested type")
    print("   • Visualizations appear in right panel")
    print("   • No need to regenerate SQL query")
    print()
    
    print_header("Validation Checklist", "-")
    
    print("For EACH test case, verify:")
    print()
    print("  □ Question is understood correctly")
    print("  □ SQL query is generated successfully")
    print("  □ SQL is syntactically valid and complete")
    print("  □ Query executes without errors")
    print("  □ Results table displays cleanly (no blank rows)")
    print("  □ Data looks correct for the question")
    print("  □ Follow-up visualization request is recognized")
    print("  □ Chart is created without regenerating SQL")
    print("  □ Correct visualization type is used")
    print("  □ Chart displays in visualization panel")
    print()
    
    return True


def create_automated_test_script():
    """
    Create a Python script that can programmatically test the UI.
    """
    script_content = '''"""
Automated Test Runner for Gradio UI
Sends test questions programmatically
"""

import requests
import json
import time

# Gradio API endpoint (adjust if using different port)
API_URL = "http://localhost:7860/api/predict"

TEST_CASES = [
    ("What are the top 10 customers by lifetime value?", "show that as a bar chart"),
    ("Show total revenue by service plan", "make it a pie chart"),
    ("Which device manufacturers are most popular? Show top 5", "visualize as a horizontal bar chart"),
    # Add remaining test cases...
]

def send_message(message, history=[]):
    """Send a message to the Gradio UI."""
    payload = {
        "data": [message, history]
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def run_tests():
    """Run all test cases."""
    print("Starting automated tests...")
    history = []
    
    for i, (question, followup) in enumerate(TEST_CASES, 1):
        print(f"\\nTest {i}:")
        print(f"  Q: {question}")
        
        # Send question
        result = send_message(question, history)
        if result:
            history = result.get("data", [{}])[0]
            print("  ✓ Question processed")
            
            time.sleep(2)
            
            # Send follow-up
            print(f"  F: {followup}")
            result = send_message(followup, history)
            if result:
                history = result.get("data", [{}])[0]
                print("  ✓ Follow-up processed")
        
        time.sleep(1)
    
    print("\\nAll tests complete!")

if __name__ == "__main__":
    run_tests()
'''
    
    # Save automated test script
    script_path = Path(__file__).parent / "test_automated.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"📝 Created automated test script: {script_path}")
    print()


def main():
    """Main test function."""
    if test_with_gradio_ui():
        print_header("Ready to Test!")
        print("Launch the UI and follow the test cases above.")
        print()
        print("💡 Tip: Keep this terminal open to reference the test cases.")
        print()
        
        # Ask if user wants automated script
        try:
            response = input("Create automated test script? (y/n): ").strip().lower()
            if response == 'y':
                create_automated_test_script()
        except KeyboardInterrupt:
            print("\n\nTest preparation complete!")


if __name__ == "__main__":
    main()
