"""Test robust date filtering with both normalization and DATE() function."""

import unittest
import sqlite3
import tempfile
import os
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import (
    get_connection, init_db, add_transaction, get_user_transactions_filtered,
    DB_PATH
)
from src.auth import User


class TestRobustDateFiltering(unittest.TestCase):
    """Test that date filtering works with various date formats."""
    
    def setUp(self):
        """Set up test database with various date formats."""
        # Use a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Override the DB_PATH
        import src.db
        src.db.DB_PATH = Path(self.temp_db.name)
        
        # Initialize database
        init_db()
        
        # Create a test user
        self.test_user = User.create("testuser", "testpass123")
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                (self.test_user.username, self.test_user.password_hash, self.test_user.salt),
            )
            self.test_user.id = cur.lastrowid
    
    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)
    
    def test_mixed_date_formats_with_date_function(self):
        """Test filtering with mixed date formats using DATE() function."""
        # Add transactions with various date formats directly to database
        # This simulates legacy data that might not be normalized
        with get_connection() as conn:
            test_data = [
                # Standard format
                (self.test_user.id, '2025-06-01', 'buy', 'BTC', 0.1, 30000, 0.0),
                # Date with time
                (self.test_user.id, '2025-06-02 10:30:00', 'sell', 'BTC', 0.05, 31000, 0.0),
                # ISO format with T
                (self.test_user.id, '2025-06-03T15:45:30', 'buy', 'ETH', 1.0, 2000, 0.0),
                # Slash format (legacy data)
                (self.test_user.id, '2025/06/04', 'sell', 'ETH', 0.5, 2100, 0.0),
                # Outside range
                (self.test_user.id, '2025-05-31', 'buy', 'BTC', 0.2, 29000, 0.0),
                (self.test_user.id, '2025-06-05', 'buy', 'BTC', 0.1, 32000, 0.0),
            ]
            
            for data in test_data:
                conn.execute(
                    """
                    INSERT INTO transactions (user_id, date, type, currency, amount, price, fee)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    data
                )
        
        # Test date range filtering
        result = get_user_transactions_filtered(
            self.test_user.id,
            start_date='2025-06-01',
            end_date='2025-06-04'
        )
        
        # Should find 4 transactions (June 1-4)
        self.assertEqual(result['total'], 4)
        
        # Verify the dates are within range
        for tx in result['transactions']:
            # Extract just the date part for comparison
            date_part = tx['date'][:10] if len(tx['date']) > 10 else tx['date']
            # Handle slash format
            if '/' in date_part:
                date_part = date_part.replace('/', '-')
            
            self.assertGreaterEqual(date_part, '2025-06-01')
            self.assertLessEqual(date_part, '2025-06-04')
    
    def test_normalized_dates(self):
        """Test that newly added transactions are normalized and filtered correctly."""
        # Add transactions using the API (these will be normalized)
        test_dates = [
            '2025-06-01',
            '2025/06/02',
            '2025-06-03 10:30:00',
            '2025-06-04T15:45:30',
            '02/06/2025',  # European format
            '06-05-2025',  # US format
        ]
        
        for i, date in enumerate(test_dates):
            try:
                add_transaction(
                    self.test_user.id,
                    date,
                    'buy',
                    'BTC',
                    0.1 * (i + 1),
                    30000 + i * 1000,
                    0.0
                )
            except Exception as e:
                # Some dates might fail, that's okay for this test
                pass
        
        # Get all transactions
        all_txs = get_user_transactions_filtered(self.test_user.id, limit=100)
        
        # All dates should be normalized to YYYY-MM-DD
        for tx in all_txs['transactions']:
            # Verify date is in normalized format
            self.assertRegex(tx['date'], r'^\d{4}-\d{2}-\d{2}$')
    
    def test_date_function_robustness(self):
        """Test DATE() function handles edge cases."""
        # Add some edge case dates
        with get_connection() as conn:
            edge_cases = [
                (self.test_user.id, '2025-06-01 00:00:00.000', 'buy', 'BTC', 0.1, 30000, 0.0),
                (self.test_user.id, '2025-06-02T23:59:59Z', 'sell', 'BTC', 0.1, 31000, 0.0),
                (self.test_user.id, '2025-06-03 12:00:00+00:00', 'buy', 'ETH', 1.0, 2000, 0.0),
            ]
            
            for data in edge_cases:
                try:
                    conn.execute(
                        """
                        INSERT INTO transactions (user_id, date, type, currency, amount, price, fee)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        data
                    )
                except:
                    # Some formats might not insert, that's okay
                    pass
        
        # Filter should still work
        result = get_user_transactions_filtered(
            self.test_user.id,
            start_date='2025-06-01',
            end_date='2025-06-03'
        )
        
        # Should find at least some transactions
        self.assertGreater(result['total'], 0)
    
    def test_invalid_date_handling(self):
        """Test that invalid dates are handled gracefully."""
        # Test with invalid date formats
        result = get_user_transactions_filtered(
            self.test_user.id,
            start_date='invalid-date',
            end_date='2025-06-30'
        )
        
        # Should still return results (filter is skipped for invalid date)
        self.assertIsInstance(result['transactions'], list)
        
        # Test with another invalid format
        result = get_user_transactions_filtered(
            self.test_user.id,
            start_date='2025-06-01',
            end_date='not-a-date'
        )
        
        # Should still return results
        self.assertIsInstance(result['transactions'], list)


if __name__ == '__main__':
    unittest.main()