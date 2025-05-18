from crypto_calculator import calculate_pnl
import pytest


def test_calculate_fifo_and_lifo():
    trades = [
        {"id": 1, "symbol": "BTCUSDT", "amount": 1.0, "price": 100.0, "timestamp": 1, "side": "buy"},
        {"id": 2, "symbol": "BTCUSDT", "amount": 1.0, "price": 200.0, "timestamp": 2, "side": "buy"},
        {"id": 3, "symbol": "BTCUSDT", "amount": 1.5, "price": 300.0, "timestamp": 3, "side": "sell"},
    ]

    fifo_pnl = calculate_pnl(trades, method="FIFO")
    lifo_pnl = calculate_pnl(trades, method="LIFO")

    assert fifo_pnl == 250.0
    assert lifo_pnl == 200.0


def test_calculate_with_implicit_side_and_insufficient_inventory():
    trades = [
        {"id": 10, "symbol": "ETHUSDT", "amount": 1.0, "price": 1000.0, "timestamp": 1},  # buy inferred
        {"id": 11, "symbol": "ETHUSDT", "amount": -2.0, "price": 1100.0, "timestamp": 2},  # sell inferred
    ]

    with pytest.raises(ValueError):
        calculate_pnl(trades, method="FIFO")
