#!/usr/bin/env python3
"""Test script to identify and fix the date filtering issue."""

import sqlite3
from datetime import datetime

def test_date_filtering_bug():
    """Test to reproduce and understand the date filtering bug."""
    
    # Create in-memory test database
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    # Create transactions table
    conn.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            currency TEXT NOT NULL,
            amount REAL NOT NULL,
            price REAL NOT NULL,
            user_id INTEGER DEFAULT 1
        )
    """)
    
    # Insert test data matching the screenshot
    test_transactions = [
        ("2025-06-21", "SELL", "BTC", 2, 40000.00),
        ("2025-06-01", "BUY", "BTC", 1, 9000.00),
        ("2025-05-17", "SELL", "BTC", 3, 20000.00),
        ("2025-05-10", "BUY", "BTC", 5, 30000.00),
        ("2025-03-03", "BUY", "ETH", 2, 2500.00),
        ("2025-03-02", "SELL", "BTC", 0.2, 42000.00),
        ("2025-02-03", "BUY", "ETH", 2, 2500.00),
        ("2025-02-02", "SELL", "BTC", 0.2, 42000.00),
        ("2025-01-02", "SELL", "BTC", 0.2, 42000.00),
        ("2025-01-01", "BUY", "BTC", 0.5, 40000.00),
    ]
    
    for date, tx_type, currency, amount, price in test_transactions:
        conn.execute(
            "INSERT INTO transactions (date, type, currency, amount, price) VALUES (?, ?, ?, ?, ?)",
            (date, tx_type, currency, amount, price)
        )
    
    # Test different date formats that might be causing issues
    print("=== Testing Different Date Storage Formats ===")
    
    # Test 1: Check what's actually in the database
    print("\n1. All transactions in database:")
    all_txs = conn.execute("SELECT id, date, type, currency FROM transactions ORDER BY date DESC").fetchall()
    for tx in all_txs:
        print(f"   ID: {tx['id']}, Date: {tx['date']}, Type: {tx['type']}, Currency: {tx['currency']}")
    
    # Test 2: Apply the exact filter from the screenshot
    start_date = "2025-06-01"
    end_date = "2025-06-26"
    
    print(f"\n2. Filtering from {start_date} to {end_date} (using DATE() function):")
    filtered_query = """
        SELECT id, date, type, currency 
        FROM transactions 
        WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
        ORDER BY date DESC
    """
    filtered_txs = conn.execute(filtered_query, (start_date, end_date)).fetchall()
    for tx in filtered_txs:
        print(f"   ID: {tx['id']}, Date: {tx['date']}, Type: {tx['type']}, Currency: {tx['currency']}")
    print(f"   Found {len(filtered_txs)} transactions (Expected: 2)")
    
    # Test 3: Check if the issue is with the DATE() function
    print("\n3. Testing DATE() function behavior:")
    date_tests = [
        "2025-06-01",
        "2025/06/01", 
        "2025-06-01 00:00:00",
        "",
        None
    ]
    for test_date in date_tests:
        result = conn.execute("SELECT DATE(?) as parsed", (test_date,)).fetchone()
        print(f"   DATE('{test_date}') = {result['parsed']}")
    
    # Test 4: Test with different parameter types
    print("\n4. Testing with empty string parameters (potential bug):")
    
    # Empty start date
    empty_start_query = """
        SELECT COUNT(*) as count
        FROM transactions 
        WHERE (? = '' OR DATE(date) >= DATE(?)) 
          AND DATE(date) <= DATE(?)
    """
    result = conn.execute(empty_start_query, ("", "", end_date)).fetchone()
    print(f"   Empty start date: {result['count']} transactions")
    
    # Test 5: Check the actual filtering logic from db.py
    print("\n5. Testing the exact logic from db.py:")
    
    # Build WHERE clause as in the actual code
    where_clauses = ["user_id = ?"]
    params = [1]
    
    if start_date and start_date.strip():
        where_clauses.append("DATE(date) >= DATE(?)")
        params.append(start_date.strip())
    
    if end_date and end_date.strip():
        where_clauses.append("DATE(date) <= DATE(?)")
        params.append(end_date.strip())
    
    where_clause = " AND ".join(where_clauses)
    query = f"""
        SELECT id, date, type, currency
        FROM transactions
        WHERE {where_clause}
        ORDER BY date DESC
    """
    
    print(f"   Query: {query}")
    print(f"   Params: {params}")
    
    results = conn.execute(query, params).fetchall()
    print(f"   Results: {len(results)} transactions")
    for tx in results:
        print(f"     ID: {tx['id']}, Date: {tx['date']}")
    
    # Test 6: Check if it's a timezone or time component issue
    print("\n6. Testing with time components:")
    
    # Clear and insert dates with times
    conn.execute("DELETE FROM transactions")
    
    datetime_transactions = [
        ("2025-06-21 10:30:00", "SELL", "BTC"),
        ("2025-06-01 14:20:00", "BUY", "BTC"),
        ("2025-05-17 09:15:00", "SELL", "BTC"),
        ("2025-03-03 11:00:00", "BUY", "ETH"),
    ]
    
    for date, tx_type, currency in datetime_transactions:
        conn.execute(
            "INSERT INTO transactions (date, type, currency, amount, price) VALUES (?, ?, ?, 1, 1000)",
            (date, tx_type, currency)
        )
    
    datetime_results = conn.execute(filtered_query, (start_date, end_date)).fetchall()
    print(f"   With datetime strings: {len(datetime_results)} results")
    for tx in datetime_results:
        print(f"     Date: {tx['date']}, DATE(date): {conn.execute('SELECT DATE(?)', (tx['date'],)).fetchone()[0]}")
    
    # Test 7: Check for potential SQL injection or escaping issues
    print("\n7. Testing with different date formats from frontend:")
    frontend_formats = [
        ("2025-06-01", "2025-06-26"),  # Standard
        ("2025/06/01", "2025/06/26"),  # With slashes (as shown in UI)
    ]
    
    for start, end in frontend_formats:
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM transactions WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)",
            (start, end)
        ).fetchone()['cnt']
        print(f"   Format {start} to {end}: {count} results")
    
    conn.close()
    
    print("\n=== Potential Issues Found ===")
    print("1. If DATE() returns NULL for invalid formats, comparisons fail")
    print("2. Empty string parameters might bypass filters")
    print("3. Frontend might be sending dates in wrong format")
    print("\nRecommended fix: Check frontend is sending correct format and handle empty strings properly")

if __name__ == "__main__":
    test_date_filtering_bug()