#!/usr/bin/env python3
"""Test script to verify import_csv can be imported from backend directory."""

import sys
import os
from pathlib import Path

# Add parent directory to path to import src modules (same as main.py)
sys.path.insert(0, str(Path(__file__).parent.parent))

print(f"Python path: {sys.path[0]}")
print(f"Current directory: {os.getcwd()}")

try:
    from src.csv_import import import_csv
    print("✓ Successfully imported import_csv from src.csv_import")
    print(f"  Function type: {type(import_csv)}")
    print(f"  Function name: {import_csv.__name__}")
    
    # Test that Transaction can also be imported
    from src.calculator import Transaction
    print("✓ Successfully imported Transaction from src.calculator")
    
    # Verify the function signature
    import inspect
    sig = inspect.signature(import_csv)
    print(f"  Function signature: {sig}")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

print("\nAll imports successful!")