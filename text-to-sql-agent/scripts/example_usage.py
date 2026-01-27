"""Example script showing how to use the agent programmatically."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import load_config
from src.utils.logger import setup_logging
from src.agent.agent import TextToSQLAgent
from src.agent.feedback import FeedbackType


def main():
    """Example usage of the Text-to-SQL agent."""
    # Load configuration
    config = load_config()
    setup_logging("INFO")
    
    # Create agent
    print("Initializing Text-to-SQL Agent...")
    agent = TextToSQLAgent(config)
    
    # Initialize metadata index (one-time setup)
    print("\nInitializing metadata index...")
    # agent.initialize_metadata_index(force_refresh=True)
    
    # Create a session
    session_id = agent.create_session()
    print(f"Session created: {session_id}")
    
    # Example questions
    questions = [
        "Show me the top 10 customers by revenue",
        "What is the total sales amount for last month?",
        "List all products with inventory below 100 units"
    ]
    
    for i, question in enumerate(questions, 1):
        print("\n" + "=" * 60)
        print(f"Question {i}: {question}")
        print("=" * 60)
        
        # Process question
        result = agent.process_question(
            question=question,
            session_id=session_id,
            visualization_type="table"
        )
        
        # Display results
        if result['success']:
            print(f"\n✅ Success!")
            print(f"SQL Query: {result['metadata']['sql_query']}")
            print(f"Rows returned: {result['data']['row_count']}")
            print(f"Execution time: {result['data']['execution_time']:.2f}s")
            print(f"Model used: {result['metadata']['query_generation']['model_used']}")
            
            # Show preview of results
            if result['data']['rows']:
                print("\nFirst few rows:")
                columns = result['data']['columns']
                print(" | ".join(columns))
                print("-" * 60)
                for row in result['data']['rows'][:5]:
                    print(" | ".join([str(v) for v in row]))
            
            # Add positive feedback (optional)
            if input("\nWas this result helpful? (y/n): ").lower() == 'y':
                agent.add_user_feedback(
                    question=question,
                    sql_query=result['metadata']['sql_query'],
                    answer=result['data'],
                    feedback_type=FeedbackType.POSITIVE,
                    comment="Good result",
                    session_id=session_id
                )
                print("Thank you for your feedback!")
        
        else:
            print(f"\n❌ Error: {result['data']['error']}")
    
    # Show feedback stats
    print("\n" + "=" * 60)
    print("Feedback Statistics")
    print("=" * 60)
    stats = agent.feedback_manager.get_feedback_stats()
    print(f"Total feedback: {stats['total']}")
    print(f"By type: {stats['by_type']}")
    print(f"Average confidence: {stats['average_confidence']:.2f}")
    
    # Cleanup
    agent.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
