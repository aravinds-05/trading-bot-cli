"""
cli/order.py
Renders the Place Order and Last Order Result panels.
"""
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.console import Group
from cli.theme import PANEL_KWARGS
import datetime

def get_place_order_panel() -> Panel:
    text = Text()
    text.append("Select 'Place New Order' from the menu to begin.\n\n", style="warning")
    text.append("Symbol (e.g., BTCUSDT): \n", style="label")
    text.append("Side (BUY/SELL): \n", style="label")
    text.append("Order Type (MARKET/LIMIT): \n", style="label")
    text.append("Quantity (BTC): \n", style="label")
    text.append("Price (USDT): \n", style="label")
    text.append("Leverage (1-125): \n", style="label")
    text.append("Reduce Only? (y/n): \n", style="label")
    
    return Panel(text, title="[header]PLACE NEW ORDER[/header]", **PANEL_KWARGS)  # type: ignore

from typing import Optional

def get_last_order_panel(last_order: Optional[dict] = None, stats: Optional[dict] = None) -> Panel:
    if not last_order:
        order_text = Text("\nNo orders placed in this session.\n", style="warning", justify="center")
        order_group = Panel(order_text, border_style="panel.border")
    else:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="label", justify="left")
        table.add_column(justify="left")
        
        status = last_order.get("status", "NEW")
        style = "success" if status in ["FILLED", "NEW"] else "danger"
        table.add_row("Order ID", f": {last_order.get('orderId', 'N/A')}")
        table.add_row("Symbol", f": [{style}]{last_order.get('symbol', 'N/A')}[/{style}]")
        table.add_row("Side", f": [{style}]{last_order.get('side', 'N/A')}[/{style}]")
        table.add_row("Type", f": [{style}]{last_order.get('type', 'N/A')}[/{style}]")
        table.add_row("Quantity", f": {last_order.get('origQty', '0')}")
        table.add_row("Price", f": {last_order.get('price', '0')} USDT")
        table.add_row("Status", f": {status}")
        if status == "REJECTED" and "reason" in last_order:
            wrapped_reason = Text(last_order['reason'], style="danger", overflow="fold")
            table.add_row("Reason", f": ")
            table.add_row("", wrapped_reason)
            
        table.add_row("Time", f": {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        
        title = "✔ ORDER PLACED SUCCESSFULLY!" if style == "success" else "✖ ORDER FAILED"
        order_group = Panel(table, title=f"[{style}]{title}[/{style}]", title_align="left", border_style="panel.border")

    stats = stats or {"positions": 0, "orders": 0, "pnl": 0.0}
    stats_table = Table.grid(padding=(0, 2))
    stats_table.add_column(style="label", justify="left")
    stats_table.add_column(justify="left")
    stats_table.add_row("Total Positions", f": [info]{stats.get('positions', 0)}[/info]")
    stats_table.add_row("Open Orders", f": [info]{stats.get('orders', 0)}[/info]")
    
    pnl = float(stats.get('pnl', 0.0))
    p_style = "value.positive" if pnl >= 0 else "value.negative"
    p_sign = "+" if pnl >= 0 else ""
    stats_table.add_row("Total PnL (Today)", f": [{p_style}]{p_sign}{pnl:.2f} USDT[/{p_style}]")
    
    stats_group = Panel(stats_table, title="[info]QUICK STATS[/info]", title_align="left", border_style="panel.border")
    
    return Panel(Group(order_group, stats_group), title="[header]LAST ORDER RESULT[/header]", **PANEL_KWARGS)  # type: ignore
