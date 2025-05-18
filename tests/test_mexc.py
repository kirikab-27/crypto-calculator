from crypto_calculator.mexc import MEXCClient


def test_parse_mexc_trade_history():
    client = MEXCClient()
    sample_response = [
        {
            "id": 200,
            "symbol": "ETHUSDT",
            "quantity": "1.5",
            "price": "2000.0",
            "timestamp": 1609459200000,
        }
    ]
    trades = client.get_trade_history(sample_response)
    assert trades == [
        {
            "id": 200,
            "symbol": "ETHUSDT",
            "amount": 1.5,
            "price": 2000.0,
            "timestamp": 1609459200000,
        }
    ]
