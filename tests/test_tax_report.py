# coding: utf-8
"""Tests for tax summary report generation."""

import pytest
from datetime import datetime
from src.tax_report import TaxReportGenerator, TaxSummaryReport, generate_tax_summary_report
from src.db import init_db, add_transaction, clear_user_transactions, create_user


@pytest.fixture
def setup_test_db():
    """Set up test database."""
    init_db()
    yield
    # Cleanup happens automatically with test database


@pytest.fixture
def test_user(setup_test_db):
    """Create a test user."""
    return create_user("test_tax_user", "password123")


@pytest.fixture
def sample_transactions():
    """Create sample transaction data."""
    return [
        {
            "date": "2024-01-15",
            "type": "buy",
            "currency": "BTC",
            "amount": 0.5,
            "price": 30000,
            "fee": 50
        },
        {
            "date": "2024-02-20",
            "type": "buy",
            "currency": "ETH",
            "amount": 5.0,
            "price": 2000,
            "fee": 30
        },
        {
            "date": "2024-03-10",
            "type": "sell",
            "currency": "BTC",
            "amount": 0.3,
            "price": 35000,
            "fee": 40
        },
        {
            "date": "2024-04-15",
            "type": "sell",
            "currency": "ETH",
            "amount": 2.0,
            "price": 2500,
            "fee": 25
        },
        {
            "date": "2024-05-20",
            "type": "buy",
            "currency": "BTC",
            "amount": 0.2,
            "price": 40000,
            "fee": 30
        },
        {
            "date": "2024-06-25",
            "type": "sell",
            "currency": "BTC",
            "amount": 0.1,
            "price": 45000,
            "fee": 20
        }
    ]


def test_tax_report_generator_basic(sample_transactions):
    """Test basic tax report generation."""
    generator = TaxReportGenerator(sample_transactions, method="FIFO")
    report = generator.generate_report()
    
    assert isinstance(report, TaxSummaryReport)
    assert report.calculation_method == "FIFO"
    assert report.total_buy_transactions == 3
    assert report.total_sell_transactions == 3
    assert report.total_fees > 0


def test_tax_report_profit_calculation_fifo(sample_transactions):
    """Test FIFO profit calculation."""
    generator = TaxReportGenerator(sample_transactions, method="FIFO")
    report = generator.generate_report()
    
    # BTC transactions:
    # Buy 0.5 @ 30000 = 15000
    # Sell 0.3 @ 35000 = 10500, cost = 0.3 * 30000 = 9000, profit = 1500
    # Buy 0.2 @ 40000 = 8000
    # Sell 0.1 @ 45000 = 4500, cost = 0.1 * 30000 = 3000, profit = 1500
    # Total BTC profit = 3000 (minus fees)
    
    # ETH transactions:
    # Buy 5.0 @ 2000 = 10000
    # Sell 2.0 @ 2500 = 5000, cost = 2.0 * 2000 = 4000, profit = 1000
    
    assert report.total_realized_profit > 0
    assert report.net_profit_loss > 0  # Should be positive overall


def test_tax_report_profit_calculation_lifo(sample_transactions):
    """Test LIFO profit calculation."""
    generator = TaxReportGenerator(sample_transactions, method="LIFO")
    report = generator.generate_report()
    
    # LIFO will use different cost basis
    # BTC sell 0.1 @ 45000 will use cost from 0.2 @ 40000
    # Profit = 45000 * 0.1 - 40000 * 0.1 = 500
    
    assert report.calculation_method == "LIFO"
    assert report.total_realized_profit > 0


def test_tax_report_date_filtering(sample_transactions):
    """Test date range filtering."""
    generator = TaxReportGenerator(
        sample_transactions, 
        method="FIFO",
        start_date="2024-03-01",
        end_date="2024-04-30"
    )
    report = generator.generate_report()
    
    # Should only include March and April transactions
    assert report.total_buy_transactions == 0  # No buys in this period
    assert report.total_sell_transactions == 2  # Two sells in this period
    assert report.report_period_start == "2024-03-01"
    assert report.report_period_end == "2024-04-30"


def test_tax_report_currency_breakdown(sample_transactions):
    """Test currency-wise breakdown."""
    generator = TaxReportGenerator(sample_transactions, method="FIFO")
    report = generator.generate_report()
    
    assert "BTC" in report.currency_breakdown
    assert "ETH" in report.currency_breakdown
    
    btc_stats = report.currency_breakdown["BTC"]
    assert btc_stats["sell_quantity"] == 0.4  # 0.3 + 0.1
    assert btc_stats["realized_profit"] > 0
    
    eth_stats = report.currency_breakdown["ETH"]
    assert eth_stats["sell_quantity"] == 2.0
    assert eth_stats["realized_profit"] > 0


def test_tax_report_monthly_breakdown(sample_transactions):
    """Test monthly breakdown."""
    generator = TaxReportGenerator(sample_transactions, method="FIFO")
    report = generator.generate_report()
    
    assert "2024-03" in report.monthly_breakdown
    assert "2024-04" in report.monthly_breakdown
    assert "2024-06" in report.monthly_breakdown
    
    # March should have BTC sell profit
    assert report.monthly_breakdown["2024-03"]["profit"] > 0


def test_tax_report_quarterly_breakdown(sample_transactions):
    """Test quarterly breakdown."""
    generator = TaxReportGenerator(sample_transactions, method="FIFO")
    report = generator.generate_report()
    
    assert "2024-Q1" in report.quarterly_breakdown
    assert "2024-Q2" in report.quarterly_breakdown
    
    # Q1 should have one sell (March)
    assert report.quarterly_breakdown["2024-Q1"]["profit"] > 0
    # Q2 should have two sells (April, June)
    assert report.quarterly_breakdown["2024-Q2"]["profit"] > 0


def test_tax_report_current_holdings(sample_transactions):
    """Test current holdings calculation."""
    generator = TaxReportGenerator(sample_transactions, method="FIFO")
    report = generator.generate_report()
    
    # BTC: bought 0.5 + 0.2 = 0.7, sold 0.3 + 0.1 = 0.4, remaining = 0.3
    assert "BTC" in report.current_holdings
    assert report.current_holdings["BTC"]["amount"] == pytest.approx(0.3, rel=1e-9)
    
    # ETH: bought 5.0, sold 2.0, remaining = 3.0
    assert "ETH" in report.current_holdings
    assert report.current_holdings["ETH"]["amount"] == pytest.approx(3.0, rel=1e-9)


def test_tax_report_tax_information(sample_transactions):
    """Test tax information calculation."""
    generator = TaxReportGenerator(sample_transactions, method="FIFO")
    report = generator.generate_report()
    
    # Taxable income should equal net profit if positive
    if report.net_profit_loss > 0:
        assert report.taxable_income == report.net_profit_loss
        assert report.loss_carryforward == 0
    else:
        assert report.taxable_income == 0
        assert report.loss_carryforward == abs(report.net_profit_loss)


def test_tax_report_export_csv(sample_transactions, tmp_path):
    """Test CSV export functionality."""
    generator = TaxReportGenerator(sample_transactions, method="FIFO")
    report = generator.generate_report()
    
    csv_path = tmp_path / "tax_report.csv"
    generator.export_csv(report, str(csv_path))
    
    assert csv_path.exists()
    content = csv_path.read_text(encoding='utf-8')
    assert "暗号資産税務サマリーレポート" in content
    assert "総実現利益" in content
    assert "BTC" in content
    assert "ETH" in content


def test_tax_report_export_json(sample_transactions):
    """Test JSON export functionality."""
    generator = TaxReportGenerator(sample_transactions, method="FIFO")
    report = generator.generate_report()
    
    json_content = generator.export_json(report)
    assert isinstance(json_content, str)
    
    import json
    data = json.loads(json_content)
    assert data["calculation_method"] == "FIFO"
    assert "currency_breakdown" in data
    assert "monthly_breakdown" in data


def test_tax_report_sell_transactions_detail(sample_transactions):
    """Test detailed sell transaction records."""
    generator = TaxReportGenerator(sample_transactions, method="FIFO")
    report = generator.generate_report()
    
    assert len(report.sell_transactions) == 3
    
    # Check first sell transaction
    first_sell = report.sell_transactions[0]
    assert first_sell["currency"] == "BTC"
    assert first_sell["amount"] == 0.3
    assert first_sell["sell_price"] == 35000
    assert "realized_gain_loss" in first_sell
    assert "cost_basis" in first_sell


def test_generate_tax_summary_report_integration(test_user):
    """Test the integrated function with database."""
    # Add transactions to database
    transactions = [
        ("2024-01-15", "buy", "BTC", 1.0, 30000, 100),
        ("2024-02-20", "sell", "BTC", 0.5, 35000, 50),
    ]
    
    for date, tx_type, currency, amount, price, fee in transactions:
        add_transaction(
            user_id=test_user.id,
            date=date,
            type=tx_type,
            currency=currency,
            amount=amount,
            price=price,
            fee=fee
        )
    
    # Generate report
    report = generate_tax_summary_report(test_user.id, method="FIFO")
    
    assert isinstance(report, TaxSummaryReport)
    assert report.total_buy_transactions == 1
    assert report.total_sell_transactions == 1
    assert report.net_profit_loss > 0  # Should have profit
    
    # Clean up
    clear_user_transactions(test_user.id)


def test_empty_transactions():
    """Test handling of empty transaction list."""
    generator = TaxReportGenerator([], method="FIFO")
    report = generator.generate_report()
    
    assert report.total_buy_transactions == 0
    assert report.total_sell_transactions == 0
    assert report.net_profit_loss == 0
    assert report.taxable_income == 0
    assert len(report.currency_breakdown) == 0


def test_insufficient_inventory_handling():
    """Test handling of insufficient inventory for sells."""
    transactions = [
        {
            "date": "2024-01-15",
            "type": "buy",
            "currency": "BTC",
            "amount": 0.5,
            "price": 30000,
            "fee": 50
        },
        {
            "date": "2024-02-20",
            "type": "sell",
            "currency": "BTC",
            "amount": 1.0,  # Trying to sell more than we have
            "price": 35000,
            "fee": 40
        }
    ]
    
    generator = TaxReportGenerator(transactions, method="FIFO")
    report = generator.generate_report()
    
    # Should handle the error gracefully
    assert report.total_buy_transactions == 1
    # The sell might be skipped or partially processed
    assert report.total_sell_transactions <= 1