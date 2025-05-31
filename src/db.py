"""SQLite database helpers for user management."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from .auth import User

DB_PATH = Path(__file__).resolve().parent / "users.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create users table if it does not already exist."""
    with get_connection() as conn:
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
