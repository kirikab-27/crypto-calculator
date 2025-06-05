"""SQLite database helpers for user management."""

from __future__ import annotations

import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .auth import User
from .date_utils import ensure_date_normalized, validate_date_format

# Set up logging
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "users.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create users and transactions tables if they do not already exist."""
    with get_connection() as conn:
        # Create users table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
            """
        )
        
        # Create transactions table with unique constraint
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
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
            """
        )
        
        # Create index for better performance
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
            ON transactions(user_id, date)
            """
        )
    
    # Run migrations for existing databases
    from .migrations import run_migrations
    run_migrations()


def add_user(username: str, password: str) -> User:
    """Create and persist a new user."""
    user = User.create(username, password)
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (user.username, user.password_hash, user.salt),
        )
        user.id = cur.lastrowid
    return user


def get_user_by_username(username: str) -> Optional[User]:
    """Retrieve a user by username."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, salt FROM users WHERE username=?",
            (username,),
        ).fetchone()
    if row:
        return User(*row)
    return None


# Alias functions for backward compatibility
def get_db_connection() -> sqlite3.Connection:
    """Get database connection (alias for get_connection)."""
    return get_connection()


def create_user(username: str, password: str) -> User:
    """Create a new user (alias for add_user)."""
    init_db()  # Ensure database is initialized
    return add_user(username, password)


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password."""
    user = get_user_by_username(username)
    if user and user.verify_password(password):
        return user
    return None


# Transaction-related functions
def add_transaction(
    user_id: int,
    date: str,
    type: str,
    currency: str,
    amount: float,
    price: float,
    fee: float = 0.0,
    gain_loss: Optional[float] = None
) -> int:
    """Add a new transaction to the database."""
    # Normalize date to YYYY-MM-DD format
    normalized_date = ensure_date_normalized(date)
    
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO transactions (user_id, date, type, currency, amount, price, fee, gain_loss)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, normalized_date, type, currency, amount, price, fee, gain_loss)
        )
        return cur.lastrowid


def get_user_transactions(user_id: int) -> List[Dict[str, Any]]:
    """Get all transactions for a specific user."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, date, type, currency, amount, price, fee, gain_loss
            FROM transactions
            WHERE user_id = ?
            ORDER BY date ASC, id ASC
            """,
            (user_id,)
        ).fetchall()
        
        return [dict(row) for row in rows]


def get_user_transactions_filtered(
    user_id: int,
    limit: int = 10,
    offset: int = 0,
    type_filter: Optional[str] = None,
    currency_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Get filtered transactions for a specific user with pagination."""
    # Debug entry
    if os.getenv('ENABLE_DEBUG_LOGS'):
        logger.debug(f"get_user_transactions_filtered called with:")
        logger.debug(f"  user_id={user_id}, start_date='{start_date}', end_date='{end_date}'")
        logger.debug(f"  type_filter='{type_filter}', currency_filter='{currency_filter}'")
        logger.debug(f"  limit={limit}, offset={offset}")
    
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        
        # Build the WHERE clause
        where_clauses = ["user_id = ?"]
        params = [user_id]
        
        if type_filter and type_filter.lower() != "both":
            where_clauses.append("type = ?")
            params.append(type_filter.lower())
        
        if currency_filter:
            where_clauses.append("currency = ?")
            params.append(currency_filter.upper())
        
        if start_date and start_date.strip():
            try:
                # Normalize the date format before comparison
                normalized_start = ensure_date_normalized(start_date.strip())
                # Use direct string comparison for better performance and reliability
                # This works because dates are normalized to YYYY-MM-DD format
                where_clauses.append("date >= ?")
                params.append(normalized_start)
                if os.getenv('ENABLE_DEBUG_LOGS') or logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Added start date filter: date >= '{normalized_start}'")
            except ValueError as e:
                error_msg = f"Invalid start date format: {start_date}. Error: {e}"
                logger.warning(error_msg)
                if os.getenv('ENABLE_DEBUG_LOGS') or logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"ERROR: {error_msg}")
                # Skip this filter if date is invalid
        
        if end_date and end_date.strip():
            try:
                # Normalize the date format before comparison
                normalized_end = ensure_date_normalized(end_date.strip())
                # Use direct string comparison for better performance and reliability
                # This works because dates are normalized to YYYY-MM-DD format
                where_clauses.append("date <= ?")
                params.append(normalized_end)
                if os.getenv('ENABLE_DEBUG_LOGS') or logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Added end date filter: date <= '{normalized_end}'")
            except ValueError as e:
                error_msg = f"Invalid end date format: {end_date}. Error: {e}"
                logger.warning(error_msg)
                if os.getenv('ENABLE_DEBUG_LOGS') or logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"ERROR: {error_msg}")
                # Skip this filter if date is invalid
        
        where_clause = " AND ".join(where_clauses)
        
        # Debug logging for date filter issue
        if os.getenv('ENABLE_DEBUG_LOGS'):
            logger.debug(f"WHERE clause built: {where_clause}")
            logger.debug(f"Parameters: {params}")
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Where clause: {where_clause}")
            logger.debug(f"Parameters: {params}")
            logger.debug(f"Date filter values - start: '{start_date}', end: '{end_date}'")
            if start_date and start_date.strip() and 'normalized_start' in locals():
                logger.debug(f"Normalized start date: '{normalized_start}'")
            if end_date and end_date.strip() and 'normalized_end' in locals():
                logger.debug(f"Normalized end date: '{normalized_end}'")
        
        # Additional debug: Check what dates are in the database
        if logger.isEnabledFor(logging.DEBUG) and (start_date or end_date):
            date_check = conn.execute(
                "SELECT DISTINCT date, DATE(date) as date_func FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 5",
                (user_id,)
            ).fetchall()
            logger.debug(f"Sample dates in DB: {[dict(row) for row in date_check]}")
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM transactions
            WHERE {where_clause}
        """
        total = conn.execute(count_query, params).fetchone()["total"]
        if os.getenv('ENABLE_DEBUG_LOGS'):
            logger.debug(f"Total count query result: {total}")
        
        # Get paginated results
        query = f"""
            SELECT id, date, type, currency, amount, price, fee, gain_loss
            FROM transactions
            WHERE {where_clause}
            ORDER BY date DESC, id DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        if os.getenv('ENABLE_DEBUG_LOGS'):
            logger.debug(f"Final SQL query: {query}")
            logger.debug(f"Final query params: {params}")
        
        # Execute and get results
        rows = conn.execute(query, params).fetchall()
        if os.getenv('ENABLE_DEBUG_LOGS'):
            logger.debug(f"Query returned {len(rows)} rows")
            logger.debug(f"Found {len(rows)} transactions")
        
        # Debug: Show first few results
        if os.getenv('ENABLE_DEBUG_LOGS') and rows and (start_date or end_date):
            logger.debug(f"First 3 results: {[dict(row) for row in rows[:3]]}")
        
        # Always show sample dates when date filter is applied
        if os.getenv('ENABLE_DEBUG_LOGS') and (start_date or end_date):
            sample_dates = conn.execute(
                "SELECT DISTINCT date FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 10",
                (user_id,)
            ).fetchall()
            logger.debug(f"Sample dates in DB for user {user_id}: {[row[0] for row in sample_dates]}")
        
        return {
            "transactions": [dict(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset
        }


def get_user_currencies(user_id: int) -> List[str]:
    """Get distinct currencies used in user's transactions."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT currency
            FROM transactions
            WHERE user_id = ?
            ORDER BY currency ASC
            """,
            (user_id,)
        ).fetchall()
        
        return [row[0] for row in rows]


def delete_transaction(user_id: int, transaction_id: int) -> bool:
    """Delete a transaction if it belongs to the specified user."""
    with get_connection() as conn:
        cur = conn.execute(
            """
            DELETE FROM transactions
            WHERE id = ? AND user_id = ?
            """,
            (transaction_id, user_id)
        )
        return cur.rowcount > 0


def update_transaction(
    user_id: int,
    transaction_id: int,
    date: str,
    type: str,
    currency: str,
    amount: float,
    price: float,
    fee: float = 0.0,
    gain_loss: Optional[float] = None
) -> bool:
    """Update a transaction if it belongs to the specified user."""
    # Normalize date to YYYY-MM-DD format
    normalized_date = ensure_date_normalized(date)
    
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE transactions
            SET date = ?, type = ?, currency = ?, amount = ?, price = ?, fee = ?, gain_loss = ?
            WHERE id = ? AND user_id = ?
            """,
            (normalized_date, type, currency, amount, price, fee, gain_loss, transaction_id, user_id)
        )
        return cur.rowcount > 0


def clear_user_transactions(user_id: int) -> None:
    """Clear all transactions for a specific user."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE user_id = ?",
            (user_id,)
        )


def remove_duplicate_transactions(user_id: int) -> int:
    """Remove duplicate transactions for a user, keeping only the oldest (by ID) of each duplicate group."""
    with get_connection() as conn:
        # Find and delete duplicates, keeping the one with the smallest ID
        cur = conn.execute(
            """
            DELETE FROM transactions
            WHERE user_id = ? AND id NOT IN (
                SELECT MIN(id)
                FROM transactions
                WHERE user_id = ?
                GROUP BY date, type, currency, amount, price, fee
            )
            """,
            (user_id, user_id)
        )
        return cur.rowcount


def check_transaction_exists(
    user_id: int,
    date: str,
    type: str,
    currency: str,
    amount: float,
    price: float,
    fee: float = 0.0
) -> bool:
    """Check if a transaction with the same details already exists."""
    # Normalize date to YYYY-MM-DD format
    normalized_date = ensure_date_normalized(date)
    
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) FROM transactions
            WHERE user_id = ? AND date = ? AND type = ? AND currency = ? 
            AND amount = ? AND price = ? AND fee = ?
            """,
            (user_id, normalized_date, type, currency, amount, price, fee)
        ).fetchone()
        return row[0] > 0
