from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


@dataclass
class SymbolConfig:
    id: str
    ticker: str


@dataclass
class StrategyConfig:
    sma_fast: int
    sma_slow: int
    history_days: int


@dataclass
class RiskConfig:
    position_size_pct: float
    max_position_pct: float
    stop_loss_pct: float
    take_profit_pct: float
    daily_loss_limit_pct: float


@dataclass
class BotConfig:
    mode: str
    symbols: List[SymbolConfig]
    capital: float
    strategy: StrategyConfig
    risk: RiskConfig
    require_confirmation: bool
    poll_interval_seconds: int
    state_file: str
    pending_file: str
    trade_log_file: str


def load_config(path: str | Path) -> BotConfig:
    raw = yaml.safe_load(Path(path).read_text())

    symbols = [SymbolConfig(**s) for s in raw["symbols"]]
    strategy = StrategyConfig(**raw["strategy"])
    risk = RiskConfig(**raw["risk"])

    return BotConfig(
        mode=raw["mode"],
        symbols=symbols,
        capital=float(raw["capital"]),
        strategy=strategy,
        risk=risk,
        require_confirmation=bool(raw["require_confirmation"]),
        poll_interval_seconds=int(raw["poll_interval_seconds"]),
        state_file=raw["state_file"],
        pending_file=raw["pending_file"],
        trade_log_file=raw["trade_log_file"],
    )
