#!/usr/bin/env python3
"""
Migration script to normalize all date formats in the database to YYYY-MM-DD.
This ensures consistency across all transactions regardless of how they were imported.
"""

import sqlite3
from datetime import datetime
import os
import sys

# Add the parent directory to the path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import get_connection


def parse_date_flexible(date_str: str) -> str:
    """
    Parse various date formats and return normalized YYYY-MM-DD format.
    
    Parameters
    ----------
    date_str : str
        Date string in various formats
        
    Returns
    -------
    str
        Date in YYYY-MM-DD format
    """
    if not date_str:
        raise ValueError("Empty date string")
    
    # If already in correct format, return as is
    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            pass
    
    # Try various formats
    formats = [
        "%Y-%m-%d %H:%M:%S",      # DateTime with seconds
        "%Y-%m-%d %H:%M:%S.%f",   # DateTime with microseconds
        "%Y-%m-%dT%H:%M:%S",      # ISO format with T
        "%Y-%m-%dT%H:%M:%S.%f",   # ISO format with microseconds
        "%Y-%m-%dT%H:%M:%SZ",     # ISO format with Z
        "%Y/%m/%d",               # Slash format
        "%Y/%m/%d %H:%M:%S",      # Slash format with time
        "%d/%m/%Y",               # European format
        "%m/%d/%Y",               # American format
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Try timestamp formats
    try:
        # Check if it's a timestamp
        if date_str.isdigit():
            timestamp = int(date_str)
            # If timestamp is in milliseconds (13 digits)
            if len(date_str) >= 13:
                timestamp = timestamp / 1000
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d")
    except (ValueError, OSError):
        pass
    
    raise ValueError(f"Unable to parse date: {date_str}")


def migrate_dates():
    """Migrate all transaction dates to YYYY-MM-DD format."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        
        # Get all transactions
        print("Fetching all transactions...")
        rows = conn.execute(
            "SELECT id, date FROM transactions"
        ).fetchall()
        
        print(f"Found {len(rows)} transactions to check")
        
        updated_count = 0
        error_count = 0
        already_normalized = 0
        
        for row in rows:
            transaction_id = row['id']
            current_date = row['date']
            
            try:
                # Try to normalize the date
                normalized_date = parse_date_flexible(current_date)
                
                # Only update if the format changed
                if normalized_date != current_date:
                    conn.execute(
                        "UPDATE transactions SET date = ? WHERE id = ?",
                        (normalized_date, transaction_id)
                    )
                    updated_count += 1
                    print(f"  Updated transaction {transaction_id}: '{current_date}' -> '{normalized_date}'")
                else:
                    already_normalized += 1
                    
            except Exception as e:
                error_count += 1
                print(f"  ERROR: Failed to parse date for transaction {transaction_id}: '{current_date}' - {str(e)}")
        
        # Commit all changes
        conn.commit()
        
        print("\nMigration Summary:")
        print(f"  Total transactions: {len(rows)}")
        print(f"  Already normalized: {already_normalized}")
        print(f"  Updated: {updated_count}")
        print(f"  Errors: {error_count}")
        
        # Verify the migration
        print("\nVerifying migration...")
        verify_dates(conn)


def verify_dates(conn):
    """Verify that all dates are now in YYYY-MM-DD format."""
    # Check for any dates that don't match the expected format
    rows = conn.execute("""
        SELECT id, date 
        FROM transactions 
        WHERE length(date) != 10 
           OR substr(date, 5, 1) != '-' 
           OR substr(date, 8, 1) != '-'
           OR DATE(date) IS NULL
    """).fetchall()
    
    if rows:
        print(f"WARNING: Found {len(rows)} transactions with non-standard date formats:")
        for row in rows[:5]:  # Show first 5
            print(f"  ID: {row['id']}, Date: '{row['date']}'")
        if len(rows) > 5:
            print(f"  ... and {len(rows) - 5} more")
    else:
        print("SUCCESS: All dates are now in YYYY-MM-DD format")
    
    # Show sample of dates
    print("\nSample of normalized dates:")
    sample = conn.execute(
        "SELECT DISTINCT date FROM transactions ORDER BY date DESC LIMIT 10"
    ).fetchall()
    for row in sample:
        print(f"  {row['date']}")


if __name__ == "__main__":
    print("Date Format Migration Script")
    print("=" * 50)
    print("This script will normalize all transaction dates to YYYY-MM-DD format.")
    print("It's safe to run multiple times - it will only update dates that need normalization.")
    print()
    
    response = input("Do you want to proceed? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        migrate_dates()
    else:
        print("Migration cancelled.")