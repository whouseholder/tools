#!/usr/bin/env python3
"""
Validation test for Gradio UI functions after fixes
"""

import sys
import os

# Mock the API key for validation
os.environ['OPENAI_API_KEY'] = 'sk-test-validation'

sys.path.insert(0, 'src/ui')
import gradio_simple

# Check all required functions exist
functions = [
    'generate_sql',
    'generate_sql_with_retry', 
    'generate_sql_with_correction',
    'validate_sql_syntax',
    'execute_query',
    'get_schema',
    'process_question',
    'clear_chat',
    'export_data'
]

print('='*60)
print('✅ Function Validation')
print('='*60)
for func in functions:
    if hasattr(gradio_simple, func):
        print(f'  ✓ {func}')
    else:
        print(f'  ✗ {func} MISSING!')
        sys.exit(1)
        
print('\n' + '='*60)
print('✅ UI Components Validation')
print('='*60)
if hasattr(gradio_simple, 'demo'):
    print('  ✓ Gradio demo interface exists')
else:
    print('  ✗ demo interface MISSING!')
    sys.exit(1)
    
print('\n' + '='*60)
print('✅ All validations passed!')
print('='*60)
