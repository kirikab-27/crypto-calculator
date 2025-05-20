import requests
from crypto_calculator.binance import BinanceClient


class MockResp:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self) -> None:
        pass

    def json(self):
        return self.data


def test_get_binance_trade_history(monkeypatch):
    sample_json = [
        {
            "id": 100,
            "symbol": "BTCUSDT",
            "qty": "0.1",
            "price": "30000.0",
            "time": 1609459200000,
        }
    ]

    def mock_get(url, params=None, headers=None, timeout=10):
        return MockResp(sample_json)

    monkeypatch.setenv("BINANCE_API_KEY", "key")
    monkeypatch.setenv("BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(requests, "get", mock_get)

    client = BinanceClient()
    trades = client.get_trade_history("BTCUSDT")
    assert trades == [
        {
            "id": 100,
            "symbol": "BTCUSDT",
            "amount": 0.1,
            "price": 30000.0,
            "timestamp": 1609459200000,
        }
    ]
