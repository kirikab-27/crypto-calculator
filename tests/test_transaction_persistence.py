"""Test transaction persistence functionality."""

import pytest
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import (
    init_db, add_user, add_transaction, get_user_transactions, 
    delete_transaction, clear_user_transactions, get_connection
)


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    # Create temporary database file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        tmp_path = tmp.name
    
    # Monkey patch the DB_PATH
    import src.db
    original_path = src.db.DB_PATH
    src.db.DB_PATH = Path(tmp_path)
    
    # Initialize database
    init_db()
    
    yield tmp_path
    
    # Cleanup
    src.db.DB_PATH = original_path
    os.unlink(tmp_path)


def test_add_transaction(test_db):
    """Test adding a transaction."""
    # Create a test user
    user = add_user("testuser", "password123")
    
    # Add a transaction
    tx_id = add_transaction(
        user_id=user.id,
        date="2024-01-15",
        type="buy",
        currency="BTC",
        amount=0.5,
        price=45000.0,
        fee=10.0
    )
    
    assert tx_id is not None
    assert isinstance(tx_id, int)


def test_get_user_transactions(test_db):
    """Test retrieving user transactions."""
    # Create test users
    user1 = add_user("user1", "password123")
    user2 = add_user("user2", "password456")
    
    # Add transactions for user1
    add_transaction(user1.id, "2024-01-15", "buy", "BTC", 0.5, 45000.0, 10.0)
    add_transaction(user1.id, "2024-02-01", "sell", "BTC", 0.2, 50000.0, 5.0, 2000.0)
    add_transaction(user1.id, "2024-02-15", "buy", "ETH", 2.0, 3000.0, 8.0)
    
    # Add transaction for user2
    add_transaction(user2.id, "2024-01-20", "buy", "BTC", 1.0, 44000.0, 20.0)
    
    # Get user1 transactions
    user1_txs = get_user_transactions(user1.id)
    assert len(user1_txs) == 3
    
    # Verify transaction details
    tx1 = user1_txs[0]
    assert tx1["date"] == "2024-01-15"
    assert tx1["type"] == "buy"
    assert tx1["currency"] == "BTC"
    assert tx1["amount"] == 0.5
    assert tx1["price"] == 45000.0
    assert tx1["fee"] == 10.0
    assert tx1["gain_loss"] is None
    
    # Verify sell transaction with gain/loss
    tx2 = user1_txs[1]
    assert tx2["type"] == "sell"
    assert tx2["gain_loss"] == 2000.0
    
    # Get user2 transactions
    user2_txs = get_user_transactions(user2.id)
    assert len(user2_txs) == 1


def test_delete_transaction(test_db):
    """Test deleting a transaction."""
    # Create a test user
    user = add_user("testuser", "password123")
    
    # Add transactions
    tx1_id = add_transaction(user.id, "2024-01-15", "buy", "BTC", 0.5, 45000.0, 10.0)
    tx2_id = add_transaction(user.id, "2024-02-01", "sell", "BTC", 0.2, 50000.0, 5.0)
    
    # Delete first transaction
    result = delete_transaction(user.id, tx1_id)
    assert result is True
    
    # Verify only one transaction remains
    txs = get_user_transactions(user.id)
    assert len(txs) == 1
    assert txs[0]["id"] == tx2_id
    
    # Try to delete transaction from wrong user
    other_user = add_user("otheruser", "password456")
    result = delete_transaction(other_user.id, tx2_id)
    assert result is False
    
    # Verify transaction still exists for original user
    txs = get_user_transactions(user.id)
    assert len(txs) == 1


def test_clear_user_transactions(test_db):
    """Test clearing all transactions for a user."""
    # Create test users
    user1 = add_user("user1", "password123")
    user2 = add_user("user2", "password456")
    
    # Add transactions
    add_transaction(user1.id, "2024-01-15", "buy", "BTC", 0.5, 45000.0, 10.0)
    add_transaction(user1.id, "2024-02-01", "sell", "BTC", 0.2, 50000.0, 5.0)
    add_transaction(user2.id, "2024-01-20", "buy", "ETH", 1.0, 3000.0, 20.0)
    
    # Clear user1 transactions
    clear_user_transactions(user1.id)
    
    # Verify user1 has no transactions
    user1_txs = get_user_transactions(user1.id)
    assert len(user1_txs) == 0
    
    # Verify user2 transactions are unaffected
    user2_txs = get_user_transactions(user2.id)
    assert len(user2_txs) == 1


def test_transaction_ordering(test_db):
    """Test that transactions are returned in chronological order."""
    user = add_user("testuser", "password123")
    
    # Add transactions in non-chronological order
    add_transaction(user.id, "2024-03-01", "sell", "BTC", 0.5, 55000.0, 10.0)
    add_transaction(user.id, "2024-01-15", "buy", "BTC", 1.0, 45000.0, 20.0)
    add_transaction(user.id, "2024-02-10", "buy", "ETH", 2.0, 3000.0, 15.0)
    
    # Get transactions
    txs = get_user_transactions(user.id)
    
    # Verify they are sorted by date
    assert txs[0]["date"] == "2024-01-15"
    assert txs[1]["date"] == "2024-02-10"
    assert txs[2]["date"] == "2024-03-01"


def test_transaction_isolation(test_db):
    """Test that users can only access their own transactions."""
    # Create multiple users
    user1 = add_user("alice", "password123")
    user2 = add_user("bob", "password456")
    user3 = add_user("charlie", "password789")
    
    # Add transactions for each user
    add_transaction(user1.id, "2024-01-15", "buy", "BTC", 1.0, 45000.0, 10.0)
    add_transaction(user2.id, "2024-01-16", "buy", "ETH", 10.0, 3000.0, 20.0)
    add_transaction(user3.id, "2024-01-17", "buy", "SOL", 100.0, 100.0, 5.0)
    
    # Each user should only see their own transactions
    assert len(get_user_transactions(user1.id)) == 1
    assert len(get_user_transactions(user2.id)) == 1
    assert len(get_user_transactions(user3.id)) == 1
    
    # Verify correct transaction content
    assert get_user_transactions(user1.id)[0]["currency"] == "BTC"
    assert get_user_transactions(user2.id)[0]["currency"] == "ETH"
    assert get_user_transactions(user3.id)[0]["currency"] == "SOL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])