#!/usr/bin/env python3
"""Script to normalize all existing transaction dates in the database to YYYY-MM-DD format."""

import sqlite3
from pathlib import Path
from typing import Tuple, List
import sys
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    updates = []  # Batch updates for better performance
    
    logger.info(f"Found {len(transactions)} transactions to check...")
    
    for tx_id, date in transactions:
        try:
            # Normalize the date
            normalized_date = ensure_date_normalized(date)
            
            # Only update if the date format changed
            if normalized_date != date:
                updates.append((normalized_date, tx_id))
                logger.info(f"Will update transaction {tx_id}: '{date}' -> '{normalized_date}'")
                
        except ValueError as e:
            error_msg = f"Invalid date format for transaction {tx_id} (date: '{date}'): {e}"
            errors.append(error_msg)
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error normalizing date for transaction {tx_id} (date: '{date}'): {e}"
            errors.append(error_msg)
            logger.error(error_msg)
    
    # Batch update all changes for better performance
    if updates:
        try:
            cursor = conn.cursor()
            cursor.executemany(
                "UPDATE transactions SET date = ? WHERE id = ?",
                updates
            )
            conn.commit()
            updated_count = len(updates)
            logger.info(f"Successfully updated {updated_count} transactions")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update transactions: {e}")
            raise
    
    logger.info(f"\nNormalization complete!")
    logger.info(f"Total transactions: {len(transactions)}")
    logger.info(f"Updated: {updated_count}")
    logger.info(f"Already normalized: {len(transactions) - updated_count - len(errors)}")
    logger.info(f"Errors: {len(errors)}")
    
    if errors:
        logger.warning("\nErrors encountered:")
        for error in errors:
            logger.warning(f"  - {error}")
    
    return updated_count


def create_backup(db_path: Path) -> Path:
    """Create a backup of the database before making changes."""
    # Include timestamp in backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_suffix(f'.db.backup_{timestamp}')
    
    # If backup already exists (unlikely with timestamp), add a number
    counter = 1
    while backup_path.exists():
        backup_path = db_path.with_suffix(f'.db.backup_{timestamp}_{counter}')
        counter += 1
    
    # Copy the database file
    import shutil
    shutil.copy2(db_path, backup_path)
    logger.info(f"Created backup at: {backup_path}")
    
    return backup_path


def main():
    """Main function to run the date normalization."""
    if not DB_PATH.exists():
        logger.error(f"Database not found at: {DB_PATH}")
        return 1
    
    logger.info(f"Database path: {DB_PATH}")
    
    # Create a backup first
    try:
        backup_path = create_backup(DB_PATH)
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return 1
    
    # Connect to database and normalize dates
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Show some sample dates before normalization
        logger.info("\nSample dates before normalization:")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT date FROM transactions ORDER BY date DESC LIMIT 10")
        for row in cursor.fetchall():
            logger.info(f"  - '{row[0]}'")
        
        # Perform normalization
        logger.info("\nStarting date normalization...")
        updated = normalize_transaction_dates(conn)
        
        # Show sample dates after normalization
        if updated > 0:
            logger.info("\nSample dates after normalization:")
            cursor.execute("SELECT DISTINCT date FROM transactions ORDER BY date DESC LIMIT 10")
            for row in cursor.fetchall():
                logger.info(f"  - '{row[0]}'")
        
        conn.close()
        
        if updated == 0:
            logger.info("\nNo dates needed normalization. All dates are already in YYYY-MM-DD format.")
            # Remove the backup since no changes were made
            backup_path.unlink()
            logger.info(f"Removed unnecessary backup: {backup_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"\nError during normalization: {e}")
        logger.error(f"Database backup is available at: {backup_path}")
        return 1


if __name__ == "__main__":
    sys.exit(main())