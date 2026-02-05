"""
Simple launcher script for Text-to-SQL Agent Gradio UI.

This script provides a simpler way to launch the UI with better error handling.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Simple logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def main():
    """Launch Gradio UI with setup checks."""
    print("=" * 60)
    print("Text-to-SQL Agent - Gradio UI Launcher")
    print("=" * 60)
    print()
    
    # Check OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not set")
        print()
        print("Please set your OpenAI API key:")
        print('  export OPENAI_API_KEY="sk-your-key-here"')
        print()
        print("Get your API key at: https://platform.openai.com/api-keys")
        print()
        sys.exit(1)
    
    print("✓ OPENAI_API_KEY is set")
    
    # Check database exists
    db_path = Path("data/telco_sample.db")
    if not db_path.exists():
        print()
        print("⚠️  Warning: Test database not found")
        print("   Creating it now...")
        print()
        
        import subprocess
        result = subprocess.run(
            ["python", "scripts/create_telco_db.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Test database created")
        else:
            print("❌ Failed to create database")
            print(result.stderr)
            sys.exit(1)
    else:
        print("✓ Test database exists")
    
    # Check required dependencies
    print()
    print("Checking dependencies...")
    
    try:
        import gradio
        print("✓ Gradio installed")
    except ImportError:
        print("❌ Gradio not installed")
        print("   Run: pip install gradio==4.15.0")
        sys.exit(1)
    
    try:
        import openai
        print("✓ OpenAI SDK installed")
    except ImportError:
        print("❌ OpenAI not installed")
        print("   Run: pip install openai")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✓ All checks passed!")
    print("=" * 60)
    print()
    print("Launching Gradio UI...")
    print()
    print("Open your browser to: http://localhost:7860")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    # Launch Gradio
    try:
        # Check if we can use full agent or need simplified mode
        can_use_full = True
        try:
            from src.agent.agent import TextToSQLAgent
        except ImportError as e:
            logger.warning(f"Full agent not available: {e}")
            can_use_full = False
        
        # Try multiple ports if needed
        ports_to_try = [7860, 7861, 7862, 7863, 7864]
        launched = False
        
        for port in ports_to_try:
            try:
                if can_use_full:
                    logger.info(f"Launching with full agent on port {port}")
                    from src.ui.gradio_app import launch_ui
                    launch_ui(server_name="127.0.0.1", server_port=port, share=False)
                else:
                    logger.info(f"Launching in simplified mode on port {port}")
                    import sys
                    sys.path.insert(0, 'src/ui')
                    import gradio_simple
                    print(f"\n✅ UI successfully launched at: http://localhost:{port}\n")
                    gradio_simple.demo.launch(server_name="127.0.0.1", server_port=port, share=False)
                
                launched = True
                break
            except OSError as e:
                if "Cannot find empty port" in str(e):
                    logger.info(f"Port {port} in use, trying next port...")
                    continue
                else:
                    raise
        
        if not launched:
            raise Exception(f"Could not find available port in range {ports_to_try[0]}-{ports_to_try[-1]}")
            
    except KeyboardInterrupt:
        print()
        print("Shutting down...")
        sys.exit(0)
    except Exception as e:
        print()
        print(f"❌ Error launching UI: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
