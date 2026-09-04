from __future__ import annotations

from typing import List, Literal, Optional

Signal = Literal["buy", "sell", "hold"]


def compute_sma(prices: List[float], window: int) -> Optional[float]:
    """Simple moving average of the last `window` prices, or None if not enough data."""
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window


def generate_signal(prices: List[float], sma_fast: int, sma_slow: int) -> Signal:
    """SMA crossover signal.

    "buy" when the fast SMA crosses above the slow SMA between the last two
    samples, "sell" on a cross below, "hold" otherwise (including when there
    isn't enough history yet).
    """
    if sma_fast >= sma_slow:
        raise ValueError("sma_fast must be smaller than sma_slow")
    if len(prices) < sma_slow + 1:
        return "hold"

    prev_fast = compute_sma(prices[:-1], sma_fast)
    prev_slow = compute_sma(prices[:-1], sma_slow)
    curr_fast = compute_sma(prices, sma_fast)
    curr_slow = compute_sma(prices, sma_slow)

    if None in (prev_fast, prev_slow, curr_fast, curr_slow):
        return "hold"

    crossed_up = prev_fast <= prev_slow and curr_fast > curr_slow
    crossed_down = prev_fast >= prev_slow and curr_fast < curr_slow

    if crossed_up:
        return "buy"
    if crossed_down:
        return "sell"
    return "hold"
