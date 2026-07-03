"""
cli/menu.py
Renders the Trading Menu panel.
"""
from rich.panel import Panel
from rich.text import Text
from cli.theme import PANEL_KWARGS

def get_menu_panel() -> Panel:
    text = Text()
    text.append("\n1. Place New Order\n", style="label")
    text.append("2. Refresh Data\n", style="label")
    text.append("0. Exit\n", style="label")
    
    return Panel(text, title="[header]TRADING MENU[/header]", **PANEL_KWARGS)  # type: ignore
