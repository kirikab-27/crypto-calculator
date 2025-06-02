#!/usr/bin/env python3
"""Comprehensive tests for date filtering functionality."""

import pytest
from datetime import datetime
from src.db import (
    init_db, add_transaction, get_user_transactions_filtered,
    add_user, get_connection
)
from src.date_migration import parse_date_flexible


class TestDateFiltering:
    """Test suite for date filtering functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, tmp_path, monkeypatch):
        """Set up a test database."""
        # Use a temporary database
        test_db = tmp_path / "test.db"
        monkeypatch.setattr("src.db.DB_PATH", test_db)
        init_db()
        
        # Create a test user
        self.user_id = add_user(
            username="testuser",
            password_hash="test_hash",
            salt="test_salt"
        )
        
        # Add test transactions with various dates
        test_data = [
            ("2025-01-15", "buy", "BTC", 0.5, 30000, 10),
            ("2025-02-20", "sell", "BTC", 0.2, 35000, 15),
            ("2025-03-10", "buy", "ETH", 2.0, 2000, 5),
            ("2025-05-05", "buy", "BTC", 0.3, 40000, 12),
            ("2025-06-01", "sell", "ETH", 1.0, 2500, 8),
            ("2025-06-15", "buy", "BTC", 0.1, 38000, 10),
            ("2025-06-30", "sell", "BTC", 0.4, 42000, 20),
            ("2025-07-10", "buy", "ETH", 1.5, 2200, 6),
        ]
        
        for date, tx_type, currency, amount, price, fee in test_data:
            add_transaction(
                user_id=self.user_id,
                date=date,
                type=tx_type,
                currency=currency,
                amount=amount,
                price=price,
                fee=fee
            )
    
    def test_date_filter_single_month(self):
        """Test filtering transactions for a single month."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-06-01",
            end_date="2025-06-30"
        )
        
        assert result['total'] == 3
        transactions = result['transactions']
        assert len(transactions) == 3
        
        # Verify all transactions are within date range
        for tx in transactions:
            assert tx['date'] >= "2025-06-01"
            assert tx['date'] <= "2025-06-30"
    
    def test_date_filter_multiple_months(self):
        """Test filtering transactions across multiple months."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-03-01",
            end_date="2025-05-31"
        )
        
        assert result['total'] == 2
        transactions = result['transactions']
        assert len(transactions) == 2
        
        # Check specific transactions
        dates = [tx['date'] for tx in transactions]
        assert "2025-03-10" in dates
        assert "2025-05-05" in dates
    
    def test_date_filter_start_only(self):
        """Test filtering with only start date."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-06-01"
        )
        
        assert result['total'] == 4  # June and July transactions
        transactions = result['transactions']
        
        for tx in transactions:
            assert tx['date'] >= "2025-06-01"
    
    def test_date_filter_end_only(self):
        """Test filtering with only end date."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            end_date="2025-03-31"
        )
        
        assert result['total'] == 3  # Jan, Feb, March transactions
        transactions = result['transactions']
        
        for tx in transactions:
            assert tx['date'] <= "2025-03-31"
    
    def test_date_filter_exact_date(self):
        """Test filtering for a single day."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-06-01",
            end_date="2025-06-01"
        )
        
        assert result['total'] == 1
        tx = result['transactions'][0]
        assert tx['date'] == "2025-06-01"
        assert tx['currency'] == "ETH"
    
    def test_date_filter_no_results(self):
        """Test filtering with date range that has no transactions."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-04-01",
            end_date="2025-04-30"
        )
        
        assert result['total'] == 0
        assert len(result['transactions']) == 0
    
    def test_date_filter_with_other_filters(self):
        """Test date filtering combined with other filters."""
        # Filter by date and type
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-06-01",
            end_date="2025-06-30",
            type_filter="buy"
        )
        
        assert result['total'] == 1
        tx = result['transactions'][0]
        assert tx['date'] == "2025-06-15"
        assert tx['type'] == "buy"
        
        # Filter by date and currency
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-01-01",
            end_date="2025-12-31",
            currency_filter="ETH"
        )
        
        assert result['total'] == 3  # All ETH transactions
    
    def test_date_format_validation(self):
        """Test that invalid date formats are rejected."""
        # Test add_transaction with invalid date format
        with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD format"):
            add_transaction(
                user_id=self.user_id,
                date="2025/06/01",  # Wrong format
                type="buy",
                currency="BTC",
                amount=1.0,
                price=40000,
                fee=10
            )
        
        with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD format"):
            add_transaction(
                user_id=self.user_id,
                date="2025-06-01 10:00:00",  # Includes time
                type="buy",
                currency="BTC",
                amount=1.0,
                price=40000,
                fee=10
            )
        
        with pytest.raises(ValueError, match="Invalid date"):
            add_transaction(
                user_id=self.user_id,
                date="2025-13-01",  # Invalid month
                type="buy",
                currency="BTC",
                amount=1.0,
                price=40000,
                fee=10
            )
    
    def test_edge_cases(self):
        """Test edge cases for date filtering."""
        # Test with empty strings
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="",
            end_date=""
        )
        assert result['total'] == 8  # All transactions
        
        # Test with whitespace
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="  ",
            end_date="  "
        )
        assert result['total'] == 8  # All transactions
        
        # Test year boundaries
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-01-01",
            end_date="2025-12-31"
        )
        assert result['total'] == 8  # All transactions in 2025


class TestDateParsing:
    """Test the date parsing utility function."""
    
    def test_parse_standard_format(self):
        """Test parsing standard YYYY-MM-DD format."""
        assert parse_date_flexible("2025-06-01") == "2025-06-01"
    
    def test_parse_datetime_formats(self):
        """Test parsing various datetime formats."""
        assert parse_date_flexible("2025-06-01 10:30:00") == "2025-06-01"
        assert parse_date_flexible("2025-06-01 10:30:00.123456") == "2025-06-01"
        assert parse_date_flexible("2025-06-01T10:30:00") == "2025-06-01"
        assert parse_date_flexible("2025-06-01T10:30:00Z") == "2025-06-01"
    
    def test_parse_slash_formats(self):
        """Test parsing slash-separated dates."""
        assert parse_date_flexible("2025/06/01") == "2025-06-01"
        assert parse_date_flexible("2025/06/01 10:30:00") == "2025-06-01"
    
    def test_parse_timestamps(self):
        """Test parsing Unix timestamps."""
        # Timestamp for 2025-06-01 00:00:00 UTC
        assert parse_date_flexible("1748736000") == "2025-06-01"
        # Timestamp in milliseconds
        assert parse_date_flexible("1748736000000") == "2025-06-01"
    
    def test_parse_invalid_formats(self):
        """Test that invalid formats raise errors."""
        with pytest.raises(ValueError):
            parse_date_flexible("")
        
        with pytest.raises(ValueError):
            parse_date_flexible("invalid-date")
        
        with pytest.raises(ValueError):
            parse_date_flexible("20250601")  # No separators


if __name__ == "__main__":
    pytest.main([__file__, "-v"])