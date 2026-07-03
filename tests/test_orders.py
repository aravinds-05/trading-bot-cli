"""Unit tests for bot.orders.OrderService, using a fake client (no network)."""

from __future__ import annotations

from typing import Any
import pytest

from bot.exceptions import APIError, TradingBotError
from bot.orders import OrderRequest, OrderService, OrderType, Side

class FakeClient:
    """A stand-in for BinanceFuturesTestnetClient that returns canned data."""

    def __init__(self, response: dict[str, Any] | None = None, error: Exception | None = None) -> None:
        self._response = response or {}
        self._error = error
        self.last_params: dict[str, Any] | None = None

    async def get_exchange_info(self) -> dict[str, Any]:
        return {
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "filters": [
                        {"filterType": "LOT_SIZE", "stepSize": "0.01"},
                        {"filterType": "PRICE_FILTER", "tickSize": "10.0"},
                    ]
                }
            ]
        }

    async def place_order(self, params: dict[str, Any]) -> dict[str, Any]:
        self.last_params = params
        if self._error:
            raise self._error
        return self._response

    async def get_order(self, symbol: str, order_id: int) -> dict[str, Any]:
        # Mirror the canned response; ensure a terminal status so MARKET-fill
        # polling resolves immediately in tests (no real network / sleeping).
        data = dict(self._response)
        data.setdefault("status", "FILLED")
        return data


def _market_request() -> OrderRequest:
    return OrderRequest(
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        quantity=0.01,
    )


def _limit_request() -> OrderRequest:
    return OrderRequest(
        symbol="BTCUSDT",
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        quantity=0.01,
        price=50000.0,
    )


class TestOrderService:
    @pytest.mark.asyncio
    async def test_market_order_builds_correct_params(self) -> None:
        client = FakeClient(response={"orderId": 1, "status": "FILLED"})
        service = OrderService(client)  # type: ignore[arg-type]

        await service.place_order(_market_request())

        assert client.last_params is not None
        assert client.last_params["type"] == "MARKET"
        assert "price" not in client.last_params

    @pytest.mark.asyncio
    async def test_limit_order_includes_price_and_time_in_force(self) -> None:
        client = FakeClient(response={"orderId": 2, "status": "NEW"})
        service = OrderService(client)  # type: ignore[arg-type]

        await service.place_order(_limit_request())

        assert client.last_params is not None
        assert client.last_params["type"] == "LIMIT"
        assert client.last_params["price"] == 50000.0
        assert client.last_params["timeInForce"] == "GTC"

    @pytest.mark.asyncio
    async def test_result_normalizes_response_fields(self) -> None:
        client = FakeClient(
            response={
                "orderId": 123,
                "status": "FILLED",
                "executedQty": "0.01",
                "avgPrice": "50000.10",
            }
        )
        service = OrderService(client)  # type: ignore[arg-type]

        result = await service.place_order(_market_request())

        assert result.order_id == 123
        assert result.status == "FILLED"
        assert result.executed_qty == "0.01"
        assert result.avg_price == "50000.10"

    @pytest.mark.asyncio
    async def test_known_error_propagates_unchanged(self) -> None:
        client = FakeClient(error=APIError("Invalid symbol.", 400))
        service = OrderService(client)  # type: ignore[arg-type]

        with pytest.raises(APIError):
            await service.place_order(_market_request())

    @pytest.mark.asyncio
    async def test_unknown_error_is_wrapped(self) -> None:
        client = FakeClient(error=RuntimeError("boom"))
        service = OrderService(client)  # type: ignore[arg-type]

        with pytest.raises(TradingBotError):
            await service.place_order(_market_request())
