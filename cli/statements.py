"""
cli/statements.py
Renders the Recent Trades / Statements panel.
"""
from typing import Any, List
from datetime import datetime, timezone
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from cli.formatters import format_pnl_markup, format_side_markup
from cli.theme import PANEL_KWARGS, TABLE_KWARGS

def get_statements_panel(trades: List[dict[str, Any]]) -> Panel:
    if not trades:
        empty_text = Text("\nNo recent statements/trades found.\n", style="warning", justify="center")
        return Panel(empty_text, title="[header]RECENT STATEMENTS (TRADES)[/header]", **PANEL_KWARGS) # type: ignore

    table = Table(
        show_header=True,
        header_style="header",
        expand=True,
        **TABLE_KWARGS
    )
    
    table.add_column("Time", justify="left")
    table.add_column("Symbol", justify="center")
    table.add_column("Side", justify="center")
    table.add_column("Price", justify="right")
    table.add_column("Qty", justify="right")
    table.add_column("Realized PnL", justify="right")
    table.add_column("Fee", justify="right")
    
    # Sort trades by time descending (newest first)
    sorted_trades = sorted(trades, key=lambda x: int(x.get("time", 0)), reverse=True)
    
    for trade in sorted_trades:
        # Time
        trade_time_ms = int(trade.get("time", 0))
        trade_dt = datetime.fromtimestamp(trade_time_ms / 1000.0, tz=timezone.utc)
        time_str = trade_dt.strftime('%m-%d %H:%M:%S')
        
        # Symbol
        symbol = trade.get("symbol", "N/A")
        
        # Side
        side = trade.get("side", "")
        side_str = format_side_markup(side)
        
        # Price and Qty
        price = float(trade.get("price", 0))
        qty = float(trade.get("qty", 0))
        
        # PnL
        pnl = float(trade.get("realizedPnl", 0))
        pnl_str = format_pnl_markup(pnl, precision=4)
        
        # Fee
        fee = float(trade.get("commission", 0))
        fee_asset = trade.get("commissionAsset", "")
        fee_str = f"{fee:.4f} {fee_asset}"
        
        table.add_row(
            time_str,
            symbol,
            side_str,
            f"{price:,.2f}",
            f"{qty}",
            pnl_str,
            fee_str
        )
        
    return Panel(table, title="[header]RECENT STATEMENTS (TRADES)[/header]", **PANEL_KWARGS) # type: ignore
