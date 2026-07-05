from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, FloatPrompt, Confirm, IntPrompt

import asyncio
from pydantic import ValidationError

from bot.client import BinanceFuturesTestnetClient
from bot.config import get_settings
from bot.core import execute_order_with_client
from bot.exceptions import TradingBotError
from bot.logging_config import configure_logging, get_logger
from bot.orders import OrderRequest, OrderResult, OrderType, Side
from bot.validators import validate_symbol_format

app = typer.Typer(
    name="trading-bot",
    help="Place MARKET/LIMIT orders on Binance Futures Testnet (USDT-M).",
    add_completion=False,
)
console = Console()
logger = get_logger(__name__)


async def _execute_order(settings, request: OrderRequest) -> OrderResult:
    client = BinanceFuturesTestnetClient(settings)
    try:
        return await execute_order_with_client(client, request)
    finally:
        await client.close()


async def _get_balance(settings) -> list[dict]:
    client = BinanceFuturesTestnetClient(settings)
    try:
        return await client.get_balance()
    finally:
        await client.close()


async def _get_price(settings, symbol: str) -> float:
    client = BinanceFuturesTestnetClient(settings)
    try:
        return await client.get_price(symbol)
    finally:
        await client.close()


async def _get_all_prices(settings) -> dict[str, float]:
    client = BinanceFuturesTestnetClient(settings)
    try:
        return await client.get_all_prices()
    finally:
        await client.close()


@app.command()
def place_order(
    symbol: str = typer.Option(..., "--symbol", "-s", help="e.g. BTCUSDT"),
    side: str = typer.Option(..., "--side", help="BUY or SELL"),
    order_type: str = typer.Option(..., "--type", "-t", help="MARKET or LIMIT"),
    quantity: float = typer.Option(..., "--quantity", "-q"),
    price: Optional[float] = typer.Option(None, "--price", "-p", help="required for LIMIT"),
    yes: bool = typer.Option(False, "--yes", "-y", help="skip the confirmation prompt"),
) -> None:
    """Validate inputs, show a summary, and place an order on the testnet."""
    try:
        settings = get_settings()
        configure_logging(settings.log_path)

        request = OrderRequest(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )

        _print_request_summary(request)

        if not yes and not Confirm.ask("[bold yellow]Submit this order to the testnet?[/bold yellow]"):
            console.print("[yellow]Cancelled - no order sent.[/yellow]")
            raise typer.Exit(code=0)

        with console.status("[bold cyan]Executing order on Binance Testnet...[/bold cyan]", spinner="dots"):
            result = asyncio.run(_execute_order(settings, request))
            
        _print_result(result)

    except ValidationError as exc:
        logger.error("Validation error: %s", exc)
        console.print(Panel(str(exc), title="[bold red]Validation Error[/bold red]", border_style="red"))
        raise typer.Exit(code=1)
    except TradingBotError as exc:
        logger.error("Order failed: %s", exc)
        console.print(Panel(str(exc), title="[bold red]Order Failed[/bold red]", border_style="red"))
        raise typer.Exit(code=1)
    except Exception as exc:  # last-resort safety net, should rarely fire
        logger.exception("Unexpected error in CLI")
        console.print(Panel(f"Unexpected error: {exc}", title="[bold red]Error[/bold red]", border_style="red"))
        raise typer.Exit(code=1)


@app.command()
def interactive() -> None:
    from cli.dashboard import run
    run()

def _interactive_view_balance(settings) -> None:
    try:
        with console.status("[bold cyan]Fetching balances...[/bold cyan]", spinner="dots"):
            balances = asyncio.run(_get_balance(settings))
        
        table = Table(title="Wallet Balance", show_header=True)
        table.add_column("Asset", style="bold cyan")
        table.add_column("Balance")
        table.add_column("Available")
        
        for asset in balances:
            # Usually we only care about assets with non-zero balances
            if float(asset.get("balance", 0)) > 0:
                table.add_row(asset.get("asset"), asset.get("balance"), asset.get("availableBalance"))
                
        console.print(table)
    except Exception as e:
        console.print(Panel(f"Failed to fetch balance: {e}", title="[bold red]Error[/bold red]", border_style="red"))

def _ask_for_symbol(settings) -> str:
    console.print()
    
    try:
        with console.status("[bold cyan]Fetching live market prices...[/bold cyan]", spinner="dots"):
            prices = asyncio.run(_get_all_prices(settings))
            
        p_btc = prices.get("BTCUSDT", 0.0)
        p_eth = prices.get("ETHUSDT", 0.0)
        p_sol = prices.get("SOLUSDT", 0.0)
        p_bnb = prices.get("BNBUSDT", 0.0)
        
        console.print(f"  [1] BTCUSDT (${p_btc})")
        console.print(f"  [2] ETHUSDT (${p_eth})")
        console.print(f"  [3] SOLUSDT (${p_sol})")
        console.print(f"  [4] BNBUSDT (${p_bnb})")
    except Exception as e:
        console.print(f"[yellow]Could not fetch live prices: {e}[/yellow]")
        console.print("  [1] BTCUSDT")
        console.print("  [2] ETHUSDT")
        console.print("  [3] SOLUSDT")
        console.print("  [4] BNBUSDT")
        
    console.print("  [5] Enter Custom Symbol...")
    choice = IntPrompt.ask("[bold yellow]Select Symbol[/bold yellow]", choices=["1", "2", "3", "4", "5"], default=1)
    
    if choice == 1: return "BTCUSDT"
    if choice == 2: return "ETHUSDT"
    if choice == 3: return "SOLUSDT"
    if choice == 4: return "BNBUSDT"
    
    while True:
        raw = Prompt.ask("[bold yellow]Type Custom Symbol[/bold yellow] (e.g. XRPUSDT)")
        try:
            return validate_symbol_format(raw)
        except TradingBotError as exc:
            console.print(f"[yellow]{exc}[/yellow]")

def _interactive_view_price(settings) -> None:
    symbol = _ask_for_symbol(settings)
    try:
        with console.status(f"[bold cyan]Fetching live price for {symbol}...[/bold cyan]", spinner="dots"):
            price = asyncio.run(_get_price(settings, symbol))
        console.print(Panel(f"The live mark price of [bold green]{symbol}[/bold green] is [bold yellow]${price}[/bold yellow]", border_style="green"))
    except Exception as e:
        console.print(Panel(f"Failed to fetch price: {e}", title="[bold red]Error[/bold red]", border_style="red"))

def _interactive_place_order(settings) -> None:
    console.print(Panel("[bold cyan]Interactive Order Entry[/bold cyan]", border_style="cyan"))
    
    symbol = _ask_for_symbol(settings)
    console.print()
    
    side = Prompt.ask("[bold yellow]Side[/bold yellow]", choices=["BUY", "SELL"], default="BUY")
    order_type = Prompt.ask("[bold yellow]Order Type[/bold yellow]", choices=["MARKET", "LIMIT"], default="MARKET")
    quantity = FloatPrompt.ask("[bold yellow]Quantity[/bold yellow]", default=0.01)

    price: Optional[float] = None
    if order_type == "LIMIT":
        price = FloatPrompt.ask("[bold yellow]Price[/bold yellow]", default=65000.0)

    console.print()
    # We call place_order programmatically. Since place_order raises typer.Exit, we should intercept it
    # so we don't break the while True loop. 
    try:
        place_order(symbol=symbol, side=side, order_type=order_type, quantity=quantity, price=price, yes=False)
    except typer.Exit:
        pass


def _print_request_summary(request: OrderRequest) -> None:
    table = Table(title="Order Request Summary", show_header=False)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")
    table.add_row("Symbol", request.symbol)
    side_str = f"[green]{request.side.value}[/green]" if request.side == Side.BUY else f"[red]{request.side.value}[/red]"
    table.add_row("Side", side_str)
    table.add_row("Order Type", request.order_type.value)
    table.add_row("Quantity", str(request.quantity))
    table.add_row("Price", str(request.price) if request.price else "MARKET (n/a)")
    console.print(table)


def _fmt_num(value: Optional[str]) -> str:
    """Show a numeric string, or 'N/A' when it's missing or zero."""
    if value is None:
        return "N/A"
    try:
        return value if float(value) != 0 else "N/A"
    except (TypeError, ValueError):
        return str(value)


def _print_result(result: OrderResult) -> None:
    table = Table(title="Order Response", show_header=False)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")
    table.add_row("Order ID", str(result.order_id))
    table.add_row("Status", str(result.status))
    table.add_row("Executed Qty", str(result.executed_qty))
    table.add_row("Avg Price", _fmt_num(result.avg_price))
    console.print(table)
    console.print(Panel(
        f"Order {result.order_id} submitted (status: {result.status}).",
        title="[bold green]Success[/bold green]", border_style="green",
    ))


if __name__ == "__main__":
    app()
