#!/usr/bin/env python3
"""
Test script to validate date filtering fix.
This script tests the date filtering functionality with various edge cases.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db import init_db, add_user, add_transaction, get_user_transactions_filtered
from datetime import datetime

# Initialize database
init_db()

# Create test user
test_user = add_user(
    username=f"testuser_{datetime.now().timestamp()}",
    password="test_password"
)
user_id = test_user.id

print("Date Filtering Validation Test")
print("=" * 60)

# Test 1: Adding transactions with various date formats
print("\nTest 1: Adding transactions with proper date format")
test_transactions = [
    ("2025-05-10", "buy", "BTC", 0.5, 40000, 20),
    ("2025-05-17", "sell", "BTC", 0.2, 42000, 15),
    ("2025-06-01", "buy", "BTC", 0.3, 41000, 18),
    ("2025-06-21", "sell", "BTC", 0.1, 43000, 10),
    ("2025-06-30", "buy", "ETH", 2.0, 2500, 25),
]

for date, tx_type, currency, amount, price, fee in test_transactions:
    try:
        tx_id = add_transaction(
            user_id=user_id,
            date=date,
            type=tx_type,
            currency=currency,
            amount=amount,
            price=price,
            fee=fee
        )
        print(f"✓ Added transaction: {date} - {tx_type} {amount} {currency}")
    except Exception as e:
        print(f"✗ Failed to add transaction: {date} - Error: {e}")

# Test 2: Try adding with invalid date formats
print("\nTest 2: Attempting to add transactions with invalid date formats")
invalid_dates = [
    "2025-06-01 10:00:00",  # DateTime format
    "2025/06/01",           # Slash format
    "06-01-2025",           # Wrong order
    "2025-6-1",             # No leading zeros
    "20250601",             # No separators
]

for invalid_date in invalid_dates:
    try:
        add_transaction(
            user_id=user_id,
            date=invalid_date,
            type="buy",
            currency="BTC",
            amount=0.1,
            price=40000,
            fee=10
        )
        print(f"✗ ERROR: Accepted invalid date format: {invalid_date}")
    except ValueError as e:
        print(f"✓ Correctly rejected: {invalid_date} - {str(e)}")
    except Exception as e:
        print(f"? Unexpected error for {invalid_date}: {e}")

# Test 3: Date filtering
print("\nTest 3: Testing date filtering")

# Test 3a: Filter for June 2025
print("\n3a. Filtering for June 2025 (2025-06-01 to 2025-06-30)")
result = get_user_transactions_filtered(
    user_id=user_id,
    start_date="2025-06-01",
    end_date="2025-06-30"
)
print(f"   Found {result['total']} transactions:")
for tx in result['transactions']:
    print(f"   - {tx['date']}: {tx['type']} {tx['amount']} {tx['currency']}")

# Test 3b: Filter for specific date
print("\n3b. Filtering for specific date (2025-06-01)")
result = get_user_transactions_filtered(
    user_id=user_id,
    start_date="2025-06-01",
    end_date="2025-06-01"
)
print(f"   Found {result['total']} transactions:")
for tx in result['transactions']:
    print(f"   - {tx['date']}: {tx['type']} {tx['amount']} {tx['currency']}")

# Test 3c: Filter with only start date
print("\n3c. Filtering from 2025-06-01 onwards")
result = get_user_transactions_filtered(
    user_id=user_id,
    start_date="2025-06-01"
)
print(f"   Found {result['total']} transactions:")
for tx in result['transactions']:
    print(f"   - {tx['date']}: {tx['type']} {tx['amount']} {tx['currency']}")

# Test 3d: Filter with only end date
print("\n3d. Filtering up to 2025-05-31")
result = get_user_transactions_filtered(
    user_id=user_id,
    end_date="2025-05-31"
)
print(f"   Found {result['total']} transactions:")
for tx in result['transactions']:
    print(f"   - {tx['date']}: {tx['type']} {tx['amount']} {tx['currency']}")

# Test 4: Edge cases
print("\nTest 4: Edge cases")

# Test 4a: Empty date strings
print("\n4a. Testing with empty date strings")
result = get_user_transactions_filtered(
    user_id=user_id,
    start_date="",
    end_date=""
)
print(f"   With empty strings: Found {result['total']} transactions (should be all)")

# Test 4b: Whitespace strings
print("\n4b. Testing with whitespace strings")
result = get_user_transactions_filtered(
    user_id=user_id,
    start_date="  ",
    end_date="  "
)
print(f"   With whitespace: Found {result['total']} transactions (should be all)")

# Test 4c: Date range with no transactions
print("\n4c. Testing date range with no transactions")
result = get_user_transactions_filtered(
    user_id=user_id,
    start_date="2025-04-01",
    end_date="2025-04-30"
)
print(f"   April 2025: Found {result['total']} transactions (should be 0)")

print("\n" + "=" * 60)
print("Date filtering validation complete!")
print("If all tests passed with ✓, the date filtering should work correctly.")