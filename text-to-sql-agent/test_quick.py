#!/usr/bin/env python3
"""Quick test to verify the agent works before launching UI."""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_basic_functionality():
    """Test basic components."""
    print("=" * 60)
    print("QUICK FUNCTIONALITY TEST")
    print("=" * 60)
    print()
    
    # Test 1: Database query
    print("1. Testing database connection...")
    try:
        import sqlite3
        conn = sqlite3.connect('data/telco_sample.db')
        cursor = conn.cursor()
        
        # Simple test query
        cursor.execute("""
            SELECT plan_name, monthly_rate 
            FROM plans 
            ORDER BY monthly_rate DESC 
            LIMIT 3
        """)
        
        results = cursor.fetchall()
        print("   ✓ Database query successful")
        print("   Top 3 plans:")
        for plan, rate in results:
            print(f"     - {plan}: ${rate}/month")
        conn.close()
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return False
    
    print()
    
    # Test 2: OpenAI connection (if real key)
    print("2. Testing OpenAI connection...")
    api_key = os.environ.get('OPENAI_API_KEY', '')
    
    if api_key.startswith('sk-proj-') or api_key.startswith('sk-'):
        if 'test' not in api_key.lower():
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                
                # Simple test call
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say 'test successful' in exactly two words"}],
                    max_tokens=10
                )
                
                result = response.choices[0].message.content.strip()
                print(f"   ✓ OpenAI API working (response: {result})")
            except Exception as e:
                print(f"   ✗ OpenAI error: {e}")
                print("   Check your API key and internet connection")
                return False
        else:
            print("   ⚠ Test API key detected - skipping API call")
            print("   Replace with real key: export OPENAI_API_KEY='sk-...'")
    else:
        print("   ✗ Invalid API key format")
        print("   Set your key: export OPENAI_API_KEY='sk-...'")
        return False
    
    print()
    
    # Test 3: Gradio UI module
    print("3. Testing UI module...")
    try:
        sys.path.insert(0, 'src/ui')
        import gradio_simple
        
        if hasattr(gradio_simple, 'demo'):
            print("   ✓ Gradio UI module loaded")
        else:
            print("   ✗ Gradio demo object missing")
            return False
    except Exception as e:
        print(f"   ✗ UI module error: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✅ ALL TESTS PASSED - Ready to launch!")
    print("=" * 60)
    print()
    print("Run: python launch.py")
    print()
    
    return True


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
