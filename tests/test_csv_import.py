import tempfile
from crypto_calculator.csv_import import read_trades_from_csv


def test_read_trades_from_csv():
    data = """id,symbol,amount,price,timestamp,side
1,BTCUSDT,0.1,30000,1609459200000,buy
2,BTCUSDT,-0.1,31000,1609462800000,sell
"""
    with tempfile.NamedTemporaryFile('w+', delete=False) as f:
        f.write(data)
        f.flush()
        trades = read_trades_from_csv(f.name)

    assert trades == [
        {
            "id": 1,
            "symbol": "BTCUSDT",
            "amount": 0.1,
            "price": 30000.0,
            "timestamp": 1609459200000,
            "side": "buy",
        },
        {
            "id": 2,
            "symbol": "BTCUSDT",
            "amount": -0.1,
            "price": 31000.0,
            "timestamp": 1609462800000,
            "side": "sell",
        },
    ]


