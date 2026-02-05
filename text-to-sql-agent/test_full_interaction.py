#!/usr/bin/env python3
"""
Simulate full Gradio interaction to debug visualization issue.
"""

import sys
import os
os.environ['OPENAI_API_KEY'] = 'sk-test'
sys.path.insert(0, 'src/ui')

print("=" * 70)
print("SIMULATING FULL GRADIO INTERACTION")
print("=" * 70)
print()

try:
    import gradio_simple
    
    print("SCENARIO: User asks question, then requests different visualization")
    print("=" * 70)
    print()
    
    # Step 1: Initial query
    print("STEP 1: Initial Query")
    print("-" * 70)
    print("User types: 'What are the top 10 customers by lifetime value?'")
    print()
    
    history = []
    q1 = "What are the top 10 customers by lifetime value?"
    
    # Mock SQL generation to avoid API call
    original_gen = gradio_simple.generate_sql
    def mock_gen(q, s):
        return "SELECT customer_id, first_name, lifetime_value FROM customers ORDER BY lifetime_value DESC LIMIT 10", 0.92, None
    gradio_simple.generate_sql = mock_gen
    
    result1 = gradio_simple.process_question(q1, history)
    
    print(f"Returns: ({len(result1)} items)")
    print(f"  [0] history: {len(result1[0])} messages")
    print(f"  [1] sql_display: '{result1[1][:60]}...'")
    print(f"  [2] schema: {len(result1[2])} chars (Database Schema)")
    print(f"  [3] viz_html: {len(result1[3])} chars")
    
    if result1[3]:
        print(f"  ✅ Initial viz generated")
    else:
        print(f"  ⚠️  No initial viz (expected if no data)")
    
    print()
    print("UI Updates:")
    print(f"  chatbot ← history ({len(result1[0])} msgs)")
    print(f"  sql_output ← sql_display")
    print(f"  data_viewer ← schema (keeps showing database structure)")
    print(f"  viz_output ← viz_html ({len(result1[3])} chars)")
    print()
    
    # Step 2: Follow-up
    print("STEP 2: Follow-Up Visualization Request")
    print("-" * 70)
    print("User types: 'show that as a pie chart'")
    print()
    
    history = result1[0]  # Use updated history
    q2 = "show that as a pie chart"
    
    result2 = gradio_simple.process_question(q2, history)
    
    print(f"Returns: ({len(result2)} items)")
    print(f"  [0] history: {len(result2[0])} messages (was {len(result1[0])}, now {len(result2[0])})")
    print(f"  [1] sql_display: '{result2[1][:60]}...'")
    print(f"  [2] schema: {len(result2[2])} chars (Database Schema)")
    print(f"  [3] viz_html: {len(result2[3])} chars")
    
    if result2[3]:
        print(f"  ✅ Follow-up viz generated!")
        print()
        print(f"Visualization content preview:")
        print(f"  {result2[3][:150]}...")
    else:
        print(f"  ❌ Follow-up viz is EMPTY - this is the bug!")
    
    print()
    print("UI Updates:")
    print(f"  chatbot ← history ({len(result2[0])} msgs) ✓")
    print(f"  sql_output ← 'Using cached results...' ✓")
    print(f"  data_viewer ← schema (unchanged) ✓")
    if result2[3]:
        print(f"  viz_output ← NEW PIE CHART HTML ({len(result2[3])} chars) ✅")
    else:
        print(f"  viz_output ← EMPTY ❌")
    
    print()
    print("=" * 70)
    
    if result2[3] and len(result2[3]) > 100:
        print("✅ FOLLOW-UP VISUALIZATION WORKING")
        print("=" * 70)
        print()
        print("The visualization HTML is being generated and returned.")
        print("If it's not showing in the UI, check:")
        print("  1. Browser console for JavaScript errors")
        print("  2. Gradio HTML component refresh issues")
        print("  3. Network tab for blocked resources")
        print()
        print(f"Generated HTML size: {len(result2[3]):,} bytes")
        print("Using CDN for Plotly.js to keep size manageable")
    else:
        print("❌ FOLLOW-UP VISUALIZATION NOT WORKING")
        print("=" * 70)
        print("Need to debug why viz_html is empty")
    
    print()
    
    # Restore original
    gradio_simple.generate_sql = original_gen
    
except Exception as e:
    print()
    print("=" * 70)
    print("❌ ERROR")
    print("=" * 70)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
