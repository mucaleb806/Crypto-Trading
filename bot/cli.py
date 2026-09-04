from __future__ import annotations

import argparse
import time

from bot.config import load_config
from bot.engine import TradingEngine


def cmd_run(engine: TradingEngine, args) -> None:
    for event in engine.run_once():
        print(event)


def cmd_loop(engine: TradingEngine, args) -> None:
    interval = engine.config.poll_interval_seconds
    print(f"looping every {interval}s, ctrl-c to stop")
    try:
        while True:
            for event in engine.run_once():
                print(event)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("stopped")


def cmd_pending(engine: TradingEngine, args) -> None:
    pending = engine.queue.list()
    if not pending:
        print("no pending orders")
        return
    for order in pending:
        print(f"[{order.id}] {order.side} {order.quantity} {order.ticker} @ {order.price:.2f} - {order.reason}")


def cmd_approve(engine: TradingEngine, args) -> None:
    print(engine.approve(args.order_id))


def cmd_reject(engine: TradingEngine, args) -> None:
    print(engine.reject(args.order_id))


def cmd_status(engine: TradingEngine, args) -> None:
    prices = engine._current_prices()
    cash = engine.broker.get_cash()
    positions = engine.broker.get_positions()
    equity = engine.broker.get_equity(prices)
    print(f"mode: {engine.config.mode}")
    print(f"cash: {cash:.2f}")
    for ticker, pos in positions.items():
        price = prices.get(ticker, pos.entry_price)
        pnl = (price - pos.entry_price) * pos.quantity
        print(f"  {ticker}: qty={pos.quantity} entry={pos.entry_price:.2f} price={price:.2f} pnl={pnl:.2f}")
    print(f"equity: {equity:.2f}")
    print(f"day-start equity: {engine._daily.get('start_equity')}")
    print(f"daily loss limit tripped: {engine._daily.get('tripped')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crypto trading bot")
    parser.add_argument("--config", default="config.yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="run a single strategy tick")
    sub.add_parser("loop", help="run strategy ticks on a timer")
    sub.add_parser("pending", help="list orders awaiting approval")
    sub.add_parser("status", help="show cash, positions, and equity")

    approve_p = sub.add_parser("approve", help="approve a pending order")
    approve_p.add_argument("order_id")

    reject_p = sub.add_parser("reject", help="reject a pending order")
    reject_p.add_argument("order_id")

    args = parser.parse_args()
    config = load_config(args.config)
    engine = TradingEngine(config)

    commands = {
        "run": cmd_run,
        "loop": cmd_loop,
        "pending": cmd_pending,
        "approve": cmd_approve,
        "reject": cmd_reject,
        "status": cmd_status,
    }
    commands[args.command](engine, args)


if __name__ == "__main__":
    main()
