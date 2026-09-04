import pytest

from bot.broker.paper import InsufficientFundsError, InsufficientPositionError, PaperBroker


def make_broker(tmp_path, capital=1000.0):
    return PaperBroker(
        state_file=str(tmp_path / "state.json"),
        trade_log_file=str(tmp_path / "trades.jsonl"),
        starting_capital=capital,
    )


def test_buy_reduces_cash_and_opens_position(tmp_path):
    broker = make_broker(tmp_path)
    broker.place_order("BTC", "buy", 2, 100)
    assert broker.get_cash() == pytest.approx(800.0)
    position = broker.get_positions()["BTC"]
    assert position.quantity == pytest.approx(2)
    assert position.entry_price == pytest.approx(100)


def test_buy_averages_entry_price(tmp_path):
    broker = make_broker(tmp_path)
    broker.place_order("BTC", "buy", 1, 100)
    broker.place_order("BTC", "buy", 1, 200)
    position = broker.get_positions()["BTC"]
    assert position.quantity == pytest.approx(2)
    assert position.entry_price == pytest.approx(150)


def test_sell_closes_position_and_adds_cash(tmp_path):
    broker = make_broker(tmp_path)
    broker.place_order("BTC", "buy", 2, 100)
    broker.place_order("BTC", "sell", 2, 120)
    assert "BTC" not in broker.get_positions()
    assert broker.get_cash() == pytest.approx(1000.0 - 200.0 + 240.0)


def test_buy_rejects_insufficient_funds(tmp_path):
    broker = make_broker(tmp_path, capital=100.0)
    with pytest.raises(InsufficientFundsError):
        broker.place_order("BTC", "buy", 2, 100)


def test_sell_rejects_oversized_position(tmp_path):
    broker = make_broker(tmp_path)
    broker.place_order("BTC", "buy", 1, 100)
    with pytest.raises(InsufficientPositionError):
        broker.place_order("BTC", "sell", 2, 100)


def test_state_persists_across_instances(tmp_path):
    broker = make_broker(tmp_path)
    broker.place_order("BTC", "buy", 1, 100)

    reloaded = PaperBroker(
        state_file=str(tmp_path / "state.json"),
        trade_log_file=str(tmp_path / "trades.jsonl"),
        starting_capital=1000.0,
    )
    assert reloaded.get_cash() == pytest.approx(900.0)
    assert reloaded.get_positions()["BTC"].quantity == pytest.approx(1)
