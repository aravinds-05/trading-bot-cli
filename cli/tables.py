"""
cli/tables.py
Provides a consistent base table configuration.
"""
from rich.table import Table

def create_base_table() -> Table:
    table = Table(
        show_header=True,
        header_style="header",
        border_style="panel.border",
        padding=(0, 2),
        expand=True
    )
    return table
