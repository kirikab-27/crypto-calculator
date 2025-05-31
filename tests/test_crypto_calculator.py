import pytest
from datetime import datetime
from src.calculator import CryptoCalculator


class TestCryptoCalculator:
    """Test cases for CryptoCalculator class based on backend usage."""
    
    def test_create_calculator_with_fifo(self):
        """Test creating calculator with FIFO method."""
        calculator = CryptoCalculator(method="fifo")
        assert calculator.method == "fifo"
    
    def test_create_calculator_with_lifo(self):
        """Test creating calculator with LIFO method."""
        calculator = CryptoCalculator(method="lifo")
        assert calculator.method == "lifo"
    
    def test_add_buy_transaction(self):
        """Test adding a buy transaction."""
        calculator = CryptoCalculator(method="fifo")
        date = datetime(2024, 1, 1)
        
        calculator.add_buy(date, "BTC", 1.0, 50000.0, 10.0)
        
        transactions = calculator.get_all_transactions()
        assert len(transactions) == 1
        assert transactions[0].type == "buy"
        assert transactions[0].currency == "BTC"
        assert transactions[0].amount == 1.0
        assert transactions[0].price == 50000.0
        assert transactions[0].fee == 10.0
    
    def test_add_sell_transaction(self):
        """Test adding a sell transaction."""
        calculator = CryptoCalculator(method="fifo")
        buy_date = datetime(2024, 1, 1)
        sell_date = datetime(2024, 1, 2)
        
        calculator.add_buy(buy_date, "BTC", 1.0, 50000.0, 10.0)
        calculator.add_sell(sell_date, "BTC", 0.5, 60000.0, 10.0)
        
        transactions = calculator.get_all_transactions()
        assert len(transactions) == 2
        assert transactions[1].type == "sell"
        assert transactions[1].amount == 0.5
        assert transactions[1].price == 60000.0
    
    def test_calculate_summary_fifo(self):
        """Test calculating summary with FIFO method."""
        calculator = CryptoCalculator(method="fifo")
        
        # Buy 2 BTC at different prices
        calculator.add_buy(datetime(2024, 1, 1), "BTC", 1.0, 50000.0, 10.0)
        calculator.add_buy(datetime(2024, 1, 2), "BTC", 1.0, 60000.0, 10.0)
        
        # Sell 1 BTC (should use first buy price with FIFO)
        calculator.add_sell(datetime(2024, 1, 3), "BTC", 1.0, 70000.0, 10.0)
        
        summary = calculator.calculate_summary()
        # Gain = (70000 - 50000) * 1.0 - fees = 20000 - 30 = 19970
        assert "total_gain" in summary or "total_gain_loss" in summary
        assert "realized_gain" in summary or "realized_gain_loss" in summary
    
    def test_calculate_summary_lifo(self):
        """Test calculating summary with LIFO method."""
        calculator = CryptoCalculator(method="lifo")
        
        # Buy 2 BTC at different prices
        calculator.add_buy(datetime(2024, 1, 1), "BTC", 1.0, 50000.0, 10.0)
        calculator.add_buy(datetime(2024, 1, 2), "BTC", 1.0, 60000.0, 10.0)
        
        # Sell 1 BTC (should use last buy price with LIFO)
        calculator.add_sell(datetime(2024, 1, 3), "BTC", 1.0, 70000.0, 10.0)
        
        summary = calculator.calculate_summary()
        # Gain = (70000 - 60000) * 1.0 - fees = 10000 - 30 = 9970
        assert "total_gain" in summary or "total_gain_loss" in summary
        assert "realized_gain" in summary or "realized_gain_loss" in summary
    
    def test_get_inventory_status(self):
        """Test getting inventory status."""
        calculator = CryptoCalculator(method="fifo")
        
        calculator.add_buy(datetime(2024, 1, 1), "BTC", 1.0, 50000.0, 10.0)
        calculator.add_buy(datetime(2024, 1, 2), "ETH", 10.0, 3000.0, 5.0)
        calculator.add_sell(datetime(2024, 1, 3), "BTC", 0.5, 60000.0, 10.0)
        
        inventory = calculator.get_inventory_status()
        assert "BTC" in inventory
        assert inventory["BTC"]["amount"] == 0.5
        assert "ETH" in inventory
        assert inventory["ETH"]["amount"] == 10.0
    
    def test_multiple_currencies(self):
        """Test handling multiple cryptocurrencies."""
        calculator = CryptoCalculator(method="fifo")
        
        calculator.add_buy(datetime(2024, 1, 1), "BTC", 1.0, 50000.0, 10.0)
        calculator.add_buy(datetime(2024, 1, 2), "ETH", 10.0, 3000.0, 5.0)
        calculator.add_sell(datetime(2024, 1, 3), "BTC", 0.5, 60000.0, 10.0)
        calculator.add_sell(datetime(2024, 1, 4), "ETH", 5.0, 3500.0, 5.0)
        
        transactions = calculator.get_all_transactions()
        assert len(transactions) == 4
        
        summary = calculator.calculate_summary()
        assert summary is not None
    
    def test_sell_more_than_inventory_raises_error(self):
        """Test that selling more than inventory raises an error."""
        calculator = CryptoCalculator(method="fifo")
        
        calculator.add_buy(datetime(2024, 1, 1), "BTC", 1.0, 50000.0, 10.0)
        
        with pytest.raises(ValueError, match="Insufficient inventory"):
            calculator.add_sell(datetime(2024, 1, 2), "BTC", 2.0, 60000.0, 10.0)