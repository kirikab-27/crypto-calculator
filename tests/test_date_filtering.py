"""Unit tests for date filtering functionality."""

import unittest
import os
import tempfile
from pathlib import Path
from datetime import datetime

from src.db import (
    init_db, create_user, add_transaction, 
    get_user_transactions_filtered, check_transaction_exists
)
from src.date_utils import ensure_date_normalized


class TestDateFiltering(unittest.TestCase):
    """Test date filtering functionality."""
    
    def setUp(self):
        """Set up test database."""
        # Create temporary database
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        
        # Temporarily change DB_PATH
        import src.db
        self.original_db_path = src.db.DB_PATH
        src.db.DB_PATH = Path(self.test_db_path)
        
        # Initialize database and create test user
        init_db()
        self.user = create_user("testuser", "testpass")
        self.user_id = self.user.id
        
        # Add test transactions
        self.test_transactions = [
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
        
        for date, tx_type, currency, amount, price, fee in self.test_transactions:
            add_transaction(self.user_id, date, tx_type, currency, amount, price, fee)
    
    def tearDown(self):
        """Clean up test database."""
        # Restore original DB_PATH
        import src.db
        src.db.DB_PATH = self.original_db_path
        
        # Close and remove test database
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_date_filter_june_only(self):
        """Test filtering for June 2025 transactions only."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-06-01",
            end_date="2025-06-26",
            limit=50
        )
        
        # Should find exactly 2 transactions
        self.assertEqual(len(result['transactions']), 2)
        
        # Verify they are June transactions
        for tx in result['transactions']:
            date = tx['date'][:10]  # Extract YYYY-MM-DD part
            self.assertTrue(date >= "2025-06-01")
            self.assertTrue(date <= "2025-06-26")
    
    def test_date_filter_with_slash_format(self):
        """Test date filtering with slash format (YYYY/MM/DD)."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025/06/01",
            end_date="2025/06/26",
            limit=50
        )
        
        # Should find exactly 2 transactions
        self.assertEqual(len(result['transactions']), 2)
    
    def test_date_filter_with_datetime_format(self):
        """Test date filtering with datetime format."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-06-01 00:00:00",
            end_date="2025-06-26 23:59:59",
            limit=50
        )
        
        # Should find exactly 2 transactions
        self.assertEqual(len(result['transactions']), 2)
    
    def test_date_filter_full_year(self):
        """Test filtering for full year 2025."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2025-01-01",
            end_date="2025-12-31",
            limit=50
        )
        
        # Should find all 10 transactions
        self.assertEqual(len(result['transactions']), 10)
    
    def test_date_filter_no_results(self):
        """Test filtering for date range with no transactions."""
        result = get_user_transactions_filtered(
            user_id=self.user_id,
            start_date="2024-01-01",
            end_date="2024-12-31",
            limit=50
        )
        
        # Should find no transactions
        self.assertEqual(len(result['transactions']), 0)
    
    def test_date_filter_with_invalid_dates(self):
        """Test filtering with invalid date formats."""
        # Set DEBUG_DB to suppress warnings during test
        old_debug = os.environ.get('DEBUG_DB')
        os.environ['DEBUG_DB'] = ''
        
        try:
            # Invalid date format should be handled gracefully
            result = get_user_transactions_filtered(
                user_id=self.user_id,
                start_date="invalid-date",
                end_date="2025-06-26",
                limit=50
            )
            
            # Should still return results (filter skipped for invalid date)
            self.assertIsNotNone(result)
            self.assertIn('transactions', result)
        finally:
            # Restore DEBUG_DB
            if old_debug is None:
                os.environ.pop('DEBUG_DB', None)
            else:
                os.environ['DEBUG_DB'] = old_debug
    
    def test_date_normalization(self):
        """Test date normalization function."""
        # Test various date formats
        test_cases = [
            ("2025-06-01", "2025-06-01"),
            ("2025/06/01", "2025-06-01"),
            ("2025-06-01 12:34:56", "2025-06-01"),
        ]
        
        for input_date, expected in test_cases:
            normalized = ensure_date_normalized(input_date)
            self.assertEqual(normalized, expected)


if __name__ == '__main__':
    unittest.main()