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


def run_migrations():
    """Run all database migrations."""
    try:
        migrate_add_unique_constraint()
    except Exception as e:
        print(f"Migration error: {e}")