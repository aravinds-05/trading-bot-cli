"""
cli/dashboard.py
Orchestrates the entire terminal UI dashboard and layout.
"""
from rich.layout import Layout
from rich.prompt import Prompt, Confirm, FloatPrompt, IntPrompt
import questionary

import asyncio
from typing import Optional

from bot.config import get_settings
from bot.client import BinanceFuturesTestnetClient
from bot.logging_config import configure_logging, get_logger
from bot.orders import OrderRequest, OrderResult, OrderType, Side
from bot.core import execute_order_with_client

from cli.theme import console
from cli.animations import show_spinner
from cli.statusbar import get_status_bar
from cli.components.hero import render_hero
from cli.account import get_account_summary_panel
from cli.wallet import get_wallet_summary_panel
from cli.positions import get_positions_panel
from cli.order import get_place_order_panel, get_last_order_panel
from cli.menu import get_menu_panel

logger = get_logger(__name__)

async def render_dashboard(client: BinanceFuturesTestnetClient, last_order: Optional[dict] = None, stats: Optional[dict] = None):
    # We will fetch data first so we know how many positions to render
    with console.status("[info]Fetching Live Exchange Data...[/info]", spinner="dots"):
        balances, positions, trades = await asyncio.gather(
            client.get_balance(),
            client.get_positions(),
            client.get_recent_trades(limit=5)
        )
        # Live prices are non-critical: never let a ticker hiccup break the dashboard.
        try:
            tickers = await client.get_24hr_tickers()
        except Exception:
            logger.warning("Could not fetch 24hr tickers; rendering prices panel without them.", exc_info=True)
            tickers = None
        
    from rich.table import Table
    from rich.console import Group
    
    # Header Grid
    header = Table.grid(expand=True)
    header.add_column(width=48)
    header.add_column(ratio=1)
    header.add_column(ratio=1)
    
    header.add_row(
        render_hero(),
        get_account_summary_panel(),
        get_wallet_summary_panel(balances)
    )
    
    # Live Market Prices (separate box)
    from cli.prices import get_prices_panel
    prices = get_prices_panel(tickers)

    # Body
    body = get_positions_panel(positions)
    
    # Statements
    from cli.statements import get_statements_panel
    statements = get_statements_panel(trades)
    
    # Status
    status = get_status_bar(latency_ms=42)
    
    dashboard = Group(header, prices, body, statements, status)
    
    console.clear()
    console.print(dashboard)
    
async def interactive_loop():
    settings = get_settings()
    configure_logging(settings.log_path)
    client = BinanceFuturesTestnetClient(settings)
    
    last_order = None
    stats = {"positions": 0, "orders": 0, "pnl": 0.0}
    
    try:
        while True:
            await render_dashboard(client, last_order, stats)
            
            choice = await questionary.select(
                "\nSelect an option:",
                choices=[
                    "1. Place New Order",
                    "2. Refresh Data",
                    "0. Exit"
                ],
                style=questionary.Style([('qmark', 'fg:cyan bold'), ('question', 'bold'), ('answer', 'fg:green bold'), ('pointer', 'fg:cyan bold'), ('highlighted', 'fg:cyan bold')])
            ).ask_async()
            
            if not choice or choice.startswith("0"):
                break
            elif choice.startswith("2"):
                continue # loop will re-render
            elif choice.startswith("1"):
                # Place Order flow
                console.print("\n[info]--- NEW ORDER ---[/info]")
                
                symbol = await questionary.select(
                    "Symbol:",
                    choices=["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
                ).ask_async()
                if not symbol: continue
                
                try:
                    live_price = await show_spinner(client.get_price(symbol), f"Fetching live price for {symbol}...")
                    console.print(f"\n[success]Current {symbol} Price:[/success] [bold]{live_price:,.2f} USDT[/bold]\n")
                except Exception as e:
                    console.print(f"\n[danger]Could not fetch live price for {symbol}: {e}[/danger]\n")
                
                side_str = await questionary.select(
                    "Side:",
                    choices=["BUY", "SELL"]
                ).ask_async()
                if not side_str: continue
                
                order_type_str = await questionary.select(
                    "Order Type:",
                    choices=["MARKET", "LIMIT"]
                ).ask_async()
                if not order_type_str: continue
                
                qty_str = await questionary.text("Quantity (e.g. 0.01):", default="0.01").ask_async()
                if not qty_str: continue
                try:
                    qty = float(qty_str)
                except ValueError:
                    console.print(f"\n[danger]'{qty_str}' is not a valid quantity. Please enter a number.[/danger]\n")
                    continue

                price = None
                if order_type_str == "LIMIT":
                    price_str = await questionary.text("Price (USDT):", default="60000").ask_async()
                    if not price_str: continue
                    try:
                        price = float(price_str)
                    except ValueError:
                        console.print(f"\n[danger]'{price_str}' is not a valid price. Please enter a number.[/danger]\n")
                        continue
                    
                confirm = await questionary.confirm("Confirm order?").ask_async()
                if confirm:
                    request = OrderRequest(
                        symbol=symbol,
                        side=Side.BUY if side_str == "BUY" else Side.SELL,
                        order_type=OrderType.MARKET if order_type_str == "MARKET" else OrderType.LIMIT,
                        quantity=qty,
                        price=price
                    )
                    
                    req_dict = {
                        "symbol": request.symbol,
                        "side": request.side.value,
                        "type": request.order_type.value,
                        "origQty": str(request.quantity),
                        "price": str(request.price) if request.price else "0",
                    }
                    
                    try:
                        result = await show_spinner(execute_order_with_client(client, request), "Sending Order...")
                        last_order = {
                            **req_dict,
                            "orderId": result.order_id,
                            "status": result.status
                        }
                        stats["orders"] += 1
                    except Exception as e:
                        logger.exception("Order failed")
                        last_order = {
                            **req_dict,
                            "status": "REJECTED",
                            "reason": str(e)
                        }
    finally:
        await client.close()

def run():
    asyncio.run(interactive_loop())
