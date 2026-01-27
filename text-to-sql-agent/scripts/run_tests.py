"""Run all tests."""

import subprocess
import sys


def main():
    """Run the full test suite."""
    print("=" * 60)
    print("Running Text-to-SQL Agent Test Suite")
    print("=" * 60)
    print()
    
    # Run pytest with coverage
    cmd = [
        "pytest",
        "-v",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term",
        "tests/"
    ]
    
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nCoverage report generated in htmlcov/index.html")
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
