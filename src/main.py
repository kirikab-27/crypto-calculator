"""Command line interface for crypto calculator."""

import argparse
from typing import List, Dict

from .binance import BinanceClient
from .mexc import MEXCClient
from .calculator import calculate_pnl
from .reporting import generate_csv_report, generate_pdf_report
from .csv_import import read_trades_from_csv




def main() -> None:
    parser = argparse.ArgumentParser(description="Crypto Calculator CLI")
    parser.add_argument("output", help="Output file path without extension")
    parser.add_argument("--exchange", choices=["binance", "mexc"], default="binance")
    parser.add_argument("--method", choices=["FIFO", "LIFO"], default="FIFO")
    parser.add_argument("--csv", help="Path to CSV file containing trades")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair symbol")
    args = parser.parse_args()

    if args.csv:
        trades = read_trades_from_csv(args.csv)
    else:
        if args.exchange == "binance":
            client = BinanceClient()
            trades = client.get_trade_history(args.symbol)
        else:
            client = MEXCClient()
            trades = client.get_trade_history(args.symbol)

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
