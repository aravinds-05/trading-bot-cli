"""Unit tests for the Live Market Prices panel."""

from rich.panel import Panel

from cli.prices import get_prices_panel


def test_prices_panel_renders_with_tickers():
    tickers = {
        "BTCUSDT": {"price": 61932.4, "change_pct": 0.55},
        "ETHUSDT": {"price": 1731.8, "change_pct": -1.93},
    }
    panel = get_prices_panel(tickers, symbols=["BTCUSDT", "ETHUSDT"])
    assert isinstance(panel, Panel)


def test_prices_panel_handles_missing_data():
    # None / empty tickers must not raise — should show a placeholder panel.
    assert isinstance(get_prices_panel(None), Panel)
    assert isinstance(get_prices_panel({}), Panel)


def test_prices_panel_skips_unknown_symbols():
    # Symbols not present in the ticker map should be skipped gracefully.
    panel = get_prices_panel({"BTCUSDT": {"price": 1.0, "change_pct": 0.0}},
                             symbols=["DOGEUSDT"])
    assert isinstance(panel, Panel)
