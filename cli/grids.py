"""
cli/grids.py

Factory for the label-value grid layout used by account, wallet, and
order panels.  Centralises the column definitions so every key-value
panel looks identical without repeating the same Table.grid() setup.
"""
from typing import Literal

from rich.table import Table

JustifyMethod = Literal["default", "left", "center", "right", "full"]


def create_label_value_grid(value_justify: JustifyMethod = "left") -> Table:
    """Return a two-column grid: label (left) + value (configurable)."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style="label", justify="left")
    table.add_column(justify=value_justify)
    return table
