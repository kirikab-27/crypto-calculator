# coding: utf-8
"""Profit and loss calculation helpers.

This module implements FIFO and LIFO cost basis methods as defined in the
requirements document. FIFO (先入先出法) means "最初に取得した資産が最初に処分されるという在庫評価方法" and
LIFO (後入先出法) means "最後に取得した資産が最初に処分されるという在庫評価方法".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


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


@dataclass
class Transaction:
    """Represents a transaction for the CryptoCalculator."""
    date: datetime
    type: str  # "buy" or "sell"
    currency: str
    amount: float
    price: float
    fee: float
    gain_loss: Optional[float] = None


class CryptoCalculator:
    """Calculator for cryptocurrency gains and losses using FIFO or LIFO method."""
    
    def __init__(self, method: str = "fifo"):
        """Initialize calculator with the specified method.
        
        Parameters
        ----------
        method : str
            Calculation method either "fifo" or "lifo".
        """
        self.method = method.lower()
        if self.method not in ["fifo", "lifo"]:
            raise ValueError(f"Invalid method: {method}. Must be 'fifo' or 'lifo'")
        
        self.transactions: List[Transaction] = []
        self.inventory: Dict[str, List[Dict[str, float]]] = {}  # currency -> [{"amount": float, "price": float}]
        self.realized_gains: Dict[str, float] = {}  # currency -> total realized gain/loss
    
    def add_buy(self, date: datetime, currency: str, amount: float, price: float, fee: float = 0.0):
        """Add a buy transaction.
        
        Parameters
        ----------
        date : datetime
            Transaction date
        currency : str
            Cryptocurrency symbol (e.g., "BTC", "ETH")
        amount : float
            Amount bought
        price : float
            Price per unit
        fee : float
            Transaction fee
        """
        tx = Transaction(
            date=date,
            type="buy",
            currency=currency,
            amount=amount,
            price=price,
            fee=fee
        )
        self.transactions.append(tx)
        
        # Add to inventory
        if currency not in self.inventory:
            self.inventory[currency] = []
        self.inventory[currency].append({"amount": amount, "price": price})
    
    def add_sell(self, date: datetime, currency: str, amount: float, price: float, fee: float = 0.0):
        """Add a sell transaction and calculate gain/loss.
        
        Parameters
        ----------
        date : datetime
            Transaction date
        currency : str
            Cryptocurrency symbol (e.g., "BTC", "ETH")
        amount : float
            Amount sold
        price : float
            Price per unit
        fee : float
            Transaction fee
        """
        if currency not in self.inventory:
            raise ValueError(f"Insufficient inventory for {currency}")
        
        # Calculate gain/loss using FIFO or LIFO
        gain_loss = self._calculate_gain_loss(currency, amount, price, fee)
        
        tx = Transaction(
            date=date,
            type="sell",
            currency=currency,
            amount=amount,
            price=price,
            fee=fee,
            gain_loss=gain_loss
        )
        self.transactions.append(tx)
        
        # Update realized gains
        if currency not in self.realized_gains:
            self.realized_gains[currency] = 0.0
        self.realized_gains[currency] += gain_loss
    
    def _calculate_gain_loss(self, currency: str, amount: float, sell_price: float, fee: float) -> float:
        """Calculate gain/loss for a sell transaction."""
        inventory = self.inventory.get(currency, [])
        if not inventory:
            raise ValueError(f"Insufficient inventory for {currency}")
        
        total_cost = 0.0
        remaining_amount = amount
        
        while remaining_amount > 0:
            if not inventory:
                raise ValueError(f"Insufficient inventory for {currency}")
            
            # Get lot based on method (FIFO or LIFO)
            if self.method == "fifo":
                lot = inventory[0]
                lot_index = 0
            else:  # LIFO
                lot = inventory[-1]
                lot_index = -1
            
            # Calculate amount from this lot
            lot_amount = min(lot["amount"], remaining_amount)
            total_cost += lot_amount * lot["price"]
            
            # Update lot
            lot["amount"] -= lot_amount
            remaining_amount -= lot_amount
            
            # Remove empty lot
            if lot["amount"] == 0:
                inventory.pop(lot_index)
        
        # Calculate gain/loss (revenue - cost - fees)
        revenue = amount * sell_price
        gain_loss = revenue - total_cost - fee
        
        return gain_loss
    
    def get_all_transactions(self) -> List[Transaction]:
        """Get all transactions."""
        return self.transactions
    
    def calculate_summary(self) -> Dict[str, float]:
        """Calculate summary of gains/losses.
        
        Returns
        -------
        dict
            Summary containing total gains/losses and other metrics.
        """
        total_realized_gain = sum(self.realized_gains.values())
        total_fees = sum(tx.fee for tx in self.transactions)
        
        # Calculate unrealized gains (current inventory value)
        total_cost_basis = 0.0
        for currency, lots in self.inventory.items():
            for lot in lots:
                total_cost_basis += lot["amount"] * lot["price"]
        
        return {
            "total_gain_loss": total_realized_gain,
            "realized_gain_loss": total_realized_gain,
            "total_fees": total_fees,
            "inventory_cost_basis": total_cost_basis,
            "currencies": list(self.realized_gains.keys())
        }
    
    def get_inventory_status(self) -> Dict[str, Dict[str, float]]:
        """Get current inventory status.
        
        Returns
        -------
        dict
            Dictionary mapping currency to inventory details.
        """
        status = {}
        
        for currency, lots in self.inventory.items():
            total_amount = sum(lot["amount"] for lot in lots)
            if total_amount > 0:
                # Calculate average cost
                total_cost = sum(lot["amount"] * lot["price"] for lot in lots)
                avg_cost = total_cost / total_amount if total_amount > 0 else 0
                
                status[currency] = {
                    "amount": total_amount,
                    "average_cost": avg_cost,
                    "total_cost": total_cost
                }
        
        return status
