from __future__ import annotations

import time
from typing import List

import requests

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


class DataFeedError(RuntimeError):
    pass


def _get(url: str, params: dict, retries: int = 3, backoff: float = 1.5) -> dict:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 429:
                raise DataFeedError("rate limited by CoinGecko")
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, DataFeedError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(backoff ** attempt)
    raise DataFeedError(f"failed to fetch {url}: {last_error}")


def get_current_price(coin_id: str, vs_currency: str = "usd") -> float:
    data = _get(
        f"{COINGECKO_BASE}/simple/price",
        {"ids": coin_id, "vs_currencies": vs_currency},
    )
    try:
        return float(data[coin_id][vs_currency])
    except KeyError as exc:
        raise DataFeedError(f"no price returned for {coin_id}") from exc


def get_price_history(coin_id: str, days: int, vs_currency: str = "usd") -> List[float]:
    data = _get(
        f"{COINGECKO_BASE}/coins/{coin_id}/market_chart",
        {"vs_currency": vs_currency, "days": days},
    )
    prices = data.get("prices")
    if not prices:
        raise DataFeedError(f"no price history returned for {coin_id}")
    return [point[1] for point in prices]
