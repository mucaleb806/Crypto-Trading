import pytest

from bot.config import RiskConfig
from bot.risk import daily_loss_breached, entry_quantity, stop_loss_price, take_profit_price

RISK = RiskConfig(
    position_size_pct=0.10,
    max_position_pct=0.25,
    stop_loss_pct=0.05,
    take_profit_pct=0.10,
    daily_loss_limit_pct=0.03,
)


def test_entry_quantity_sizes_to_position_size_pct():
    qty = entry_quantity(capital=10000, price=100, existing_quantity=0, risk=RISK)
    assert qty == pytest.approx(10.0)


def test_entry_quantity_capped_by_max_position_pct():
    # existing position is already worth 2400 of a 2500 (25%) cap, room=100
    qty = entry_quantity(capital=10000, price=100, existing_quantity=24, risk=RISK)
    assert qty == pytest.approx(1.0)


def test_entry_quantity_zero_when_over_cap():
    qty = entry_quantity(capital=10000, price=100, existing_quantity=30, risk=RISK)
    assert qty == 0.0


def test_stop_loss_and_take_profit_prices():
    assert stop_loss_price(100, RISK) == pytest.approx(95.0)
    assert take_profit_price(100, RISK) == pytest.approx(110.0)


def test_daily_loss_breached_true_over_limit():
    assert daily_loss_breached(day_start_equity=10000, current_equity=9600, risk=RISK) is True


def test_daily_loss_breached_false_under_limit():
    assert daily_loss_breached(day_start_equity=10000, current_equity=9800, risk=RISK) is False
