"""Quick test to verify date normalization functionality."""

import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.date_utils import normalize_date_to_string, validate_date_format

# Test basic functionality
print("Testing date normalization...")

test_cases = [
    ("2023-12-25", "2023-12-25"),
    ("2023/12/25", "2023-12-25"),
    ("2023-12-25 10:30:45", "2023-12-25"),
    ("25-12-2023", "2023-12-25"),
    ("12/25/2023", "2023-12-25"),
]

for input_date, expected in test_cases:
    try:
        result = normalize_date_to_string(input_date)
        status = "✓" if result == expected else "✗"
        print(f"{status} {input_date} -> {result} (expected: {expected})")
    except Exception as e:
        print(f"✗ {input_date} -> ERROR: {e}")

print("\nTesting date validation...")
valid_tests = [
    ("2023-12-25", True),
    ("2023/12/25", False),
    ("25-12-2023", False),
    ("2023-12-25 10:30:00", False),
]

for date_str, expected in valid_tests:
    result = validate_date_format(date_str)
    status = "✓" if result == expected else "✗"
    print(f"{status} {date_str} -> {result} (expected: {expected})")

print("\nDate normalization tests completed!")