"""
Test script for CML Model deployment.

Tests the deployed Text-to-SQL agent model via API calls.
"""

import os
import sys
import json
import requests
from loguru import logger


def call_model(
    host: str,
    access_key: str,
    data: dict,
    function_name: str = "predict"
) -> dict:
    """
    Call a deployed CML model.
    
    Args:
        host: CML workspace host
        access_key: Model access key
        data: Request data
        function_name: Function to call (predict, feedback, health_check, etc.)
    
    Returns:
        Response dictionary
    """
    url = f"https://{host}/model"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_key}"
    }
    
    payload = {
        "accessKey": access_key,
        "request": data
    }
    
    logger.info(f"Calling {function_name} endpoint...")
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()


def test_health_check(host: str, access_key: str):
    """Test health check endpoint."""
    logger.info("Testing health check...")
    
    result = call_model(
        host=host,
        access_key=access_key,
        data={},
        function_name="health_check"
    )
    
    print("\n=== Health Check ===")
    print(json.dumps(result, indent=2))
    
    return result


def test_prediction(host: str, access_key: str, question: str):
    """Test prediction endpoint."""
    logger.info(f"Testing prediction with question: {question}")
    
    result = call_model(
        host=host,
        access_key=access_key,
        data={
            "question": question,
            "session_id": "test-session"
        }
    )
    
    print("\n=== Prediction Result ===")
    print(f"Question: {question}")
    print(f"Success: {result.get('success')}")
    print(f"Response Type: {result.get('response_type')}")
    
    if result.get('success'):
        print(f"SQL Query: {result.get('metadata', {}).get('sql_query')}")
        print(f"Row Count: {result.get('data', {}).get('row_count', 0)}")
    else:
        print(f"Error: {result.get('error')}")
    
    return result


def test_batch_prediction(host: str, access_key: str, questions: list):
    """Test batch prediction endpoint."""
    logger.info(f"Testing batch prediction with {len(questions)} questions")
    
    data = [{"question": q} for q in questions]
    
    result = call_model(
        host=host,
        access_key=access_key,
        data=data,
        function_name="batch_predict"
    )
    
    print("\n=== Batch Prediction Results ===")
    for i, (question, res) in enumerate(zip(questions, result)):
        print(f"\n{i+1}. {question}")
        print(f"   Success: {res.get('success')}")
        if res.get('success'):
            print(f"   Rows: {res.get('data', {}).get('row_count', 0)}")
    
    return result


def test_feedback(host: str, access_key: str):
    """Test feedback endpoint."""
    logger.info("Testing feedback submission...")
    
    result = call_model(
        host=host,
        access_key=access_key,
        data={
            "question": "Test question",
            "sql_query": "SELECT * FROM test",
            "answer": {"test": "data"},
            "feedback_type": "positive",
            "comment": "Test feedback"
        },
        function_name="feedback"
    )
    
    print("\n=== Feedback Result ===")
    print(json.dumps(result, indent=2))
    
    return result


def test_stats(host: str, access_key: str):
    """Test stats endpoint."""
    logger.info("Testing stats retrieval...")
    
    result = call_model(
        host=host,
        access_key=access_key,
        data={},
        function_name="get_stats"
    )
    
    print("\n=== Stats ===")
    print(json.dumps(result, indent=2))
    
    return result


def main():
    """Run all tests."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test deployed CML Model"
    )
    parser.add_argument(
        "--host",
        required=True,
        help="CML workspace host (e.g., ml-xxxxx.cml.company.com)"
    )
    parser.add_argument(
        "--access-key",
        required=True,
        help="Model access key"
    )
    parser.add_argument(
        "--question",
        default="What are the top 10 customers by revenue?",
        help="Question to test"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Text-to-SQL Agent - CML Model Test")
    print("=" * 60)
    
    try:
        # Test health check
        test_health_check(args.host, args.access_key)
        
        # Test single prediction
        test_prediction(args.host, args.access_key, args.question)
        
        # Test batch prediction
        batch_questions = [
            "Show total revenue",
            "List active customers",
            "Count transactions by month"
        ]
        test_batch_prediction(args.host, args.access_key, batch_questions)
        
        # Test feedback
        test_feedback(args.host, args.access_key)
        
        # Test stats
        test_stats(args.host, args.access_key)
        
        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
