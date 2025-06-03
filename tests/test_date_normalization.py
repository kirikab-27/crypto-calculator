"""Comprehensive tests for date normalization and filtering."""

import pytest
import tempfile
import sqlite3
from datetime import datetime
import os
import sys

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.date_utils import normalize_date_to_string, validate_date_format, ensure_date_normalized
from src.db import init_db, add_transaction, get_user_transactions_filtered, get_connection, add_user
from src.migrations import run_migrations


class TestDateUtils:
    """Test date utility functions."""
    
    def test_normalize_various_date_formats(self):
        """Test normalization of various date formats."""
        test_cases = [
            # Already normalized
            ("2023-12-25", "2023-12-25"),
            # With time
            ("2023-12-25 10:30:45", "2023-12-25"),
            # With slashes
            ("2023/12/25", "2023-12-25"),
            # European format
            ("25-12-2023", "2023-12-25"),
            ("25/12/2023", "2023-12-25"),
            # US format
            ("12-25-2023", "2023-12-25"),
            ("12/25/2023", "2023-12-25"),
            # Compact format
            ("20231225", "2023-12-25"),
            # German format
            ("25.12.2023", "2023-12-25"),
            # Unix timestamp (seconds)
            (1703462400, "2023-12-25"),  # 2023-12-25 00:00:00 UTC
            # Unix timestamp (milliseconds)
            (1703462400000, "2023-12-25"),
            # Datetime object
            (datetime(2023, 12, 25), "2023-12-25"),
        ]
        
        for input_date, expected in test_cases:
            result = normalize_date_to_string(input_date)
            assert result == expected, f"Failed for {input_date}: expected {expected}, got {result}"
    
    def test_validate_date_format(self):
        """Test date format validation."""
        # Valid formats
        assert validate_date_format("2023-12-25") is True
        assert validate_date_format("2023-01-01") is True
        assert validate_date_format("1999-12-31") is True
        
        # Invalid formats
        assert validate_date_format("2023/12/25") is False
        assert validate_date_format("25-12-2023") is False
        assert validate_date_format("2023-13-01") is False  # Invalid month
        assert validate_date_format("2023-12-32") is False  # Invalid day
        assert validate_date_format("not a date") is False
        assert validate_date_format("") is False
        assert validate_date_format(None) is False
    
    def test_ensure_date_normalized(self):
        """Test the ensure_date_normalized convenience function."""
        # Already normalized
        assert ensure_date_normalized("2023-12-25") == "2023-12-25"
        
        # Needs normalization
        assert ensure_date_normalized("2023/12/25") == "2023-12-25"
        assert ensure_date_normalized(datetime(2023, 12, 25)) == "2023-12-25"


class TestDateFiltering:
    """Test date filtering in database operations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Temporarily override DB_PATH
        import src.db
        original_db_path = src.db.DB_PATH
        src.db.DB_PATH = db_path
        
        # Initialize database
        init_db()
        
        # Run migrations
        with get_connection() as conn:
            run_migrations()
        
        yield db_path
        
        # Cleanup
        src.db.DB_PATH = original_db_path
        os.unlink(db_path)
    
    def test_date_normalization_on_insert(self, temp_db):
        """Test that dates are normalized when inserting transactions."""
        # Create a test user
        user = add_user("testuser", "password123")
        
        # Add transactions with various date formats
        test_dates = [
            "2023-12-25",          # Already normalized
            "2023/12/25",          # Slash format (should be rejected by CHECK constraint)
            "2023-12-25 10:30:00", # With time (should be normalized)
        ]
        
        for date in test_dates:
            try:
                add_transaction(
                    user_id=user.id,
                    date=date,
                    type="buy",
                    currency="BTC",
                    amount=1.0,
                    price=40000.0,
                    fee=10.0
                )
            except sqlite3.IntegrityError:
                # This is expected for non-normalized dates with the CHECK constraint
                pass
        
        # Retrieve all transactions
        transactions = get_user_transactions_filtered(user.id, limit=100)["transactions"]
        
        # All stored dates should be in YYYY-MM-DD format
        for tx in transactions:
            assert validate_date_format(tx["date"]), f"Invalid date format: {tx['date']}"
    
    def test_date_filtering_with_normalized_dates(self, temp_db):
        """Test date filtering with properly normalized dates."""
        # Create a test user
        user = add_user("testuser", "password123")
        
        # Add transactions with normalized dates
        dates = [
            "2023-12-20",
            "2023-12-25",
            "2023-12-30",
            "2024-01-05",
            "2024-01-10"
        ]
        
        for date in dates:
            add_transaction(
                user_id=user.id,
                date=date,
                type="buy",
                currency="BTC",
                amount=1.0,
                price=40000.0,
                fee=10.0
            )
        
        # Test various date filters
        
        # Filter by start date only
        result = get_user_transactions_filtered(
            user_id=user.id,
            start_date="2023-12-25"
        )
        filtered_dates = [tx["date"] for tx in result["transactions"]]
        assert len(filtered_dates) == 4  # 2023-12-25, 2023-12-30, 2024-01-05, 2024-01-10
        assert all(date >= "2023-12-25" for date in filtered_dates)
        
        # Filter by end date only
        result = get_user_transactions_filtered(
            user_id=user.id,
            end_date="2023-12-30"
        )
        filtered_dates = [tx["date"] for tx in result["transactions"]]
        assert len(filtered_dates) == 3  # 2023-12-20, 2023-12-25, 2023-12-30
        assert all(date <= "2023-12-30" for date in filtered_dates)
        
        # Filter by date range
        result = get_user_transactions_filtered(
            user_id=user.id,
            start_date="2023-12-25",
            end_date="2024-01-05"
        )
        filtered_dates = [tx["date"] for tx in result["transactions"]]
        assert len(filtered_dates) == 3  # 2023-12-25, 2023-12-30, 2024-01-05
        assert all("2023-12-25" <= date <= "2024-01-05" for date in filtered_dates)
    
    def test_edge_cases(self, temp_db):
        """Test edge cases for date filtering."""
        # Create a test user
        user = add_user("testuser", "password123")
        
        # Add transactions at year/month boundaries
        boundary_dates = [
            "2023-01-01",  # Start of year
            "2023-12-31",  # End of year
            "2024-01-01",  # Start of next year
            "2023-02-28",  # End of February (non-leap year)
            "2024-02-29",  # Leap day
        ]
        
        for date in boundary_dates:
            add_transaction(
                user_id=user.id,
                date=date,
                type="buy",
                currency="ETH",
                amount=1.0,
                price=2000.0,
                fee=5.0
            )
        
        # Test year boundary
        result = get_user_transactions_filtered(
            user_id=user.id,
            start_date="2023-12-31",
            end_date="2024-01-01"
        )
        filtered_dates = [tx["date"] for tx in result["transactions"]]
        assert len(filtered_dates) == 2
        assert "2023-12-31" in filtered_dates
        assert "2024-01-01" in filtered_dates
        
        # Test leap year
        result = get_user_transactions_filtered(
            user_id=user.id,
            start_date="2024-02-28",
            end_date="2024-02-29"
        )
        filtered_dates = [tx["date"] for tx in result["transactions"]]
        assert len(filtered_dates) == 1
        assert "2024-02-29" in filtered_dates


if __name__ == "__main__":
    pytest.main([__file__, "-v"])