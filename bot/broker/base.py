from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Literal

Side = Literal["buy", "sell"]


@dataclass
class Position:
    ticker: str
    quantity: float
    entry_price: float


@dataclass
class Fill:
    ticker: str
    side: Side
    quantity: float
    price: float


class Broker(ABC):
    """Order execution + account state, implemented by PaperBroker (simulated)
    and RobinhoodBroker (real orders via the Robinhood MCP server)."""

    @abstractmethod
    def get_cash(self) -> float:
        ...

    @abstractmethod
    def get_positions(self) -> Dict[str, Position]:
        ...

    @abstractmethod
    def place_order(self, ticker: str, side: Side, quantity: float, price: float) -> Fill:
        ...

    def get_equity(self, prices: Dict[str, float]) -> float:
        equity = self.get_cash()
        for ticker, position in self.get_positions().items():
            equity += position.quantity * prices.get(ticker, position.entry_price)
        return equity
