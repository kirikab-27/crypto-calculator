"""CSV import utilities for trade data."""

from typing import Any, Dict, List
import csv
from datetime import datetime
from .calculator import Transaction
from .date_utils import normalize_date_to_string


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


def import_csv(filepath: str, source: str = "generic") -> List[Transaction]:
    """Import CSV file and convert to Transaction objects.
    
    Parameters
    ----------
    filepath : str
        Path to the CSV file
    source : str
        Source exchange ("generic", "binance", "mexc")
        
    Returns
    -------
    List[Transaction]
        List of Transaction objects
    """
    # For now, we'll implement a basic version that handles generic CSV format
    # The CSV should have columns: date, type, currency, amount, price, fee
    transactions: List[Transaction] = []
    
    with open(filepath, newline="", encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle different column name variations
            date_str = row.get('date') or row.get('Date') or row.get('timestamp') or row.get('Timestamp')
            type_str = row.get('type') or row.get('Type') or row.get('side') or row.get('Side')
            currency = row.get('currency') or row.get('Currency') or row.get('symbol') or row.get('Symbol')
            amount_str = row.get('amount') or row.get('Amount') or row.get('quantity') or row.get('Quantity')
            price_str = row.get('price') or row.get('Price')
            fee_str = row.get('fee') or row.get('Fee') or '0'
            
            # Parse date - use our centralized date normalization
            if date_str:
                try:
                    # Normalize to YYYY-MM-DD string format first
                    normalized_date_str = normalize_date_to_string(date_str)
                    # Then convert to datetime object for Transaction
                    date = datetime.strptime(normalized_date_str, "%Y-%m-%d")
                except ValueError as e:
                    print(f"Warning: Could not parse date '{date_str}': {e}")
                    # Skip this row if date is invalid
                    continue
            
            # Normalize type
            if type_str:
                type_str = type_str.lower()
                if type_str not in ['buy', 'sell']:
                    # Map common variations
                    if type_str in ['purchase', 'bought']:
                        type_str = 'buy'
                    elif type_str in ['sale', 'sold']:
                        type_str = 'sell'
            
            # Extract currency symbol from trading pair if needed
            if currency and '/' in currency:
                # Handle pairs like "BTC/USDT"
                currency = currency.split('/')[0]
            
            # Create transaction
            transaction = Transaction(
                date=date,
                type=type_str,
                currency=currency,
                amount=float(amount_str),
                price=float(price_str),
                fee=float(fee_str) if fee_str else 0.0
            )
            transactions.append(transaction)
    
    # Sort transactions by date
    transactions.sort(key=lambda x: x.date)
    
    return transactions
