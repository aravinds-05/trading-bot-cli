"""
cli/positions.py
Renders the Open Positions table.
"""
from rich.panel import Panel
from rich.console import Group
from cli.formatters import format_pnl, format_pnl_markup
from cli.tables import create_base_table
from cli.theme import PANEL_KWARGS

def get_positions_panel(positions: list[dict]) -> Panel:
    table = create_base_table()
    table.add_column("#", justify="center")
    table.add_column("Symbol", justify="center")
    table.add_column("Side", justify="center")
    table.add_column("Size", justify="right")
    table.add_column("Entry Price", justify="right")
    table.add_column("Mark Price", justify="right")
    table.add_column("Unrealized PnL", justify="right")
    table.add_column("ROE", justify="right")
    table.add_column("Margin", justify="right")
    table.add_column("Leverage", justify="center")
    
    total_pnl = 0.0
    active_positions = [p for p in positions if float(p.get("positionAmt", 0.0)) != 0.0]
    
    if not active_positions:
        table.add_row("", "", "", "", "[warning]No Open Positions[/warning]", "", "", "", "", "")
    else:
        for idx, pos in enumerate(active_positions, 1):
            amt = float(pos.get("positionAmt", 0.0))
            side = "[success]LONG[/success]" if amt > 0 else "[danger]SHORT[/danger]"
            pnl = float(pos.get("unRealizedProfit", 0.0))
            total_pnl += pnl
            
            pnl_style, pnl_sign, _ = format_pnl(pnl)
            
            table.add_row(
                str(idx),
                pos.get("symbol"),
                side,
                f"{abs(amt):.4f}",
                f"{float(pos.get('entryPrice', 0.0)):.2f}",
                f"{float(pos.get('markPrice', 0.0)):.2f}",
                format_pnl_markup(pnl, "USDT"),
                f"[{pnl_style}]{pnl_sign}0.00%[/{pnl_style}]",  # Mock ROE for UI fidelity
                f"{float(pos.get('isolatedMargin', 0.0)) or 0.0:,.2f} USDT",
                f"[warning]{pos.get('leverage', '1')}x[/warning]"
            )
            
    footer = f"\nTotal Unrealized PnL: {format_pnl_markup(total_pnl, 'USDT')}"
    
    return Panel(Group(table, footer), title="[header]YOUR POSITIONS (CURRENTLY OPEN)[/header]", **PANEL_KWARGS)  # type: ignore
