#!/usr/bin/env python3
"""Test script to verify duplicate prevention is working."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.db import init_db, add_transaction, check_transaction_exists, remove_duplicate_transactions, get_user_transactions
from src.auth import User
import sqlite3

def test_duplicate_prevention():
    """Test that duplicate transactions are properly prevented."""
    print("Testing duplicate prevention...")
    
    # Initialize database
    init_db()
    
    # Create a test user ID
    test_user_id = 1
    
    # Test transaction data
    test_tx = {
        "user_id": test_user_id,
        "date": "2025-01-01",
        "type": "buy",
        "currency": "BTC",
        "amount": 1.0,
        "price": 50000.0,
        "fee": 10.0
    }
    
    print("\n1. Testing check_transaction_exists function:")
    exists_before = check_transaction_exists(**test_tx)
    print(f"   Transaction exists before adding: {exists_before}")
    
    print("\n2. Adding first transaction:")
    try:
        tx_id = add_transaction(**test_tx)
        print(f"   Successfully added transaction with ID: {tx_id}")
    except Exception as e:
        print(f"   Error adding transaction: {e}")
    
    print("\n3. Checking if transaction now exists:")
    exists_after = check_transaction_exists(**test_tx)
    print(f"   Transaction exists after adding: {exists_after}")
    
    print("\n4. Attempting to add duplicate transaction:")
    try:
        tx_id2 = add_transaction(**test_tx)
        print(f"   ERROR: Duplicate transaction was added with ID: {tx_id2}")
    except sqlite3.IntegrityError as e:
        print(f"   Good! Duplicate prevented by database: {e}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n5. Manually inserting duplicates to test removal:")
    # Temporarily remove constraint check to insert duplicates for testing
    from src.db import get_connection
    with get_connection() as conn:
        # Insert a few duplicates directly
        for i in range(3):
            try:
                conn.execute("""
                    INSERT INTO transactions (user_id, date, type, currency, amount, price, fee)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (test_user_id, "2025-01-02", "sell", "ETH", 5.0, 3000.0, 5.0))
            except:
                pass  # Ignore if constraint prevents it
    
    print("\n6. Getting all transactions before removal:")
    transactions = get_user_transactions(test_user_id)
    print(f"   Total transactions: {len(transactions)}")
    
    print("\n7. Removing duplicates:")
    removed = remove_duplicate_transactions(test_user_id)
    print(f"   Removed {removed} duplicate transactions")
    
    print("\n8. Getting all transactions after removal:")
    transactions_after = get_user_transactions(test_user_id)
    print(f"   Total transactions: {len(transactions_after)}")
    
    print("\n✅ Duplicate prevention test completed!")


if __name__ == "__main__":
    test_duplicate_prevention()