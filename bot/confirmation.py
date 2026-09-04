from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Literal

Side = Literal["buy", "sell"]


@dataclass
class PendingOrder:
    id: str
    ticker: str
    side: Side
    quantity: float
    price: float
    reason: str
    created_at: float


class PendingOrderQueue:
    """A tiny JSON-backed queue of orders awaiting human approval before
    they're sent to the broker."""

    def __init__(self, pending_file: str):
        self.path = Path(pending_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}")

    def _load(self) -> Dict[str, dict]:
        return json.loads(self.path.read_text())

    def _save(self, data: Dict[str, dict]) -> None:
        self.path.write_text(json.dumps(data, indent=2))

    def add(self, ticker: str, side: Side, quantity: float, price: float, reason: str) -> PendingOrder:
        order = PendingOrder(
            id=uuid.uuid4().hex[:8],
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=price,
            reason=reason,
            created_at=time.time(),
        )
        data = self._load()
        data[order.id] = asdict(order)
        self._save(data)
        return order

    def list(self) -> List[PendingOrder]:
        return [PendingOrder(**o) for o in self._load().values()]

    def pop(self, order_id: str) -> PendingOrder:
        data = self._load()
        if order_id not in data:
            raise KeyError(f"no pending order with id {order_id}")
        order = PendingOrder(**data.pop(order_id))
        self._save(data)
        return order
