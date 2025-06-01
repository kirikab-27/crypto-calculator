# coding: utf-8
"""Tax summary report generation module.

This module implements comprehensive tax summary reporting for cryptocurrency transactions,
including profit/loss summaries, currency breakdowns, period analysis, and multiple export formats.
"""

from __future__ import annotations

import json
import csv
from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import io

from .calculator import CryptoCalculator, Transaction
from .db import get_user_transactions


@dataclass
class TaxSummaryReport:
    """Tax summary report data structure."""
    
    # Basic Information
    report_period_start: str
    report_period_end: str
    creation_date: str
    calculation_method: str
    base_currency: str = "JPY"
    
    # Profit/Loss Summary
    total_realized_profit: float = 0.0
    total_realized_loss: float = 0.0
    net_profit_loss: float = 0.0
    total_fees: float = 0.0
    
    # Currency Breakdown
    currency_breakdown: Dict[str, Dict[str, float]] = None
    
    # Period Breakdown
    monthly_breakdown: Dict[str, Dict[str, float]] = None
    quarterly_breakdown: Dict[str, Dict[str, float]] = None
    
    # Transaction Summary
    total_buy_transactions: int = 0
    total_sell_transactions: int = 0
    total_buy_amount: float = 0.0
    total_sell_amount: float = 0.0
    exchange_breakdown: Dict[str, int] = None
    
    # Current Holdings
    current_holdings: Dict[str, Dict[str, float]] = None
    
    # Tax Information
    taxable_income: float = 0.0
    loss_carryforward: float = 0.0
    
    # Detailed Transactions
    sell_transactions: List[Dict[str, Any]] = None
    
    # Metadata
    data_sources: List[str] = None
    calculation_notes: List[str] = None
    
    def __post_init__(self):
        """Initialize empty collections if not provided."""
        if self.currency_breakdown is None:
            self.currency_breakdown = {}
        if self.monthly_breakdown is None:
            self.monthly_breakdown = {}
        if self.quarterly_breakdown is None:
            self.quarterly_breakdown = {}
        if self.exchange_breakdown is None:
            self.exchange_breakdown = {}
        if self.current_holdings is None:
            self.current_holdings = {}
        if self.sell_transactions is None:
            self.sell_transactions = []
        if self.data_sources is None:
            self.data_sources = []
        if self.calculation_notes is None:
            self.calculation_notes = []


class TaxReportGenerator:
    """Generate tax summary reports from cryptocurrency transactions."""
    
    def __init__(self, transactions: List[Dict[str, Any]], method: str = "FIFO", 
                 start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Initialize the tax report generator.
        
        Parameters
        ----------
        transactions : List[Dict[str, Any]]
            List of transaction dictionaries
        method : str
            Calculation method (FIFO or LIFO)
        start_date : Optional[str]
            Start date for the report period (YYYY-MM-DD)
        end_date : Optional[str]
            End date for the report period (YYYY-MM-DD)
        """
        self.transactions = transactions
        self.method = method.upper()
        self.start_date = start_date
        self.end_date = end_date
        
        # Process transactions
        self._filter_transactions()
        self._sort_transactions()
        
    def _filter_transactions(self):
        """Filter transactions by date range if specified."""
        if not self.start_date and not self.end_date:
            return
            
        filtered = []
        for tx in self.transactions:
            tx_date = tx.get("date", "")
            if isinstance(tx_date, str):
                # Handle both date and datetime strings
                tx_date = tx_date.split("T")[0]
            
            include = True
            if self.start_date and tx_date < self.start_date:
                include = False
            if self.end_date and tx_date > self.end_date:
                include = False
                
            if include:
                filtered.append(tx)
                
        self.transactions = filtered
        
    def _sort_transactions(self):
        """Sort transactions by date."""
        self.transactions.sort(key=lambda x: x.get("date", ""))
        
    def generate_report(self) -> TaxSummaryReport:
        """Generate a comprehensive tax summary report.
        
        Returns
        -------
        TaxSummaryReport
            Complete tax summary report
        """
        # Initialize calculator
        calculator = CryptoCalculator(method=self.method)
        
        # Process transactions
        sell_transactions = []
        currency_stats = defaultdict(lambda: {
            "realized_profit": 0.0,
            "realized_loss": 0.0,
            "sell_quantity": 0.0,
            "sell_total": 0.0,
            "buy_quantity": 0.0,
            "buy_total": 0.0,
            "transactions": 0
        })
        
        monthly_stats = defaultdict(lambda: {"profit": 0.0, "loss": 0.0, "net": 0.0})
        exchange_counts = defaultdict(int)
        
        # Determine report period
        if self.transactions:
            actual_start = self.start_date or self.transactions[0].get("date", "").split("T")[0]
            actual_end = self.end_date or self.transactions[-1].get("date", "").split("T")[0]
        else:
            actual_start = self.start_date or datetime.now().strftime("%Y-01-01")
            actual_end = self.end_date or datetime.now().strftime("%Y-%m-%d")
        
        # Process each transaction
        total_buy_count = 0
        total_sell_count = 0
        total_buy_amount = 0.0
        total_sell_amount = 0.0
        
        for tx in self.transactions:
            tx_date = tx.get("date", "")
            if isinstance(tx_date, str):
                tx_datetime = datetime.fromisoformat(tx_date.replace("Z", "+00:00"))
            else:
                tx_datetime = tx_date
                
            currency = tx.get("currency", "")
            amount = float(tx.get("amount", 0))
            price = float(tx.get("price", 0))
            fee = float(tx.get("fee", 0))
            tx_type = tx.get("type", "").lower()
            
            # Track exchange usage (if we had exchange data)
            exchange = tx.get("exchange", "Unknown")
            exchange_counts[exchange] += 1
            
            # Update currency stats
            currency_stats[currency]["transactions"] += 1
            
            if tx_type == "buy":
                calculator.add_buy(tx_datetime, currency, amount, price, fee)
                total_buy_count += 1
                total_buy_amount += amount * price
                currency_stats[currency]["buy_quantity"] += amount
                currency_stats[currency]["buy_total"] += amount * price
                
            elif tx_type == "sell":
                try:
                    calculator.add_sell(tx_datetime, currency, amount, price, fee)
                    
                    # Get the transaction with calculated gain/loss
                    calc_tx = calculator.transactions[-1]
                    gain_loss = calc_tx.gain_loss or 0.0
                    
                    # Track sell transaction details
                    sell_tx = {
                        "date": tx_date,
                        "currency": currency,
                        "amount": amount,
                        "sell_price": price,
                        "cost_basis": (amount * price) - gain_loss,
                        "realized_gain_loss": gain_loss,
                        "fee": fee,
                        "exchange": exchange
                    }
                    sell_transactions.append(sell_tx)
                    
                    # Update statistics
                    total_sell_count += 1
                    total_sell_amount += amount * price
                    currency_stats[currency]["sell_quantity"] += amount
                    currency_stats[currency]["sell_total"] += amount * price
                    
                    if gain_loss > 0:
                        currency_stats[currency]["realized_profit"] += gain_loss
                    else:
                        currency_stats[currency]["realized_loss"] += abs(gain_loss)
                    
                    # Monthly breakdown
                    month_key = tx_datetime.strftime("%Y-%m")
                    if gain_loss > 0:
                        monthly_stats[month_key]["profit"] += gain_loss
                    else:
                        monthly_stats[month_key]["loss"] += abs(gain_loss)
                    monthly_stats[month_key]["net"] += gain_loss
                    
                except ValueError as e:
                    # Handle insufficient inventory
                    print(f"Warning: {e}")
        
        # Calculate totals
        summary = calculator.calculate_summary()
        total_realized_profit = sum(
            stats["realized_profit"] for stats in currency_stats.values()
        )
        total_realized_loss = sum(
            stats["realized_loss"] for stats in currency_stats.values()
        )
        net_profit_loss = total_realized_profit - total_realized_loss
        
        # Calculate quarterly breakdown
        quarterly_stats = defaultdict(lambda: {"profit": 0.0, "loss": 0.0, "net": 0.0})
        for month, stats in monthly_stats.items():
            year, month_num = month.split("-")
            quarter = f"{year}-Q{(int(month_num) - 1) // 3 + 1}"
            quarterly_stats[quarter]["profit"] += stats["profit"]
            quarterly_stats[quarter]["loss"] += stats["loss"]
            quarterly_stats[quarter]["net"] += stats["net"]
        
        # Prepare currency breakdown
        currency_breakdown = {}
        for currency, stats in currency_stats.items():
            if stats["transactions"] > 0:
                currency_breakdown[currency] = {
                    "realized_profit": stats["realized_profit"],
                    "realized_loss": stats["realized_loss"],
                    "net_profit_loss": stats["realized_profit"] - stats["realized_loss"],
                    "sell_quantity": stats["sell_quantity"],
                    "average_sell_price": stats["sell_total"] / stats["sell_quantity"] if stats["sell_quantity"] > 0 else 0,
                    "average_buy_price": stats["buy_total"] / stats["buy_quantity"] if stats["buy_quantity"] > 0 else 0
                }
        
        # Get current holdings
        current_holdings = calculator.get_inventory_status()
        
        # Tax information
        taxable_income = max(0, net_profit_loss)  # Only positive income is taxable
        loss_carryforward = abs(min(0, net_profit_loss))  # Negative becomes carryforward
        
        # Create report
        report = TaxSummaryReport(
            report_period_start=actual_start,
            report_period_end=actual_end,
            creation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            calculation_method=self.method,
            total_realized_profit=total_realized_profit,
            total_realized_loss=total_realized_loss,
            net_profit_loss=net_profit_loss,
            total_fees=summary["total_fees"],
            currency_breakdown=currency_breakdown,
            monthly_breakdown=dict(monthly_stats),
            quarterly_breakdown=dict(quarterly_stats),
            total_buy_transactions=total_buy_count,
            total_sell_transactions=total_sell_count,
            total_buy_amount=total_buy_amount,
            total_sell_amount=total_sell_amount,
            exchange_breakdown=dict(exchange_counts),
            current_holdings=current_holdings,
            taxable_income=taxable_income,
            loss_carryforward=loss_carryforward,
            sell_transactions=sell_transactions,
            data_sources=["Database Import"],
            calculation_notes=[
                f"計算方法: {self.method}（{'先入先出法' if self.method == 'FIFO' else '後入先出法'}）",
                "基準通貨: 日本円（JPY）",
                "注意: この報告書は参考情報です。正確な税務申告については税務専門家にご相談ください。"
            ]
        )
        
        return report
    
    def export_csv(self, report: TaxSummaryReport, filepath: str) -> None:
        """Export report to CSV format.
        
        Parameters
        ----------
        report : TaxSummaryReport
            The report to export
        filepath : str
            Path to save the CSV file
        """
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(["暗号資産税務サマリーレポート"])
            writer.writerow([])
            
            # Basic Information
            writer.writerow(["基本情報"])
            writer.writerow(["レポート期間", f"{report.report_period_start} 〜 {report.report_period_end}"])
            writer.writerow(["作成日時", report.creation_date])
            writer.writerow(["計算方法", report.calculation_method])
            writer.writerow(["基準通貨", report.base_currency])
            writer.writerow([])
            
            # Profit/Loss Summary
            writer.writerow(["損益サマリー"])
            writer.writerow(["総実現利益", f"¥{report.total_realized_profit:,.2f}"])
            writer.writerow(["総実現損失", f"¥{report.total_realized_loss:,.2f}"])
            writer.writerow(["純損益", f"¥{report.net_profit_loss:,.2f}"])
            writer.writerow(["総取引手数料", f"¥{report.total_fees:,.2f}"])
            writer.writerow([])
            
            # Currency Breakdown
            writer.writerow(["通貨別損益内訳"])
            writer.writerow(["通貨", "実現利益", "実現損失", "純損益", "売却数量", "平均売却価格", "平均取得価格"])
            for currency, stats in report.currency_breakdown.items():
                writer.writerow([
                    currency,
                    f"¥{stats['realized_profit']:,.2f}",
                    f"¥{stats['realized_loss']:,.2f}",
                    f"¥{stats['net_profit_loss']:,.2f}",
                    f"{stats['sell_quantity']:.8f}",
                    f"¥{stats['average_sell_price']:,.2f}",
                    f"¥{stats['average_buy_price']:,.2f}"
                ])
            writer.writerow([])
            
            # Monthly Breakdown
            writer.writerow(["月次損益内訳"])
            writer.writerow(["年月", "利益", "損失", "純損益"])
            for month in sorted(report.monthly_breakdown.keys()):
                stats = report.monthly_breakdown[month]
                writer.writerow([
                    month,
                    f"¥{stats['profit']:,.2f}",
                    f"¥{stats['loss']:,.2f}",
                    f"¥{stats['net']:,.2f}"
                ])
            writer.writerow([])
            
            # Transaction Summary
            writer.writerow(["取引サマリー"])
            writer.writerow(["総買い取引件数", report.total_buy_transactions])
            writer.writerow(["総売り取引件数", report.total_sell_transactions])
            writer.writerow(["総買い取引額", f"¥{report.total_buy_amount:,.2f}"])
            writer.writerow(["総売り取引額", f"¥{report.total_sell_amount:,.2f}"])
            writer.writerow([])
            
            # Current Holdings
            writer.writerow(["現在の保有状況"])
            writer.writerow(["通貨", "保有数量", "平均取得単価", "取得原価合計"])
            for currency, holding in report.current_holdings.items():
                writer.writerow([
                    currency,
                    f"{holding['amount']:.8f}",
                    f"¥{holding['average_cost']:,.2f}",
                    f"¥{holding['total_cost']:,.2f}"
                ])
            writer.writerow([])
            
            # Tax Information
            writer.writerow(["税務関連情報"])
            writer.writerow(["課税対象所得", f"¥{report.taxable_income:,.2f}"])
            writer.writerow(["損失繰越可能額", f"¥{report.loss_carryforward:,.2f}"])
            writer.writerow([])
            
            # Detailed Sell Transactions
            writer.writerow(["売却取引詳細"])
            writer.writerow(["日付", "通貨", "数量", "売却価格", "取得原価", "実現損益", "手数料"])
            for tx in report.sell_transactions:
                writer.writerow([
                    tx['date'],
                    tx['currency'],
                    f"{tx['amount']:.8f}",
                    f"¥{tx['sell_price']:,.2f}",
                    f"¥{tx['cost_basis']:,.2f}",
                    f"¥{tx['realized_gain_loss']:,.2f}",
                    f"¥{tx['fee']:,.2f}"
                ])
            writer.writerow([])
            
            # Notes
            writer.writerow(["注記事項"])
            for note in report.calculation_notes:
                writer.writerow([note])
    
    def export_json(self, report: TaxSummaryReport) -> str:
        """Export report to JSON format.
        
        Parameters
        ----------
        report : TaxSummaryReport
            The report to export
            
        Returns
        -------
        str
            JSON string representation of the report
        """
        # Convert dataclass to dictionary
        report_dict = asdict(report)
        
        # Format dates for JSON
        for key in ['report_period_start', 'report_period_end', 'creation_date']:
            if key in report_dict and report_dict[key]:
                # Ensure dates are in ISO format
                report_dict[key] = str(report_dict[key])
        
        return json.dumps(report_dict, ensure_ascii=False, indent=2)
    
    def export_pdf(self, report: TaxSummaryReport, filepath: str) -> None:
        """Export report to PDF format.
        
        Parameters
        ----------
        report : TaxSummaryReport
            The report to export
        filepath : str
            Path to save the PDF file
        """
        try:
            from fpdf import FPDF
            
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font('NotoSans', '', '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', uni=True)
            pdf.set_font('NotoSans', size=12)
            
            # Title
            pdf.set_font('NotoSans', size=16)
            pdf.cell(0, 10, '暗号資産税務サマリーレポート', ln=True, align='C')
            pdf.ln(5)
            
            # Basic Information
            pdf.set_font('NotoSans', size=14)
            pdf.cell(0, 8, '基本情報', ln=True)
            pdf.set_font('NotoSans', size=10)
            pdf.cell(0, 6, f'レポート期間: {report.report_period_start} 〜 {report.report_period_end}', ln=True)
            pdf.cell(0, 6, f'作成日時: {report.creation_date}', ln=True)
            pdf.cell(0, 6, f'計算方法: {report.calculation_method}', ln=True)
            pdf.ln(5)
            
            # Profit/Loss Summary
            pdf.set_font('NotoSans', size=14)
            pdf.cell(0, 8, '損益サマリー', ln=True)
            pdf.set_font('NotoSans', size=10)
            pdf.cell(0, 6, f'総実現利益: ¥{report.total_realized_profit:,.2f}', ln=True)
            pdf.cell(0, 6, f'総実現損失: ¥{report.total_realized_loss:,.2f}', ln=True)
            pdf.cell(0, 6, f'純損益: ¥{report.net_profit_loss:,.2f}', ln=True)
            pdf.cell(0, 6, f'総取引手数料: ¥{report.total_fees:,.2f}', ln=True)
            pdf.ln(5)
            
            # Save PDF
            pdf.output(filepath)
            
        except ImportError:
            # Fallback to text file if fpdf is not available
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('暗号資産税務サマリーレポート\n')
                f.write('=' * 50 + '\n\n')
                
                f.write('基本情報\n')
                f.write(f'レポート期間: {report.report_period_start} 〜 {report.report_period_end}\n')
                f.write(f'作成日時: {report.creation_date}\n')
                f.write(f'計算方法: {report.calculation_method}\n\n')
                
                f.write('損益サマリー\n')
                f.write(f'総実現利益: ¥{report.total_realized_profit:,.2f}\n')
                f.write(f'総実現損失: ¥{report.total_realized_loss:,.2f}\n')
                f.write(f'純損益: ¥{report.net_profit_loss:,.2f}\n')
                f.write(f'総取引手数料: ¥{report.total_fees:,.2f}\n\n')
                
                # Add more sections as needed...
                
                f.write('\n注記事項\n')
                for note in report.calculation_notes:
                    f.write(f'- {note}\n')


def generate_tax_summary_report(user_id: int, method: str = "FIFO", 
                               start_date: Optional[str] = None, 
                               end_date: Optional[str] = None) -> TaxSummaryReport:
    """Generate a tax summary report for a user.
    
    Parameters
    ----------
    user_id : int
        User ID
    method : str
        Calculation method (FIFO or LIFO)
    start_date : Optional[str]
        Start date for the report (YYYY-MM-DD)
    end_date : Optional[str]
        End date for the report (YYYY-MM-DD)
        
    Returns
    -------
    TaxSummaryReport
        Generated tax summary report
    """
    # Get user transactions
    transactions = get_user_transactions(user_id)
    
    # Generate report
    generator = TaxReportGenerator(transactions, method, start_date, end_date)
    return generator.generate_report()