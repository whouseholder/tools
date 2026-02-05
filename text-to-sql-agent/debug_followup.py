#!/usr/bin/env python3
"""Debug follow-up visualization issue."""

import sys
import os
os.environ['OPENAI_API_KEY'] = 'sk-test-debug'

# Add to path
sys.path.insert(0, 'src/ui')

print("=" * 60)
print("DEBUGGING FOLLOW-UP VISUALIZATION")
print("=" * 60)
print()

try:
    import gradio_simple
    
    # Setup cached data
    print("1. Setting up cached data...")
    gradio_simple.last_query = {
        'sql': 'SELECT customer_id, first_name, lifetime_value FROM customers ORDER BY lifetime_value DESC LIMIT 10',
        'data': [
            (1, 'John', 10000),
            (2, 'Jane', 9500),
            (3, 'Bob', 9000),
            (4, 'Alice', 8500),
            (5, 'Charlie', 8000),
        ],
        'columns': ['customer_id', 'first_name', 'lifetime_value']
    }
    print(f"   ✓ Cached {len(gradio_simple.last_query['data'])} rows")
    print(f"   ✓ Columns: {gradio_simple.last_query['columns']}")
    print()
    
    # Simulate initial query
    print("2. Simulating initial query...")
    history = []
    result1 = gradio_simple.process_question("What are the top customers?", history)
    print(f"   ✓ Returned {len(result1)} values")
    print(f"   ✓ History has {len(result1[0])} messages")
    print(f"   ✓ Viz HTML length: {len(result1[3])} chars")
    history = result1[0]
    print()
    
    # Simulate follow-up
    print("3. Simulating follow-up visualization request...")
    print("   Question: 'show that as a pie chart'")
    print()
    
    result2 = gradio_simple.process_question("show that as a pie chart", history)
    
    print("4. Analyzing results...")
    print(f"   Return tuple length: {len(result2)}")
    print(f"   [0] History: {len(result2[0])} messages")
    print(f"   [1] SQL display: {result2[1][:50]}...")
    print(f"   [2] Data viewer: First 50 chars: {result2[2][:50]}...")
    print(f"   [3] Visualization HTML: {len(result2[3])} chars")
    print()
    
    # Check visualization content
    viz_html = result2[3]
    if viz_html:
        print("5. Visualization HTML Analysis:")
        print(f"   ✓ Not empty")
        print(f"   ✓ Length: {len(viz_html):,} characters")
        
        if 'plotly' in viz_html.lower():
            print(f"   ✓ Contains 'plotly'")
        if '<div' in viz_html:
            print(f"   ✓ Contains HTML div")
        if 'pie' in viz_html.lower():
            print(f"   ✓ Contains 'pie' (pie chart)")
        
        # Show first part
        print()
        print("   First 200 chars of HTML:")
        print(f"   {viz_html[:200]}")
    else:
        print("5. ❌ Visualization HTML is EMPTY!")
    
    print()
    
    # Check chat message
    print("6. Chat Response:")
    last_msg = result2[0][-1]['content']
    print(f"   {last_msg[:150]}...")
    print()
    
    print("=" * 60)
    if viz_html and len(viz_html) > 1000:
        print("✅ VISUALIZATION IS BEING GENERATED")
        print("=" * 60)
        print()
        print("The issue must be in how Gradio updates the HTML component.")
        print("Possible causes:")
        print("  1. Gradio HTML component not refreshing")
        print("  2. Output order mismatch")
        print("  3. Component reference issue")
        print()
        print("Check console/terminal when running live UI for errors.")
    else:
        print("❌ VISUALIZATION NOT GENERATED")
        print("=" * 60)
    
except Exception as e:
    print()
    print("=" * 60)
    print("❌ ERROR")
    print("=" * 60)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
