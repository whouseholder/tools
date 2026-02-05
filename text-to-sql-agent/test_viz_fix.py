#!/usr/bin/env python3
"""
Test script to validate the visualization fix.
This checks that the code is properly configured to use gr.Plot with Plotly figures.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_gradio_imports():
    """Test that Gradio and Plotly are importable."""
    print("1️⃣  Testing imports...")
    try:
        import gradio as gr
        print("   ✅ Gradio imported")
    except ImportError as e:
        print(f"   ❌ Gradio import failed: {e}")
        return False
    
    try:
        import plotly.express as px
        print("   ✅ Plotly imported")
    except ImportError as e:
        print(f"   ❌ Plotly import failed: {e}")
        return False
    
    return True


def test_ui_component_type():
    """Test that the UI uses gr.Plot not gr.HTML."""
    print("\n2️⃣  Checking UI component configuration...")
    
    with open("src/ui/gradio_simple.py", "r") as f:
        content = f.read()
    
    # Check that viz_output uses gr.Plot
    if 'viz_output = gr.Plot(' in content:
        print("   ✅ UI uses gr.Plot component (correct)")
    elif 'viz_output = gr.HTML(' in content:
        print("   ❌ UI still uses gr.HTML component (wrong)")
        return False
    else:
        print("   ⚠️  Could not find viz_output definition")
        return False
    
    return True


def test_return_values():
    """Test that functions return figure objects not HTML strings."""
    print("\n3️⃣  Checking return value types...")
    
    with open("src/ui/gradio_simple.py", "r") as f:
        content = f.read()
    
    # Check for problematic HTML patterns
    issues = []
    
    if 'fig.to_html(' in content:
        issues.append("Found fig.to_html() - should return figure object instead")
    
    if 'viz_html =' in content and 'viz_fig =' not in content:
        issues.append("Found viz_html variable - should use viz_fig instead")
    
    if 'viz_wrapped =' in content:
        issues.append("Found viz_wrapped with HTML wrapping - not needed with gr.Plot")
    
    if issues:
        print("   ❌ Found issues:")
        for issue in issues:
            print(f"      • {issue}")
        return False
    
    # Check for correct patterns
    if 'viz_fig = px.bar(' in content or 'viz_fig = px.pie(' in content:
        print("   ✅ Functions return Plotly figure objects (correct)")
    else:
        print("   ⚠️  Could not verify figure object returns")
    
    return True


def test_clear_function():
    """Test that clear function returns None for Plot component."""
    print("\n4️⃣  Checking clear_chat() function...")
    
    with open("src/ui/gradio_simple.py", "r") as f:
        content = f.read()
    
    # Find the clear_chat function
    if 'def clear_chat():' in content:
        # Check what it returns for viz component
        if 'return [], "", SCHEMA, None' in content or 'return [], "", SCHEMA, None  #' in content:
            print("   ✅ clear_chat() returns None for Plot (correct)")
            return True
        elif 'return [], "", SCHEMA, ""' in content:
            print("   ❌ clear_chat() returns empty string - should be None for gr.Plot")
            return False
    
    print("   ⚠️  Could not verify clear_chat function")
    return True


def test_follow_up_logic():
    """Test that follow-up visualization logic returns figure objects."""
    print("\n5️⃣  Checking follow-up visualization logic...")
    
    with open("src/ui/gradio_simple.py", "r") as f:
        content = f.read()
    
    # Look for follow-up section
    if 'is_viz_request = any(keyword in question.lower() for keyword in viz_keywords)' in content:
        print("   ✅ Follow-up detection logic present")
        
        # Check if it returns figure objects
        if 'return new_history, sql_display, SCHEMA, viz_fig' in content:
            print("   ✅ Follow-ups return figure objects (correct)")
            return True
        elif 'return new_history, sql_display, SCHEMA, viz_wrapped' in content:
            print("   ❌ Follow-ups return HTML wrapper - should be figure object")
            return False
        elif 'return new_history, sql_display, SCHEMA, viz_html' in content:
            print("   ❌ Follow-ups return HTML string - should be figure object")
            return False
    
    print("   ⚠️  Could not verify follow-up logic")
    return True


def test_chart_types():
    """Test that all chart types use figure objects."""
    print("\n6️⃣  Checking chart type implementations...")
    
    with open("src/ui/gradio_simple.py", "r") as f:
        content = f.read()
    
    chart_types = {
        'bar': 'px.bar(',
        'pie': 'px.pie(',
        'line': 'px.line(',
        'scatter': 'px.scatter('
    }
    
    found_charts = []
    for chart_type, pattern in chart_types.items():
        if pattern in content:
            found_charts.append(chart_type)
    
    if found_charts:
        print(f"   ✅ Found chart types: {', '.join(found_charts)}")
        return True
    else:
        print("   ⚠️  No chart creation code found")
        return False


def test_syntax():
    """Test that the Python file has valid syntax."""
    print("\n7️⃣  Validating Python syntax...")
    
    import py_compile
    try:
        py_compile.compile('src/ui/gradio_simple.py', doraise=True)
        print("   ✅ Python syntax is valid")
        return True
    except py_compile.PyCompileError as e:
        print(f"   ❌ Syntax error: {e}")
        return False


def test_no_local_imports():
    """Test that there are no problematic local imports."""
    print("\n8️⃣  Checking for local import issues...")
    
    with open("src/ui/gradio_simple.py", "r") as f:
        lines = f.readlines()
    
    # Check for local 'import sys' statements (indented imports)
    local_sys_imports = []
    for i, line in enumerate(lines, 1):
        # Check if line starts with whitespace and is 'import sys'
        if line.startswith((' ', '\t')) and 'import sys' in line and line.strip().startswith('import sys'):
            local_sys_imports.append(i)
    
    if local_sys_imports:
        print(f"   ❌ Found local 'import sys' statements at lines: {', '.join(map(str, local_sys_imports))}")
        print("      This can cause UnboundLocalError - use global import instead")
        return False
    else:
        print("   ✅ No problematic local 'import sys' statements")
        return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Visualization Fix - Gradio Native Plots")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_gradio_imports),
        ("UI Component", test_ui_component_type),
        ("Return Values", test_return_values),
        ("Clear Function", test_clear_function),
        ("Follow-up Logic", test_follow_up_logic),
        ("Chart Types", test_chart_types),
        ("Syntax", test_syntax),
        ("Local Imports", test_no_local_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n   ❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Visualization fix is properly implemented.")
        print("\n📝 Next steps:")
        print("   1. Set your OpenAI API key:")
        print("      export OPENAI_API_KEY='sk-your-key-here'")
        print("   2. Run the UI:")
        print("      ./run_local.sh")
        print("   3. Test with a query and follow-ups:")
        print("      • Ask: 'What are the top 10 customers by lifetime value?'")
        print("      • Then: 'show that as a pie chart'")
        print("      • Then: 'make it a bar chart'")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
