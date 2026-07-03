"""
cli/prices.py
Renders the Live Market Prices panel (a watchlist of key symbols with
their latest mark price and 24h change).
"""
from typing import Optional

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cli.theme import PANEL_KWARGS, TABLE_KWARGS

# Default symbols shown in the live-prices box.
WATCHLIST = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]


def get_prices_panel(
    tickers: Optional[dict[str, dict[str, float]]] = None,
    symbols: Optional[list[str]] = None,
) -> Panel:
    """Build the LIVE MARKET PRICES panel.

    Args:
        tickers: mapping of symbol -> {"price": float, "change_pct": float}
                 (as returned by client.get_24hr_tickers()). If None/empty,
                 a friendly placeholder is shown instead of crashing.
        symbols: which symbols to display (defaults to WATCHLIST).
    """
    symbols = symbols or WATCHLIST

    if not tickers:
        empty = Text("\nLive prices unavailable right now.\n", style="warning", justify="center")
        return Panel(empty, title="[header]LIVE MARKET PRICES[/header]", **PANEL_KWARGS)  # type: ignore

    table = Table(show_header=True, header_style="header", expand=True, **TABLE_KWARGS)  # type: ignore
    table.add_column("Symbol", justify="left")
    table.add_column("Last Price (USDT)", justify="right")
    table.add_column("24h Change", justify="right")

    rendered_any = False
    for sym in symbols:
        ticker = tickers.get(sym)
        if not ticker:
            continue
        rendered_any = True

        price = float(ticker.get("price", 0.0))
        change = float(ticker.get("change_pct", 0.0))
        change_style = "value.positive" if change >= 0 else "value.negative"
        arrow = "▲" if change >= 0 else "▼"
        sign = "+" if change >= 0 else ""

        table.add_row(
            f"[label]{sym}[/label]",
            f"{price:,.2f}",
            f"[{change_style}]{arrow} {sign}{change:.2f}%[/{change_style}]",
        )

    if not rendered_any:
        empty = Text("\nNo watchlist symbols available.\n", style="warning", justify="center")
        return Panel(empty, title="[header]LIVE MARKET PRICES[/header]", **PANEL_KWARGS)  # type: ignore

    return Panel(table, title="[header]LIVE MARKET PRICES[/header]", **PANEL_KWARGS)  # type: ignore
