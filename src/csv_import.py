"""CSV import utilities for trade data."""

from typing import Any, Dict, List
import csv


def read_trades_from_csv(filepath: str) -> List[Dict[str, Any]]:
    """Read trade history from a CSV file.

    The CSV is expected to have the following columns: ``id``, ``symbol``,
    ``amount``, ``price``, ``timestamp`` and optionally ``side``. Column names
    are case-insensitive.
    """
    trades: List[Dict[str, Any]] = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trade: Dict[str, Any] = {
                "id": int(row["id"]),
                "symbol": row["symbol"],
                "amount": float(row["amount"]),
                "price": float(row["price"]),
                "timestamp": int(row["timestamp"]),
            }
            if "side" in row and row["side"]:
                trade["side"] = row["side"]
            trades.append(trade)
    return trades
