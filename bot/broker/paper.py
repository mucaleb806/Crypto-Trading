from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict

from bot.broker.base import Broker, Fill, Position, Side


class InsufficientFundsError(RuntimeError):
    pass


class InsufficientPositionError(RuntimeError):
    pass


class PaperBroker(Broker):
    """Simulated broker: fills orders instantly at the given price against a
    virtual cash/position ledger persisted to `state_file`."""

    def __init__(self, state_file: str, trade_log_file: str, starting_capital: float):
        self.state_file = Path(state_file)
        self.trade_log_file = Path(trade_log_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.trade_log_file.parent.mkdir(parents=True, exist_ok=True)

        if self.state_file.exists():
            raw = json.loads(self.state_file.read_text())
            self._cash = raw["cash"]
            self._positions = {
                ticker: Position(ticker=ticker, **p) for ticker, p in raw["positions"].items()
            }
        else:
            self._cash = starting_capital
            self._positions = {}
            self._save()

    def get_cash(self) -> float:
        return self._cash

    def get_positions(self) -> Dict[str, Position]:
        return dict(self._positions)

    def place_order(self, ticker: str, side: Side, quantity: float, price: float) -> Fill:
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        if side == "buy":
            cost = quantity * price
            if cost > self._cash + 1e-9:
                raise InsufficientFundsError(
                    f"need {cost:.2f} cash to buy {quantity} {ticker}, have {self._cash:.2f}"
                )
            self._cash -= cost
            existing = self._positions.get(ticker)
            if existing:
                total_qty = existing.quantity + quantity
                existing.entry_price = (
                    existing.entry_price * existing.quantity + price * quantity
                ) / total_qty
                existing.quantity = total_qty
            else:
                self._positions[ticker] = Position(ticker=ticker, quantity=quantity, entry_price=price)
        else:
            existing = self._positions.get(ticker)
            held = existing.quantity if existing else 0.0
            if quantity > held + 1e-9:
                raise InsufficientPositionError(
                    f"tried to sell {quantity} {ticker}, only hold {held}"
                )
            self._cash += quantity * price
            remaining = held - quantity
            if remaining <= 1e-9:
                self._positions.pop(ticker, None)
            else:
                existing.quantity = remaining

        fill = Fill(ticker=ticker, side=side, quantity=quantity, price=price)
        self._save()
        self._log_fill(fill)
        return fill

    def _save(self) -> None:
        raw = {
            "cash": self._cash,
            "positions": {
                ticker: {"quantity": p.quantity, "entry_price": p.entry_price}
                for ticker, p in self._positions.items()
            },
        }
        self.state_file.write_text(json.dumps(raw, indent=2))

    def _log_fill(self, fill: Fill) -> None:
        entry = {
            "timestamp": time.time(),
            "ticker": fill.ticker,
            "side": fill.side,
            "quantity": fill.quantity,
            "price": fill.price,
        }
        with self.trade_log_file.open("a") as f:
            f.write(json.dumps(entry) + "\n")
