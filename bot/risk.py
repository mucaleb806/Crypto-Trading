from __future__ import annotations

from bot.config import RiskConfig


def entry_quantity(
    capital: float,
    price: float,
    existing_quantity: float,
    risk: RiskConfig,
) -> float:
    """Size a new entry, capped so total exposure to the symbol stays under
    `max_position_pct` of capital. Returns 0 if already at/above the cap."""
    if price <= 0:
        return 0.0

    target_value = capital * risk.position_size_pct
    max_value = capital * risk.max_position_pct
    existing_value = existing_quantity * price

    room = max_value - existing_value
    if room <= 0:
        return 0.0

    value_to_buy = min(target_value, room)
    return round(value_to_buy / price, 8)


def stop_loss_price(entry_price: float, risk: RiskConfig) -> float:
    return entry_price * (1 - risk.stop_loss_pct)


def take_profit_price(entry_price: float, risk: RiskConfig) -> float:
    return entry_price * (1 + risk.take_profit_pct)


def daily_loss_breached(day_start_equity: float, current_equity: float, risk: RiskConfig) -> bool:
    if day_start_equity <= 0:
        return False
    drawdown = (day_start_equity - current_equity) / day_start_equity
    return drawdown >= risk.daily_loss_limit_pct
