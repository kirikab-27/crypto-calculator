"""Command line interface for crypto calculator."""

import argparse
from typing import List, Dict

from .binance import BinanceClient
from .mexc import MEXCClient
from .calculator import calculate_pnl
from .reporting import generate_csv_report, generate_pdf_report
from .csv_import import read_trades_from_csv


def _sample_binance_data() -> List[Dict[str, object]]:
    return [
        {"id": 1, "symbol": "BTCUSDT", "qty": "0.1", "price": "30000.0", "time": 1609459200000},
        {"id": 2, "symbol": "BTCUSDT", "qty": "-0.1", "price": "31000.0", "time": 1609462800000},
    ]


def _sample_mexc_data() -> List[Dict[str, object]]:
    return [
        {"id": 1, "symbol": "BTCUSDT", "quantity": "0.1", "price": "30000.0", "timestamp": 1609459200000},
        {"id": 2, "symbol": "BTCUSDT", "quantity": "-0.1", "price": "31000.0", "timestamp": 1609462800000},
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Crypto Calculator CLI")
    parser.add_argument("output", help="Output file path without extension")
    parser.add_argument("--exchange", choices=["binance", "mexc"], default="binance")
    parser.add_argument("--method", choices=["FIFO", "LIFO"], default="FIFO")
    parser.add_argument("--csv", help="Path to CSV file containing trades")
    args = parser.parse_args()

    if args.csv:
        trades = read_trades_from_csv(args.csv)
    else:
        if args.exchange == "binance":
            client = BinanceClient()
            trades = client.get_trade_history(_sample_binance_data())
        else:
            client = MEXCClient()
            trades = client.get_trade_history(_sample_mexc_data())

    pnl = calculate_pnl(trades, method=args.method)
    summary = {"realised_pnl": pnl, "method": args.method}

    csv_path = f"{args.output}.csv"
    pdf_path = f"{args.output}.pdf"
    generate_csv_report(summary, csv_path)
    generate_pdf_report(summary, pdf_path)

    print(f"CSV report saved to {csv_path}")
    print(f"PDF report saved to {pdf_path}")


if __name__ == "__main__":
    main()
