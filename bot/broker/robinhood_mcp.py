from __future__ import annotations

from typing import Dict

from bot.broker.base import Broker, Fill, Position, Side


class RobinhoodBrokerNotConfigured(RuntimeError):
    pass


class RobinhoodMCPBroker(Broker):
    """Live broker backed by the `robinhood-trading` MCP server
    (see .mcp.json, https://agent.robinhood.com/mcp/trading).

    NOT YET IMPLEMENTED. This server's tool names/schema (get quote, get
    positions, place order, etc.) haven't been introspected from a session
    that's actually authenticated to it, so the calls below are unfilled.

    To finish this:
      1. From a Claude Code session with the robinhood-trading MCP server
         connected (check with `/mcp`), list its tools and note the exact
         tool names and input/output shapes.
      2. Replace the NotImplementedError bodies below with real calls
         (likely via an MCP client library, or however this process is
         meant to reach that HTTP MCP endpoint).
      3. Test thoroughly against a small position size before trusting it
         with real capital, and keep `require_confirmation: true` in
         config.yaml while you do.
    """

    def __init__(self):
        raise RobinhoodBrokerNotConfigured(
            "RobinhoodMCPBroker is a stub. See the module docstring in "
            "bot/broker/robinhood_mcp.py for what needs to be filled in "
            "before mode: live can be used."
        )

    def get_cash(self) -> float:
        raise NotImplementedError

    def get_positions(self) -> Dict[str, Position]:
        raise NotImplementedError

    def place_order(self, ticker: str, side: Side, quantity: float, price: float) -> Fill:
        raise NotImplementedError
