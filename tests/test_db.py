from crypto_calculator.db import init_db, add_user, get_user_by_username, add_transaction, update_transaction, get_user_transactions


def test_add_and_get_user(tmp_path, monkeypatch):
    db_file = tmp_path / "users.db"
    monkeypatch.setattr("crypto_calculator.db.DB_PATH", db_file)
    init_db()
    user = add_user("bob", "password")
    fetched = get_user_by_username("bob")
    assert fetched is not None
    assert fetched.username == "bob"
    assert fetched.verify_password("password")


def test_update_transaction(tmp_path, monkeypatch):
    db_file = tmp_path / "users.db"
    monkeypatch.setattr("crypto_calculator.db.DB_PATH", db_file)
    init_db()
    
    # Create a user
    user = add_user("alice", "password")
    
    # Add a transaction
    tx_id = add_transaction(
        user_id=user.id,
        date="2025-01-01",
        type="buy",
        currency="BTC",
        amount=1.0,
        price=30000.0,
        fee=10.0
    )
    
    # Update the transaction
    success = update_transaction(
        user_id=user.id,
        transaction_id=tx_id,
        date="2025-01-15",
        type="sell",
        currency="ETH",
        amount=2.0,
        price=2000.0,
        fee=5.0,
        gain_loss=100.0
    )
    assert success is True
    
    # Verify the update
    transactions = get_user_transactions(user.id)
    assert len(transactions) == 1
    tx = transactions[0]
    assert tx['date'] == "2025-01-15"
    assert tx['type'] == "sell"
    assert tx['currency'] == "ETH"
    assert tx['amount'] == 2.0
    assert tx['price'] == 2000.0
    assert tx['fee'] == 5.0
    assert tx['gain_loss'] == 100.0
    
    # Try to update with wrong user_id
    success = update_transaction(
        user_id=user.id + 1,  # Different user
        transaction_id=tx_id,
        date="2025-02-01",
        type="buy",
        currency="LTC",
        amount=10.0,
        price=100.0,
        fee=1.0
    )
    assert success is False
    
    # Verify transaction unchanged
    transactions = get_user_transactions(user.id)
    tx = transactions[0]
    assert tx['currency'] == "ETH"  # Should still be ETH
