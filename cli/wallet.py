"""
cli/wallet.py
Renders the Wallet Summary panel.
"""
from rich.panel import Panel
from cli.formatters import format_pnl_markup
from cli.grids import create_label_value_grid
from cli.theme import PANEL_KWARGS

def get_wallet_summary_panel(balances: list[dict]) -> Panel:
    usdt_balance = 0.0
    usdt_available = 0.0
    usdt_pnl = 0.0
    
    for asset in balances:
        if asset.get("asset") == "USDT":
            usdt_balance = float(asset.get("balance", 0.0))
            usdt_available = float(asset.get("availableBalance", 0.0))
            usdt_pnl = float(asset.get("crossUnPnl", 0.0))
            break
            
    used_margin = usdt_balance - usdt_available
    equity = usdt_balance + usdt_pnl
    
    table = create_label_value_grid(value_justify="right")
    
    table.add_row("Total Balance", f": {usdt_balance:,.2f} USDT", style="value.positive" if usdt_balance > 0 else "value.neutral")
    table.add_row("Available Balance", f": {usdt_available:,.2f} USDT", style="value.positive" if usdt_available > 0 else "value.neutral")
    table.add_row("Used Margin", f": {used_margin:,.2f} USDT", style="warning")
    
    table.add_row("Unrealized PnL", f": {format_pnl_markup(usdt_pnl, 'USDT')}")
    
    table.add_row("Account Equity", f": {equity:,.2f} USDT", style="value.positive")
    
    return Panel(table, title="[header]WALLET SUMMARY (USDT)[/header]", **PANEL_KWARGS)  # type: ignore
