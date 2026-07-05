"""Unit tests for bot.core.execute_order_with_client."""

from __future__ import annotations

from typing import Any

import pytest

from bot.core import execute_order_with_client
from bot.orders import OrderRequest, OrderType, Side


class FakeClient:
    """Minimal stand-in for BinanceFuturesTestnetClient."""

    def __init__(self, response: dict[str, Any]) -> None:
        self._response = response
        self.placed_params: dict[str, Any] | None = None

    async def get_exchange_info(self) -> dict[str, Any]:
        return {
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "filters": [
                        {"filterType": "LOT_SIZE", "stepSize": "0.01"},
                        {"filterType": "PRICE_FILTER", "tickSize": "10.0"},
                    ],
                }
            ]
        }

    async def place_order(self, params: dict[str, Any]) -> dict[str, Any]:
        self.placed_params = params
        return self._response

    async def get_order(self, symbol: str, order_id: int) -> dict[str, Any]:
        data = dict(self._response)
        data.setdefault("status", "FILLED")
        return data


class TestExecuteOrderWithClient:
    @pytest.mark.asyncio
    async def test_returns_order_result(self) -> None:
        client = FakeClient(
            {"orderId": 42, "status": "FILLED", "executedQty": "0.01", "avgPrice": "50000.0"}
        )
        request = OrderRequest(
            symbol="BTCUSDT",
            side=Side.BUY,
            order_type=OrderType.MARKET,
            quantity=0.01,
        )
        result = await execute_order_with_client(client, request)  # type: ignore[arg-type]
        assert result.order_id == 42
        assert result.status == "FILLED"

    @pytest.mark.asyncio
    async def test_delegates_to_order_service(self) -> None:
        client = FakeClient({"orderId": 7, "status": "NEW"})
        request = OrderRequest(
            symbol="BTCUSDT",
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            quantity=0.01,
            price=50000.0,
        )
        result = await execute_order_with_client(client, request)  # type: ignore[arg-type]
        assert client.placed_params is not None
        assert client.placed_params["symbol"] == "BTCUSDT"
        assert result.order_id == 7
