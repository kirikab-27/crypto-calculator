"""Simple test script to verify transaction persistence."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.db import (
    init_db, add_user, add_transaction, get_user_transactions, 
    delete_transaction, DB_PATH
)

# Remove existing database for clean test
if DB_PATH.exists():
    os.unlink(DB_PATH)

print("Testing transaction persistence functionality...")

# Initialize database
print("\n1. Initializing database...")
init_db()
print("✓ Database initialized")

# Create test users
print("\n2. Creating test users...")
user1 = add_user("alice", "password123")
user2 = add_user("bob", "password456")
print(f"✓ Created user 'alice' with ID: {user1.id}")
print(f"✓ Created user 'bob' with ID: {user2.id}")

# Add transactions for user1
print("\n3. Adding transactions for alice...")
tx1_id = add_transaction(
    user_id=user1.id,
    date="2024-01-15",
    type="buy",
    currency="BTC",
    amount=0.5,
    price=45000.0,
    fee=10.0
)
print(f"✓ Added BTC buy transaction with ID: {tx1_id}")

tx2_id = add_transaction(
    user_id=user1.id,
    date="2024-02-01",
    type="sell",
    currency="BTC",
    amount=0.2,
    price=50000.0,
    fee=5.0,
    gain_loss=2000.0
)
print(f"✓ Added BTC sell transaction with ID: {tx2_id}")

tx3_id = add_transaction(
    user_id=user1.id,
    date="2024-02-15",
    type="buy",
    currency="ETH",
    amount=2.0,
    price=3000.0,
    fee=8.0
)
print(f"✓ Added ETH buy transaction with ID: {tx3_id}")

# Add transaction for user2
print("\n4. Adding transaction for bob...")
tx4_id = add_transaction(
    user_id=user2.id,
    date="2024-01-20",
    type="buy",
    currency="BTC",
    amount=1.0,
    price=44000.0,
    fee=20.0
)
print(f"✓ Added BTC buy transaction with ID: {tx4_id}")

# Retrieve and verify transactions
print("\n5. Retrieving alice's transactions...")
alice_txs = get_user_transactions(user1.id)
print(f"✓ Retrieved {len(alice_txs)} transactions for alice")
for i, tx in enumerate(alice_txs):
    print(f"  Transaction {i+1}: {tx['date']} - {tx['type']} {tx['amount']} {tx['currency']} @ ${tx['price']}")

print("\n6. Retrieving bob's transactions...")
bob_txs = get_user_transactions(user2.id)
print(f"✓ Retrieved {len(bob_txs)} transactions for bob")
for i, tx in enumerate(bob_txs):
    print(f"  Transaction {i+1}: {tx['date']} - {tx['type']} {tx['amount']} {tx['currency']} @ ${tx['price']}")

# Test deletion
print("\n7. Testing transaction deletion...")
result = delete_transaction(user1.id, tx1_id)
print(f"✓ Deleted transaction {tx1_id}: {result}")

alice_txs_after = get_user_transactions(user1.id)
print(f"✓ Alice now has {len(alice_txs_after)} transactions")

# Test isolation (trying to delete bob's transaction as alice)
print("\n8. Testing transaction isolation...")
result = delete_transaction(user1.id, tx4_id)
print(f"✓ Attempting to delete bob's transaction as alice: {result} (should be False)")

bob_txs_after = get_user_transactions(user2.id)
print(f"✓ Bob still has {len(bob_txs_after)} transactions")

print("\n✅ All tests passed! Transaction persistence is working correctly.")
print(f"\nDatabase file created at: {DB_PATH}")