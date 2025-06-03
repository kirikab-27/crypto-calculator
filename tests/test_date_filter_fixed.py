#!/usr/bin/env python3
"""Test the date filter fix."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_user_transactions_filtered
from src.db import init_db, add_transaction, create_user
import sqlite3
from datetime import datetime
import os

# Use a test database
test_db = "test_filter.db"
if os.path.exists(test_db):
    os.remove(test_db)

# Temporarily change DB_PATH
import src.db
original_db_path = src.db.DB_PATH
src.db.DB_PATH = Path(test_db)

try:
    # Initialize database
    init_db()
    
    # Create test user
    user = create_user("testuser", "testpass")
    user_id = user.id
    
    # Add test transactions matching the screenshot
    test_transactions = [
        ("2025-06-21", "sell", "BTC", 2, 40000.00, 0.00),
        ("2025-06-01", "buy", "BTC", 1, 9000.00, 0.00),
        ("2025-05-17", "sell", "BTC", 3, 20000.00, 0.00),
        ("2025-05-10", "buy", "BTC", 5, 30000.00, 0.00),
        ("2025-03-03", "buy", "ETH", 2, 2500.00, 5.00),
        ("2025-03-02", "sell", "BTC", 0.2, 42000.00, 8.00),
        ("2025-02-03", "buy", "ETH", 2, 2500.00, 5.00),
        ("2025-02-02", "sell", "BTC", 0.2, 42000.00, 8.00),
        ("2025-01-02", "sell", "BTC", 0.2, 42000.00, 8.00),
        ("2025-01-01", "buy", "BTC", 0.5, 40000.00, 10.00),
    ]
    
    print("Adding test transactions...")
    for date, tx_type, currency, amount, price, fee in test_transactions:
        add_transaction(user_id, date, tx_type, currency, amount, price, fee)
    
    # Test the filter - June 2025 only
    print("\n=== Testing Date Filter (June 2025) ===")
    print("Filter: 2025-06-01 to 2025-06-26")
    
    result = get_user_transactions_filtered(
        user_id=user_id,
        start_date="2025-06-01",
        end_date="2025-06-26",
        limit=50
    )
    
    print(f"\nFound {len(result['transactions'])} transactions (Expected: 2)")
    print("\nTransactions found:")
    for tx in result['transactions']:
        print(f"  Date: {tx['date']}, Type: {tx['type']}, Currency: {tx['currency']}")
    
    # Verify the fix
    if len(result['transactions']) == 2:
        print("\n✅ SUCCESS: Date filter is working correctly!")
        print("Only June 2025 transactions are returned.")
    else:
        print("\n❌ FAILED: Date filter is still not working correctly.")
        print(f"Expected 2 transactions, but got {len(result['transactions'])}")
    
    # Test with different date formats
    print("\n=== Testing Different Date Formats ===")
    
    test_formats = [
        ("2025/06/01", "2025/06/26", "Slash format"),
        ("2025-06-01 00:00:00", "2025-06-26 23:59:59", "DateTime format"),
    ]
    
    for start, end, desc in test_formats:
        result = get_user_transactions_filtered(
            user_id=user_id,
            start_date=start,
            end_date=end,
            limit=50
        )
        print(f"\n{desc}: Found {len(result['transactions'])} transactions")
        
finally:
    # Restore original DB_PATH
    src.db.DB_PATH = original_db_path
    
    # Clean up test database
    if os.path.exists(test_db):
        os.remove(test_db)
    
    print("\nTest completed.")