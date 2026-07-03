"""
cli/account.py
Renders the Account Summary panel.
"""
from rich.panel import Panel
from rich.table import Table
from datetime import datetime, timezone
from cli.theme import PANEL_KWARGS

def get_account_summary_panel() -> Panel:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="label", justify="left")
    table.add_column(justify="left")
    
    table.add_row("Account Type", ": USD-M Futures (Testnet)")
    table.add_row("API Key", ": [success]Loaded[/success]")
    table.add_row("Server Time", f": [info]{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} (UTC)[/info]")
    table.add_row("Connection", ": [success]✔ Connected[/success]")
    
    return Panel(table, title="[header]ACCOUNT SUMMARY[/header]", **PANEL_KWARGS)  # type: ignore
