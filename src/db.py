"""SQLite database helpers for user management."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .auth import User

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
        
        # Create transactions table
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
                FOREIGN KEY (user_id) REFERENCES users(id)
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
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO transactions (user_id, date, type, currency, amount, price, fee, gain_loss)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, date, type, currency, amount, price, fee, gain_loss)
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


def clear_user_transactions(user_id: int) -> None:
    """Clear all transactions for a specific user."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE user_id = ?",
            (user_id,)
        )
