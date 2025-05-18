# coding: utf-8
"""Profit and loss calculation helpers.

This module implements FIFO and LIFO cost basis methods as defined in the
requirements document. FIFO (先入先出法) means "最初に取得した資産が最初に処分されるという在庫評価方法" and
LIFO (後入先出法) means "最後に取得した資産が最初に処分されるという在庫評価方法".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Trade:
    """Normalised trade record.

    Parameters
    ----------
    id : int
        Unique identifier from the exchange.
    symbol : str
        Trading pair symbol.
    amount : float
        Quantity of the asset. Positive value represents a buy and negative
        value represents a sell if ``side`` is not explicitly provided.
    price : float
        Trade price denominated in quote currency.
    timestamp : int
        Unix timestamp in milliseconds.
    side : str | None
        Optional trade side ("buy" or "sell"). If not provided the side is
        determined from the sign of ``amount``.
    """

    id: int
    symbol: str
    amount: float
    price: float
    timestamp: int
    side: str | None = None

    def resolved_side(self) -> str:
        if self.side:
            return self.side.lower()
        return "buy" if self.amount >= 0 else "sell"

    def abs_amount(self) -> float:
        return abs(self.amount)


def _apply_sale(inventory: List[Dict[str, float]], amount: float, price: float, *, fifo: bool) -> float:
    """Apply a sale to the inventory and return realised profit or loss."""
    realised = 0.0
    qty_to_sell = amount
    while qty_to_sell > 0:
        if not inventory:
            raise ValueError("Insufficient inventory for sale")
        item = inventory[0] if fifo else inventory[-1]
        qty = min(item["amount"], qty_to_sell)
        realised += qty * (price - item["price"])
        item["amount"] -= qty
        qty_to_sell -= qty
        if item["amount"] == 0:
            if fifo:
                inventory.pop(0)
            else:
                inventory.pop()
    return realised


def calculate_pnl(trades: List[Dict[str, object]], method: str = "FIFO") -> float:
    """Calculate realised profit/loss for a list of trades.

    Trades should be dictionaries compatible with the data output by the data
    retrieval modules. The following keys are expected: ``amount``, ``price``,
    ``timestamp`` and optionally ``side``. When ``side`` is omitted a positive
    ``amount`` is treated as a buy and a negative value as a sell.

    Parameters
    ----------
    trades : List[Dict[str, object]]
        Normalised trade dictionaries.
    method : str
        Calculation method either ``"FIFO"`` or ``"LIFO"``.

    Returns
    -------
    float
        The total realised profit or loss.
    """
    fifo = method.upper() == "FIFO"
    inventory: List[Dict[str, float]] = []  # each item: {"amount": float, "price": float}
    realised = 0.0
    for raw in sorted(trades, key=lambda x: x["timestamp"]):
        trade = Trade(**raw) if not isinstance(raw, Trade) else raw
        side = trade.resolved_side()
        amount = trade.abs_amount()
        if side == "buy":
            inventory.append({"amount": amount, "price": trade.price})
        elif side == "sell":
            realised += _apply_sale(inventory, amount, trade.price, fifo=fifo)
        else:
            raise ValueError(f"Unknown side: {side}")
    return realised
