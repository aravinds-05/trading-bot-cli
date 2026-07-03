"""
cli/panels.py
Contains standard panels like the Logo.
"""
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from cli.theme import PANEL_KWARGS
import pyfiglet

def get_logo_panel() -> Panel:
    ascii_logo = pyfiglet.figlet_format("TRADING\nBOT", font="cybermedium")
    logo = f"[bold green]{ascii_logo}[/bold green]"
    desc = """
[warning]Binance Futures Testnet Trading Bot[/warning]
[info]Fast. Reliable. Automated.[/info]
"""
    text = Text.from_markup(logo + "\n" + desc)
    return Panel(Align.center(text, vertical="middle"), **PANEL_KWARGS)  # type: ignore
