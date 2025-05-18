from crypto_calculator.binance import BinanceClient


def test_parse_binance_trade_history():
    client = BinanceClient()
    sample_response = [
        {
            "id": 100,
            "symbol": "BTCUSDT",
            "qty": "0.1",
            "price": "30000.0",
            "time": 1609459200000,
        }
    ]
    trades = client.get_trade_history(sample_response)
    assert trades == [
        {
            "id": 100,
            "symbol": "BTCUSDT",
            "amount": 0.1,
            "price": 30000.0,
            "timestamp": 1609459200000,
        }
    ]
