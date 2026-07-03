"""
cli/components/hero.py
"""
from rich.console import Group
from rich.text import Text
from rich.align import Align

ASCII_LOGO = r"""
 _____ _____ _____ ____  _____ _____ _____ 
|_   _| __  |  _  |    \|     |   | |   __|
  | | |    -|     |  |  |-   -| | | |  |  |
  |_| |__|__|__|__|____/|_____|_|___|_____|
"""

def render_hero() -> Align:
    # 1. Exact ASCII art, no colors (white on black)
    logo_text = Text(ASCII_LOGO.strip("\n"), style="white on black")
    
    # 2. Exact text and spacing
    info_text = Text(style="white on black")
    info_text.append("\n\nTrading Bot\n")
    info_text.append("Binance Futures Testnet\n\n")
    info_text.append("Version   1.0.0\n")
    info_text.append("Author    Aravind S\n")
    info_text.append("Status    ● Live")
    
    # Group the components
    group = Group(logo_text, info_text)
    
    # 5. Adapt to width and center
    return Align.center(group, vertical="middle")
