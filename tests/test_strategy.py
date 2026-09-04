import pytest

from bot.strategy import compute_sma, generate_signal


def test_compute_sma_basic():
    assert compute_sma([1, 2, 3, 4], 2) == pytest.approx(3.5)


def test_compute_sma_not_enough_data():
    assert compute_sma([1, 2, 3], 5) is None


def test_generate_signal_buy_on_upward_crossover():
    prices = [10, 10, 10, 10, 10, 20]
    assert generate_signal(prices, sma_fast=2, sma_slow=4) == "buy"


def test_generate_signal_sell_on_downward_crossover():
    prices = [10, 10, 10, 10, 10, 0]
    assert generate_signal(prices, sma_fast=2, sma_slow=4) == "sell"


def test_generate_signal_hold_when_no_crossover():
    prices = [10, 11, 10, 11, 10, 11]
    assert generate_signal(prices, sma_fast=2, sma_slow=4) == "hold"


def test_generate_signal_hold_with_insufficient_history():
    assert generate_signal([1, 2, 3], sma_fast=2, sma_slow=4) == "hold"


def test_generate_signal_rejects_bad_windows():
    with pytest.raises(ValueError):
        generate_signal([1, 2, 3, 4, 5], sma_fast=4, sma_slow=4)
