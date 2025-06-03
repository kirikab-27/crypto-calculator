"""Database migrations module."""

import sqlite3
from pathlib import Path
from .db import get_connection, DB_PATH


def migrate_add_unique_constraint():
    """Add unique constraint to prevent duplicate transactions."""
    with get_connection() as conn:
        # First, check if the new table already exists
        existing_tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions_new'"
        ).fetchall()
        
        if existing_tables:
            # Migration already applied
            return
        
        # Create new table with unique constraint
        conn.execute("""
            CREATE TABLE transactions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('buy', 'sell')),
                currency TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                fee REAL DEFAULT 0.0,
                gain_loss REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date, type, currency, amount, price, fee)
            )
        """)
        
        # Copy existing data (excluding duplicates)
        conn.execute("""
            INSERT INTO transactions_new 
            SELECT DISTINCT id, user_id, date, type, currency, amount, price, fee, gain_loss, created_at
            FROM transactions
            WHERE id IN (
                SELECT MIN(id)
                FROM transactions
                GROUP BY user_id, date, type, currency, amount, price, fee
            )
        """)
        
        # Drop old table and rename new one
        conn.execute("DROP TABLE transactions")
        conn.execute("ALTER TABLE transactions_new RENAME TO transactions")
        
        # Recreate index
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
            ON transactions(user_id, date)
        """)


def migrate_normalize_dates():
    """Normalize all date values to YYYY-MM-DD format and add CHECK constraint."""
    with get_connection() as conn:
        # Check if migration already applied by looking for _normalized suffix
        existing_tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions_normalized'"
        ).fetchall()
        
        if existing_tables:
            # Migration already applied
            return
            
        print("Starting date normalization migration...")
        
        # Create new table with CHECK constraint for date format
        conn.execute("""
            CREATE TABLE transactions_normalized (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL CHECK(date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
                type TEXT NOT NULL CHECK(type IN ('buy', 'sell')),
                currency TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                fee REAL DEFAULT 0.0,
                gain_loss REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date, type, currency, amount, price, fee)
            )
        """)
        
        # Copy and normalize data
        # DATE() function in SQLite normalizes various date formats to YYYY-MM-DD
        conn.execute("""
            INSERT INTO transactions_normalized (id, user_id, date, type, currency, amount, price, fee, gain_loss, created_at)
            SELECT 
                id, 
                user_id, 
                DATE(date) as normalized_date,
                type, 
                currency, 
                amount, 
                price, 
                fee, 
                gain_loss, 
                created_at
            FROM transactions
            WHERE DATE(date) IS NOT NULL
        """)
        
        # Check how many records were processed
        original_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        normalized_count = conn.execute("SELECT COUNT(*) FROM transactions_normalized").fetchone()[0]
        
        if original_count != normalized_count:
            print(f"Warning: {original_count - normalized_count} records had invalid dates and were skipped")
        
        # Drop old table and rename new one
        conn.execute("DROP TABLE transactions")
        conn.execute("ALTER TABLE transactions_normalized RENAME TO transactions")
        
        # Recreate index
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
            ON transactions(user_id, date)
        """)
        
        print(f"Successfully normalized {normalized_count} date entries to YYYY-MM-DD format")


def migrate_add_substr_index():
    """Add index for substr date queries for better performance."""
    with get_connection() as conn:
        # Check if index already exists
        existing_indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_transactions_date_substr'"
        ).fetchall()
        
        if existing_indexes:
            # Migration already applied
            return
            
        print("Adding substr date index for better query performance...")
        
        # Create index on substr(date, 1, 10) for date filtering
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date_substr 
            ON transactions(user_id, substr(date, 1, 10))
        """)
        
        print("Successfully added substr date index")


def run_migrations():
    """Run all database migrations."""
    try:
        migrate_add_unique_constraint()
    except Exception as e:
        print(f"Migration error (unique constraint): {e}")
    
    try:
        migrate_normalize_dates()
    except Exception as e:
        print(f"Migration error (date normalization): {e}")
    
    try:
        migrate_add_substr_index()
    except Exception as e:
        print(f"Migration error (substr index): {e}")