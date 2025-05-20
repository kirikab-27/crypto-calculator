import requests
from crypto_calculator.mexc import MEXCClient


class MockResp:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self) -> None:
        pass

    def json(self):
        return self.data


def test_get_mexc_trade_history(monkeypatch):
    sample_json = [
        {
            "id": 200,
            "symbol": "ETHUSDT",
            "quantity": "1.5",
            "price": "2000.0",
            "timestamp": 1609459200000,
        }
    ]

    def mock_get(url, params=None, headers=None, timeout=10):
        return MockResp(sample_json)

    monkeypatch.setenv("MEXC_API_KEY", "key")
    monkeypatch.setenv("MEXC_API_SECRET", "secret")
    monkeypatch.setattr(requests, "get", mock_get)

    client = MEXCClient()
    trades = client.get_trade_history("ETHUSDT")
    assert trades == [
        {
            "id": 200,
            "symbol": "ETHUSDT",
            "amount": 1.5,
            "price": 2000.0,
            "timestamp": 1609459200000,
        }
    ]
