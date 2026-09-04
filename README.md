# Crypto-Trading

An automated crypto trading bot: an SMA-crossover strategy with built-in
risk controls, running against a simulated paper-trading ledger today, with
a broker interface ready to wire up to real Robinhood orders later.

## How it works

- **Strategy** (`bot/strategy.py`): buys when the fast SMA crosses above the
  slow SMA, sells when it crosses back below (`config.yaml` → `strategy`).
- **Risk management** (`bot/risk.py`, `bot/engine.py`):
  - position sizing as a % of equity, capped per-symbol exposure
  - per-position stop-loss / take-profit, which exit automatically —
    delaying a protective exit to wait for approval would defeat it
  - a daily loss limit that halts *new* entries for the rest of the day
    once tripped (existing stop-losses/take-profits still fire)
- **Manual confirmation**: every new entry/exit signal (other than
  stop-loss/take-profit/kill-switch) is queued rather than executed
  immediately when `require_confirmation: true` (the default). Review and
  approve/reject with the CLI before it's sent to the broker.
- **Brokers** (`bot/broker/`): a `Broker` interface with two
  implementations —
  - `PaperBroker`: simulates fills against a JSON-file cash/position
    ledger, using live public prices from CoinGecko. No account or API
    keys needed — this is what `mode: paper` uses.
  - `RobinhoodMCPBroker`: a stub for `mode: live`, meant to place real
    orders through the `robinhood-trading` MCP server registered in
    `.mcp.json`. **Not implemented yet** — see the docstring in
    `bot/broker/robinhood_mcp.py` for what's needed before flipping to
    live trading.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Edit `config.yaml` to set symbols, strategy windows, and risk limits.

## Running

```bash
# one strategy tick
python -m bot.cli run

# repeat on a timer (config.yaml -> poll_interval_seconds)
python -m bot.cli loop

# see cash / positions / equity / daily kill-switch state
python -m bot.cli status

# review and act on orders awaiting approval
python -m bot.cli pending
python -m bot.cli approve <order_id>
python -m bot.cli reject <order_id>
```

State lives under `data/` (gitignored): `paper_state.json` (ledger),
`pending_orders.json` (approval queue), `trade_log.jsonl` (fill history).

## Tests

```bash
python -m pytest
```

## Going live

Do not switch `mode: live` until:

1. `bot/broker/robinhood_mcp.py` is implemented against the actual
   `robinhood-trading` MCP server's tools (its schema needs to be
   introspected from a session that's authenticated to it — it isn't
   reachable from a generic session just because `.mcp.json` lists it).
2. You've run it against a small position size and confirmed order
   placement, fills, and position/cash reporting all behave as expected.
3. `require_confirmation: true` stays on until you trust it unattended.

This bot places trades with real financial risk once live. Treat every
config change to `risk` or `require_confirmation` deliberately.
