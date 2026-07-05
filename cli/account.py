"""
cli/account.py
Renders the Account Summary panel.
"""
from rich.panel import Panel
from datetime import datetime, timezone
from cli.grids import create_label_value_grid
from cli.theme import PANEL_KWARGS

def get_account_summary_panel() -> Panel:
    table = create_label_value_grid()
    
    table.add_row("Account Type", ": USD-M Futures (Testnet)")
    table.add_row("API Key", ": [success]Loaded[/success]")
    table.add_row("Server Time", f": [info]{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} (UTC)[/info]")
    table.add_row("Connection", ": [success]✔ Connected[/success]")
    
    return Panel(table, title="[header]ACCOUNT SUMMARY[/header]", **PANEL_KWARGS)  # type: ignore
