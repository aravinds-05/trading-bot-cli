"""
cli/formatters.py

Shared formatting utilities for PnL values, numeric styling, and
change-direction indicators used across multiple dashboard panels.
"""
from typing import Optional


def format_pnl(value: float, precision: int = 2) -> tuple[str, str, str]:
    """Return (style, sign_prefix, formatted_value) for a PnL number.

    >>> style, sign, text = format_pnl(12.5)
    >>> # style="value.positive", sign="+", text="+12.50"
    """
    style = "value.positive" if value >= 0 else "value.negative"
    sign = "+" if value >= 0 else ""
    text = f"{sign}{value:,.{precision}f}"
    return style, sign, text


def format_pnl_markup(value: float, suffix: str = "", precision: int = 2) -> str:
    """Return a Rich-markup string for a PnL value, ready for add_row().

    Example output: ``"[value.positive]+12.50 USDT[/value.positive]"``
    """
    style, _sign, text = format_pnl(value, precision)
    body = f"{text} {suffix}".rstrip()
    return f"[{style}]{body}[/{style}]"


def format_side_markup(side: str) -> str:
    """Return Rich-markup for a BUY/SELL or LONG/SHORT side string."""
    if side in ("BUY", "LONG"):
        return f"[value.positive]{side}[/value.positive]"
    return f"[value.negative]{side}[/value.negative]"


def format_change_arrow(change_pct: float) -> tuple[str, str, str]:
    """Return (style, arrow, sign) for a percentage change value."""
    style = "value.positive" if change_pct >= 0 else "value.negative"
    arrow = "\u25b2" if change_pct >= 0 else "\u25bc"
    sign = "+" if change_pct >= 0 else ""
    return style, arrow, sign


def fmt_num(value: Optional[str]) -> str:
    """Show a numeric string, or 'N/A' when it is missing or zero."""
    if value is None:
        return "N/A"
    try:
        return value if float(value) != 0 else "N/A"
    except (TypeError, ValueError):
        return str(value)
