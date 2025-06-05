#!/usr/bin/env python3
"""Comprehensive test for date filtering functionality."""

import pytest
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import init_db, add_transaction, create_user, get_user_transactions_filtered
from src.date_utils import ensure_date_normalized
import sqlite3


@pytest.fixture
def test_db(tmp_path):
    """Create a temporary database for testing."""
    import src.db
    
    # Save original DB_PATH
    original_db_path = src.db.DB_PATH
    
    # Use temporary database
    test_db_path = tmp_path / "test.db"
    src.db.DB_PATH = test_db_path
    
    # Initialize database
    init_db()
    
    yield test_db_path
    
    # Restore original DB_PATH
    src.db.DB_PATH = original_db_path


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = create_user("testuser", "testpass")
    return user


@pytest.fixture
def sample_transactions(test_user):
    """Add sample transactions across multiple months."""
    user_id = test_user.id
    
    transactions = [
        # 2025 transactions
        ("2025-06-21", "sell", "BTC", 2, 40000.00, 0.00),
        ("2025-06-15", "buy", "ETH", 3, 3000.00, 10.00),
        ("2025-06-01", "buy", "BTC", 1, 38000.00, 5.00),
        ("2025-05-20", "sell", "ETH", 2, 3200.00, 8.00),
        ("2025-05-10", "buy", "BTC", 0.5, 37000.00, 0.00),
        ("2025-04-15", "buy", "ETH", 1, 2800.00, 5.00),
        ("2025-03-01", "sell", "BTC", 0.3, 35000.00, 10.00),
        ("2025-01-15", "buy", "BTC", 1, 30000.00, 0.00),
        # 2024 transactions
        ("2024-12-25", "buy", "ETH", 2, 2500.00, 5.00),
        ("2024-11-10", "sell", "BTC", 0.5, 32000.00, 0.00),
        ("2024-06-15", "buy", "BTC", 1, 25000.00, 10.00),
        ("2024-01-01", "buy", "ETH", 1, 2000.00, 0.00),
    ]
    
    for date, tx_type, currency, amount, price, fee in transactions:
        add_transaction(user_id, date, tx_type, currency, amount, price, fee)
    
    return transactions


def test_date_normalization():
    """Test date normalization function."""
    # Test various date formats
    assert ensure_date_normalized("2025-06-15") == "2025-06-15"
    assert ensure_date_normalized("2025/06/15") == "2025-06-15"
    assert ensure_date_normalized("2025-06-15 10:30:00") == "2025-06-15"
    assert ensure_date_normalized("2025/06/15 10:30:00") == "2025-06-15"
    
    # Test datetime object
    dt = datetime(2025, 6, 15, 10, 30, 0)
    assert ensure_date_normalized(dt) == "2025-06-15"


def test_single_month_filter(test_user, sample_transactions):
    """Test filtering for a single month."""
    # Filter for June 2025
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025-06-01",
        end_date="2025-06-30",
        limit=50
    )
    
    assert result["total"] == 3  # 3 transactions in June 2025
    dates = [tx["date"] for tx in result["transactions"]]
    assert all(date.startswith("2025-06") for date in dates)
    
    # Verify specific transactions
    assert "2025-06-21" in dates
    assert "2025-06-15" in dates
    assert "2025-06-01" in dates


def test_quarter_filter(test_user, sample_transactions):
    """Test filtering for a quarter."""
    # Filter for Q2 2025 (April-June)
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025-04-01",
        end_date="2025-06-30",
        limit=50
    )
    
    assert result["total"] == 5  # 5 transactions in Q2 2025
    dates = [tx["date"] for tx in result["transactions"]]
    
    # Check all dates are in Q2
    for date in dates:
        month = int(date.split("-")[1])
        assert 4 <= month <= 6


def test_year_filter(test_user, sample_transactions):
    """Test filtering for a full year."""
    # Filter for 2024
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2024-01-01",
        end_date="2024-12-31",
        limit=50
    )
    
    assert result["total"] == 4  # 4 transactions in 2024
    dates = [tx["date"] for tx in result["transactions"]]
    assert all(date.startswith("2024") for date in dates)


def test_cross_year_filter(test_user, sample_transactions):
    """Test filtering across years."""
    # Filter from Nov 2024 to Feb 2025
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2024-11-01",
        end_date="2025-02-28",
        limit=50
    )
    
    expected_dates = ["2025-01-15", "2024-12-25", "2024-11-10"]
    dates = [tx["date"] for tx in result["transactions"]]
    
    assert result["total"] == 3
    for expected in expected_dates:
        assert expected in dates


def test_single_day_filter(test_user, sample_transactions):
    """Test filtering for a single day."""
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025-06-15",
        end_date="2025-06-15",
        limit=50
    )
    
    assert result["total"] == 1
    assert result["transactions"][0]["date"] == "2025-06-15"


def test_empty_date_range(test_user, sample_transactions):
    """Test filtering with no matching transactions."""
    # Filter for 2023 (no transactions)
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2023-01-01",
        end_date="2023-12-31",
        limit=50
    )
    
    assert result["total"] == 0
    assert len(result["transactions"]) == 0


def test_filter_with_currency(test_user, sample_transactions):
    """Test date filter combined with currency filter."""
    # Filter for BTC transactions in 2025
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025-01-01",
        end_date="2025-12-31",
        currency_filter="BTC",
        limit=50
    )
    
    assert all(tx["currency"] == "BTC" for tx in result["transactions"])
    assert all(tx["date"].startswith("2025") for tx in result["transactions"])


def test_filter_with_type(test_user, sample_transactions):
    """Test date filter combined with type filter."""
    # Filter for buy transactions in Q2 2025
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025-04-01",
        end_date="2025-06-30",
        type_filter="buy",
        limit=50
    )
    
    assert all(tx["type"] == "buy" for tx in result["transactions"])
    # Should have 3 buy transactions in Q2 2025
    assert result["total"] == 3


def test_different_date_formats(test_user, sample_transactions):
    """Test filtering with different date input formats."""
    # Test with slash format
    result1 = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025/06/01",
        end_date="2025/06/30",
        limit=50
    )
    
    # Test with datetime format
    result2 = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025-06-01 00:00:00",
        end_date="2025-06-30 23:59:59",
        limit=50
    )
    
    # Both should return same results
    assert result1["total"] == result2["total"] == 3
    
    dates1 = sorted([tx["date"] for tx in result1["transactions"]])
    dates2 = sorted([tx["date"] for tx in result2["transactions"]])
    assert dates1 == dates2


def test_pagination_with_date_filter(test_user, sample_transactions):
    """Test pagination works correctly with date filters."""
    # Get all 2025 transactions with pagination
    page1 = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025-01-01",
        end_date="2025-12-31",
        limit=3,
        offset=0
    )
    
    page2 = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025-01-01",
        end_date="2025-12-31",
        limit=3,
        offset=3
    )
    
    # Should have 8 total transactions in 2025
    assert page1["total"] == 8
    assert len(page1["transactions"]) == 3
    assert len(page2["transactions"]) == 3
    
    # Make sure no duplicates between pages
    page1_ids = {tx["id"] for tx in page1["transactions"]}
    page2_ids = {tx["id"] for tx in page2["transactions"]}
    assert len(page1_ids & page2_ids) == 0


def test_invalid_date_handling(test_user, sample_transactions):
    """Test handling of invalid date formats."""
    # Invalid start date should be skipped
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="invalid-date",
        end_date="2025-06-30",
        limit=50
    )
    
    # Should return all transactions up to end date
    assert result["total"] > 0
    
    # Invalid end date should be skipped
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025-01-01",
        end_date="not-a-date",
        limit=50
    )
    
    # Should return all transactions from start date
    assert result["total"] > 0


def test_date_boundary_inclusivity(test_user, sample_transactions):
    """Test that date boundaries are inclusive."""
    # Add transactions on boundary dates
    add_transaction(test_user.id, "2025-07-01", "buy", "BTC", 1, 40000, 0)
    add_transaction(test_user.id, "2025-06-30", "sell", "BTC", 0.5, 41000, 0)
    
    # Filter for June with exact boundaries
    result = get_user_transactions_filtered(
        user_id=test_user.id,
        start_date="2025-06-01",
        end_date="2025-06-30",
        limit=50
    )
    
    dates = [tx["date"] for tx in result["transactions"]]
    
    # Should include June 1st and June 30th
    assert "2025-06-01" in dates
    assert "2025-06-30" in dates
    
    # Should NOT include July 1st
    assert "2025-07-01" not in dates


if __name__ == "__main__":
    pytest.main([__file__, "-v"])