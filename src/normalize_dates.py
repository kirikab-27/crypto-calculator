#!/usr/bin/env python3
"""Script to normalize all existing transaction dates in the database to YYYY-MM-DD format."""

import sqlite3
from pathlib import Path
from typing import Tuple, List
import sys
import os

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.date_utils import ensure_date_normalized
from src.db import DB_PATH


def get_all_transactions(conn: sqlite3.Connection) -> List[Tuple[int, str]]:
    """Get all transaction IDs and dates from the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, date FROM transactions")
    return cursor.fetchall()


def normalize_transaction_dates(conn: sqlite3.Connection) -> int:
    """Normalize all transaction dates to YYYY-MM-DD format.
    
    Returns the number of transactions that were updated.
    """
    transactions = get_all_transactions(conn)
    updated_count = 0
    errors = []
    
    print(f"Found {len(transactions)} transactions to check...")
    
    for tx_id, date in transactions:
        try:
            # Normalize the date
            normalized_date = ensure_date_normalized(date)
            
            # Only update if the date format changed
            if normalized_date != date:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE transactions SET date = ? WHERE id = ?",
                    (normalized_date, tx_id)
                )
                updated_count += 1
                print(f"Updated transaction {tx_id}: '{date}' -> '{normalized_date}'")
                
        except Exception as e:
            error_msg = f"Error normalizing date for transaction {tx_id} (date: '{date}'): {e}"
            errors.append(error_msg)
            print(f"ERROR: {error_msg}")
    
    # Commit all changes
    conn.commit()
    
    print(f"\nNormalization complete!")
    print(f"Total transactions: {len(transactions)}")
    print(f"Updated: {updated_count}")
    print(f"Already normalized: {len(transactions) - updated_count - len(errors)}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    return updated_count


def create_backup(db_path: Path) -> Path:
    """Create a backup of the database before making changes."""
    backup_path = db_path.with_suffix('.db.backup')
    
    # If backup already exists, add a number
    counter = 1
    while backup_path.exists():
        backup_path = db_path.with_suffix(f'.db.backup{counter}')
        counter += 1
    
    # Copy the database file
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"Created backup at: {backup_path}")
    
    return backup_path


def main():
    """Main function to run the date normalization."""
    if not DB_PATH.exists():
        print(f"Database not found at: {DB_PATH}")
        return 1
    
    print(f"Database path: {DB_PATH}")
    
    # Create a backup first
    try:
        backup_path = create_backup(DB_PATH)
    except Exception as e:
        print(f"Failed to create backup: {e}")
        return 1
    
    # Connect to database and normalize dates
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Show some sample dates before normalization
        print("\nSample dates before normalization:")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT date FROM transactions ORDER BY date DESC LIMIT 10")
        for row in cursor.fetchall():
            print(f"  - '{row[0]}'")
        
        # Perform normalization
        print("\nStarting date normalization...")
        updated = normalize_transaction_dates(conn)
        
        # Show sample dates after normalization
        if updated > 0:
            print("\nSample dates after normalization:")
            cursor.execute("SELECT DISTINCT date FROM transactions ORDER BY date DESC LIMIT 10")
            for row in cursor.fetchall():
                print(f"  - '{row[0]}'")
        
        conn.close()
        
        if updated == 0:
            print("\nNo dates needed normalization. All dates are already in YYYY-MM-DD format.")
            # Remove the backup since no changes were made
            backup_path.unlink()
            print(f"Removed unnecessary backup: {backup_path}")
        
        return 0
        
    except Exception as e:
        print(f"\nError during normalization: {e}")
        print(f"Database backup is available at: {backup_path}")
        return 1


if __name__ == "__main__":
    sys.exit(main())