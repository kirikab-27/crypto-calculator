#!/usr/bin/env python3
"""Debug script to test date filtering logic."""

import sqlite3
from datetime import datetime

# Test data with the dates from the screenshot
test_dates = [
    ("2025-06-21", "SELL", "BTC"),
    ("2025-06-01", "BUY", "BTC"),
    ("2025-05-17", "SELL", "BTC"),
    ("2025-05-10", "BUY", "BTC"),
    ("2025-03-03", "BUY", "ETH"),
]

# Also test with datetime formats
test_dates_with_time = [
    ("2025-06-21 10:30:00", "SELL", "BTC"),
    ("2025-06-01 14:20:00", "BUY", "BTC"),
    ("2025-05-17 09:15:00", "SELL", "BTC"),
    ("2025-05-10 16:45:00", "BUY", "BTC"),
    ("2025-03-03 11:00:00", "BUY", "ETH"),
]

# Create test database
conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row

# Create simplified table
conn.execute("""
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        currency TEXT NOT NULL
    )
""")

# Insert test data
for date, tx_type, currency in test_dates:
    conn.execute(
        "INSERT INTO transactions (date, type, currency) VALUES (?, ?, ?)",
        (date, tx_type, currency)
    )

# Test date filtering
start_date = "2025-06-01"
end_date = "2025-06-30"

print(f"\nTesting date filter: From {start_date} to {end_date}")
print("=" * 60)

# Test 1: Basic date comparison
print("\nTest 1: Basic string comparison")
query1 = """
    SELECT id, date, type, currency
    FROM transactions
    WHERE date >= ? AND date <= ?
    ORDER BY date DESC
"""
rows1 = conn.execute(query1, (start_date, end_date)).fetchall()
for row in rows1:
    print(f"  {dict(row)}")

# Test 2: Using DATE() function (current implementation)
print("\nTest 2: Using DATE() function")
query2 = """
    SELECT id, date, type, currency
    FROM transactions
    WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
    ORDER BY date DESC
"""
rows2 = conn.execute(query2, (start_date, end_date)).fetchall()
for row in rows2:
    print(f"  {dict(row)}")

# Test 3: Check what DATE() returns
print("\nTest 3: DATE() function output")
query3 = """
    SELECT date, DATE(date) as date_func_result
    FROM transactions
"""
rows3 = conn.execute(query3).fetchall()
for row in rows3:
    print(f"  Original: {row['date']}, DATE(): {row['date_func_result']}")

# Test 4: Test with different date formats
print("\nTest 4: Testing various date formats")
test_formats = [
    "2025-06-01",
    "2025/06/01",
    "2025-06-01 00:00:00",
    "2025-06-01T00:00:00",
]
for fmt in test_formats:
    result = conn.execute("SELECT DATE(?) as parsed", (fmt,)).fetchone()
    print(f"  DATE('{fmt}') = {result['parsed']}")

# Test 5: Test with datetime strings in database
print("\nTest 5: Testing with datetime strings in database")
# Clear table
conn.execute("DELETE FROM transactions")

# Insert datetime strings
for date, tx_type, currency in test_dates_with_time:
    conn.execute(
        "INSERT INTO transactions (date, type, currency) VALUES (?, ?, ?)",
        (date, tx_type, currency)
    )

# Test filtering with datetime strings
rows = conn.execute(query2, (start_date, end_date)).fetchall()
print(f"  Date filter results with datetime strings:")
for row in rows:
    print(f"    {dict(row)}")

# Test 6: Check edge cases
print("\nTest 6: Edge case - exact date match")
exact_date = "2025-06-01"
rows = conn.execute(
    "SELECT * FROM transactions WHERE DATE(date) = DATE(?)",
    (exact_date,)
).fetchall()
print(f"  Transactions on exactly {exact_date}:")
for row in rows:
    print(f"    {dict(row)}")

conn.close()