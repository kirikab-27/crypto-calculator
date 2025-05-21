"""Command line interface for crypto calculator."""

import argparse
from typing import List, Dict

from .dashboard import run_dashboard
from .db import init_db, add_user, get_user_by_username

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
    init_db()

    parser = argparse.ArgumentParser(description="Crypto Calculator CLI")
    subparsers = parser.add_subparsers(dest="command")

    register_p = subparsers.add_parser("register", help="Register new user")
    register_p.add_argument("username")
    register_p.add_argument("password")

    login_p = subparsers.add_parser("login", help="Authenticate user")
    login_p.add_argument("username")
    login_p.add_argument("password")

    # Arguments for calculation (default command)
    parser.add_argument("output", nargs="?", help="Output file path without extension")
    parser.add_argument("--exchange", choices=["binance", "mexc"], default="binance")
    parser.add_argument("--method", choices=["FIFO", "LIFO"], default="FIFO")
    parser.add_argument("--csv", help="Path to CSV file containing trades")
    parser.add_argument("--serve", action="store_true", help="Run dashboard web server")
    args = parser.parse_args()

    if args.command == "register":
        user = add_user(args.username, args.password)
        print(f"Registered user {user.username} (id: {user.id})")
        return
    if args.command == "login":
        user = get_user_by_username(args.username)
        if not user:
            print("User not found")
            return
        if user.verify_password(args.password):
            print("Login successful")
        else:
            print("Invalid password")
        return

    if not args.output:
        parser.print_help()
        return

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

    if args.serve:
        run_dashboard(summary)


if __name__ == "__main__":
    main()
