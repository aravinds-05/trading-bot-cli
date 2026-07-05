"""Unit tests for CLI presentation modules – account, wallet, positions,
order, statements, panels, tables, statusbar, menu, hero, animations.

These modules produce Rich renderables (Panel, Table, etc.). The tests
verify they return the correct types and don't crash on representative
input data, without asserting on exact rendered strings.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from rich.align import Align
from rich.panel import Panel
from rich.table import Table

from cli.account import get_account_summary_panel
from cli.animations import show_spinner
from cli.components.hero import render_hero
from cli.menu import get_menu_panel
from cli.order import get_last_order_panel, get_place_order_panel
from cli.panels import get_logo_panel
from cli.positions import get_positions_panel
from cli.statements import get_statements_panel
from cli.statusbar import get_status_bar
from cli.tables import create_base_table
from cli.wallet import get_wallet_summary_panel


# ── tables ────────────────────────────────────────────────────────────

class TestCreateBaseTable:
    def test_returns_table(self) -> None:
        t = create_base_table()
        assert isinstance(t, Table)

    def test_has_header(self) -> None:
        t = create_base_table()
        assert t.show_header is True


# ── account ───────────────────────────────────────────────────────────

class TestAccountSummaryPanel:
    def test_returns_panel(self) -> None:
        panel = get_account_summary_panel()
        assert isinstance(panel, Panel)


# ── menu ──────────────────────────────────────────────────────────────

class TestMenuPanel:
    def test_returns_panel(self) -> None:
        panel = get_menu_panel()
        assert isinstance(panel, Panel)


# ── statusbar ─────────────────────────────────────────────────────────

class TestStatusBar:
    def test_returns_panel(self) -> None:
        panel = get_status_bar()
        assert isinstance(panel, Panel)

    def test_custom_latency(self) -> None:
        panel = get_status_bar(latency_ms=100)
        assert isinstance(panel, Panel)


# ── panels (logo) ────────────────────────────────────────────────────

class TestLogoPanel:
    def test_returns_panel(self) -> None:
        panel = get_logo_panel()
        assert isinstance(panel, Panel)


# ── hero ──────────────────────────────────────────────────────────────

class TestHero:
    def test_returns_align(self) -> None:
        hero = render_hero()
        assert isinstance(hero, Align)


# ── wallet ────────────────────────────────────────────────────────────

class TestWalletPanel:
    def test_with_usdt_balance(self) -> None:
        balances: list[dict[str, Any]] = [
            {"asset": "USDT", "balance": "10000.0", "availableBalance": "8000.0", "crossUnPnl": "50.0"},
        ]
        panel = get_wallet_summary_panel(balances)
        assert isinstance(panel, Panel)

    def test_empty_balances(self) -> None:
        panel = get_wallet_summary_panel([])
        assert isinstance(panel, Panel)

    def test_non_usdt_only(self) -> None:
        balances: list[dict[str, Any]] = [{"asset": "BTC", "balance": "1.0"}]
        panel = get_wallet_summary_panel(balances)
        assert isinstance(panel, Panel)

    def test_negative_pnl(self) -> None:
        balances: list[dict[str, Any]] = [
            {"asset": "USDT", "balance": "5000.0", "availableBalance": "3000.0", "crossUnPnl": "-200.0"},
        ]
        panel = get_wallet_summary_panel(balances)
        assert isinstance(panel, Panel)


# ── positions ─────────────────────────────────────────────────────────

class TestPositionsPanel:
    def test_no_positions(self) -> None:
        panel = get_positions_panel([])
        assert isinstance(panel, Panel)

    def test_long_position(self) -> None:
        positions: list[dict[str, Any]] = [
            {
                "symbol": "BTCUSDT",
                "positionAmt": "0.01",
                "entryPrice": "60000.0",
                "markPrice": "61000.0",
                "unRealizedProfit": "10.0",
                "isolatedMargin": "100.0",
                "leverage": "10",
            }
        ]
        panel = get_positions_panel(positions)
        assert isinstance(panel, Panel)

    def test_short_position(self) -> None:
        positions: list[dict[str, Any]] = [
            {
                "symbol": "ETHUSDT",
                "positionAmt": "-0.5",
                "entryPrice": "1800.0",
                "markPrice": "1750.0",
                "unRealizedProfit": "25.0",
                "leverage": "5",
            }
        ]
        panel = get_positions_panel(positions)
        assert isinstance(panel, Panel)

    def test_mixed_positions(self) -> None:
        positions: list[dict[str, Any]] = [
            {"symbol": "BTCUSDT", "positionAmt": "0.01", "unRealizedProfit": "10.0", "leverage": "10"},
            {"symbol": "ETHUSDT", "positionAmt": "-0.5", "unRealizedProfit": "-5.0", "leverage": "5"},
            {"symbol": "SOLUSDT", "positionAmt": "0", "unRealizedProfit": "0"},  # inactive
        ]
        panel = get_positions_panel(positions)
        assert isinstance(panel, Panel)


# ── order ─────────────────────────────────────────────────────────────

class TestPlaceOrderPanel:
    def test_returns_panel(self) -> None:
        panel = get_place_order_panel()
        assert isinstance(panel, Panel)


class TestLastOrderPanel:
    def test_no_order(self) -> None:
        panel = get_last_order_panel()
        assert isinstance(panel, Panel)

    def test_successful_order(self) -> None:
        order: dict[str, Any] = {
            "orderId": 123,
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "origQty": "0.01",
            "price": "60000",
            "status": "FILLED",
        }
        panel = get_last_order_panel(last_order=order)
        assert isinstance(panel, Panel)

    def test_rejected_order(self) -> None:
        order: dict[str, Any] = {
            "orderId": 456,
            "symbol": "BTCUSDT",
            "side": "SELL",
            "type": "LIMIT",
            "origQty": "0.01",
            "price": "50000",
            "status": "REJECTED",
            "reason": "Insufficient balance for this order",
        }
        panel = get_last_order_panel(last_order=order)
        assert isinstance(panel, Panel)

    def test_with_stats(self) -> None:
        stats: dict[str, Any] = {"positions": 2, "orders": 5, "pnl": -12.34}
        panel = get_last_order_panel(stats=stats)
        assert isinstance(panel, Panel)

    def test_with_positive_pnl_stats(self) -> None:
        stats: dict[str, Any] = {"positions": 1, "orders": 3, "pnl": 99.99}
        panel = get_last_order_panel(stats=stats)
        assert isinstance(panel, Panel)


# ── statements ────────────────────────────────────────────────────────

class TestStatementsPanel:
    def test_empty_trades(self) -> None:
        panel = get_statements_panel([])
        assert isinstance(panel, Panel)

    def test_with_trades(self) -> None:
        trades: list[dict[str, Any]] = [
            {
                "time": 1700000000000,
                "symbol": "BTCUSDT",
                "side": "BUY",
                "price": "61000.0",
                "qty": "0.01",
                "realizedPnl": "5.1234",
                "commission": "0.0061",
                "commissionAsset": "USDT",
            },
            {
                "time": 1700000100000,
                "symbol": "ETHUSDT",
                "side": "SELL",
                "price": "1800.0",
                "qty": "0.5",
                "realizedPnl": "-2.5",
                "commission": "0.009",
                "commissionAsset": "USDT",
            },
        ]
        panel = get_statements_panel(trades)
        assert isinstance(panel, Panel)

    def test_trade_with_zero_pnl(self) -> None:
        trades: list[dict[str, Any]] = [
            {
                "time": 1700000000000,
                "symbol": "SOLUSDT",
                "side": "BUY",
                "price": "100.0",
                "qty": "1",
                "realizedPnl": "0",
                "commission": "0.01",
                "commissionAsset": "USDT",
            }
        ]
        panel = get_statements_panel(trades)
        assert isinstance(panel, Panel)


# ── animations ────────────────────────────────────────────────────────

class TestShowSpinner:
    @pytest.mark.asyncio
    async def test_returns_coroutine_result(self) -> None:
        async def dummy() -> int:
            return 42

        result = await show_spinner(dummy(), message="Testing...")
        assert result == 42
