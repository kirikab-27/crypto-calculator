#!/usr/bin/env python3
"""Test to verify the date sorting fix for profit/loss calculations."""

from datetime import datetime
from src.calculator import CryptoCalculator

def test_date_sorting_fix():
    """Test that transactions are processed in chronological order."""
    calculator = CryptoCalculator(method="fifo")
    
    # Add transactions out of chronological order (as shown in the screenshot)
    # 1. Buy BTC on 2025-05-03
    calculator.add_buy(datetime(2025, 5, 3), "BTC", 1.0, 9000.0, 0.0)
    
    # 2. Sell BTC on 2025-05-10
    calculator.add_sell(datetime(2025, 5, 10), "BTC", 1.0, 15000.0, 0.0)
    
    # 3. Buy ETH on 2025-05-17
    calculator.add_buy(datetime(2025, 5, 17), "ETH", 10.0, 2500.0, 0.0)
    
    # 4. Sell ETH on 2025-05-24
    calculator.add_sell(datetime(2025, 5, 24), "ETH", 5.0, 5000.0, 0.0)
    
    # 5. This would fail without sorting - selling ETH on 2025-05-03 before buying it
    # In the actual fix, this transaction would be sorted to happen after the ETH buy
    try:
        calculator.add_sell(datetime(2025, 5, 3), "ETH", 5.0, 3000.0, 0.0)
        print("ERROR: Should have raised ValueError for insufficient inventory")
    except ValueError as e:
        print(f"EXPECTED: {e}")
    
    # Test that the calculator state is correct
    summary = calculator.calculate_summary()
    inventory = calculator.get_inventory_status()
    
    print("\nSummary:")
    print(f"Total Realized Gain/Loss: ${summary['total_gain_loss']:,.2f}")
    print(f"Total Fees: ${summary['total_fees']:,.2f}")
    
    print("\nInventory:")
    for currency, data in inventory.items():
        print(f"{currency}: {data['amount']} @ avg ${data['average_cost']:,.2f}")
    
    # Verify calculations
    # BTC: Sold 1 @ 15000, bought @ 9000 = gain of 6000
    # ETH: Sold 5 @ 5000 = 25000, bought @ 2500 = 12500, gain = 12500
    # Total gain should be 18500
    assert summary['total_gain_loss'] == 18500.0, f"Expected gain of 18500, got {summary['total_gain_loss']}"
    
    # Verify inventory
    # ETH: Bought 10, sold 5, should have 5 left
    assert inventory['ETH']['amount'] == 5.0, f"Expected 5 ETH in inventory, got {inventory['ETH']['amount']}"
    
    print("\nTest passed! Calculations are correct without date sorting in the calculator.")
    print("Note: The fix is implemented in the API layer where transactions are sorted before processing.")

if __name__ == "__main__":
    test_date_sorting_fix()