from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Dict

from bot import data_feed, risk
from bot.broker.base import Broker, Fill
from bot.broker.paper import PaperBroker
from bot.confirmation import PendingOrder, PendingOrderQueue
from bot.config import BotConfig
from bot.strategy import generate_signal


def build_broker(config: BotConfig) -> Broker:
    if config.mode == "paper":
        return PaperBroker(config.state_file, config.trade_log_file, config.capital)
    if config.mode == "live":
        from bot.broker.robinhood_mcp import RobinhoodMCPBroker

        return RobinhoodMCPBroker()
    raise ValueError(f"unknown mode: {config.mode}")


class TradingEngine:
    def __init__(self, config: BotConfig):
        self.config = config
        self.broker = build_broker(config)
        self.queue = PendingOrderQueue(config.pending_file)
        self.daily_state_path = Path(config.state_file).parent / "daily_state.json"
        self._daily = self._load_daily_state()

    def _load_daily_state(self) -> dict:
        if self.daily_state_path.exists():
            return json.loads(self.daily_state_path.read_text())
        return {"date": None, "start_equity": None, "tripped": False}

    def _save_daily_state(self) -> None:
        self.daily_state_path.write_text(json.dumps(self._daily, indent=2))

    def _roll_daily_state(self, current_equity: float) -> None:
        today = datetime.date.today().isoformat()
        if self._daily["date"] != today:
            self._daily = {"date": today, "start_equity": current_equity, "tripped": False}
            self._save_daily_state()

    def _current_prices(self) -> Dict[str, float]:
        prices = {}
        for symbol in self.config.symbols:
            prices[symbol.ticker] = data_feed.get_current_price(symbol.id)
        return prices

    def run_once(self) -> list[str]:
        """Runs one strategy tick. Returns a list of human-readable events
        for logging/notification."""
        events: list[str] = []
        prices = self._current_prices()
        equity = self.broker.get_equity(prices)
        self._roll_daily_state(equity)

        if not self._daily["tripped"] and risk.daily_loss_breached(
            self._daily["start_equity"], equity, self.config.risk
        ):
            self._daily["tripped"] = True
            self._save_daily_state()
            events.append(
                f"DAILY LOSS LIMIT HIT: equity {equity:.2f} vs day-start "
                f"{self._daily['start_equity']:.2f}. New entries halted for today."
            )

        for symbol in self.config.symbols:
            ticker = symbol.ticker
            price = prices[ticker]
            positions = self.broker.get_positions()
            position = positions.get(ticker)

            if position:
                sl = risk.stop_loss_price(position.entry_price, self.config.risk)
                tp = risk.take_profit_price(position.entry_price, self.config.risk)
                if price <= sl or price >= tp:
                    fill = self.broker.place_order(ticker, "sell", position.quantity, price)
                    kind = "stop-loss" if price <= sl else "take-profit"
                    events.append(self._fill_message(fill, kind))
                    continue

            history = data_feed.get_price_history(symbol.id, self.config.strategy.history_days)
            signal = generate_signal(history, self.config.strategy.sma_fast, self.config.strategy.sma_slow)

            if signal == "buy":
                if self._daily["tripped"]:
                    continue
                existing_qty = position.quantity if position else 0.0
                qty = risk.entry_quantity(equity, price, existing_qty, self.config.risk)
                if qty <= 0:
                    continue
                events.append(self._handle_order(ticker, "buy", qty, price, "sma crossover buy signal"))
            elif signal == "sell" and position:
                events.append(
                    self._handle_order(ticker, "sell", position.quantity, price, "sma crossover sell signal")
                )

        return [e for e in events if e]

    def _handle_order(self, ticker: str, side: str, quantity: float, price: float, reason: str) -> str:
        if self.config.require_confirmation:
            order = self.queue.add(ticker, side, quantity, price, reason)
            return f"PENDING approval [{order.id}]: {side} {quantity} {ticker} @ {price:.2f} ({reason})"
        fill = self.broker.place_order(ticker, side, quantity, price)
        return self._fill_message(fill, reason)

    def approve(self, order_id: str) -> str:
        order: PendingOrder = self.queue.pop(order_id)
        fill = self.broker.place_order(order.ticker, order.side, order.quantity, order.price)
        return self._fill_message(fill, f"approved {order.id}")

    def reject(self, order_id: str) -> str:
        order = self.queue.pop(order_id)
        return f"rejected [{order.id}]: {order.side} {order.quantity} {order.ticker}"

    @staticmethod
    def _fill_message(fill: Fill, reason: str) -> str:
        return f"FILLED: {fill.side} {fill.quantity} {fill.ticker} @ {fill.price:.2f} ({reason})"
