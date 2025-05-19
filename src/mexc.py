"""MEXC REST API client."""

from dataclasses import dataclass, field
from typing import Any, Dict, List
import os
import time
import hmac
import hashlib
from urllib.parse import urlencode
import requests

BASE_URL = "https://api.mexc.com"
API_KEY_ENV = "MEXC_API_KEY"
API_SECRET_ENV = "MEXC_API_SECRET"
RATE_LIMIT = 1000  # requests per minute


@dataclass
class MEXCClient:
    """Minimal MEXC API client."""

    api_key: str = field(default_factory=lambda: os.getenv(API_KEY_ENV, ""))
    api_secret: str = field(default_factory=lambda: os.getenv(API_SECRET_ENV, ""))

    def authenticate(self) -> bool:
        """Validate API credentials."""
        return bool(self.api_key and self.api_secret)

    def get_trade_history(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch trade history from MEXC and normalise the result."""

        if not self.authenticate():
            raise ValueError("Invalid API credentials")

        timestamp = int(time.time() * 1000)
        params = {"symbol": symbol, "timestamp": timestamp}
        query = urlencode(params)
        signature = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        params["signature"] = signature
        headers = {"X-MEXC-APIKEY": self.api_key}

        response = requests.get(f"{BASE_URL}/api/v3/private/trades", params=params, headers=headers, timeout=10)
        response.raise_for_status()

        raw_response = response.json()
        trades: List[Dict[str, Any]] = []
        for trade in raw_response:
            trades.append(
                {
                    "id": trade.get("id"),
                    "symbol": trade.get("symbol"),
                    "amount": float(trade.get("quantity")),
                    "price": float(trade.get("price")),
                    "timestamp": int(trade.get("timestamp")),
                }
            )
        return trades
