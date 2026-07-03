"""
cli/animations.py

Provides standardized loading animations and spinners.
Ensures that all async data fetching operations block the UI with a consistent
professional spinner before re-rendering the layout.
"""
from typing import Any, Coroutine
from rich.status import Status
import asyncio

from cli.theme import console

async def show_spinner(coro: Coroutine, message: str = "Loading...") -> Any:
    """
    Displays a cyan dots spinner while awaiting a coroutine.
    
    Args:
        coro: The async operation to await.
        message: The message to display next to the spinner.
        
    Returns:
        The result of the awaited coroutine.
    """
    with console.status(f"[info]{message}[/info]", spinner="dots"):
        result = await coro
    return result
